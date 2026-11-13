"""Experimento: fine-tuning do BLIP-2 (OPT-2.7b) nos mesmos dados do BLIP e
avaliação no mesmo split de validação, com a mesma métrica (src.evaluate).

Só roda de verdade em GPU (Kaggle): o modelo tem ~3,8 bilhões de parâmetros.
O encoder de visão e o modelo de linguagem ficam congelados em fp16; treinam
o Q-Former, a projeção e adaptadores LoRA no modelo de linguagem (o OPT foi
treinado quase só em inglês — sem LoRA ele não aprende a escrever em
português no estilo das legendas). Treino e avaliação ficam no mesmo script
porque o checkpoint inteiro é grande demais pra baixar e rodar localmente.

Uso:
    python -m src.blip2_experiment --epochs 5 --batch-size 4
"""

import argparse
import json
import time
from pathlib import Path

import peft
import torch
import transformers
from peft import LoraConfig, get_peft_model
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from transformers import Blip2ForConditionalGeneration, Blip2Processor

from src.config import CHECKPOINTS_DIR, DATASET_RAW_DIR, TRAIN_MANIFEST, VAL_MANIFEST
from src.evaluate import load_examples
from src.metrics import similarity, summary

BLIP2_MODEL = "Salesforce/blip2-opt-2.7b"


class CaptionDataset(Dataset):
    def __init__(self, manifest_path: Path):
        self.examples = load_all(manifest_path)

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, idx: int) -> tuple[Image.Image, str]:
        example = self.examples[idx]
        return Image.open(DATASET_RAW_DIR / example["image"]).convert("RGB"), example["caption"]


def load_all(manifest_path: Path) -> list[dict]:
    text = Path(manifest_path).read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def make_collate(processor, model, max_length: int):
    tokenizer = processor.tokenizer
    image_token_id = model.config.image_token_id
    num_query_tokens = model.config.num_query_tokens

    def collate(batch):
        images, captions = zip(*batch)
        # o tokenizador do OPT não põe EOS no fim — sem isso o modelo nunca aprende a parar
        encoding = processor(
            images=list(images),
            text=[caption + tokenizer.eos_token for caption in captions],
            padding=True,
            truncation=True,
            max_length=max_length + num_query_tokens,  # o processor desconta os tokens de imagem
            return_tensors="pt",
        )
        labels = encoding["input_ids"].clone()
        labels[encoding["attention_mask"] == 0] = -100
        labels[labels == image_token_id] = -100
        encoding["labels"] = labels
        return dict(encoding)

    return collate


def trainable_state(model) -> dict:
    return {name: param.detach().cpu().clone() for name, param in model.named_parameters() if param.requires_grad}


def run_epoch(model, loader, device, use_amp, optimizer=None, scaler=None, grad_accum: int = 1, log_every: int = 50):
    training = optimizer is not None
    model.train(training)
    total_loss, n = 0.0, 0
    for step, batch in enumerate(loader, start=1):
        batch = {key: value.to(device) for key, value in batch.items()}
        with torch.set_grad_enabled(training), torch.autocast(device.type, dtype=torch.float16, enabled=use_amp):
            loss = model(**batch).loss
        if training:
            scaler.scale(loss / grad_accum).backward()
            if step % grad_accum == 0 or step == len(loader):
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad()
            if step % log_every == 0:
                print(f"  step {step}/{len(loader)} loss {loss.item():.4f}", flush=True)
        batch_size = batch["pixel_values"].size(0)
        total_loss += loss.item() * batch_size
        n += batch_size
    return total_loss / max(n, 1)


