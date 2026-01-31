from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    Iterator,
    List,
    Protocol,
    Tuple,
    Union,
    runtime_checkable,
)

import polars as pl
from evaluation_embedder.src.constants import TDataset
from langchain_core.documents import Document

if TYPE_CHECKING:

    from evaluation_embedder.src.datasets import TextDataset


@runtime_checkable
class SupportsPolarsDataset(Protocol[TDataset]):
    @property
    def polars(self) -> pl.DataFrame: ...

    def to_polars(self) -> pl.DataFrame: ...

    @classmethod
    def from_polars(cls, df: Union[pl.DataFrame, pl.LazyFrame]) -> "TextDataset[TDataset]":
        raise NotImplementedError


class TextDatasetMixin(SupportsPolarsDataset[TDataset], Generic[TDataset]):
    REQUIRED_COLUMNS = {"page_content", "metadata"}

    def _validate_schema(self) -> None:
        df = self.polars
        missing = self.REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(
                f"{self.__class__.__name__} requires columns {self.REQUIRED_COLUMNS}, " f"but missing {missing}"
            )

    def iter_documents(self) -> Iterator[Document]:
        df = self.to_polars()
        for row in df.iter_rows(named=True):
            yield Document(
                page_content=row["page_content"],
                metadata=row["metadata"],
            )

    @classmethod
    def from_records(
        cls,
        records: List[Tuple[str, Dict[str, Any]]],
    ) -> "TextDataset[TDataset]":
        if not records:
            raise ValueError("records must be non-empty")
        df = pl.DataFrame(
            {
                "page_content": [text for text, _ in records],
                "metadata": [meta for _, meta in records],
            }
        )
        return cls.from_polars(df)

    def dump_documents(
        self,
        out_dir: str,
        prefix: str = "doc",
        ext: str = ".md",
        encoding: str = "utf-8",
    ) -> None:
        out_dir_path = Path(out_dir)
        out_dir_path.mkdir(parents=True, exist_ok=True)
        for i, row in enumerate(self.polars.iter_rows(named=True)):
            path = out_dir_path / f"{prefix}_{i:05d}{ext}"
            path.write_text(row["page_content"], encoding=encoding)

    def to_langchain_documents(
        self,
    ) -> List[Document]:
        docs: list[Document] = []
        for row in self.polars.iter_rows(named=True):
            docs.append(
                Document(
                    page_content=row["page_content"],
                    metadata=row["metadata"],
                )
            )
        return docs

    @classmethod
    def from_documents(cls, docs: List[Document]) -> "TextDataset[TDataset]":
        df = pl.DataFrame(
            {
                "page_content": [d.page_content for d in docs],
                "metadata": [d.metadata or {} for d in docs],
            }
        )
        return cls.from_polars(df)
