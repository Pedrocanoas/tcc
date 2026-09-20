import os
from pathlib import Path

MODEL_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = MODEL_DIR.parent


def _env_path(var: str, default: Path) -> Path:
    value = os.environ.get(var)
    return Path(value) if value else default


# As três variáveis abaixo podem ser sobrescritas por ambiente para rodar em
# outro lugar (ex: Kaggle, onde os dados ficam em /kaggle/input e as saídas
# precisam ir para /kaggle/working, que é a única área com permissão de escrita).
DATASET_RAW_DIR = _env_path("TCC_DATASET_RAW_DIR", REPO_ROOT / "dataset" / "raw")
DATASET_PROCESSED_DIR = _env_path("TCC_DATASET_PROCESSED_DIR", REPO_ROOT / "dataset" / "processed")
CHECKPOINTS_DIR = _env_path("TCC_CHECKPOINTS_DIR", MODEL_DIR / "checkpoints")

TRAIN_MANIFEST = DATASET_PROCESSED_DIR / "train.jsonl"
VAL_MANIFEST = DATASET_PROCESSED_DIR / "val.jsonl"

BASE_MODEL = "Salesforce/blip-image-captioning-base"
