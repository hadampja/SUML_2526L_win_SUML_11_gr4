"""Modeling nodes for the Steam item-based recommender."""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


def build_recommendations(
    interactions: pd.DataFrame,
    top_k: int = 5,
    min_game_users: int = 5,
) -> pd.DataFrame:
    """Build Top-K game recommendations per user using item-based CF.

    The recommender treats every positive play event as implicit feedback,
    computes item-item cosine similarity, and scores unseen games from the
    games already played by each user.
    """
    logger.info("Building item-based CF recommendations (Top-%d).", top_k)

    df = interactions.copy()
    df = df.dropna(subset=["user_id", "game_title", "play_time_hours"])
    df["play_time_hours"] = pd.to_numeric(df["play_time_hours"], errors="coerce")
    df = df[df["play_time_hours"] > 0]
    df = df.drop_duplicates(subset=["user_id", "game_title"])

    game_counts = df.groupby("game_title")["user_id"].nunique()
    popular_games = game_counts[game_counts >= min_game_users].index
    df = df[df["game_title"].isin(popular_games)]
    logger.info(
        "After filtering games with <%d users: %d interactions, %d users, %d games.",
        min_game_users,
        len(df),
        df["user_id"].nunique(),
        df["game_title"].nunique(),
    )

    if df.empty:
        logger.warning("No interactions left after filtering; returning empty recs.")
        return pd.DataFrame(columns=["user_id", "rank", "game_title", "score"])

    user_item = df.pivot_table(
        index="user_id",
        columns="game_title",
        values="play_time_hours",
        aggfunc="sum",
        fill_value=0.0,
    )
    user_item_binary = (user_item > 0).astype(np.float32)

    item_sim = cosine_similarity(user_item_binary.T)
    np.fill_diagonal(item_sim, 0.0)
    logger.info("Item similarity matrix shape: %s", item_sim.shape)

    weights = np.log1p(user_item.to_numpy())
    scores_matrix = weights @ item_sim
    scores_matrix = np.where(user_item_binary.to_numpy() > 0, -np.inf, scores_matrix)

    rows: list[dict[str, object]] = []
    games_array = np.array(user_item.columns)

    for row_idx, user_id in enumerate(user_item.index):
        user_scores = scores_matrix[row_idx]
        if not np.isfinite(user_scores).any():
            continue

        candidate_count = min(top_k, len(user_scores))
        top_idx = np.argpartition(-user_scores, candidate_count - 1)[:candidate_count]
        top_idx = top_idx[np.argsort(-user_scores[top_idx])]

        for rank, idx in enumerate(top_idx, start=1):
            score = float(user_scores[idx])
            if not np.isfinite(score):
                continue
            rows.append(
                {
                    "user_id": user_id,
                    "rank": rank,
                    "game_title": games_array[idx],
                    "score": score,
                }
            )

    recommendations_df = pd.DataFrame(rows)
    logger.info(
        "Built recommendations for %d users (%d rows).",
        recommendations_df["user_id"].nunique() if not recommendations_df.empty else 0,
        len(recommendations_df),
    )
    return recommendations_df
