"""
IP-SAKTI SAHAYAK
Isolated Regulatory Vector Store
==================================
Dedicated vector database for the Regulatory RAG Engine.
Maintains total physical and logical isolation from the IP knowledge base
(spec Section 5), preventing contamination between IP law and specialized
product regulations.

Supports FAISS IndexFlatIP (cosine similarity via normalized embeddings) with
automatic zero-dependency NumPy matrix dot-product fallback.
"""

import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import numpy as np

from config import settings
from rag.vector_store import NumpyFlatIPIndex

logger = logging.getLogger(__name__)


class RegulatoryVectorStore:
    def __init__(self, index_path: str = None, dimension: int = None):
        self.index_path = Path(index_path or settings.REGULATORY_INDEX_PATH)
        self.meta_path = self.index_path.with_suffix(".meta.pkl")
        self.npy_path = self.index_path.with_suffix(".npy")
        self.dimension = dimension or settings.EMBEDDING_DIMENSION
        self._index = None
        self._metadata: List[Dict[str, Any]] = []
        self._backend = "uninitialized"

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
            logger.info("Created new Regulatory FAISS IndexFlatIP(dim=%d)", self.dimension)
        else:
            self._index = NumpyFlatIPIndex(self.dimension)
            self._backend = "numpy"
            logger.info("Created new Regulatory NumPy IndexFlatIP(dim=%d)", self.dimension)
        self._metadata = []

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
                    self._metadata = pickle.load(f)
            else:
                self._metadata = []

            logger.info("Loaded RegulatoryVectorStore (%d vectors, backend=%s)", self.size, self._backend)
            return True
        except Exception as e:
            logger.warning("Failed to load regulatory vector store (%s); initializing fresh.", e)
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

            with open(self.meta_path, "wb") as f:
                pickle.dump(self._metadata, f)
            logger.info("Saved RegulatoryVectorStore (%d vectors) to disk", self.size)
        except Exception as e:
            logger.error("Failed to save regulatory vector store: %s", e)

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

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 20,
        country_filter: Optional[str] = None,
        domain_filter: Optional[str] = None,
        status_filter: Optional[str] = "CURRENT",
        max_priority: Optional[int] = None,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Executes similarity search with regulatory metadata filtering
        (country, domain, priority hierarchy, and active version status).
        """
        if self._index is None:
            self.load_or_create()
        if self.size == 0:
            return []

        query_vector = query_vector.reshape(1, -1).astype("float32")
        scores, indices = self._index.search(query_vector, self.size)
        results = []

        for score, idx in zip(scores[0], indices[0]):
            if idx == -1 or idx >= len(self._metadata):
                continue
            meta = self._metadata[idx]

            # Country filter
            if country_filter and country_filter not in ("All", "Auto Detect", "Global", "Unspecified"):
                m_c = meta.get("country", "")
                m_j = meta.get("jurisdiction", "")
                if m_c.lower() != country_filter.lower() and m_j.lower() != country_filter.lower() and m_c != "Global":
                    continue

            # Domain filter
            if domain_filter and domain_filter not in ("All", "Auto Detect", "General Regulation"):
                m_d = meta.get("domain", "")
                if domain_filter.lower() not in m_d.lower():
                    continue

            # Priority filter
            if max_priority is not None and meta.get("source_priority", 5) > max_priority:
                continue

            # Status filter (default: prioritize CURRENT regulations unless searching historical versions)
            if status_filter and meta.get("status") and meta.get("status") != status_filter:
                # Downweight non-current versions rather than hard drop
                score *= 0.7

            results.append((meta, float(score)))
            if len(results) >= top_k:
                break

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


regulatory_vector_store = RegulatoryVectorStore()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    rvs = RegulatoryVectorStore()
    rvs.load_or_create()
    print("RegulatoryVectorStore status: backend =", rvs.backend, "size =", rvs.size)
