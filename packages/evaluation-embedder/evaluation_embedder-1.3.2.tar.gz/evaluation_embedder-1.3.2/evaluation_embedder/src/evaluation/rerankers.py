import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from evaluation_embedder.src.evaluation import Reranker, VectorStore
from evaluation_embedder.src.settings import HFRerankerSettings


class HFReranker(Reranker[HFRerankerSettings]):

    def __init__(self, config: HFRerankerSettings) -> None:
        super().__init__(config)

        self.tokenizer = AutoTokenizer.from_pretrained(
            config.model_name,
            revision=config.revision,
        )
        self.model = AutoModelForSequenceClassification.from_pretrained(
            config.model_name,
            revision=config.revision,
        ).to(config.device)

        self.model.eval()

    async def rerank(
        self,
        query: str,
        response: VectorStore.QueryResponse,
        limit: int,
    ) -> VectorStore.QueryResponse:

        if not response.points:
            return response

        pairs = [(query, p.document.page_content) for p in response.points]

        with torch.no_grad():
            inputs = self.tokenizer(
                pairs,
                padding=True,
                truncation=True,
                return_tensors="pt",
            ).to(self.model.device)

            scores = self.model(**inputs).logits.squeeze(-1)

        reranked = sorted(
            zip(scores.tolist(), response.points),
            key=lambda x: x[0],
            reverse=True,
        )[:limit]

        return VectorStore.QueryResponse(
            points=[
                VectorStore.ScoredPoint(
                    score=float(score),
                    document=point.document,
                )
                for score, point in reranked
            ]
        )
