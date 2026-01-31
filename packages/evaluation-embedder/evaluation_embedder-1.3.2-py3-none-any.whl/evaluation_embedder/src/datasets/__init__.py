import logging
from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    Iterable,
    Iterator,
    Literal,
    Optional,
    Self,
    Tuple,
    Union,
    overload,
)

import polars as pl
from evaluation_embedder.src.constants import TDataset
from evaluation_embedder.src.datasets.mixins import TextDatasetMixin
from evaluation_embedder.src.utils import _get_minio_connector, _get_parquet_connector
from polars._typing import ColumnNameOrSelector, IntoExpr, IntoExprColumn

if TYPE_CHECKING:
    pass
_logger = logging.getLogger(__name__)


class Dataset(ABC, Generic[TDataset]):
    def __init__(self, service: TDataset):
        super().__init__()
        self.service = service
        self._polars: Optional[pl.DataFrame] = None
        self._lazy_polars: Optional[pl.LazyFrame] = None

    @classmethod
    @abstractmethod
    def from_polars(cls, df: Union[pl.DataFrame, pl.LazyFrame]) -> Self:
        raise NotImplementedError

    @abstractmethod
    def to_polars(self) -> pl.DataFrame:
        raise NotImplementedError

    @abstractmethod
    def to_lazy_polars(self) -> pl.LazyFrame:
        raise NotImplementedError

    @classmethod
    def from_parquet(
        cls,
        path: str,
        *,
        lazy: bool = True,
    ) -> "Dataset[Union[pl.DataFrame, pl.LazyFrame]]":
        return _get_parquet_connector(path, lazy=lazy).load()

    def to_parquet(self, path: str, *, lazy: bool = True) -> None:
        return _get_parquet_connector(path, lazy=lazy).to(self)

    @classmethod
    def from_minio(
        cls,
        bucket: str,
        key: str,
        endpoint: str,
        access_key: str,
        secret_key: str,
    ) -> "Dataset[Union[pl.DataFrame, pl.LazyFrame]]":
        return _get_minio_connector(bucket, key, endpoint, access_key, secret_key).load()

    def to_minio(self, bucket: str, key: str, endpoint: str, access_key: str, secret_key: str) -> None:
        return _get_minio_connector(bucket, key, endpoint, access_key, secret_key).to(self)

    @property
    def polars(self) -> pl.DataFrame:
        if self._polars is None:
            self._polars = self.to_polars()
        return self._polars

    @property
    def lazy_polars(self) -> pl.LazyFrame:
        if self._lazy_polars is None:
            self._lazy_polars = self.to_lazy_polars()
        return self._lazy_polars

    @property
    def polars_shape(self) -> Tuple[int, int]:
        return self.polars.shape

    def with_columns(
        self,
        *exprs: IntoExpr | Iterable[IntoExpr],
        **named_exprs: IntoExpr,
    ) -> Self:
        df = self.polars.with_columns(*exprs, **named_exprs)
        return self.__class__.from_polars(df)

    def filter(
        self,
        *predicates: (IntoExprColumn | Iterable[IntoExprColumn] | bool | list[bool]),
        **constraints: Any,
    ) -> Self:
        return self.__class__.from_polars(self.polars.filter(*predicates, **constraints))

    def drop(
        self,
        *columns: ColumnNameOrSelector | Iterable[ColumnNameOrSelector],
        strict: bool = True,
    ) -> Self:
        return self.__class__.from_polars(self.polars.drop(*columns, strict=strict))

    def __len__(self) -> int:
        return self.polars_shape[0]

    @overload
    def iter_rows(self, *, named: Literal[False] = ..., buffer_size: int = ...) -> Iterator[Tuple[Any, ...]]: ...

    @overload
    def iter_rows(self, *, named: Literal[True], buffer_size: int = ...) -> Iterator[Dict[str, Any]]: ...

    def iter_rows(
        self, *, named: Literal[False, True] = False, buffer_size: int = 512
    ) -> Iterator[Tuple[Any, ...]] | Iterator[Dict[str, Any]]:
        df_stream = self.lazy_polars.collect(streaming=True)  # type: ignore[call-overload]
        return df_stream.iter_rows(named=named, buffer_size=buffer_size)  # type: ignore[no-any-return]


class TextDataset(Dataset[TDataset], TextDatasetMixin[TDataset], Generic[TDataset]):

    def __init__(self, service: TDataset):
        super().__init__(service)
        self._validate_schema()

    @classmethod
    def from_parquet(
        cls,
        path: str,
        *,
        lazy: bool = True,
    ) -> "TextDataset[Union[pl.DataFrame, pl.LazyFrame]]":
        return _get_parquet_connector(path, lazy=lazy).load_text()

    @classmethod
    def from_minio(
        cls,
        bucket: str,
        key: str,
        endpoint: str,
        access_key: str,
        secret_key: str,
    ) -> "TextDataset[Union[pl.DataFrame, pl.LazyFrame]]":
        return _get_minio_connector(bucket, key, endpoint, access_key, secret_key).load_text()
