"""Processo persistente de inferência: carrega o modelo uma única vez e atende
pedidos via stdin/stdout, um por linha — evita recarregar ~1 GB de pesos a
cada chamada (é o que `infer.py` faz quando rodado como processo avulso).

Protocolo (uma linha JSON por pedido/resposta, sempre com \n no final):
    entrada: {"fotos": ["foto1.jpg", "foto2.jpg"], "capa": "dura", "condicao": "seminovo"}
             (também aceita uma lista pura de caminhos, sem capa/condicao)
    saída:   {"ok": [{"image": "...", "caption": "..."}, ...]}
    erro:    {"error": "mensagem"}

Uso (chamado pelo backend/, não interativamente):
    .venv/Scripts/python.exe -m src.serve
"""

import json
import sys
from pathlib import Path

import torch

from src.config import BASE_MODEL, CHECKPOINTS_DIR
from src.infer import generate_caption, load_model
from src.prompt import build_prefix


def main() -> None:
    checkpoint = CHECKPOINTS_DIR / "best"
    if not checkpoint.exists():
        print(
            f"[aviso] nenhum checkpoint treinado em {checkpoint}, usando o modelo base ({BASE_MODEL})",
            file=sys.stderr,
            flush=True,
        )
        checkpoint = BASE_MODEL

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    processor, model = load_model(checkpoint, device)
    print("[serve] modelo carregado, pronto para receber pedidos", file=sys.stderr, flush=True)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            pedido = json.loads(line)
            if isinstance(pedido, list):
                image_paths, capa, condicao = pedido, None, None
            else:
                image_paths, capa, condicao = pedido["fotos"], pedido.get("capa"), pedido.get("condicao")

            prefix = build_prefix(capa, condicao)
            results = [
                {
                    "image": path,
                    "caption": generate_caption(
                        processor, model, Path(path), device, max_new_tokens=128, prefix=prefix
                    ),
                }
                for path in image_paths
            ]
            print(json.dumps({"ok": results}, ensure_ascii=False), flush=True)
        except Exception as exc:
            print(json.dumps({"error": str(exc)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
