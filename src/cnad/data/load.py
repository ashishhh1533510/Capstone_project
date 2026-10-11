"""Read the UNSW-NB15 partition CSVs and clean them into analysis-ready frames."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import pandas as pd

from cnad.config import get_config

Split = Literal["train", "test"]

TEXT_COLUMNS = ["proto", "service", "state", "attack_cat"]

# The 10 classes of the partition files, in descending training-set frequency
CLASSES = [
    "Normal",
    "Generic",
    "Exploits",
    "Fuzzers",
    "DoS",
    "Reconnaissance",
    "Analysis",
    "Backdoor",
    "Shellcode",
    "Worms",
]

# Variant spellings found in other UNSW-NB15 releases (e.g. the full 2.5M-row CSVs)
CLASS_ALIASES = {"Backdoors": "Backdoor"}


def raw_path(split: Split, cfg: dict[str, Any] | None = None) -> Path:
    """Path of the raw CSV for `split` (see config: the official file names are swapped)."""
    cfg = cfg or get_config()
    return cfg["paths"]["raw"] / cfg["data"][f"{split}_csv"]


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Drop `id`, strip whitespace in text columns and standardise class names."""
    df = df.drop(columns="id", errors="ignore")
    for col in TEXT_COLUMNS:
        df[col] = df[col].str.strip()
    df["attack_cat"] = df["attack_cat"].replace(CLASS_ALIASES)
    unknown = set(df["attack_cat"].unique()) - set(CLASSES)
    if unknown:
        raise ValueError(f"Unknown attack_cat values: {sorted(unknown)}")
    return df


def load_split(split: Split, cfg: dict[str, Any] | None = None) -> pd.DataFrame:
    """Read and clean one partition. The CSVs start with a UTF-8 byte-order mark."""
    return clean(pd.read_csv(raw_path(split, cfg), encoding="utf-8-sig"))


def load_both(cfg: dict[str, Any] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return the cleaned (train, test) partitions."""
    return load_split("train", cfg), load_split("test", cfg)
