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

from PIL import Image, ImageOps
from pyzbar.pyzbar import decode

ISBN13_RE = re.compile(r"^(978|979)\d{10}$")

# Fotos de contracapa no dataset costumam ser produto fotografado em ângulo
# (não um scan reto) — o zbar tolera um pouco de inclinação sozinho, mas não
# o suficiente pra esses casos. Cobre virada de 90/180/270 (foto na
# orientação errada) e uma leve inclinação pros dois lados.
ROTACOES = (90, 180, 270, -20, -10, 10, 20)


def _tentativas(image: Image.Image):
    """Gera variações da imagem pra tentar decodificar, da mais barata
    (cobre o caso que já funciona hoje) pra mais cara."""
    yield image

    cinza_realcado = ImageOps.autocontrast(image.convert("L"))
    yield cinza_realcado
    for angulo in ROTACOES:
        yield cinza_realcado.rotate(angulo, expand=True, fillcolor=255)

    # fotos pequenas (miniaturas) ficam com o código abaixo da resolução
    # mínima que o zbar reconhece
    if max(image.size) < 1200:
        fator = 1200 / max(image.size)
        yield cinza_realcado.resize((round(image.width * fator), round(image.height * fator)))


def detect_isbn(image_path: Path) -> str | None:
    image = Image.open(image_path).convert("RGB")
    for tentativa in _tentativas(image):
        for barcode in decode(tentativa):
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
