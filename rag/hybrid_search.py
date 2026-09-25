"""
IP-SAKTI SAHAYAK
Hybrid Search Core
===================
Combines semantic (FAISS/BGE-M3) and keyword (BM25) retrieval with a
configurable weighted score.
Includes a built-in pure-Python BM25Okapi implementation so that hybrid
search never fails even if rank-bm25 is not externally installed.

Upgraded to support consistent domain & jurisdiction filtering across both
BM25 and Vector search, query expansion search loops, and degraded fallback safety.
"""

import math
import logging
import re
from typing import List, Dict, Any, Optional
from collections import Counter

from config import settings
from rag.retriever import semantic_search

logger = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:\(\w+\))?")


def _tokenize(text: str) -> List[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


class PurePythonBM25Okapi:
    """Zero-dependency BM25Okapi fallback matching rank_bm25 API."""

    def __init__(self, corpus: List[List[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.avgdl = sum(len(doc) for doc in corpus) / max(1, self.corpus_size) if corpus else 1.0
        self.doc_freqs: List[Counter] = [Counter(doc) for doc in corpus]
        self.doc_lens: List[int] = [len(doc) for doc in corpus]
        self.nd: Dict[str, int] = Counter()
        for df in self.doc_freqs:
            for term in df.keys():
                self.nd[term] += 1
        self.idf: Dict[str, float] = {}
        for term, freq in self.nd.items():
            self.idf[term] = math.log(1.0 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

    def get_scores(self, query: List[str]) -> List[float]:
        scores = [0.0] * self.corpus_size
        for term in query:
            if term not in self.idf:
                continue
            idf = self.idf[term]
            for i, doc_freq in enumerate(self.doc_freqs):
                freq = doc_freq.get(term, 0)
                if freq > 0:
                    denom = freq + self.k1 * (1.0 - self.b + self.b * (self.doc_lens[i] / max(1e-6, self.avgdl)))
                    scores[i] += idf * (freq * (self.k1 + 1.0)) / denom
        return scores


try:
    from rank_bm25 import BM25Okapi
except ImportError:
    BM25Okapi = PurePythonBM25Okapi
    logger.info("Using built-in PurePythonBM25Okapi engine.")


class BM25Index:
    """In-memory BM25 index over the chunk corpus."""

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
        top_k: int,
        jurisdiction: Optional[str] = None,
        allowed_domains: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        if self._bm25 is None or not self._corpus_meta:
            return []
        tokenized_query = _tokenize(query)
        if not tokenized_query:
            return []
        scores = self._bm25.get_scores(tokenized_query)
        ranked = sorted(zip(self._corpus_meta, scores), key=lambda x: x[1], reverse=True)
        max_score = max((s for _, s in ranked), default=1.0) or 1.0

        results = []
        for meta, score in ranked:
            if score <= 0:
                continue

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

            results.append({**meta, "score": float(score) / max_score, "retrieval_method": "keyword"})
            if len(results) >= top_k:
                break

        return results

    @property
    def size(self) -> int:
        return len(self._corpus_meta)


bm25_index = BM25Index()


def _merge(
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
        final_score = (
            semantic_weight * entry["semantic_score"] + keyword_weight * entry["keyword_score"]
        )
        entry["final_score"] = round(final_score, 4)
        entry["retrieval_method"] = "hybrid"
        merged.append(entry)

    merged.sort(key=lambda e: e["final_score"], reverse=True)
    return merged


def hybrid_search(
    query: str,
    top_k: int = None,
    jurisdiction: Optional[str] = None,
    domain: Optional[str] = None,
    allowed_domains: Optional[List[str]] = None,
    query_expansions: Optional[List[str]] = None,
    semantic_weight: Optional[float] = None,
    keyword_weight: Optional[float] = None,
) -> List[Dict[str, Any]]:
    top_k = top_k or settings.RETRIEVAL_TOP_K
    semantic_weight = semantic_weight if semantic_weight is not None else settings.HYBRID_SEMANTIC_WEIGHT
    keyword_weight = keyword_weight if keyword_weight is not None else settings.HYBRID_KEYWORD_WEIGHT

    # Boost keyword search weight for statutory citations (e.g. Section 3(d), Rule 158B)
    if re.search(r"(section|article|rule|clause|act)\s+[\dIVXLC]+", query, re.IGNORECASE):
        keyword_weight = min(1.0, keyword_weight + 0.3)
        semantic_weight = max(0.0, 1.0 - keyword_weight)

    queries_to_search = query_expansions or [query]
    all_semantic_results = []
    all_keyword_results = []

    for q in queries_to_search:
        try:
            sem_res = semantic_search(
                q, top_k=top_k, jurisdiction=jurisdiction, domain=domain, allowed_domains=allowed_domains
            )
            all_semantic_results.extend(sem_res)
        except Exception as e:
            logger.error("Semantic search failed for query %r: %s", q, e)

        if bm25_index.size:
            try:
                kw_res = bm25_index.search(
                    q, top_k=top_k, jurisdiction=jurisdiction, allowed_domains=allowed_domains
                )
                all_keyword_results.extend(kw_res)
            except Exception as e:
                logger.error("BM25 search failed for query %r: %s", q, e)

    # Deduplicate semantic and keyword results keeping highest score per chunk
    def _dedup_list(lst: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        best = {}
        for item in lst:
            cid = str(item.get("chunk_id") or item.get("text", "")[:80])
            if cid not in best or item.get("score", 0) > best[cid].get("score", 0):
                best[cid] = item
        return list(best.values())

    unique_semantic = _dedup_list(all_semantic_results)
    unique_keyword = _dedup_list(all_keyword_results)

    if not unique_semantic and not unique_keyword:
        logger.info("hybrid_search: 0 results for query=%r", query)
        return []

    return _merge(unique_semantic, unique_keyword, semantic_weight, keyword_weight)[:top_k]


# =====================================================
# TEST
# =====================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bm25_index.build([
        {"chunk_id": "c1", "text": "Section 3(d) excludes mere discovery of a new form of a known substance.", "jurisdiction": "India", "domain": "Patent"},
        {"chunk_id": "c2", "text": "Geographical Indications protect products originating from a specific region.", "jurisdiction": "India", "domain": "GI"},
    ])
    results = hybrid_search("What does Section 3(d) say?", top_k=5)
    assert results and results[0]["chunk_id"] == "c1"
    print("hybrid_search self-test passed:", results[0]["chunk_id"], results[0]["final_score"])
