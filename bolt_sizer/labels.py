"""labels.csv format shared by real captures and synthetic data (no torch)."""
import csv
from pathlib import Path

FIELDS = ["file", "label", "is_bolt", "system", "diameter_mm", "length_mm", "head_type", "finish", "source", "mask"]


def append_label(folder, row):
    path = Path(folder) / "labels.csv"
    new = not path.exists()
    fields = FIELDS
    if not new:
        with open(path, newline="") as f:
            fields = next(csv.reader(f))
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        if new:
            w.writeheader()
        w.writerow(row)
