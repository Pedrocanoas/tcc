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
# ID interno de listagem (sempre 8-9 dígitos) que às vezes sobra no fim do
# texto, ex.: "...sem grifos. - 201641077." — achado medindo outliers de
# comprimento no dataset (ver model/README.md). Exige "-" explícito antes do
# número pra não cortar um ano de 4 dígitos ou outro número de verdade.
TRAILING_ID_RE = re.compile(r"\s*-\s*\d{7,}\.?\s*$")
FOTO_ORIGINAL_RE = re.compile(r"foto original\.?", re.IGNORECASE)
WHITESPACE_RE = re.compile(r"\s+")

# Palavras comuns do português — um prefixo que contenha alguma delas já é
# texto de verdade (não um código), então a remoção para por ali. Achado ao
# medir vazamento de código nos dados de treino (ver model/README.md).
STOPWORDS = {
    "em", "de", "da", "do", "das", "dos", "com", "sem", "muito", "bem",
    "para", "as", "os", "um", "uma", "e", "mas", "que", "a", "o", "na",
    "no", "nas", "nos", "ao", "aos", "se", "ou", "tem", "está", "esta",
    "são", "pela", "pelo", "bom", "boa", "ótimo", "otimo",
}

# Formatos observados no scraping: "EI805/350AP - <texto>",
# "Local: <categoria> <código> - <texto>", "SKU: <número>. <código>; <texto>",
# além de variações com "<código>. <texto>" no lugar do " - ".
SKU_PREFIX_RE = re.compile(r"^sku:\s*\d+\.\s*", re.IGNORECASE)
LOCAL_CATEGORY_RE = re.compile(r"^local:\s*(?:(?!\S*\d)\S+\s+){0,4}", re.IGNORECASE)
SHORT_CODE_DOT_RE = re.compile(r"^[a-z]{1,6}\d\w*\.\s*", re.IGNORECASE)
CODE_SEPARATOR_RE = re.compile(r"\s*[-;]\s*")

# Livro-coleção/multi-volume: a legenda fala de vários volumes/estados ao
# mesmo tempo (ex.: "São 26 volumes; coleção incompleta; ..."), estrutura
# bem diferente do padrão 1 livro = 1 estado — achado medindo outliers no
# dataset (ver model/README.md). Usado por --exclude-colecoes.
TITULO_RE = re.compile(r"^Titulo:\s*(.*)$", re.MULTILINE)
COLECAO_CAPTION_RE = re.compile(
    r"\b(\d+\s+volumes?|\d+\s+fasc[ií]culos?|\d+\s+livr(?:o|os)\b|caixa\s+com|box\s+com|"
    r"cole[cç][aã]o\b|kit\s+com|s[aã]o\s+\d+|conjunto\s+de|\d+\s+exemplares?)",
    re.IGNORECASE,
)
TITULO_MULTIVOL_RE = re.compile(r"\b(vol\.?\s*\d+|v\.\s*\d+|box\b|cole[cç][aã]o\b)\b", re.IGNORECASE)


def is_colecao(titulo: str, caption: str) -> bool:
    return bool(COLECAO_CAPTION_RE.search(caption) or TITULO_MULTIVOL_RE.search(titulo))


def extract_seller_description(raw_text: str) -> str | None:
    if SELLER_DESC_HEADER not in raw_text:
        return None
    return raw_text.split(SELLER_DESC_HEADER, 1)[1].strip()


