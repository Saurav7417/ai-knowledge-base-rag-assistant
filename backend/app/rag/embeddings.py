import abc
import hashlib
import re
import math
from typing import List
import numpy as np
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class BaseEmbeddingProvider(abc.ABC):
    @property
    @abc.abstractmethod
    def dimension(self) -> int:
        pass

    @abc.abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        pass

    @abc.abstractmethod
    def embed_query(self, text: str) -> List[float]:
        pass


class DeterministicMockEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic pseudo-semantic embedding generator for offline development,
    CI tests, and reproducible benchmarks without requiring external API keys.
    Uses token hashing into a high-dimensional sparse bag-of-features,
    random projection via seed hashing, and L2 unit-norm scaling.
    """
    def __init__(self, dimension: int = 1536):
        self._dim = dimension

    @property
    def dimension(self) -> int:
        return self._dim

    def _text_to_vector(self, text: str) -> List[float]:
        vec = np.zeros(self._dim, dtype=np.float32)
        words = re.findall(r"\w+", text.lower())
        if not words:
            # Return uniform unit vector
            u = np.ones(self._dim, dtype=np.float32)
            return (u / np.linalg.norm(u)).tolist()

        # Feature hashing for words and character bi-grams
        for word in words:
            # Word feature hash
            h_val = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx1 = h_val % self._dim
            sign1 = 1.0 if ((h_val >> 16) & 1) else -1.0
            vec[idx1] += sign1 * 1.5

            # Word prefix/suffix subword features
            if len(word) >= 4:
                prefix_h = int(hashlib.sha256(word[:4].encode("utf-8")).hexdigest(), 16)
                idx2 = prefix_h % self._dim
                vec[idx2] += 0.8

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        else:
            vec[0] = 1.0
        return vec.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._text_to_vector(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._text_to_vector(text)


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """Production OpenAI embedding provider supporting text-embedding-3-small/large."""
    def __init__(self, api_key: str, model: str = "text-embedding-3-small", base_url: str = "https://api.openai.com/v1"):
        import openai
        self._model = model
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self._dim = 1536 if "small" in model or "ada" in model else 3072

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # Process in batches of 64
        batch_size = 64
        all_embeddings: List[List[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = [t if t.strip() else "empty document chunk" for t in texts[i:i + batch_size]]
            resp = self.client.embeddings.create(
                input=batch,
                model=self._model
            )
            all_embeddings.extend([item.embedding for item in resp.data])
        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        clean_text = text if text.strip() else "empty query"
        resp = self.client.embeddings.create(
            input=[clean_text],
            model=self._model
        )
        return resp.data[0].embedding


def get_embedding_provider() -> BaseEmbeddingProvider:
    provider = settings.EMBEDDING_PROVIDER.lower()
    if provider == "openai" and settings.OPENAI_API_KEY:
        try:
            return OpenAIEmbeddingProvider(
                api_key=settings.OPENAI_API_KEY,
                model=settings.EMBEDDING_MODEL,
                base_url=settings.OPENAI_BASE_URL
            )
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI embedding provider: {e}. Falling back to deterministic mock.")
            return DeterministicMockEmbeddingProvider(dimension=settings.EMBEDDING_DIMENSION)
    
    return DeterministicMockEmbeddingProvider(dimension=settings.EMBEDDING_DIMENSION)
