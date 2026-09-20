import json
from pathlib import Path

from PIL import Image
from torch.utils.data import Dataset

from src.config import DATASET_RAW_DIR


class BookConditionDataset(Dataset):
    """Pares (foto do livro, descrição de condição) a partir de um manifesto JSONL."""

    def __init__(self, manifest_path: Path, processor, max_length: int = 128):
        text = Path(manifest_path).read_text(encoding="utf-8")
        self.examples = [json.loads(line) for line in text.splitlines() if line.strip()]
        self.processor = processor
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, idx: int) -> dict:
        example = self.examples[idx]
        image = Image.open(DATASET_RAW_DIR / example["image"]).convert("RGB")

        encoding = self.processor(
            images=image,
            text=example["caption"],
            padding="max_length",
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )
        item = {key: value.squeeze(0) for key, value in encoding.items()}

        labels = item["input_ids"].clone()
        labels[labels == self.processor.tokenizer.pad_token_id] = -100
        item["labels"] = labels
        return item
