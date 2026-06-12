from kedro.pipeline import Pipeline, node, pipeline

from ai_project_s28551.pipelines.eda.nodes import (
    compute_basic_stats,
    compute_correlations,
    compute_missing_values,
    compute_outliers,
    prepare_steam_play,
    save_basic_plots,
    summarize_data_quality,
)


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=prepare_steam_play,
                inputs="steam_raw",
                outputs="steam_play_interactions",
                name="prepare_steam_play",
            ),
            node(
                func=compute_basic_stats,
                inputs="steam_play_interactions",
                outputs="eda_stats",
                name="compute_basic_stats",
            ),
            node(
                func=compute_missing_values,
                inputs="steam_play_interactions",
                outputs="eda_missing",
                name="compute_missing_values",
            ),
            node(
                func=compute_outliers,
                inputs="steam_play_interactions",
                outputs="eda_outliers",
                name="compute_outliers",
            ),
            node(
                func=summarize_data_quality,
                inputs="steam_play_interactions",
                outputs="eda_quality_report",
                name="summarize_data_quality",
            ),
            node(
                func=compute_correlations,
                inputs="steam_play_interactions",
                outputs="eda_correlations",
                name="compute_correlations",
            ),
            node(
                func=save_basic_plots,
                inputs="steam_play_interactions",
                outputs=None,
                name="save_basic_plots",
            ),
        ]
    )
