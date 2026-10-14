"""Compara, lado a lado, o BLIP "cru" (sem fine-tuning, direto do Hugging
Face) com o checkpoint fine-tuned, nas mesmas fotos — evidência de por que o
fine-tuning foi necessário (ver model/README.md).

Uso:
    .venv/Scripts/python.exe -m src.compare_base_vs_finetuned foto1.jpg foto2.jpg
    .venv/Scripts/python.exe -m src.compare_base_vs_finetuned --checkpoint model/checkpoints/best foto1.jpg
"""

import argparse
from pathlib import Path

import torch
from transformers import BlipForConditionalGeneration, BlipProcessor

from src.config import BASE_MODEL, CHECKPOINTS_DIR
from src.infer import generate_caption, load_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("--checkpoint", type=Path, default=CHECKPOINTS_DIR / "best")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    device = torch.device(args.device)

    print(f"Carregando modelo BASE (sem fine-tuning): {BASE_MODEL}")
    processor_base = BlipProcessor.from_pretrained(BASE_MODEL)
    model_base = BlipForConditionalGeneration.from_pretrained(BASE_MODEL).to(device)
    model_base.eval()

    print(f"Carregando checkpoint FINE-TUNED: {args.checkpoint}")
    processor_ft, model_ft = load_model(args.checkpoint, device)

    for image_path in args.images:
        caption_base = generate_caption(processor_base, model_base, image_path, device, max_new_tokens=64)
        caption_ft = generate_caption(processor_ft, model_ft, image_path, device, max_new_tokens=64)
        print(f"\n=== {image_path} ===")
        print(f"SEM fine-tuning : {caption_base}")
        print(f"COM fine-tuning : {caption_ft}")


if __name__ == "__main__":
    main()
