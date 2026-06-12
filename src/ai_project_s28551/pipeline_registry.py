from typing import Dict

from kedro.pipeline import Pipeline

from ai_project_s28551.pipelines import eda as eda_pipeline
from ai_project_s28551.pipelines import preprocessing as preprocessing_pipeline
from ai_project_s28551.pipelines import modeling as modeling_pipeline
from ai_project_s28551.pipelines import evaluation as evaluation_pipeline

def register_pipelines() -> Dict[str, Pipeline]:
    """Register the project's pipelines."""
    eda = eda_pipeline.create_pipeline()
    preprocessing = preprocessing_pipeline.create_pipeline()
    modeling = modeling_pipeline.create_pipeline()
    evaluation = evaluation_pipeline.create_pipeline()
    full_pipeline = eda + preprocessing + modeling + evaluation

    return {
        "__default__": full_pipeline,
        "full": full_pipeline,
        "eda": eda,
        "preprocessing": preprocessing,
        "modeling": modeling,
        "evaluation": evaluation,
    }
