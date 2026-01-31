import re
from typing import Any, Dict, List

import polars as pl
from evaluation_embedder.src.datasets import TextDataset
from evaluation_embedder.src.datasets.preprocess import TextPreprocessor, TokenCounter
from evaluation_embedder.src.settings import (
    ChunkTextPreprocessorSettings,
    HuggingFaceTokenCounterSettings,
    MaxTokenFilterSettings,
    MinTokenFilterSettings,
    PreprocessPipelineSettings,
    ProcedureDocumentTextPreprocessorSettings,
    QuantileTokenFilterSettings,
    SigmaBandTokenFilterSettings,
)
from evaluation_embedder.src.utils import load_class


class MinTokenFilter(TextPreprocessor[MinTokenFilterSettings[Any]]):

    def __init__(self, config: MinTokenFilterSettings[Any]):
        super().__init__(config)
        self.token_counter: TokenCounter[Any] = load_class(self.config.token_counter.module_path).from_config(
            self.config.token_counter
        )

    def apply(self, ds: TextDataset[Any]) -> TextDataset[Any]:
        return ds.__class__.from_polars(
            ds.polars.with_columns(pl.col("page_content").map_elements(self.token_counter.count).alias("n_tokens"))
            .filter(pl.col("n_tokens") >= self.config.min_tokens)
            .drop("n_tokens")
        )


class MaxTokenFilter(TextPreprocessor[MaxTokenFilterSettings[Any]]):
    def __init__(self, config: MaxTokenFilterSettings[Any]):
        super().__init__(config)
        self.token_counter: TokenCounter[Any] = load_class(self.config.token_counter.module_path).from_config(
            self.config.token_counter
        )

    def apply(self, ds: TextDataset[Any]) -> TextDataset[Any]:
        return ds.__class__.from_polars(
            ds.polars.with_columns(pl.col("page_content").map_elements(self.token_counter.count).alias("n_tokens"))
            .filter(pl.col("n_tokens") <= self.config.max_tokens)
            .drop("n_tokens")
        )


class QuantileTokenFilter(TextPreprocessor[QuantileTokenFilterSettings[Any]]):
    def __init__(self, config: QuantileTokenFilterSettings[Any]):
        super().__init__(config)
        self.token_counter: TokenCounter[Any] = load_class(self.config.token_counter.module_path).from_config(
            self.config.token_counter
        )

    def apply(self, ds: TextDataset[Any]) -> TextDataset[Any]:
        df = ds.polars.with_columns(pl.col("page_content").map_elements(self.token_counter.count).alias("n_tokens"))
        cutoff = df.select(pl.col("n_tokens").quantile(self.config.q)).item()
        return ds.__class__.from_polars(df.filter(pl.col("n_tokens") <= cutoff).drop("n_tokens"))


class SigmaBandTokenFilter(TextPreprocessor[SigmaBandTokenFilterSettings[Any]]):
    def __init__(self, config: SigmaBandTokenFilterSettings[Any]):
        super().__init__(config)
        self.token_counter: TokenCounter[Any] = load_class(self.config.token_counter.module_path).from_config(
            self.config.token_counter
        )

    def apply(self, ds: TextDataset[Any]) -> TextDataset[Any]:
        df = ds.polars.with_columns(pl.col("page_content").map_elements(self.token_counter.count).alias("n_tokens"))
        mu, sigma = df.select(
            pl.col("n_tokens").mean(),
            pl.col("n_tokens").std(),
        ).row(0)
        return ds.__class__.from_polars(
            df.filter(pl.col("n_tokens").is_between(mu - self.config.z * sigma, mu + self.config.z * sigma)).drop(
                "n_tokens"
            )
        )


