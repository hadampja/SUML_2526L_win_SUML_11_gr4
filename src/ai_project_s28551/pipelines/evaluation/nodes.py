"""Evaluation nodes for the Steam recommender."""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from ai_project_s28551.pipelines.modeling.nodes import build_recommendations

logger = logging.getLogger(__name__)


def evaluate_recommender(
    recommendations: pd.DataFrame,
    interactions: pd.DataFrame,
    holdout_fraction: float = 0.2,
    random_state: int = 42,
    top_k: int = 5,
    min_game_users: int = 5,
) -> dict[str, float]:
    """Compute Precision@K, Recall@K and catalogue coverage.

    Evaluation holds out a fraction of each multi-interaction user's played
    games, rebuilds recommendations from the remaining interactions, and checks
    how often held-out games appear in the Top-K list.
    """
    logger.info("Evaluating recommender (Precision@%d / Recall@%d).", top_k, top_k)

    inter = interactions.copy()
    inter = inter.dropna(subset=["user_id", "game_title", "play_time_hours"])
    inter["play_time_hours"] = pd.to_numeric(
        inter["play_time_hours"], errors="coerce"
    )
    inter = inter[inter["play_time_hours"] > 0]
    inter = inter.drop_duplicates(subset=["user_id", "game_title"])

    rng = np.random.default_rng(random_state)
    holdout: dict[object, set[str]] = {}
    train_rows: list[pd.DataFrame] = []

    for user_id, group in inter.groupby("user_id"):
        if len(group) < 2:
            train_rows.append(group)
            continue

        n_holdout = max(1, int(round(len(group) * holdout_fraction)))
        n_holdout = min(n_holdout, len(group) - 1)
        sampled = group.sample(n=n_holdout, random_state=int(rng.integers(0, 2**31 - 1)))
        holdout[user_id] = set(sampled["game_title"].tolist())
        train_rows.append(group.drop(sampled.index))

    if not holdout:
        logger.warning("No users with enough interactions for hold-out evaluation.")
        return {
            "precision_at_k": 0.0,
            "recall_at_k": 0.0,
            "coverage": 0.0,
            "users_evaluated": 0.0,
            "users_with_recommendations": 0.0,
            "unique_recommended_games": 0.0,
        }

    train_df = pd.concat(train_rows, ignore_index=True)
    train_recs = build_recommendations(
        train_df, top_k=top_k, min_game_users=min_game_users
    )
    recs_by_user = train_recs.groupby("user_id")["game_title"].apply(list).to_dict()

    precisions: list[float] = []
    recalls: list[float] = []
    for user_id, held_games in holdout.items():
        user_recs = recs_by_user.get(user_id, [])[:top_k]
        if not user_recs:
            continue
        hits = sum(1 for game in user_recs if game in held_games)
        precisions.append(hits / top_k)
        recalls.append(hits / len(held_games))

    catalogue = set(inter["game_title"].unique())
    recommended = (
        set(recommendations["game_title"].unique()) if not recommendations.empty else set()
    )
    coverage = len(recommended) / len(catalogue) if catalogue else 0.0

    metrics = {
        "precision_at_k": float(np.mean(precisions)) if precisions else 0.0,
        "recall_at_k": float(np.mean(recalls)) if recalls else 0.0,
        "coverage": float(coverage),
        "users_evaluated": float(len(precisions)),
        "users_with_recommendations": float(
            recommendations["user_id"].nunique() if not recommendations.empty else 0
        ),
        "unique_recommended_games": float(
            recommendations["game_title"].nunique() if not recommendations.empty else 0
        ),
    }
    logger.info("Recommender metrics: %s", metrics)
    return metrics
