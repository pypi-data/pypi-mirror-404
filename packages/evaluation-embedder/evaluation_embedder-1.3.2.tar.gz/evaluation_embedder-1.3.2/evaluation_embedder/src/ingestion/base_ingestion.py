from evaluation_embedder.src.constants import TCTextIngestionPipeline
from evaluation_embedder.src.ingestion import TextIngestionPipeline
from evaluation_embedder.src.settings import (
    MinioDatasetConnectorSettings,
    PreprocessPipelineSettings,
    TextIngestionPipelineSettings,
)


class BaseTextIngestionPipeline(
    TextIngestionPipeline[TextIngestionPipelineSettings[MinioDatasetConnectorSettings, PreprocessPipelineSettings]]
):

    def __init__(self, config: TCTextIngestionPipeline) -> None:
        super().__init__(config)
