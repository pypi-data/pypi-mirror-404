from evaluation_embedder.src.constants import EmbeddingPurposeEnum
from evaluation_embedder.src.evaluation import Processor
from evaluation_embedder.src.settings import NomicProcessorSettings


class NomicProcessor(Processor[NomicProcessorSettings]):

    def __init__(self, config: NomicProcessorSettings) -> None:
        super().__init__(config)

    def __call__(self, text: str, purpose: EmbeddingPurposeEnum) -> str:
        if purpose == EmbeddingPurposeEnum.DOCUMENT:
            return f"search_document: {text}"
        if purpose == EmbeddingPurposeEnum.QUERY:
            return f"search_query: {text}"
        raise ValueError(f"Unsupported embedding purpose {purpose}")
