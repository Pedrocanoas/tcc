"""Detecta um código de barras EAN-13 de ISBN em uma ou mais fotos.

Usa a primeira foto em que achar um código válido (978/979 + 10 dígitos).
Não depende de nenhum checkpoint treinado — é leitura de código de barras,
não inferência do modelo.

Uso:
    .venv/Scripts/python.exe -m src.detect_barcode caminho/para/foto1.jpg foto2.jpg
"""

import argparse
import json
import re
from pathlib import Path

from PIL import Image
from pyzbar.pyzbar import decode

ISBN13_RE = re.compile(r"^(978|979)\d{10}$")


def detect_isbn(image_path: Path) -> str | None:
    image = Image.open(image_path).convert("RGB")
    for barcode in decode(image):
        value = barcode.data.decode("utf-8", errors="ignore")
        if ISBN13_RE.match(value):
            return value
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", nargs="+", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    isbn = None
    for image_path in args.images:
        isbn = detect_isbn(image_path)
        if isbn:
            break

    print(json.dumps({"isbn": isbn}))


if __name__ == "__main__":
    main()
