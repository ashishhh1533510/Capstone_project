import hashlib

import pandas as pd
import pytest

from cnad.config import load_config
from cnad.data.load import CLASSES, clean, load_split, raw_path

CFG = load_config()
needs_data = pytest.mark.skipif(
    not all(raw_path(s, CFG).exists() for s in ("train", "test")),
    reason="UNSW-NB15 CSVs not in data/raw",
)


def test_clean_strips_and_standardises():
    df = pd.DataFrame(
        {
            "id": [1, 2],
            "proto": [" tcp", "udp "],
            "service": ["-", " http"],
            "state": ["FIN ", "INT"],
            "attack_cat": [" Backdoors ", "Normal"],
            "label": [1, 0],
        }
    )
    out = clean(df)
    assert "id" not in out.columns
    assert out["proto"].tolist() == ["tcp", "udp"]
    assert out["attack_cat"].tolist() == ["Backdoor", "Normal"]


def test_clean_rejects_unknown_class():
    df = pd.DataFrame(
        {"proto": ["tcp"], "service": ["-"], "state": ["FIN"], "attack_cat": ["Ransomware"]}
    )
    with pytest.raises(ValueError, match="Ransomware"):
        clean(df)


@needs_data
@pytest.mark.parametrize("split", ["train", "test"])
def test_raw_files_match_recorded_hash(split):
    path = raw_path(split, CFG)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == CFG["data"]["sha256"][path.name]


@needs_data
@pytest.mark.parametrize("split", ["train", "test"])
def test_loaded_split_shape_and_labels(split):
    df = load_split(split, CFG)
    assert len(df) == CFG["data"]["expected_rows"][split]
    assert "id" not in df.columns
    assert set(df["attack_cat"]) == set(CLASSES)
    assert ((df["attack_cat"] == "Normal") == (df["label"] == 0)).all()
