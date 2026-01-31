from typing import Annotated, Any, Generic, List, Literal, Optional, Union

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from evaluation_embedder.src.constants import (
    CONFIG_PATH,
    FAISSIndexType,
    TCDatasetConnector,
    TCDenseRetriever,
    TCEmbedder,
    TCProcessor,
    TCReranker,
    TCRetriever,
    TCScore,
    TCTextPreprocessor,
    TCTokenCounter,
    TCVectorStore,
)


class FromConfigMixinSettings(BaseSettings):
    module_path: str
    model_config = SettingsConfigDict(
        yaml_file=CONFIG_PATH,
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            YamlConfigSettingsSource(settings_cls),
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )


class DatasetConnectorSettings(FromConfigMixinSettings):
    pass


class ParquetDatasetConnectorSettings(DatasetConnectorSettings):
    path: str
    lazy: bool


class MinioDatasetConnectorSettings(DatasetConnectorSettings):
    endpoint: str
    bucket: str
    key: str
    access_key: SecretStr
    secret_key: SecretStr
    model_config = SettingsConfigDict(env_prefix='MINIO_', extra="ignore")


class EmbedderSettings(FromConfigMixinSettings):
    model_name: str


class VLLMEmbedderSettings(EmbedderSettings):
    base_url: str


class HuggingFaceEmbedderSettings(EmbedderSettings):
    model_name: str
    tokenizer_name: Optional[str]
    revision: Optional[str]
    device: str


class ProcessorSettings(FromConfigMixinSettings):
    pass


class NomicProcessorSettings(ProcessorSettings):
    pass


class ScoreSettings(BaseSettings):
    module_path: str


class RecallAtKScoreSettings(ScoreSettings):
    k: int


class PrecisionAtKScoreSettings(ScoreSettings):
    k: int


class HitAtKScoreSettings(ScoreSettings):
    k: int


class MRRAtKScoreSettings(ScoreSettings):
    k: int


class VectorStoreSettings(FromConfigMixinSettings):
    pass


class QdrantVectorStoreSettings(VectorStoreSettings):
    url: str
    collection_name: str
    timeout: Optional[int]


class FaissVectorStoreSettings(VectorStoreSettings):
    index_type: FAISSIndexType
    normalize: bool

    @field_validator("index_type", mode="before")
    @classmethod
    def normalize_index_type(cls, v: Any) -> FAISSIndexType:
        if isinstance(v, FAISSIndexType):
            return v
        if isinstance(v, str):
            try:
                return FAISSIndexType(v.lower())
            except ValueError as e:
                raise ValueError(f"Invalid FAISS index_type '{v}'.") from e
        raise TypeError(f"index_type must be a string or FAISSIndexType, got {type(v).__name__}")


class RerankerSettings(FromConfigMixinSettings):
    pass


class HFRerankerSettings(RerankerSettings):
    model_name: str
    revision: Optional[str]
    device: str


class RetrieverSettings(FromConfigMixinSettings, Generic[TCReranker]):
    reranker: Optional[TCReranker]


class BM25RetrieverSettings(
    RetrieverSettings[TCReranker],
    Generic[TCDatasetConnector, TCReranker],
):
    dataset_connector: TCDatasetConnector


class DenseRetrieverSettings(
    RetrieverSettings[TCReranker], Generic[TCEmbedder, TCVectorStore, TCProcessor, TCReranker]
):
    embedder: TCEmbedder
    vector_store: TCVectorStore
    processor: TCProcessor


class HybridRetrieverSettings(RetrieverSettings[TCReranker], Generic[TCDenseRetriever, TCDatasetConnector, TCReranker]):
    dense_retriever: TCDenseRetriever
    bm25_retriever: BM25RetrieverSettings[TCDatasetConnector, TCReranker]
    rrf_k: int


class BM25QdrantVLLMHybridRetrieverSettings(
    HybridRetrieverSettings[
        DenseRetrieverSettings[
            VLLMEmbedderSettings, QdrantVectorStoreSettings, NomicProcessorSettings, HFRerankerSettings
        ],
        MinioDatasetConnectorSettings,
        HFRerankerSettings,
    ]
):
    pass


