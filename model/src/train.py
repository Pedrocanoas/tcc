"""Fine-tuning do BLIP para gerar a descrição de condição do livro a partir das fotos.

O encoder de visão fica congelado por padrão (dataset pequeno, ~740 exemplos
vindos de 401 livros) — só o decoder de texto é treinado. Use --no-freeze-vision
para destravar o encoder também.

Uso:
    .venv/Scripts/python.exe -m src.train --epochs 5 --batch-size 4
"""

import argparse
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from transformers import BlipForConditionalGeneration, BlipProcessor

from src.config import BASE_MODEL, CHECKPOINTS_DIR, TRAIN_MANIFEST, VAL_MANIFEST
from src.dataset import BookConditionDataset
from src.infer import needs_pos_interpolation


def evaluate(model, loader: DataLoader, device: torch.device, interpolate: bool) -> float:
    model.eval()
    total_loss, n = 0.0, 0
    with torch.no_grad():
        for batch in loader:
            batch = {key: value.to(device) for key, value in batch.items()}
            outputs = model(**batch, interpolate_pos_encoding=interpolate)
            batch_size = batch["pixel_values"].size(0)
            total_loss += outputs.loss.item() * batch_size
            n += batch_size
    return total_loss / max(n, 1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--lr", type=float, default=5e-5)
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--freeze-vision", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument(
        "--unfreeze-vision-layers",
        type=int,
        default=0,
        help=(
            "com o encoder congelado, destrava só as N últimas camadas dele (+ tabela de posições e "
            "post_layernorm) — destravar o encoder inteiro já deu mode collapse (ver model/README.md)"
        ),
    )
    parser.add_argument(
        "--vision-lr",
        type=float,
        default=None,
        help="learning rate dos parâmetros treináveis do encoder (padrão = --lr)",
    )
    parser.add_argument(
        "--image-size",
        type=int,
        default=None,
        help="resolução de entrada (quadrada); padrão = 384 do BLIP base. Ex.: 576 (ver model/README.md)",
    )
    parser.add_argument("--limit-train", type=int, default=None, help="usa só os N primeiros exemplos (debug)")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--output-dir", type=Path, default=CHECKPOINTS_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    device = torch.device(args.device)

    processor = BlipProcessor.from_pretrained(BASE_MODEL)
    model = BlipForConditionalGeneration.from_pretrained(BASE_MODEL).to(device)
    if args.image_size:
        processor.image_processor.size = {"height": args.image_size, "width": args.image_size}
    interpolate = needs_pos_interpolation(processor, model)
    print(f"resolução de entrada: {processor.image_processor.size} (interpolate_pos_encoding={interpolate})")

    if args.freeze_vision:
        for param in model.vision_model.parameters():
            param.requires_grad = False
        if args.unfreeze_vision_layers:
            vision = model.vision_model
            # a tabela de posições entra junto: com --image-size ela é interpolada e
            # precisa poder se ajustar ao novo grid de patches
            unfrozen = [vision.embeddings.position_embedding, *vision.post_layernorm.parameters()]
            for layer in vision.encoder.layers[-args.unfreeze_vision_layers :]:
                unfrozen += list(layer.parameters())
            for param in unfrozen:
                param.requires_grad = True

    train_ds = BookConditionDataset(TRAIN_MANIFEST, processor, args.max_length)
    val_ds = BookConditionDataset(VAL_MANIFEST, processor, args.max_length)
    if args.limit_train:
        train_ds.examples = train_ds.examples[: args.limit_train]

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size)

    vision_param_ids = {id(p) for p in model.vision_model.parameters()}
    vision_params = [p for p in model.vision_model.parameters() if p.requires_grad]
    other_params = [p for p in model.parameters() if p.requires_grad and id(p) not in vision_param_ids]
    vision_lr = args.vision_lr if args.vision_lr is not None else args.lr
    param_groups = [{"params": other_params, "lr": args.lr}]
    if vision_params:
        param_groups.append({"params": vision_params, "lr": vision_lr})
    print(
        f"parâmetros treináveis: decoder/resto={sum(p.numel() for p in other_params) / 1e6:.1f}M (lr={args.lr}), "
        f"encoder={sum(p.numel() for p in vision_params) / 1e6:.1f}M (lr={vision_lr})"
    )
    optimizer = torch.optim.AdamW(param_groups, lr=args.lr)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    best_val_loss = float("inf")

    for epoch in range(1, args.epochs + 1):
        model.train()
        running_loss = 0.0
        for step, batch in enumerate(train_loader, start=1):
            batch = {key: value.to(device) for key, value in batch.items()}
            outputs = model(**batch, interpolate_pos_encoding=interpolate)
            loss = outputs.loss

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            running_loss += loss.item()
            print(f"epoch {epoch} step {step}/{len(train_loader)} loss {loss.item():.4f}")

        val_loss = evaluate(model, val_loader, device, interpolate) if len(val_ds) else float("nan")
        train_loss = running_loss / max(len(train_loader), 1)
        print(f"== epoch {epoch}: train_loss={train_loss:.4f} val_loss={val_loss:.4f} ==")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            save_dir = args.output_dir / "best"
            model.save_pretrained(save_dir)
            processor.save_pretrained(save_dir)
            print(f"novo melhor checkpoint salvo em {save_dir}")

    final_dir = args.output_dir / "last"
    model.save_pretrained(final_dir)
    processor.save_pretrained(final_dir)
    print(f"checkpoint final salvo em {final_dir}")


if __name__ == "__main__":
    main()
