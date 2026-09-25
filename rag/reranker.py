"""
IP-SAKTI SAHAYAK
Reranker
========
Cross-encoder reranking of top-N hybrid candidates down to the final
evidence set (spec Section 12 & 16: top 20 -> top 5).

Upgraded with full exception safety and candidate metadata preservation.
"""

import logging
from typing import List, Dict, Any

from config import settings

logger = logging.getLogger(__name__)


class Reranker:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model = None
            cls._instance._backend = "uninitialized"
        return cls._instance

    def _load(self):
        if self._model is not None or self._backend == "fallback":
            return
        try:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(settings.RERANKER_MODEL)
            self._backend = "cross-encoder"
            logger.info("Loaded reranker model %s", settings.RERANKER_MODEL)
        except Exception as e:
            logger.warning(
                "Reranker model '%s' unavailable (%s) — falling back to incoming hybrid ranking.",
                settings.RERANKER_MODEL, e,
            )
            self._backend = "fallback"

    def rerank(self, query: str, candidates: List[Dict[str, Any]], top_n: int = None) -> List[Dict[str, Any]]:
        top_n = top_n or settings.RERANK_TOP_N
        if not candidates:
            return []

        # Deduplicate candidates by chunk_id/text snippet while preserving order
        seen = set()
        unique_candidates = []
        for c in candidates:
            key = str(c.get("chunk_id") or c.get("text", "")[:80])
            if key not in seen:
                seen.add(key)
                # Create clean copy so incoming dict is not mutated in place
                unique_candidates.append(dict(c))

        self._load()

        if self._backend != "cross-encoder":
            ranked = sorted(unique_candidates, key=lambda c: c.get("final_score", c.get("score", 0)), reverse=True)
            for c in ranked:
                c["rerank_score"] = c.get("final_score", c.get("score", 0))
            return ranked[:top_n]

        try:
            pairs = [(query, c["text"]) for c in unique_candidates]
            scores = self._model.predict(pairs)
            for c, s in zip(unique_candidates, scores):
                c["rerank_score"] = float(s)
            ranked = sorted(unique_candidates, key=lambda c: c["rerank_score"], reverse=True)
            return ranked[:top_n]
        except Exception as e:
            logger.error("Reranker prediction failed (%s); falling back to hybrid scores.", e)
            ranked = sorted(unique_candidates, key=lambda c: c.get("final_score", c.get("score", 0)), reverse=True)
            for c in ranked:
                c["rerank_score"] = c.get("final_score", c.get("score", 0))
            return ranked[:top_n]

    @property
    def backend(self) -> str:
        self._load()
        return self._backend


reranker = Reranker()


# =====================================================
# TEST
# =====================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fake_candidates = [
        {"chunk_id": "c1", "text": "Section 3(d) excludes mere discovery.", "final_score": 0.4},
        {"chunk_id": "c2", "text": "Geographical Indications protect regional products.", "final_score": 0.9},
    ]
    result = reranker.rerank("What does Section 3(d) say?", fake_candidates, top_n=2)
    print("backend:", reranker.backend)
    print("reranker self-test passed:", [c["chunk_id"] for c in result])
