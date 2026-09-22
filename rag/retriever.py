"""
IP-SAKTI SAHAYAK
Retriever
=========
Semantic-only retrieval interface over the vector store: embeds a query
and returns the top-k nearest chunks with metadata. hybrid_search.py
composes this together with BM25 keyword search; this module exists
standalone so Phase 1 works before Phase 2 hybrid features exist.
"""

import logging
from typing import List, Dict, Any, Optional

from rag.embeddings import embedding_service
from rag.vector_store import vector_store, VectorStoreUnavailableError
from config import settings

logger = logging.getLogger(__name__)


def semantic_search(
    query: str,
    top_k: int = None,
    jurisdiction: Optional[str] = None,
    domain: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Returns a list of {chunk metadata..., "score": float, "retrieval_method": "semantic"}
    sorted by descending similarity. Empty list (not an exception) on any
    unavailable-backend condition, so callers can fall back gracefully.
    """
    top_k = top_k or settings.RETRIEVAL_TOP_K
    try:
        query_vec = embedding_service.embed_one(query)
        raw_results = vector_store.search(query_vec, top_k=top_k)
    except VectorStoreUnavailableError as e:
        logger.warning("Vector store unavailable, semantic_search returning no results: %s", e)
        return []
    except Exception as e:
        logger.error("Unexpected error in semantic_search: %s", e)
        return []

    results = []
    for meta, score in raw_results:
        if jurisdiction and meta.get("jurisdiction") and meta["jurisdiction"] != jurisdiction:
            continue
        if domain and meta.get("domain") and meta["domain"] != domain:
            continue
        results.append({**meta, "score": score, "retrieval_method": "semantic"})
    return results


# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = semantic_search("What is Section 3(d)?", top_k=5)
    print(f"retriever self-test: {len(results)} results (empty is fine on an unseeded index).")
