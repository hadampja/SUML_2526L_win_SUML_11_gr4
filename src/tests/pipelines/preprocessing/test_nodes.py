import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_SRC = Path(__file__).resolve().parents[3] / "ai_project_s28551"
if str(PROJECT_SRC.parent) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC.parent))

from ai_project_s28551.pipelines.preprocessing.nodes import (  # noqa: E402
    clean_data,
    scale_data,
    split_data,
)


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "user_id": ["u1", "u1", "u2", "u3", "u3"],
            "game_title": ["g1", "g1", "g2", "g3", "g3"],
            "behavior": ["play"] * 5,
            "play_time_hours": [1.0, 1.0, 5.0, 200.0, -3.0],
        }
    )


def test_clean_data_removes_duplicates_and_negatives():
    cleaned = clean_data(_sample_df())
    assert len(cleaned) < len(_sample_df())
    assert (cleaned["play_time_hours"] > 0).all()
    assert cleaned.duplicated().sum() == 0


def test_scale_data_keeps_play_time_hours_raw():
    cleaned = clean_data(_sample_df())
    scaled = scale_data(cleaned)
    assert np.allclose(
        scaled["play_time_hours"].to_numpy(),
        cleaned["play_time_hours"].to_numpy(),
        atol=1e-9,
    )


def test_split_data_respects_sizes():
    df = pd.DataFrame(
        {
            "user_id": [f"u{i}" for i in range(100)],
            "game_title": [f"g{i % 10}" for i in range(100)],
            "play_time_hours": np.linspace(1, 10, 100),
        }
    )
    train, val, test = split_data(df, train_frac=0.7, val_frac=0.15, random_state=42)
    total = len(train) + len(val) + len(test)
    assert total == len(df)
    assert abs(len(train) - round(0.7 * len(df))) <= 1
    assert abs(len(val) - round(0.15 * len(df))) <= 1
    assert abs(len(test) - round(0.15 * len(df))) <= 1


def test_split_data_handles_empty_dataframe():
    empty = pd.DataFrame(columns=["user_id", "game_title", "play_time_hours"])
    train, val, test = split_data(empty)
    assert len(train) == 0
    assert len(val) == 0
    assert len(test) == 0