def generate_caption(processor, model, image_path: Path, device, use_amp, max_new_tokens: int, num_beams: int) -> str:
    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt").to(device)
    with torch.no_grad(), torch.autocast(device.type, dtype=torch.float16, enabled=use_amp):
        output_ids = model.generate(**inputs, max_new_tokens=max_new_tokens, num_beams=num_beams)
    return processor.batch_decode(output_ids, skip_special_tokens=True)[0].strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=BLIP2_MODEL)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--grad-accum", type=int, default=2, help="batch efetivo = batch-size × grad-accum")
    parser.add_argument("--lr", type=float, default=1e-4, help="learning rate dos adaptadores LoRA")
    parser.add_argument("--qformer-lr", type=float, default=2e-5, help="learning rate do Q-Former e da projeção")
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=128, help="tokens de texto (cobre ~91%% das legendas)")
    parser.add_argument("--num-beams", type=int, default=4)
    parser.add_argument("--num-workers", type=int, default=2)
    parser.add_argument("--limit-train", type=int, default=None, help="usa só os N primeiros exemplos (debug)")
    parser.add_argument("--limit-eval", type=int, default=None, help="avalia só os N primeiros livros (debug)")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--output-dir", type=Path, default=CHECKPOINTS_DIR / "blip2")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    device = torch.device(args.device)
    use_amp = device.type == "cuda"

    print(f"versões: torch={torch.__version__} transformers={transformers.__version__} peft={peft.__version__}", flush=True)
    processor = Blip2Processor.from_pretrained(args.model)
    model = Blip2ForConditionalGeneration.from_pretrained(
        args.model, torch_dtype=torch.float16 if use_amp else torch.float32
    )
    for param in model.parameters():
        param.requires_grad = False

    model.language_model = get_peft_model(
        model.language_model,
        LoraConfig(r=args.lora_r, lora_alpha=2 * args.lora_r, lora_dropout=0.05, target_modules=["q_proj", "v_proj"]),
    )
    # partes treináveis ficam em fp32 (o autocast cuida da conversão); fp16 puro não treina bem
    model.qformer.float()
    model.language_projection.float()
    model.query_tokens.data = model.query_tokens.data.float()
    qformer_params = [*model.qformer.parameters(), *model.language_projection.parameters(), model.query_tokens]
    for param in qformer_params:
        param.requires_grad = True
    lora_params = [p for p in model.language_model.parameters() if p.requires_grad]
    model.to(device)
    print(
        f"parâmetros treináveis: Q-Former+projeção={sum(p.numel() for p in qformer_params) / 1e6:.1f}M "
        f"(lr={args.qformer_lr}), LoRA={sum(p.numel() for p in lora_params) / 1e6:.1f}M (lr={args.lr}); "
        f"total do modelo={sum(p.numel() for p in model.parameters()) / 1e6:.0f}M",
        flush=True,
    )

    train_ds, val_ds = CaptionDataset(TRAIN_MANIFEST), CaptionDataset(VAL_MANIFEST)
    if args.limit_train:
        train_ds.examples = train_ds.examples[: args.limit_train]
    collate = make_collate(processor, model, args.max_length)
    loader_kwargs = {"batch_size": args.batch_size, "collate_fn": collate, "num_workers": args.num_workers}
    train_loader = DataLoader(train_ds, shuffle=True, **loader_kwargs)
    val_loader = DataLoader(val_ds, **loader_kwargs)

    optimizer = torch.optim.AdamW(
        [{"params": lora_params, "lr": args.lr}, {"params": qformer_params, "lr": args.qformer_lr}]
    )
    scaler = torch.amp.GradScaler(device.type, enabled=use_amp)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    best_path = args.output_dir / "best_trainable.pt"
    best_val_loss = float("inf")
    for epoch in range(1, args.epochs + 1):
        started = time.time()
        train_loss = run_epoch(model, train_loader, device, use_amp, optimizer, scaler, args.grad_accum)
        val_loss = run_epoch(model, val_loader, device, use_amp)
        print(
            f"== epoch {epoch}: train_loss={train_loss:.4f} val_loss={val_loss:.4f} ({time.time() - started:.0f}s) ==",
            flush=True,
        )
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(trainable_state(model), best_path)
            print(f"novo melhor checkpoint (só os pesos treináveis) salvo em {best_path}", flush=True)

    model.load_state_dict(torch.load(best_path), strict=False)
    model.eval()

    examples = load_examples(VAL_MANIFEST)
    if args.limit_eval:
        examples = examples[: args.limit_eval]
    pairs = []
    for ex in examples:
        predicted = generate_caption(
            processor, model, DATASET_RAW_DIR / ex["image"], device, use_amp, args.max_length, args.num_beams
        )
        pairs.append((predicted, ex["caption"]))
        print(f"\n=== {ex['livro_id']} (similaridade: {similarity(predicted, ex['caption']):.2f}) ===", flush=True)
        print(f"esperado : {ex['caption']}")
        print(f"gerado   : {predicted}", flush=True)
    if pairs:
        print("\n" + summary(pairs), flush=True)


if __name__ == "__main__":
    main()
