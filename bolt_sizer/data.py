"""Datasets. Real captures and pre-generated synthetic data share one format:
a folder of rectified canvas images plus labels.csv."""
import csv
from pathlib import Path

import cv2
import numpy as np
import torch
from torch.utils.data import Dataset

from .model import DIAM_SCALE, LEN_SCALE, to_tensor


def _targets(row):
    """Size/system/type are only meaningful for bolts; -1 marks "ignore"."""
    size = torch.tensor([float(row["diameter_mm"]) / DIAM_SCALE,
                         float(row["length_mm"]) / LEN_SCALE])
    is_bolt = int(row.get("is_bolt") or 1)           # older CSVs: bolts only
    return size, int(row["system"]), int(row["head_type"]), is_bolt


def augment(x, mask):
    """Augmentations that keep the mm-per-pixel scale intact."""
    k = int(torch.randint(4, (1,)))
    x, mask = torch.rot90(x, k, (1, 2)), torch.rot90(mask, k, (0, 1))
    if torch.rand(1) < 0.5:
        x, mask = x.flip(2), mask.flip(1)
    x = x * (0.8 + 0.4 * torch.rand(1)) + 0.1 * (torch.rand(1) - 0.5)
    x = x + 0.02 * torch.rand(1) * torch.randn_like(x)
    return x.clamp(0, 1), mask


class FolderDataset(Dataset):
    def __init__(self, folder, train=True):
        self.folder = Path(folder)
        with open(self.folder / "labels.csv") as f:
            self.rows = list(csv.DictReader(f))
        self.train = train

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        row = self.rows[i]
        img = cv2.imread(str(self.folder / row["file"]), cv2.IMREAD_COLOR)
        if img is None:
            raise FileNotFoundError(self.folder / row["file"])
        x = to_tensor(img)
        if row.get("mask"):
            mask = cv2.imread(str(self.folder / row["mask"]), cv2.IMREAD_GRAYSCALE)
            if mask is None:
                raise FileNotFoundError(self.folder / row["mask"])
            if mask.shape != (256, 256) or not np.isin(mask, (0, 1, 2)).all():
                raise ValueError(f"invalid mask {row['mask']}")
            mask = torch.from_numpy(mask.astype(np.int64))
        else:
            mask = torch.full((256, 256), 255, dtype=torch.long)
        if self.train:
            x, mask = augment(x, mask)
        return (x, *_targets(row), mask)

