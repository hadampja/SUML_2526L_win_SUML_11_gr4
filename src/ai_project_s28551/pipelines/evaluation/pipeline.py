from kedro.pipeline import Pipeline, node, pipeline

from .nodes import evaluate_recommender


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=evaluate_recommender,
                inputs={
                    "recommendations": "recommendations_top5",
                    "interactions": "clean_data",
                    "holdout_fraction": "params:recommender.holdout_fraction",
                    "random_state": "params:recommender.random_state",
                    "top_k": "params:recommender.top_k",
                    "min_game_users": "params:recommender.min_game_users",
                },
                outputs="recommender_metrics",
                name="evaluate_recommender",
            ),
        ]
    )
