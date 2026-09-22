"""
IP-SAKTI SAHAYAK
Regulatory Hybrid Search Engine
=================================
Combines dense semantic retrieval (BAAI/bge-m3 via isolated RegulatoryVectorStore)
with lexical keyword search (isolated RegulatoryBM25Index) and authority-tier weighting.

Boosts regulatory-specific identifiers (e.g. 'FSSAI Regulation 4', 'Rule 158B',
'Schedule T', '21 CFR 312', 'THMPD 2004/24/EC', 'Form 1', 'Section 6 BDA').
"""

import math
import logging
import re
from typing import List, Dict, Any, Optional
from collections import Counter

from config import settings
from rag.embeddings import embedding_service
from rag.hybrid_search import _tokenize, BM25Okapi
from regulatory.vector_store import regulatory_vector_store

logger = logging.getLogger(__name__)

# Statutory & regulatory section regex patterns for keyword boosting
REGULATORY_KEYWORD_RE = re.compile(
    r"(?:section|rule|regulation|schedule|clause|article|cfr|directive|notification|guideline|form)\s+[\dIVXLC]+[\w.()/\-]*|"
    r"\b(?:fssai|cdsco|ayush|nba|tkdl|fda|ema|mhra|nmpa|pmda|tga|hsa|thmpd|dshea|gmp|gacp|rda)\b",
    re.IGNORECASE,
)


