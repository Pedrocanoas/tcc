"""Prepara os manifestos e treina o BLIP em um ambiente Kaggle.

Exemplo:
    python kaggle_train.py --raw-dir /kaggle/input/livros/raw --epochs 20 --batch-size 8
"""

import argparse
import os
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--processed-dir", type=Path, default=Path("/kaggle/working/processed"))
    parser.add_argument("--checkpoints-dir", type=Path, default=Path("/kaggle/working/checkpoints"))
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=5e-5)
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--freeze-vision", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--val-ratio", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    os.environ["TCC_DATASET_RAW_DIR"] = str(args.raw_dir)
    os.environ["TCC_DATASET_PROCESSED_DIR"] = str(args.processed_dir)
    os.environ["TCC_CHECKPOINTS_DIR"] = str(args.checkpoints_dir)

    from src.data.prepare_dataset import main as prepare_dataset
    from src.train import main as train

    original_argv = sys.argv
    try:
        sys.argv = ["prepare_dataset", "--val-ratio", str(args.val_ratio), "--seed", str(args.seed)]
        prepare_dataset()
        sys.argv = [
            "train",
            "--epochs",
            str(args.epochs),
            "--batch-size",
            str(args.batch_size),
            "--lr",
            str(args.lr),
            "--max-length",
            str(args.max_length),
            "--freeze-vision" if args.freeze_vision else "--no-freeze-vision",
        ]
        train()
    finally:
        sys.argv = original_argv


if __name__ == "__main__":
    main()