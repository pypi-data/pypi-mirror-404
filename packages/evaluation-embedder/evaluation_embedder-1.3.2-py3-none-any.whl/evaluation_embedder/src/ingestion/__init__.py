import logging
from abc import ABC
from typing import Any, Generic

from evaluation_embedder.src.connectors import DatasetConnector
from evaluation_embedder.src.constants import TCTextIngestionPipeline
from evaluation_embedder.src.datasets import TextDataset
from evaluation_embedder.src.datasets.preprocess import TextPreprocessor
from evaluation_embedder.src.mixins import FromConfigMixin
from evaluation_embedder.src.utils import load_class

_logger = logging.getLogger(__name__)


class TextIngestionPipeline(
    FromConfigMixin[TCTextIngestionPipeline],
    ABC,
    Generic[TCTextIngestionPipeline],
):
    def __init__(self, config: TCTextIngestionPipeline) -> None:
        super().__init__(config)

        _logger.info(
            f"Initializing text ingestion pipeline | "
            f"class={self.__class__.__name__} | "
            f"module={self.__class__.__module__}"
        )

        _logger.info(f"Instantiating dataset connector | " f"module_path={self.config.connector.module_path}")
        self.connector: DatasetConnector[Any] = load_class(self.config.connector.module_path).from_config(
            self.config.connector
        )

        _logger.info(f"Instantiating text preprocessor | " f"module_path={self.config.preprocessor.module_path}")
        self.preprocessor: TextPreprocessor[Any] = load_class(self.config.preprocessor.module_path).from_config(
            self.config.preprocessor
        )

    def ingest(self) -> TextDataset[Any]:
        _logger.info("Starting text ingestion")

        ds = self.connector.load_text()

        _logger.info(f"Dataset loaded | " f"rows={len(ds)}")

        _logger.info(f"Applying text preprocessing | " f"preprocessor={self.preprocessor.__class__.__name__}")

        ds = self.preprocessor.apply(ds)

        _logger.info(f"Text ingestion completed | " f"rows={len(ds)}")

        return ds
