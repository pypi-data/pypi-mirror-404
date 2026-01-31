from typing import TYPE_CHECKING, Any, Union

import polars as pl
from evaluation_embedder.src.connectors import DatasetConnector
from evaluation_embedder.src.settings import ParquetDatasetConnectorSettings

if TYPE_CHECKING:
    from evaluation_embedder.src.datasets import Dataset


class ParquetDatasetConnector(DatasetConnector[ParquetDatasetConnectorSettings]):

    def __init__(self, config: ParquetDatasetConnectorSettings):
        super().__init__(config)

    def _load(self) -> Union[pl.DataFrame, pl.LazyFrame]:
        return pl.scan_parquet(self.config.path) if self.config.lazy else pl.read_parquet(self.config.path)

    def to(self, ds: "Dataset[Any]") -> None:
        ds.polars.write_parquet(self.config.path)
