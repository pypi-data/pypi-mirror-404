from typing import List

import torch
from evaluation_embedder.src.evaluation import Embedder
from evaluation_embedder.src.settings import (
    HuggingFaceEmbedderSettings,
    VLLMEmbedderSettings,
)
from openai import AsyncOpenAI
from transformers import AutoModel, AutoTokenizer


class VLLMEmbedder(Embedder[VLLMEmbedderSettings]):
    def __init__(self, config: VLLMEmbedderSettings):
        super().__init__(config)
        self.client = AsyncOpenAI(
            base_url=self.config.base_url,
            api_key="",  # vLLM does not require a key
        )

    async def _aembed(self, texts: List[str]) -> List[List[float]]:
        """
        Async embedding via vLLM OpenAI-compatible API.
        """
        response = await self.client.embeddings.create(
            model=self.config.model_name,
            input=texts,
        )

        # Preserve order
        return [item.embedding for item in response.data]


class HuggingFaceEmbedder(Embedder[HuggingFaceEmbedderSettings]):

    def __init__(self, config: HuggingFaceEmbedderSettings):
        super().__init__(config)

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.tokenizer_name,
            revision=self.config.revision,
            trust_remote_code=True,
        )

        self.model = AutoModel.from_pretrained(
            self.config.model_name,
            revision=self.config.revision,
            trust_remote_code=True,
        )

        self.device = torch.device(self.config.device)
        self.model.to(self.config.device)
        self.model.eval()

    @torch.no_grad()
    async def _aembed(self, texts: List[str]) -> List[List[float]]:
        encoded = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            return_tensors="pt",
        )
        encoded = {k: v.to(self.device) for k, v in encoded.items()}
        outputs = self.model(**encoded)
        hidden_states = outputs.last_hidden_state  # query: normalized
        # CLS pooling
        embeddings = hidden_states[:, 0, :]
        return embeddings.cpu().tolist()  # type: ignore[no-any-return]
