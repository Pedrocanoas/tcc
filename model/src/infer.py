"""Gera a descrição de condição de um livro a partir de uma ou mais fotos.

Uso:
    .venv/Scripts/python.exe -m src.infer caminho/para/foto1.jpg caminho/para/foto2.jpg
    .venv/Scripts/python.exe -m src.infer --json caminho/para/foto1.jpg  # p/ consumo por outro processo (ex: backend/)
"""

import argparse
import json
import sys
from pathlib import Path

import torch
from PIL import Image
from transformers import BlipForConditionalGeneration, BlipProcessor

from src.config import BASE_MODEL, CHECKPOINTS_DIR
from src.prompt import build_prefix


def load_model(checkpoint: str | Path, device: torch.device):
    processor = BlipProcessor.from_pretrained(checkpoint)
    model = BlipForConditionalGeneration.from_pretrained(checkpoint).to(device)
    model.eval()
    return processor, model


def generate_caption(
    processor,
    model,
    image_path: Path,
    device: torch.device,
    max_new_tokens: int = 128,
    prefix: str | None = None,
) -> str:
    image = Image.open(image_path).convert("RGB")
    if prefix:
        inputs = processor(images=image, text=prefix, return_tensors="pt").to(device)
    else:
        inputs = processor(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        output_ids = model.generate(**inputs, max_new_tokens=max_new_tokens)
    return processor.decode(output_ids[0], skip_special_tokens=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("--checkpoint", type=Path, default=CHECKPOINTS_DIR / "best")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--max-new-tokens", type=int, default=128)
    parser.add_argument("--capa", choices=["mole", "dura"], help="condiciona a legenda ao tipo de capa já conhecido")
    parser.add_argument(
        "--condicao",
        choices=["novo", "seminovo", "usado", "antigo"],
        help="condiciona a legenda à condição já conhecida",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="imprime só um JSON (lista de {image, caption}) no stdout, p/ outro processo consumir",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    checkpoint = args.checkpoint if args.checkpoint.exists() else BASE_MODEL
    if checkpoint == BASE_MODEL:
        print(
            f"[aviso] nenhum checkpoint treinado em {args.checkpoint}, usando o modelo base ({BASE_MODEL})",
            file=sys.stderr,
        )

    device = torch.device(args.device)
    processor, model = load_model(checkpoint, device)
    prefix = build_prefix(args.capa, args.condicao)

    results = []
    for image_path in args.images:
        caption = generate_caption(
            processor, model, image_path, device, max_new_tokens=args.max_new_tokens, prefix=prefix
        )
        results.append({"image": str(image_path), "caption": caption})
        if not args.json:
            print(f"{image_path}: {caption}")

    if args.json:
        print(json.dumps(results, ensure_ascii=False))


if __name__ == "__main__":
    main()
