from evaluation_embedder.src.datasets.preprocess import TokenCounter
from evaluation_embedder.src.settings import (
    HeuristicTokenCounterSettings,
    HuggingFaceTokenCounterSettings,
)
from transformers import AutoTokenizer


class HeuristicTokenCounter(TokenCounter[HeuristicTokenCounterSettings]):

    def __init__(self, config: HeuristicTokenCounterSettings) -> None:
        super().__init__(config)

    def count(self, text: str) -> int:
        return max(1, int(len(text) / self.config.chars_per_token))


class HuggingFaceTokenCounter(TokenCounter[HuggingFaceTokenCounterSettings]):
    def __init__(self, config: HuggingFaceTokenCounterSettings) -> None:
        super().__init__(config)
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.name,
            revision=self.config.revision,
            trust_remote_code=True,
        )

    def count(self, text: str) -> int:
        return len(
            self.tokenizer(
                text,
                add_special_tokens=self.config.add_special_tokens,
                truncation=False,
                return_attention_mask=False,
                return_token_type_ids=False,
            )["input_ids"]
        )
