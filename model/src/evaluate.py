"""Compara as legendas geradas pelo checkpoint treinado com as legendas originais
do vendedor, para livros que o modelo não viu no treino (conjunto de validação).

Uso:
    .venv/Scripts/python.exe -m src.evaluate
    .venv/Scripts/python.exe -m src.evaluate --split train --limit 5
"""

import argparse
import json
from difflib import SequenceMatcher
from pathlib import Path

import torch
from PIL import Image

from src.config import BASE_MODEL, CHECKPOINTS_DIR, DATASET_RAW_DIR, TRAIN_MANIFEST, VAL_MANIFEST
from src.infer import generate_caption, load_model


def load_examples(manifest_path: Path) -> list[dict]:
    text = manifest_path.read_text(encoding="utf-8")
    examples = [json.loads(line) for line in text.splitlines() if line.strip()]
    seen_books = set()
    deduped = []
    for ex in examples:
        if ex["livro_id"] in seen_books:
            continue
        seen_books.add(ex["livro_id"])
        deduped.append(ex)
    return deduped


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=["train", "val"], default="val")
    parser.add_argument("--checkpoint", type=Path, default=CHECKPOINTS_DIR / "best")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = VAL_MANIFEST if args.split == "val" else TRAIN_MANIFEST

    checkpoint = args.checkpoint if args.checkpoint.exists() else BASE_MODEL
    if checkpoint == BASE_MODEL:
        print(f"[aviso] nenhum checkpoint treinado em {args.checkpoint}, usando o modelo base ({BASE_MODEL})")

    device = torch.device(args.device)
    processor, model = load_model(checkpoint, device)

    examples = load_examples(manifest)
    if args.limit:
        examples = examples[: args.limit]

    scores = []
    for ex in examples:
        image_path = DATASET_RAW_DIR / ex["image"]
        predicted = generate_caption(processor, model, image_path, device)
        score = similarity(predicted, ex["caption"])
        scores.append(score)

        print(f"\n=== {ex['livro_id']} (similaridade: {score:.2f}) ===")
        print(f"esperado : {ex['caption']}")
        print(f"gerado   : {predicted}")

    if scores:
        print(f"\n== média de similaridade em {len(scores)} livros ({args.split}): {sum(scores) / len(scores):.2f} ==")


if __name__ == "__main__":
    main()