class RegulatoryBM25Index:
    """Isolated in-memory BM25 index over the regulatory knowledge corpus."""

    def __init__(self):
        self._bm25 = None
        self._corpus_meta: List[Dict[str, Any]] = []

    def build(self, chunks: List[Dict[str, Any]]) -> None:
        tokenized = [_tokenize(c["text"]) for c in chunks]
        if tokenized:
            self._bm25 = BM25Okapi(tokenized)
        else:
            self._bm25 = None
        self._corpus_meta = chunks

    def search(
        self,
        query: str,
        top_k: int = 20,
        country_filter: Optional[str] = None,
        domain_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if self._bm25 is None or not self._corpus_meta:
            if regulatory_vector_store.size > 0:
                self.build(regulatory_vector_store._metadata)
            else:
                return []
        tokenized_query = _tokenize(query)
        if not tokenized_query:
            return []

        scores = self._bm25.get_scores(tokenized_query)
        ranked = sorted(zip(self._corpus_meta, scores), key=lambda x: x[1], reverse=True)
        max_score = max((s for _, s in ranked), default=1.0) or 1.0

        filtered_results = []
        for meta, score in ranked:
            if score <= 0:
                continue

            # Metadata filtering
            if country_filter and country_filter not in ("All", "Auto Detect", "Global", "Unspecified"):
                m_c = meta.get("country", "")
                m_j = meta.get("jurisdiction", "")
                if m_c.lower() != country_filter.lower() and m_j.lower() != country_filter.lower() and m_c != "Global":
                    continue

            if domain_filter and domain_filter not in ("All", "Auto Detect", "General Regulation"):
                m_d = meta.get("domain", "")
                if domain_filter.lower() not in m_d.lower():
                    continue

            filtered_results.append({
                **meta,
                "score": float(score) / max_score,
                "retrieval_method": "keyword",
            })
            if len(filtered_results) >= top_k:
                break

        return filtered_results

    @property
    def size(self) -> int:
        return len(self._corpus_meta)


regulatory_bm25_index = RegulatoryBM25Index()


def _merge_regulatory_results(
    semantic_results: List[Dict[str, Any]],
    keyword_results: List[Dict[str, Any]],
    semantic_weight: float,
    keyword_weight: float,
) -> List[Dict[str, Any]]:
    combined: Dict[str, Dict[str, Any]] = {}

    for r in semantic_results:
        key = str(r.get("chunk_id") or r.get("text", "")[:80])
        combined[key] = {**r, "semantic_score": r["score"], "keyword_score": 0.0}

    for r in keyword_results:
        key = str(r.get("chunk_id") or r.get("text", "")[:80])
        if key in combined:
            combined[key]["keyword_score"] = r["score"]
        else:
            combined[key] = {**r, "semantic_score": 0.0, "keyword_score": r["score"]}

    merged = []
    for entry in combined.values():
        raw_score = (
            semantic_weight * entry["semantic_score"] + keyword_weight * entry["keyword_score"]
        )

        # Apply Priority hierarchy multiplier:
        # Priority 1 (Acts/Primary Regs) -> 1.15x boost
        # Priority 2 (Standards/Rules) -> 1.05x boost
        # Priority 3 (Guidelines/Manuals) -> 1.0x
        # Priority 4 (Advisory) -> 0.90x
        priority = entry.get("source_priority", 3)
        priority_multiplier = {1: 1.15, 2: 1.05, 3: 1.00, 4: 0.90, 5: 0.80}.get(priority, 1.0)

        # Apply active status boost
        status = entry.get("status", "CURRENT")
        status_multiplier = 1.0 if status == "CURRENT" else 0.70

        final_score = raw_score * priority_multiplier * status_multiplier
        entry["final_score"] = round(final_score, 4)
        entry["retrieval_method"] = "regulatory_hybrid"
        merged.append(entry)

    merged.sort(key=lambda e: e["final_score"], reverse=True)
    return merged


def regulatory_hybrid_search(
    query: str,
    top_k: int = 20,
    country: Optional[str] = None,
    domain: Optional[str] = None,
    semantic_weight: float = 0.6,
    keyword_weight: float = 0.4,
    status_filter: Optional[str] = "CURRENT",
) -> List[Dict[str, Any]]:
    """
    Executes isolated hybrid retrieval over the regulatory corpus with
    authority hierarchy boosting and metadata filtering.
    """
    if not query.strip():
        return []

    # Check for statutory citation keywords in the query to boost exact lexical matching
    if REGULATORY_KEYWORD_RE.search(query):
        keyword_weight = min(0.70, keyword_weight + 0.25)
        semantic_weight = round(1.0 - keyword_weight, 2)

    # 1. Dense Semantic Search
    try:
        query_vec = embedding_service.embed_one(query)
        raw_semantic = regulatory_vector_store.search(
            query_vec,
            top_k=top_k,
            country_filter=country,
            domain_filter=domain,
            status_filter=status_filter,
        )
        semantic_results = [{**m, "score": s, "retrieval_method": "semantic"} for m, s in raw_semantic]
    except Exception as e:
        logger.warning("Regulatory semantic search failed: %s", e)
        semantic_results = []

    # 2. Lexical Keyword Search
    keyword_results = regulatory_bm25_index.search(
        query,
        top_k=top_k,
        country_filter=country,
        domain_filter=domain,
    ) if regulatory_bm25_index.size else []

    merged = _merge_regulatory_results(semantic_results, keyword_results, semantic_weight, keyword_weight)

    # If domain filter was restrictive and produced fewer than 2 results, relax domain filter
    if len(merged) < 2 and domain:
        try:
            extra_semantic = regulatory_vector_store.search(
                query_vec,
                top_k=top_k,
                country_filter=country,
                domain_filter=None,
                status_filter=status_filter,
            )
            extra_sem_results = [{**m, "score": s, "retrieval_method": "semantic"} for m, s in extra_semantic]
        except Exception:
            extra_sem_results = []

        extra_kw_results = regulatory_bm25_index.search(
            query,
            top_k=top_k,
            country_filter=country,
            domain_filter=None,
        )
        extra_merged = _merge_regulatory_results(extra_sem_results, extra_kw_results, semantic_weight, keyword_weight)
        seen_ids = {m.get("chunk_id") or m.get("text", "")[:60] for m in merged}
        for item in extra_merged:
            k = item.get("chunk_id") or item.get("text", "")[:60]
            if k not in seen_ids:
                merged.append(item)
                seen_ids.add(k)
        merged.sort(key=lambda e: e.get("final_score", 0), reverse=True)

    return merged[:top_k]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    regulatory_bm25_index.build([
        {"chunk_id": "r1", "text": "FSSAI Nutraceutical Regulations 2022 mandate RDA limits.", "source_priority": 1, "status": "CURRENT"},
        {"chunk_id": "r2", "text": "AYUSH Rule 158B governs licensing of Ayurvedic medicines.", "source_priority": 1, "status": "CURRENT"},
    ])
    res = regulatory_hybrid_search("FSSAI nutraceutical RDA limits", top_k=2)
    print("regulatory_hybrid_search self-test passed:", res)
