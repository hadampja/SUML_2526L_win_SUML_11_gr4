import logging
from pathlib import Path

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib
matplotlib.use("Agg")  # ważne przy uruchamianiu bez GUI (Airflow, serwery)

import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


def prepare_steam_play(steam_raw: pd.DataFrame) -> pd.DataFrame:
    logger.info(
        "prepare_steam_play: input steam_raw shape=%s, columns=%s",
        steam_raw.shape, list(steam_raw.columns)
    )

    if steam_raw.empty:
        logger.warning("steam_raw is empty -> returning empty steam_play_interactions.")
        return pd.DataFrame(columns=["user_id", "game_title", "play_time_hours"])

    df = steam_raw.copy()

    # 🔹 Normalizacja kolumny behavior: string, małe litery, przycięte spacje
    df["behavior"] = (
        df["behavior"]
        .astype(str)
        .str.lower()
        .str.strip()
    )

    # 🔹 Zaloguj, co tam tak naprawdę siedzi:
    logger.info("Behavior value_counts: %s", df["behavior"].value_counts().to_dict())

    # 🔹 Bierzemy tylko interakcje typu 'play'
    df = df[df["behavior"] == "play"]
    logger.info("After behavior=='play': shape=%s", df.shape)

    if df.empty:
        logger.warning("No 'play' interactions found -> returning empty.")
        return pd.DataFrame(columns=["user_id", "game_title", "play_time_hours"])

    # In steam-200k rows with behavior == "play", value is already the play
    # duration in hours. Keeping it raw avoids shrinking the signal by /60.
    df["play_time_hours"] = df["value"].astype(float)

    # Usuwamy wiersze z nie-dodatnim czasem gry
    df = df[df["play_time_hours"] > 0]

    if df.empty:
        logger.warning("No rows with play_time_hours>0 -> returning empty.")
        return pd.DataFrame(columns=["user_id", "game_title", "play_time_hours"])

    # Typy i agregacja
    df["user_id"] = df["user_id"].astype(str)
    df["game_title"] = df["game_title"].astype(str)

    df = (
        df.groupby(["user_id", "game_title"], as_index=False)
          .agg(play_time_hours=("play_time_hours", "sum"))
    )

    logger.info(
        "Prepared steam_play_interactions: %d rows, %d users, %d games",
        len(df),
        df["user_id"].nunique(),
        df["game_title"].nunique(),
    )

    return df


def compute_basic_stats(steam_play_interactions: pd.DataFrame) -> pd.DataFrame:
    logger.info("Computing basic stats for Steam play interactions...")
    stats = steam_play_interactions.describe(include="all").transpose()
    stats["n_unique"] = steam_play_interactions.nunique()
    return stats


def compute_missing_values(steam_play_interactions: pd.DataFrame) -> pd.DataFrame:
    logger.info("Computing missing values...")
    missing = steam_play_interactions.isnull().sum().to_frame("n_missing")
    missing["missing_frac"] = missing["n_missing"] / len(steam_play_interactions)
    return missing


def compute_correlations(steam_play_interactions: pd.DataFrame) -> pd.DataFrame:
    logger.info("Computing correlation matrix for numeric columns...")
    numeric_cols = ["play_time_hours"]
    df_num = steam_play_interactions[numeric_cols].fillna(0)
    return df_num.corr()


def compute_outliers(steam_play_interactions: pd.DataFrame) -> pd.DataFrame:
    """
    Simple IQR-based outlier detection for play_time_hours.
    """
    logger.info("Detecting outliers using IQR rule...")
    series = steam_play_interactions["play_time_hours"]
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    mask = (series < lower) | (series > upper)
    outliers = pd.DataFrame(
        {
            "column": ["play_time_hours"],
            "q1": [q1],
            "q3": [q3],
            "iqr": [iqr],
            "lower_fence": [lower],
            "upper_fence": [upper],
            "n_outliers": [mask.sum()],
            "frac_outliers": [mask.mean()],
        }
    )
    return outliers


def summarize_data_quality(steam_play_interactions: pd.DataFrame) -> pd.DataFrame:
    """
    Collect a few quick data-quality signals: duplicates, zero durations, etc.
    """
    logger.info("Summarizing basic data-quality checks...")
    duplicated_rows = steam_play_interactions.duplicated().sum()
    zero_play_time = (steam_play_interactions["play_time_hours"] <= 0).sum()
    summary = pd.DataFrame(
        {
            "metric": [
                "n_rows",
                "n_unique_users",
                "n_unique_games",
                "duplicated_rows",
                "zero_or_negative_play_time",
            ],
            "value": [
                len(steam_play_interactions),
                steam_play_interactions["user_id"].nunique(),
                steam_play_interactions["game_title"].nunique(),
                duplicated_rows,
                zero_play_time,
            ],
        }
    )
    return summary


def save_basic_plots(steam_play_interactions: pd.DataFrame) -> None:
    """Zapisuje podstawowe wykresy EDA do plików PNG.

    Funkcja jest odporna na pusty DataFrame – jeśli nie ma danych,
    loguje ostrzeżenie i kończy się bez błędu.
    """
    logger.info("Saving basic EDA plots...")

    # Jeśli nie ma żadnych danych, nie próbujemy rysować wykresów
    if steam_play_interactions is None or steam_play_interactions.empty:
        logger.warning(
            "steam_play_interactions is empty – skipping save_basic_plots() "
            "(no plots will be generated)."
        )
        return None

    plots_dir = Path("docs/plots")
    plots_dir.mkdir(parents=True, exist_ok=True)

    # ========= TOP 15 GIER WG LICZBY INTERAKCJI =========
    if "game_title" in steam_play_interactions.columns:
        top_games = (
            steam_play_interactions["game_title"]
            .value_counts()
            .head(15)
            .sort_values(ascending=True)
        )

        if top_games.empty:
            logger.warning(
                "No top games to plot (value_counts() returned empty). "
                "Skipping top games bar plot."
            )
        else:
            plt.figure(figsize=(8, 6))
            top_games.plot(kind="barh")
            plt.title("Top 15 gier wg liczby interakcji")
            plt.xlabel("liczba interakcji")
            plt.tight_layout()
            plt.savefig(plots_dir / "top_games.png")
            plt.close()
    else:
        logger.warning(
            "'game_title' column not found in steam_play_interactions – "
            "skipping top games plot."
        )

    # ========= HISTOGRAM CZASU GRY (JEŚLI KOLUMNA ISTNIEJE) =========
    if "play_time_hours" in steam_play_interactions.columns:
        if steam_play_interactions["play_time_hours"].dropna().empty:
            logger.warning(
                "Column 'play_time_hours' is empty – skipping play time histogram."
            )
        else:
            plt.figure(figsize=(8, 6))
            steam_play_interactions["play_time_hours"].hist(bins=50)
            plt.title("Rozkład czasu gry (w godzinach)")
            plt.xlabel("czas gry [h]")
            plt.ylabel("liczba użytkowników")
            plt.tight_layout()
            plt.savefig(plots_dir / "play_time_hist.png")
            plt.close()
    else:
        logger.warning(
            "'play_time_hours' column not found in steam_play_interactions – "
            "skipping play time histogram."
        )

    logger.info("Basic EDA plots saved successfully.")
