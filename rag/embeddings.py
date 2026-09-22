"""
IP-SAKTI SAHAYAK
Embeddings Module
==================
Wraps BAAI/bge-m3 (multilingual: English/Hindi/Odia) behind a small
singleton service so the model is loaded once, not per-request
(spec Section 55). Embeddings are L2-normalized so inner product ==
cosine similarity, which is what the FAISS index expects.

Degrades gracefully: if sentence-transformers / the model weights are
unavailable (e.g. no network), falls back to a deterministic lightweight
hashing-based embedding so the rest of the pipeline keeps functioning
in a degraded-but-alive state rather than crashing.
"""

import logging
import hashlib
import numpy as np
from typing import List

from config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model = None
            cls._instance._dimension = settings.EMBEDDING_DIMENSION
            cls._instance._backend = "uninitialized"
        return cls._instance

    def _load_model(self):
        if self._model is not None or self._backend == "fallback":
            return
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL, model_kwargs={"use_safetensors": False})
            self._backend = "sentence-transformers"
            logger.info("Loaded embedding model %s", settings.EMBEDDING_MODEL)
        except Exception as e:
            logger.warning(
                "Could not load embedding model '%s' (%s). Falling back to a lightweight "
                "hashing-based embedding — retrieval quality will be reduced until the "
                "real model is available.",
                settings.EMBEDDING_MODEL, e,
            )
            self._backend = "fallback"

    def embed(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self._dimension), dtype="float32")
        self._load_model()
        if self._backend == "sentence-transformers":
            vectors = self._model.encode(
                texts, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False
            )
            return vectors.astype("float32")
        return np.stack([self._fallback_embed(t) for t in texts]).astype("float32")

    def embed_one(self, text: str) -> np.ndarray:
        return self.embed([text])[0]

    def _fallback_embed(self, text: str) -> np.ndarray:
        """
        Deterministic, dependency-free embedding used only when the real
        model can't be loaded. Not semantically meaningful beyond crude
        token-hash overlap — purely keeps the pipeline from crashing.
        """
        vec = np.zeros(self._dimension, dtype="float32")
        for token in text.lower().split():
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            vec[h % self._dimension] += 1.0
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    @property
    def backend(self) -> str:
        self._load_model()
        return self._backend

    @property
    def dimension(self) -> int:
        return self._dimension


embedding_service = EmbeddingService()


# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    vecs = embedding_service.embed(["Section 3(d) of the Patents Act", "Geographical Indication registration"])
    print("backend:", embedding_service.backend)
    print("shape:", vecs.shape)
    assert vecs.shape[0] == 2
    print("embeddings self-test passed.")
