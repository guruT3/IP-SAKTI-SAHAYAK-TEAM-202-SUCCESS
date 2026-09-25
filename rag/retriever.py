"""
IP-SAKTI SAHAYAK
Retriever
=========
Semantic-only retrieval interface over the vector store: embeds a query
and returns the top-k nearest chunks with metadata.

Upgraded to support flexible domain group matching and safe jurisdiction filtering.
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
    allowed_domains: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Returns a list of {chunk metadata..., "score": float, "retrieval_method": "semantic"}
    sorted by descending similarity. Empty list on unavailable-backend condition.
    """
    top_k = top_k or settings.RETRIEVAL_TOP_K
    try:
        query_vec = embedding_service.embed_one(query)
        # Search a broader candidate pool to allow domain/jurisdiction filtering
        raw_results = vector_store.search(query_vec, top_k=top_k * 3)
    except VectorStoreUnavailableError as e:
        logger.warning("Vector store unavailable, semantic_search returning no results: %s", e)
        return []
    except Exception as e:
        logger.error("Unexpected error in semantic_search: %s", e)
        return []

    results = []
    for meta, score in raw_results:
        # Flexible Jurisdiction Check
        chunk_jur = meta.get("jurisdiction")
        if jurisdiction and chunk_jur and jurisdiction not in (None, "Unspecified", "Auto Detect"):
            if jurisdiction == "India" and chunk_jur not in ("India", "India & International", "Unspecified", None):
                continue
            elif jurisdiction == "International" and chunk_jur not in ("International", "India & International", "Unspecified", None):
                continue

        # Flexible Domain Check
        chunk_dom = meta.get("domain")
        if allowed_domains and chunk_dom:
            if chunk_dom not in allowed_domains and chunk_dom != "General IP":
                continue

        results.append({**meta, "score": float(score), "retrieval_method": "semantic"})
        if len(results) >= top_k:
            break

    return results


# =====================================================
# TEST
# =====================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = semantic_search("What is Section 3(d)?", top_k=5)
    print(f"retriever self-test: {len(results)} results.")
