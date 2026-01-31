import asyncio
import logging
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document
from rank_bm25 import BM25Okapi  # type: ignore[import-untyped]

from evaluation_embedder.src.constants import TCHybridRetriever, TCRetriever
from evaluation_embedder.src.datasets import TextDataset
from evaluation_embedder.src.evaluation import (
    DenseRetriever,
    Reranker,
    Retriever,
    VectorStore,
)
from evaluation_embedder.src.settings import (
    BM25RetrieverSettings,
    DenseRetrieverSettings,
    FaissVectorStoreSettings,
    HybridRetrieverSettings,
    NomicProcessorSettings,
    QdrantVectorStoreSettings,
    RetrieverSettings,
    VLLMEmbedderSettings,
)
from evaluation_embedder.src.utils import load_class

_logger = logging.getLogger(__name__)


class BM25Retriever(Retriever[BM25RetrieverSettings]):

    def __init__(self, config: BM25RetrieverSettings) -> None:
        super().__init__(config)
        # ---- load dataset ----
        dataset: TextDataset[Any] = (
            load_class(self.config.dataset_connector.module_path).from_config(config.dataset_connector).load_text()
        )
        self.documents: List[Document] = [
            Document(
                page_content=row["page_content"],
                metadata=row.get("metadata"),
            )
            for row in dataset.iter_rows(named=True)
        ]
        # ---- tokenize corpus ----
        self.corpus_tokens = [doc.page_content.lower().split() for doc in self.documents]
        # ---- build BM25 index ----
        self.bm25 = BM25Okapi(self.corpus_tokens)
        _logger.info(f"BM25Retriever initialized | documents={len(self.documents)}")

    # --------------------------------------------------
    # Retrieval API
    # --------------------------------------------------

    async def retrieve(
        self,
        query: str,
        limit: int,
    ) -> VectorStore.QueryResponse:
        query_tokens = query.lower().split()

        scores = self.bm25.get_scores(query_tokens)

        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True,
        )[:limit]

        return self._build_response(scores, top_indices)

    async def retrieve_batch(
        self,
        queries: List[str],
        limit: int,
    ) -> List[VectorStore.QueryResponse]:
        return [await self.retrieve(query, limit) for query in queries]

    def _build_response(self, scores: List[float], indices: List[int]) -> VectorStore.QueryResponse:
        return VectorStore.QueryResponse(
            points=[
                VectorStore.ScoredPoint(
                    score=float(scores[i]),
                    document=self.documents[i],
                )
                for i in indices
            ]
        )


class HybridRetriever(Retriever[TCHybridRetriever]):
    """
    Hybrid retriever combining DenseRetriever and BM25Retriever
    using Reciprocal Rank Fusion (RRF).
    """

    def __init__(self, config: TCHybridRetriever) -> None:
        super().__init__(config)

        self.dense: DenseRetriever = load_class(self.config.dense_retriever.module_path).from_config(
            self.config.dense_retriever
        )
        self.bm25: BM25Retriever = load_class(self.config.bm25_retriever.module_path).from_config(
            self.config.bm25_retriever
        )

        _logger.info(
            f"HybridRetriever initialized | dense={type(self.dense).__name__} "
            f"| bm25={type(self.bm25).__name__} | rrf_k={self.config.rrf_k}"
        )

    # --------------------------------------------------
    # Retrieval API
    # --------------------------------------------------

    async def _retrieve(self, query: str, limit: int) -> VectorStore.QueryResponse:
        dense, bm25 = await asyncio.gather(
            self.dense.retrieve(query, limit),
            self.bm25.retrieve(query, limit),
        )
        fused = self._fuse(dense, bm25, limit)
        return fused

    async def retrieve_batch(
        self,
        queries: List[str],
        limit: int,
    ) -> List[VectorStore.QueryResponse]:

        dense_resps, bm25_resps = await asyncio.gather(
            self.dense.retrieve_batch(queries, limit),
            self.bm25.retrieve_batch(queries, limit),
        )

        return [self._fuse(d, b, limit) for d, b in zip(dense_resps, bm25_resps)]

    # --------------------------------------------------
    # Fusion logic (RRF)
    # --------------------------------------------------

    def _fuse(
        self,
        dense: VectorStore.QueryResponse,
        bm25: VectorStore.QueryResponse,
        limit: int,
    ) -> VectorStore.QueryResponse:
        scores: Dict[str, float] = {}
        documents: Dict[str, VectorStore.ScoredPoint] = {}

        def add_results(response: VectorStore.QueryResponse) -> None:
            for rank, point in enumerate(response.points):
                doc_id = point.document.page_content
                rrf_score = 1.0 / (self.config.rrf_k + rank + 1)
                scores[doc_id] = scores.get(doc_id, 0.0) + rrf_score
                documents[doc_id] = point

        add_results(dense)
        add_results(bm25)
        fused = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:limit]
        return VectorStore.QueryResponse(
            points=[
                VectorStore.ScoredPoint(
                    score=scores[doc_id],
                    document=documents[doc_id].document,
                )
                for doc_id, _ in fused
            ]
        )

    async def aclose(self) -> None:
        await self.dense.aclose()
        await self.bm25.aclose()
