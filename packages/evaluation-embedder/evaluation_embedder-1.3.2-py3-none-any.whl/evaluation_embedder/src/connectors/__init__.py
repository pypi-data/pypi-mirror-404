import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, Union

import polars as pl
from evaluation_embedder.src.constants import TCDatasetConnector
from evaluation_embedder.src.mixins import FromConfigMixin

if TYPE_CHECKING:
    from evaluation_embedder.src.datasets import Dataset, TextDataset

_logger = logging.getLogger(__name__)


class DatasetConnector(
    FromConfigMixin[TCDatasetConnector],
    ABC,
    Generic[TCDatasetConnector],
):
    def __init__(self, config: TCDatasetConnector):
        super().__init__(config)

        _logger.info(
            f"Initializing dataset connector | "
            f"class={self.__class__.__name__} | "
            f"module={self.__class__.__module__}"
        )

    @abstractmethod
    def _load(self) -> Union[pl.DataFrame, pl.LazyFrame]:
        """
        Load raw data as Polars DataFrame or LazyFrame.
        """
        raise NotImplementedError()

    @abstractmethod
    def to(self, ds: "Dataset[Any]") -> None:
        raise NotImplementedError()

    def load(self) -> "Dataset[Union[pl.DataFrame, pl.LazyFrame]]":
        from evaluation_embedder.src.datasets.polars import PolarsDataset

        _logger.info(f"Loading dataset | connector={self.__class__.__name__}")

        df = self._load()
        self._log_polars_info(df)

        return PolarsDataset.from_polars(df)

    def load_text(self) -> "TextDataset[Union[pl.DataFrame, pl.LazyFrame]]":
        from evaluation_embedder.src.datasets.polars import PolarsTextDataset

        _logger.info(f"Loading text dataset | connector={self.__class__.__name__}")

        df = self._load()
        self._log_polars_info(df)

        return PolarsTextDataset.from_polars(df)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _log_polars_info(self, df: Union[pl.DataFrame, pl.LazyFrame]) -> None:
        """
        Log dataset structure without forcing materialization.
        """
        if isinstance(df, pl.DataFrame):
            schema = df.schema
            _logger.info(f"Loaded DataFrame | " f"columns={len(schema)} | " f"schema={list(schema.items())}")