class ChunkTextPreprocessor(TextPreprocessor[ChunkTextPreprocessorSettings[HuggingFaceTokenCounterSettings]]):
    def __init__(
        self,
        config: ChunkTextPreprocessorSettings[HuggingFaceTokenCounterSettings],
    ) -> None:
        super().__init__(config)
        if self.config.overlap_tokens >= self.config.max_tokens:
            raise ValueError("overlap_tokens must be < max_tokens")
        self.token_counter: TokenCounter[Any] = load_class(self.config.token_counter.module_path).from_config(
            self.config.token_counter
        )
        self.chunk_size_chars = self.config.max_tokens
        self.overlap_chars = self.config.overlap_tokens

    def chunk_text_overlap(
        self,
        text: str,
        *,
        chunk_size_chars: int,
        overlap_chars: int,
    ) -> List[str]:
        if chunk_size_chars <= overlap_chars:
            raise ValueError("chunk_size_chars must be > overlap_chars")
        chunks = []
        start = 0
        text_len = len(text)
        while start < text_len:
            end = start + chunk_size_chars
            chunks.append(text[start:end])
            start += chunk_size_chars - overlap_chars
        return chunks

    def apply(self, ds: TextDataset[Any]) -> TextDataset[Any]:
        df = ds.polars

        df = df.with_columns(
            pl.col("page_content")
            .map_elements(
                lambda text: self.chunk_text_overlap(
                    text,
                    chunk_size_chars=self.chunk_size_chars,
                    overlap_chars=self.overlap_chars,
                ),
                return_dtype=pl.List(pl.String),
            )
            .alias("chunks")
        )

        df = df.with_columns(pl.col("chunks").list.len().alias("n_chunks"))

        df = (
            df.explode("chunks")
            .with_columns(
                pl.col("chunks").alias("page_content"),
                pl.int_range(0, pl.len()).over(pl.col("metadata").struct.field("doc_id")).alias("chunk_idx"),
            )
            .drop("chunks")
        )

        df = df.with_columns(
            pl.col("metadata").struct.with_fields(
                pl.col("chunk_idx"),
                pl.col("n_chunks"),
            )
        ).drop("chunk_idx", "n_chunks")
        return ds.__class__.from_polars(df)


class ProcedureDocumentTextPreprocessor(TextPreprocessor[ProcedureDocumentTextPreprocessorSettings]):

    SECTION_RE = re.compile(r"^##\s+(.*)$", re.MULTILINE)
    STEP_RE = re.compile(r"^\s*\d+\.\s+(.*)$", re.MULTILINE)

    def __init__(
        self,
        config: ProcedureDocumentTextPreprocessorSettings,
    ) -> None:
        super().__init__(config)

    def parse_procedure(self, text: str) -> Dict[str, List[str]]:
        sections: Dict[str, List[str]] = {}
        matches = list(self.__class__.SECTION_RE.finditer(text))
        for i, m in enumerate(matches):
            section = m.group(1).strip()
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            block = text[start:end]
            steps = [s.strip() for s in self.__class__.STEP_RE.findall(block)]
            if steps:
                sections[section] = steps

        return sections

    def build_procedure_document(self, text: str, title: str) -> str | None:
        sections = self.parse_procedure(text)

        if not sections:
            return None  # 👈 mark row for removal

        blocks: List[str] = []
        for section, steps in sections.items():
            block = section.upper() + ":\n"
            for s in steps:
                block += f"- {s}\n"
            blocks.append(block)

        document = f"TITLE: {title}\n" + "\n".join(blocks)
        return document

    def apply(self, ds: TextDataset[Any]) -> TextDataset[Any]:
        df = ds.polars
        df = (
            df.with_columns(
                pl.struct(
                    [
                        pl.col("page_content"),
                        pl.col("metadata").struct.field("procedure_title"),
                    ]
                )
                .map_elements(
                    lambda s: self.build_procedure_document(
                        s["page_content"],
                        s["procedure_title"],
                    ),
                    return_dtype=pl.String,
                )
                .alias("page_content")
            )
            # 👇 DROP rows where parsing failed
            .filter(pl.col("page_content").is_not_null())
        )
        df = (
            df.with_columns(pl.col("metadata").struct.field("queries").alias("query"))
            .explode("query")
            # rebuild metadata explicitly
            .with_columns(
                pl.struct(
                    pl.col("metadata").struct.field("source").alias("source"),
                    pl.col("metadata").struct.field("bucket").alias("bucket"),
                    pl.col("metadata").struct.field("procedure_title").alias("procedure_title"),
                    pl.col("metadata").struct.field("parent_topic").alias("parent_topic"),
                    pl.col("query").struct.field("query").alias("query"),
                    pl.col("query").struct.field("section").alias("query_section"),
                    pl.col("query").struct.field("step_range").alias("query_step_range"),
                ).alias("metadata")
            )
            .drop("query")
        )
        return ds.__class__.from_polars(df)


class PreprocessPipeline(TextPreprocessor[PreprocessPipelineSettings]):

    def __init__(self, config: PreprocessPipelineSettings):
        super().__init__(config)
        self.steps = self._load_steps()

    def _load_steps(self) -> List[TextPreprocessor[Any]]:
        steps = []
        for step_config in self.config.steps:
            step: TextPreprocessor[Any] = load_class(step_config.module_path)(step_config)
            steps.append(step)
        return steps

    def apply(self, ds: TextDataset[Any]) -> TextDataset[Any]:
        current = ds
        for step in self.steps:
            current = step.apply(current)
        return current