class EvaluatorSettings(FromConfigMixinSettings, Generic[TCDatasetConnector, TCRetriever, TCScore]):
    dataset_connector: TCDatasetConnector
    retriever: TCRetriever
    scores: List[TCScore]


class QdrantEvaluatorSettings(
    EvaluatorSettings[
        MinioDatasetConnectorSettings,
        DenseRetrieverSettings[
            VLLMEmbedderSettings, QdrantVectorStoreSettings, NomicProcessorSettings, HFRerankerSettings
        ],
        RecallAtKScoreSettings,
    ]
):
    pass


class FaissEvaluatorSettings(
    EvaluatorSettings[
        MinioDatasetConnectorSettings,
        DenseRetrieverSettings[TCEmbedder, FaissVectorStoreSettings, NomicProcessorSettings, HFRerankerSettings],
        RecallAtKScoreSettings,
    ],
    Generic[TCEmbedder],
):
    pass


class BM25EvaluatorSettings(
    EvaluatorSettings[
        MinioDatasetConnectorSettings,
        BM25RetrieverSettings[MinioDatasetConnectorSettings, HFRerankerSettings],
        RecallAtKScoreSettings,
    ]
):
    pass


class HybridRetrieverEvaluatorSettings(
    EvaluatorSettings[
        MinioDatasetConnectorSettings,
        BM25QdrantVLLMHybridRetrieverSettings,
        RecallAtKScoreSettings,
    ]
):
    pass


class TextPreprocessorSettings(FromConfigMixinSettings):
    pass


class ProcedureDocumentTextPreprocessorSettings(TextPreprocessorSettings):
    kind: Literal["procedure"]


class TokenCounterSettings(FromConfigMixinSettings):
    pass


class HeuristicTokenCounterSettings(TokenCounterSettings):
    chars_per_token: int


class HuggingFaceTokenCounterSettings(TokenCounterSettings):
    name: str
    add_special_tokens: bool
    revision: Optional[str]


class TokenFilterSettings(TextPreprocessorSettings, Generic[TCTokenCounter]):
    token_counter: TCTokenCounter


class MinTokenFilterSettings(TokenFilterSettings[TCTokenCounter], Generic[TCTokenCounter]):
    kind: Literal["min_tokens"]
    min_tokens: int


class MaxTokenFilterSettings(TokenFilterSettings[TCTokenCounter], Generic[TCTokenCounter]):
    kind: Literal["max_tokens"]
    max_tokens: int


class QuantileTokenFilterSettings(TokenFilterSettings[TCTokenCounter], Generic[TCTokenCounter]):
    kind: Literal["quantile"]
    q: float


class SigmaBandTokenFilterSettings(TokenFilterSettings[TCTokenCounter], Generic[TCTokenCounter]):
    kind: Literal["sigma"]
    z: float


class ChunkTextPreprocessorSettings(TextPreprocessorSettings, Generic[TCTokenCounter]):
    kind: Literal["chunk"]
    token_counter: TCTokenCounter
    max_tokens: int
    overlap_tokens: int


AnyTextPreprocessorSettings = Annotated[
    Union[
        MinTokenFilterSettings[HuggingFaceTokenCounterSettings],
        MaxTokenFilterSettings[HuggingFaceTokenCounterSettings],
        QuantileTokenFilterSettings[HuggingFaceTokenCounterSettings],
        SigmaBandTokenFilterSettings[HuggingFaceTokenCounterSettings],
        ChunkTextPreprocessorSettings[HuggingFaceTokenCounterSettings],
        ProcedureDocumentTextPreprocessorSettings,
    ],
    Field(discriminator="kind"),
]


class PreprocessPipelineSettings(TextPreprocessorSettings):
    kind: Literal["steps"]
    steps: List[AnyTextPreprocessorSettings]


class TextIngestionPipelineSettings(FromConfigMixinSettings, Generic[TCDatasetConnector, TCTextPreprocessor]):
    connector: TCDatasetConnector
    preprocessor: TCTextPreprocessor
