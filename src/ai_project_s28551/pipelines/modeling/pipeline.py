"""Kedro pipeline wiring for the recommender modeling stage."""
from __future__ import annotations

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import build_recommendations


def create_pipeline(**_kwargs) -> Pipeline:
    """Return the modeling pipeline that builds deployable recommendations."""
    return pipeline(
        [
            node(
                func=build_recommendations,
                inputs={
                    "interactions": "clean_data",
                    "top_k": "params:recommender.top_k",
                    "min_game_users": "params:recommender.min_game_users",
                },
                outputs="recommendations_top5",
                name="build_recommendations",
            ),
        ]
    )
