from abc import ABC, abstractmethod
from typing import Any, Generic

from evaluation_embedder.src.constants import TCTextPreprocessor, TCTokenCounter
from evaluation_embedder.src.datasets.polars import TextDataset
from evaluation_embedder.src.mixins import FromConfigMixin


class TextPreprocessor(FromConfigMixin[TCTextPreprocessor], ABC, Generic[TCTextPreprocessor]):

    def __init__(self, config: TCTextPreprocessor) -> None:
        self.config = config

    @abstractmethod
    def apply(self, ds: TextDataset[Any]) -> TextDataset[Any]:
        raise NotImplementedError


class TokenCounter(FromConfigMixin[TCTokenCounter], ABC, Generic[TCTokenCounter]):
    def __init__(self, config: TCTokenCounter) -> None:
        self.config = config

    @abstractmethod
    def count(self, text: str) -> int:
        raise NotImplementedError()

    def count_batch(self, texts: list[str]) -> list[int]:
        return [self.count(t) for t in texts]
