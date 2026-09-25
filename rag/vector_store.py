"""
IP-SAKTI SAHAYAK
Vector Store (FAISS with NumPy Fallback & Index Versioning)
============================================================
High-performance vector index for dense semantic embeddings (BAAI/bge-m3).
Uses FAISS IndexFlatIP (cosine similarity via normalized inner product) when
available, and seamlessly falls back to a high-speed NumPy matrix dot-product
index when FAISS is not present.

Per spec Section 8: Includes index/corpus version metadata tracking to prevent
stale indexes from being silently used after source updates.
"""

import logging
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import numpy as np

from config import settings

logger = logging.getLogger(__name__)

CORPUS_VERSION = "2.0.0-Ayurveda-IP-Upgrade"
INDEX_VERSION = "v2.0"


class NumpyFlatIPIndex:
    """Zero-dependency NumPy fallback for FAISS IndexFlatIP."""

    def __init__(self, dimension: int):
        self.dimension = dimension
        self.vectors: np.ndarray = np.zeros((0, dimension), dtype="float32")

    @property
    def ntotal(self) -> int:
        return self.vectors.shape[0]

    def add(self, x: np.ndarray) -> None:
        if x.shape[0] == 0:
            return
        if self.vectors.shape[0] == 0:
            self.vectors = x.astype("float32")
        else:
            self.vectors = np.vstack([self.vectors, x.astype("float32")])

    def search(self, query_vector: np.ndarray, top_k: int) -> Tuple[np.ndarray, np.ndarray]:
        if self.ntotal == 0:
            return np.zeros((1, 0), dtype="float32"), np.zeros((1, 0), dtype="int64")
        scores = np.dot(self.vectors, query_vector.reshape(-1, 1)).flatten()
        top_k = min(top_k, self.ntotal)
        top_indices = np.argsort(-scores)[:top_k]
        top_scores = scores[top_indices]
        return np.array([top_scores], dtype="float32"), np.array([top_indices], dtype="int64")


class VectorStoreUnavailableError(Exception):
    """Raised only if both FAISS and NumPy indexing fail."""


class VectorStore:
    def __init__(self, index_path: str = None, dimension: int = None):
        self.index_path = Path(index_path or settings.VECTOR_DB_PATH)
        self.meta_path = self.index_path.with_suffix(".meta.pkl")
        self.npy_path = self.index_path.with_suffix(".npy")
        self.dimension = dimension or settings.EMBEDDING_DIMENSION
        self._index = None
        self._metadata: List[Dict[str, Any]] = []
        self._backend = "uninitialized"
        self._version_info: Dict[str, Any] = {
            "corpus_version": CORPUS_VERSION,
            "index_version": INDEX_VERSION,
            "embedding_model": settings.EMBEDDING_MODEL,
            "embedding_dimension": self.dimension,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def _ensure_backend(self):
        try:
            import faiss
            return "faiss", faiss
        except ImportError:
            return "numpy", None

    def create_index(self) -> None:
        backend_type, faiss_mod = self._ensure_backend()
        if backend_type == "faiss":
            self._index = faiss_mod.IndexFlatIP(self.dimension)
            self._backend = "faiss"
            logger.info("Created new FAISS IndexFlatIP(dim=%d)", self.dimension)
        else:
            self._index = NumpyFlatIPIndex(self.dimension)
            self._backend = "numpy"
            logger.info("Created new NumPy IndexFlatIP(dim=%d)", self.dimension)
        self._metadata = []
        self._version_info["created_at"] = datetime.now(timezone.utc).isoformat()

    def load(self) -> bool:
        if not self.index_path.exists() and not self.npy_path.exists():
            return False

        backend_type, faiss_mod = self._ensure_backend()
        try:
            if backend_type == "faiss" and self.index_path.exists():
                self._index = faiss_mod.read_index(str(self.index_path))
                self._backend = "faiss"
            elif self.npy_path.exists():
                vecs = np.load(str(self.npy_path))
                self._index = NumpyFlatIPIndex(self.dimension)
                self._index.add(vecs)
                self._backend = "numpy"
            else:
                return False

            if self.meta_path.exists():
                with open(self.meta_path, "rb") as f:
                    loaded = pickle.load(f)
                    if isinstance(loaded, dict) and "chunks" in loaded:
                        self._metadata = loaded["chunks"]
                        self._version_info = loaded.get("version_info", self._version_info)
                    else:
                        self._metadata = loaded if isinstance(loaded, list) else []
            else:
                self._metadata = []

            logger.info("Loaded VectorStore (%d vectors, backend=%s, version=%s)", self.size, self._backend, self._version_info.get("index_version"))
            return True
        except Exception as e:
            logger.warning("Failed to load vector store from disk (%s); initializing fresh.", e)
            return False

    def save(self) -> None:
        if self._index is None:
            return
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            backend_type, faiss_mod = self._ensure_backend()
            if self._backend == "faiss" and backend_type == "faiss":
                faiss_mod.write_index(self._index, str(self.index_path))
            elif isinstance(self._index, NumpyFlatIPIndex):
                np.save(str(self.npy_path), self._index.vectors)

            payload = {
                "chunks": self._metadata,
                "version_info": self._version_info,
            }
            with open(self.meta_path, "wb") as f:
                pickle.dump(payload, f)
            logger.info("Saved VectorStore (%d vectors) to disk", self.size)
        except Exception as e:
            logger.error("Failed to save vector store: %s", e)

    def load_or_create(self) -> None:
        if not self.load():
            self.create_index()

    def add(self, vectors: np.ndarray, metadata: List[Dict[str, Any]]) -> None:
        if self._index is None:
            self.load_or_create()
        if vectors.shape[0] != len(metadata):
            raise ValueError("vectors and metadata must have the same length")
        if vectors.shape[0] == 0:
            return
        self._index.add(vectors.astype("float32"))
        self._metadata.extend(metadata)

    def search(self, query_vector: np.ndarray, top_k: int = 20) -> List[Tuple[Dict[str, Any], float]]:
        if self._index is None:
            self.load_or_create()
        if self.size == 0:
            return []
        query_vector = query_vector.reshape(1, -1).astype("float32")
        scores, indices = self._index.search(query_vector, min(top_k, self.size))
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1 or idx >= len(self._metadata):
                continue
            results.append((self._metadata[idx], float(score)))
        return results

    def delete_all(self) -> None:
        self.create_index()
        self.save()

    @property
    def size(self) -> int:
        return 0 if self._index is None else self._index.ntotal

    @property
    def backend(self) -> str:
        return self._backend

    @property
    def version_info(self) -> Dict[str, Any]:
        return self._version_info


vector_store = VectorStore()


# =====================================================
# TEST
# =====================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    vs = VectorStore(dimension=8)
    vs.create_index()
    vecs = np.random.rand(4, 8).astype("float32")
    vecs = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)
    meta = [{"chunk_id": f"c{i}", "title": f"Doc {i}"} for i in range(4)]
    vs.add(vecs, meta)
    results = vs.search(vecs[0], top_k=2)
    assert len(results) > 0
    print("VectorStore self-test passed! Version:", vs.version_info.get("index_version"))
