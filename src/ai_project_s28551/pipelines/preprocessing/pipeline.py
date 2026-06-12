"""Kedro pipeline wiring for preprocessing."""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import clean_data, scale_data, split_data


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=clean_data,
                inputs="steam_play_interactions",
                outputs="clean_data",
                name="clean_data_node",
            ),
            node(
                func=scale_data,
                inputs="clean_data",
                outputs="scaled_data",
                name="scale_data_node",
            ),
            node(
                func=split_data,
                inputs="scaled_data",
                outputs=["train_data", "val_data", "test_data"],
                name="split_data_node",
            ),
        ]
    )
