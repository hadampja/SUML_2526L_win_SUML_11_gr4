"""Data preprocessing nodes: cleaning, scaling and dataset splitting."""

from __future__ import annotations

import logging
from typing import Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


def clean_data(steam_play_interactions: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicates/outliers, fix dtypes and fill missing values."""
    df = steam_play_interactions.copy()
    logger.info("Cleaning Steam interactions: %d rows before", len(df))

    df = df.drop_duplicates()

    if "play_time_hours" in df.columns:
        df = df[df["play_time_hours"].notnull()]
        df = df[df["play_time_hours"] > 0]

        q1 = df["play_time_hours"].quantile(0.25)
        q3 = df["play_time_hours"].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        before_outliers = len(df)
        df = df[(df["play_time_hours"] >= lower) & (df["play_time_hours"] <= upper)]
        logger.info(
            "Removed %d outliers via IQR rule",
            before_outliers - len(df),
        )

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    categorical_cols = df.select_dtypes(include=["object"]).columns

    for col in numeric_cols:
        median = df[col].median()
        df[col] = df[col].fillna(median)

    for col in categorical_cols:
        mode = df[col].mode(dropna=True)
        if not mode.empty:
            df[col] = df[col].fillna(mode.iloc[0])
        else:
            df[col] = df[col].fillna("unknown")

    df = df.reset_index(drop=True)
    logger.info("Completed cleaning: %d rows after", len(df))
    return df


def scale_data(clean_data: pd.DataFrame) -> pd.DataFrame:
    """Keep recommender inputs on their original scale.

    The recommender uses ``play_time_hours`` as an interaction strength, so it
    should stay in real hours. This node is kept to preserve the Kedro artifact
    layout, but it only scales extra numeric feature columns if they appear in
    the future.
    """
    df = clean_data.copy()
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    columns_to_keep_raw = ["user_id", "game_id", "play_time_hours"]
    cols_to_scale = [col for col in numeric_cols if col not in columns_to_keep_raw]

    if not cols_to_scale:
        logger.info("No auxiliary numeric columns to scale; returning data unchanged.")
        return df

    scaler = StandardScaler()
    df[cols_to_scale] = scaler.fit_transform(df[cols_to_scale])
    logger.info("Scaled %d auxiliary numeric columns: %s (kept raw: %s)",
                len(cols_to_scale), cols_to_scale, 
                [col for col in numeric_cols if col in columns_to_keep_raw])
    return df


def split_data(
    scaled_data: pd.DataFrame,
    train_frac: float = 0.7,
    val_frac: float = 0.15,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split dataset into train/val/test.

    Domyślne proporcje: 70/15/15. Funkcja jest odporna na pusty DataFrame –
    jeśli nie ma danych, zwraca trzy puste DataFrame'y i loguje ostrzeżenie.
    """

    df = scaled_data.copy()

    if df is None or df.empty:
        logger.warning(
            "scaled_data is empty – skipping split_data() and returning "
            "empty train/val/test splits."
        )
        empty = df.copy()
        return empty.copy(), empty.copy(), empty.copy()

    test_frac = 1.0 - train_frac  # tu wyjdzie 0.3

    # podział: train vs (val+test)
    train_df, temp_df = train_test_split(
        df,
        test_size=test_frac,
        random_state=random_state,
        shuffle=True,
    )

    # teraz dzielimy (val+test) na val i test po połowie
    val_relative = val_frac / (1.0 - train_frac)  # 0.15 / 0.3 = 0.5

    val_df, test_df = train_test_split(
        temp_df,
        test_size=1.0 - val_relative,
        random_state=random_state,
        shuffle=True,
    )

    logger.info(
        "Split data into: train=%d rows, val=%d rows, test=%d rows",
        len(train_df),
        len(val_df),
        len(test_df),
    )

    return train_df, val_df, test_df
