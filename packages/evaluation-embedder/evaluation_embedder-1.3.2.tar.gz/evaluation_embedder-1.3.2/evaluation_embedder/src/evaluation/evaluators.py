import asyncio
import logging
from typing import Any, Generic, List, Self, cast

import numpy as np
from langchain_core.documents import Document

from evaluation_embedder.src.constants import (
    TCDenseEvaluator,
    TCFaissEvaluator,
    TCScore,
)
from evaluation_embedder.src.datasets.polars import PolarsTextDataset
from evaluation_embedder.src.evaluation import (
    DenseRetriever,
    Evaluator,
    Retriever,
    Score,
)
from evaluation_embedder.src.evaluation.vector_stores import FaissVectorStore
from evaluation_embedder.src.settings import (
    BM25EvaluatorSettings,
    BM25RetrieverSettings,
    DenseRetrieverSettings,
    EvaluatorSettings,
    FaissEvaluatorSettings,
    HuggingFaceEmbedderSettings,
    HybridRetrieverEvaluatorSettings,
    QdrantEvaluatorSettings,
)
from evaluation_embedder.src.utils import load_class

_logger = logging.getLogger(__name__)


class DenseEvaluator(Evaluator[TCDenseEvaluator]):

    def __init__(self, config: TCDenseEvaluator) -> None:
        super().__init__(config)
        if not isinstance(self.retriever, DenseRetriever):
            raise TypeError(
                f"{self.__class__.__name__} requires a DenseRetriever, " f"got {type(self.retriever).__name__} instead."
            )


class QdrantEvaluator(DenseEvaluator[QdrantEvaluatorSettings]):
    def __init__(self, config: QdrantEvaluatorSettings):
        super().__init__(config)


class FaissEvaluator(DenseEvaluator[TCFaissEvaluator], Generic[TCFaissEvaluator]):
    def __init__(self, config: TCFaissEvaluator):
        super().__init__(config)

    @classmethod
    async def create(cls, config: TCFaissEvaluator) -> Self:
        self = cls(config)
        docs = self.get_docs()
        texts = [d.page_content for d in docs]
        embeddings = np.asarray(
            await self.retriever.embedder.aembed_documents(texts, processor=self.retriever.processor),
            dtype="float32",
        )
        vector_store = cast(FaissVectorStore, self.retriever.vector_store)
        vector_store.index = vector_store.build_faiss_index(embeddings.shape[-1])
        vector_store.add_documents(docs, embeddings)
        return self

    def get_docs(self) -> List[Document]:
        docs_idx = []
        seen = set()
        for i, row in enumerate(self.dataset.iter_rows(named=True)):
            doc_id = row["metadata"]["doc_id"]
            if doc_id not in seen:
                seen.add(doc_id)
                docs_idx.append(i)
        return PolarsTextDataset(self.dataset.polars[docs_idx]).to_langchain_documents()


class HuggingFaceFaissEvaluator(FaissEvaluator[FaissEvaluatorSettings[HuggingFaceEmbedderSettings]]):
    pass


class BM25Evaluator(Evaluator[BM25EvaluatorSettings]):
    def __init__(self, config: BM25EvaluatorSettings) -> None:
        super().__init__(config)


class HybridRetrieverEvaluator(Evaluator[HybridRetrieverEvaluatorSettings]):
    def __init__(self, config: HybridRetrieverEvaluatorSettings) -> None:
        super().__init__(config)
