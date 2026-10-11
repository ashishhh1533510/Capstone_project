"""Load configs/config.yaml and resolve its paths against the project root."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = PROJECT_ROOT / "configs" / "config.yaml"


def load_config(path: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    """Read the YAML config. `CNAD_CONFIG` overrides the default location."""
    config_path = Path(path or os.environ.get("CNAD_CONFIG", DEFAULT_CONFIG))
    with config_path.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg["paths"] = {name: PROJECT_ROOT / rel for name, rel in cfg["paths"].items()}
    return cfg


@lru_cache(maxsize=1)
def get_config() -> dict[str, Any]:
    """Cached default config for use across modules."""
    return load_config()
