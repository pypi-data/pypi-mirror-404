from typing import List

from evaluation_embedder.src.evaluation import Score
from evaluation_embedder.src.settings import (
    HitAtKScoreSettings,
    MRRAtKScoreSettings,
    PrecisionAtKScoreSettings,
    RecallAtKScoreSettings,
)


class RecallAtK(Score[RecallAtKScoreSettings]):

    def __call__(self, hits: List[bool]) -> Score.ScoreResult:
        hits_k = hits[: self.config.k]
        value = sum(hits_k) / len(hits_k) if hits_k else 0.0

        return Score.ScoreResult(
            name=f"Recall@{self.config.k}",
            value=value,
        )


class PrecisionAtK(Score[PrecisionAtKScoreSettings]):
    def __call__(self, hits: List[bool]) -> Score.ScoreResult:
        hits_k = hits[: self.config.k]
        value = sum(hits_k) / self.config.k
        return Score.ScoreResult(
            name=f"Precision@{self.config.k}",
            value=value,
        )


class HitAtK(Score[HitAtKScoreSettings]):

    def __call__(self, hits: List[bool]) -> Score.ScoreResult:
        hits_k = hits[: self.config.k]
        value = 1.0 if any(hits_k) else 0.0

        return Score.ScoreResult(
            name=f"Hit@{self.config.k}",
            value=value,
        )


class MRRAtK(Score[MRRAtKScoreSettings]):

    def __call__(self, hits: List[bool]) -> Score.ScoreResult:
        value = 0.0

        for rank, is_hit in enumerate(hits[: self.config.k], start=1):
            if is_hit:
                value = 1.0 / rank
                break

        return Score.ScoreResult(
            name=f"MRR@{self.config.k}",
            value=value,
        )