def strip_leading_seller_code(text: str, max_iterations: int = 8) -> str:
    """Remove o código interno do vendedor (categoria/prateleira + SKU) do
    início da legenda. Um prefixo só é cortado se, até o próximo separador
    (" - ", ";" ou "<código>."), tiver algum dígito (todo código observado
    tem número; "brochura", "novo", "lacrado" etc. não têm) e nenhuma
    STOPWORDS — os dois sinais juntos distinguem código de início de frase."""
    text = LOCAL_CATEGORY_RE.sub("", text)
    text = SKU_PREFIX_RE.sub("", text)
    for _ in range(max_iterations):
        dot_match = SHORT_CODE_DOT_RE.match(text)
        if dot_match:
            text = text[dot_match.end() :]
            continue
        sep_match = CODE_SEPARATOR_RE.search(text)
        if not sep_match:
            break
        prefix = text[: sep_match.start()]
        if not any(char.isdigit() for char in prefix):
            break
        words = re.findall(r"[^\s:]+", prefix.lower())
        if any(word in STOPWORDS for word in words):
            break
        text = text[sep_match.end() :]
    return text.strip()


def clean_caption(raw_text: str) -> str | None:
    text = extract_seller_description(raw_text)
    if not text:
        return None
    text = TRAILING_TAG_RE.sub("", text).strip()
    text = TRAILING_ID_RE.sub("", text).strip()
    text = FOTO_ORIGINAL_RE.sub("", text).strip()
    text = strip_leading_seller_code(text)
    text = WHITESPACE_RE.sub(" ", text).strip(" .") + "."
    return text if len(text) > 3 else None


def collect_examples(raw_dir: Path) -> list[dict]:
    """Coleta TODOS os livros, inclusive coleções — o sorteio treino/validação
    (split_by_book) precisa ver a população inteira pra não mudar de corrida
    pra corrida. Quem decide excluir coleções é o chamador, depois do split
    (ver --exclude-colecoes em main())."""
    examples = []
    for book_dir in sorted(raw_dir.iterdir()):
        if not book_dir.is_dir():
            continue
        descricao_path = book_dir / "descricao.txt"
        if not descricao_path.exists():
            continue

        raw_text = descricao_path.read_text(encoding="utf-8")
        caption = clean_caption(raw_text)
        if not caption:
            continue

        titulo_match = TITULO_RE.search(raw_text)
        titulo = titulo_match.group(1).strip() if titulo_match else ""
        colecao = is_colecao(titulo, caption)

        photos = sorted(book_dir.glob("foto*.jpg"))
        for photo_path in photos:
            examples.append(
                {
                    "livro_id": book_dir.name,
                    "image": photo_path.relative_to(raw_dir).as_posix(),
                    "caption": caption,
                    "colecao": colecao,
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
    parser.add_argument(
        "--exclude-colecoes",
        action="store_true",
        help=(
            "remove livros-coleção/multi-volume do treino (não da validação — "
            "o split já foi decidido com todos os livros, pra ficar comparável "
            "com uma corrida sem essa flag; ver is_colecao e o campo 'colecao' "
            "no manifesto)"
        ),
    )
    args = parser.parse_args()

    # O split é feito com TODOS os livros antes de qualquer filtro, senão
    # --exclude-colecoes muda o sorteio treino/validação e invalida a
    # comparação com uma corrida sem a flag (ver model/README.md).
    examples = collect_examples(DATASET_RAW_DIR)
    if not examples:
        raise SystemExit(f"Nenhum exemplo encontrado em {DATASET_RAW_DIR}")

    train, val = split_by_book(examples, args.val_ratio, args.seed)
    if args.exclude_colecoes:
        train = [ex for ex in train if not ex["colecao"]]
    write_jsonl(TRAIN_MANIFEST, train)
    write_jsonl(VAL_MANIFEST, val)

    n_books = len({ex["livro_id"] for ex in examples})
    print(f"Livros: {n_books} | Exemplos (imagem, legenda): {len(examples)}")
    print(f"Treino: {len(train)} exemplos -> {TRAIN_MANIFEST.relative_to(DATASET_PROCESSED_DIR.parent.parent)}")
    print(f"Validação: {len(val)} exemplos -> {VAL_MANIFEST.relative_to(DATASET_PROCESSED_DIR.parent.parent)}")


if __name__ == "__main__":
    main()
