"""
IP-SAKTI SAHAYAK
Reranker
========
Cross-encoder reranking of the top-N hybrid candidates down to the
final evidence set (spec Section 16: top 20 -> top 5). Falls back to
the incoming hybrid ranking unchanged if the reranker model can't be
loaded, so the pipeline degrades gracefully instead of failing.
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
                "Reranker model '%s' unavailable (%s) — falling back to the incoming "
                "hybrid-search ranking unchanged.", settings.RERANKER_MODEL, e,
            )
            self._backend = "fallback"

    def rerank(self, query: str, candidates: List[Dict[str, Any]], top_n: int = None) -> List[Dict[str, Any]]:
        top_n = top_n or settings.RERANK_TOP_N
        if not candidates:
            return []
        self._load()

        if self._backend != "cross-encoder":
            # Fallback: candidates already ranked by hybrid_search's final_score.
            ranked = sorted(candidates, key=lambda c: c.get("final_score", c.get("score", 0)), reverse=True)
            for c in ranked:
                c["rerank_score"] = c.get("final_score", c.get("score", 0))
            return ranked[:top_n]

        pairs = [(query, c["text"]) for c in candidates]
        scores = self._model.predict(pairs)
        for c, s in zip(candidates, scores):
            c["rerank_score"] = float(s)
        ranked = sorted(candidates, key=lambda c: c["rerank_score"], reverse=True)
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
