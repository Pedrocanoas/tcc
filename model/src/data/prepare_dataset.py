"""Monta o manifesto de treino/validação a partir de dataset/raw/.

Cada pasta `dataset/raw/livroNNN/` tem um `descricao.txt` (com a seção
"Descricao do vendedor:") e uma ou mais fotos (`foto*.jpg`). Este script
extrai a descrição de condição do vendedor, limpa o texto (remove o código
interno do vendedor e a tag de foto no fim) e gera um par
(imagem, legenda) para cada foto do livro.

O split treino/validação é feito por livro (não por foto), para não vazar
fotos do mesmo livro entre os dois conjuntos.

Uso:
    .venv/Scripts/python.exe -m src.data.prepare_dataset
"""

import argparse
import json
import random
import re
from pathlib import Path

from src.config import DATASET_PROCESSED_DIR, DATASET_RAW_DIR, TRAIN_MANIFEST, VAL_MANIFEST

SELLER_DESC_HEADER = "Descricao do vendedor:"
TRAILING_TAG_RE = re.compile(r"_[A-Za-z0-9]+_\.?\s*$")
FOTO_ORIGINAL_RE = re.compile(r"foto original\.?", re.IGNORECASE)
WHITESPACE_RE = re.compile(r"\s+")


def extract_seller_description(raw_text: str) -> str | None:
    if SELLER_DESC_HEADER not in raw_text:
        return None
    return raw_text.split(SELLER_DESC_HEADER, 1)[1].strip()


def strip_leading_seller_code(text: str, max_code_len: int = 25) -> str:
    if " - " in text:
        prefix, rest = text.split(" - ", 1)
        if len(prefix) <= max_code_len:
            return rest.strip()
    return text


def clean_caption(raw_text: str) -> str | None:
    text = extract_seller_description(raw_text)
    if not text:
        return None
    text = TRAILING_TAG_RE.sub("", text).strip()
    text = FOTO_ORIGINAL_RE.sub("", text).strip()
    text = strip_leading_seller_code(text)
    text = WHITESPACE_RE.sub(" ", text).strip(" .") + "."
    return text if len(text) > 3 else None


def collect_examples(raw_dir: Path) -> list[dict]:
    examples = []
    for book_dir in sorted(raw_dir.iterdir()):
        if not book_dir.is_dir():
            continue
        descricao_path = book_dir / "descricao.txt"
        if not descricao_path.exists():
            continue

        caption = clean_caption(descricao_path.read_text(encoding="utf-8"))
        if not caption:
            continue

        photos = sorted(book_dir.glob("foto*.jpg"))
        for photo_path in photos:
            examples.append(
                {
                    "livro_id": book_dir.name,
                    "image": photo_path.relative_to(raw_dir).as_posix(),
                    "caption": caption,
                }
            )
    return examples


def split_by_book(examples: list[dict], val_ratio: float, seed: int) -> tuple[list[dict], list[dict]]:
    book_ids = sorted({ex["livro_id"] for ex in examples})
    rng = random.Random(seed)
    rng.shuffle(book_ids)

    n_val = max(1, round(len(book_ids) * val_ratio))
    val_books = set(book_ids[:n_val])

    train, val = [], []
    for ex in examples:
        (val if ex["livro_id"] in val_books else train).append(ex)
    return train, val


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--val-ratio", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    examples = collect_examples(DATASET_RAW_DIR)
    if not examples:
        raise SystemExit(f"Nenhum exemplo encontrado em {DATASET_RAW_DIR}")

    train, val = split_by_book(examples, args.val_ratio, args.seed)
    write_jsonl(TRAIN_MANIFEST, train)
    write_jsonl(VAL_MANIFEST, val)

    n_books = len({ex["livro_id"] for ex in examples})
    print(f"Livros: {n_books} | Exemplos (imagem, legenda): {len(examples)}")
    print(f"Treino: {len(train)} exemplos -> {TRAIN_MANIFEST.relative_to(DATASET_PROCESSED_DIR.parent.parent)}")
    print(f"Validação: {len(val)} exemplos -> {VAL_MANIFEST.relative_to(DATASET_PROCESSED_DIR.parent.parent)}")


if __name__ == "__main__":
    main()
