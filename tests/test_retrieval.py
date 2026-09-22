"""Tests for chunking, BM25, and hybrid retrieval basics."""
import pytest

from rag.chunker import chunk_document
from rag.hybrid_search import bm25_index, hybrid_search


def test_chunker_preserves_sections():
    text = "Section 3. Heading text.\nSection 3(d) body text about discovery."
    chunks = chunk_document("doc1", text, authority="IP India", jurisdiction="India")
    assert len(chunks) >= 1
    assert all(c.document_id == "doc1" for c in chunks)


def test_bm25_ranks_exact_match_first(monkeypatch):
    # Isolate from any persisted FAISS index (e.g. from a prior ingestion run)
    # so this test exercises BM25/keyword ranking behaviour specifically.
    monkeypatch.setattr("rag.hybrid_search.semantic_search", lambda *a, **kw: [])
    # BM25's IDF calculation needs a few documents to produce meaningful
    # separation (a 2-document corpus is a known degenerate edge case for
    # the underlying library), so pad with unrelated filler chunks.
    bm25_index.build([
        {"chunk_id": "a", "text": "Section 3(d) excludes mere discovery of a known substance."},
        {"chunk_id": "b", "text": "Geographical indications protect regional products."},
        {"chunk_id": "c", "text": "Trademark registration follows the Madrid Protocol process."},
        {"chunk_id": "d", "text": "Plant variety protection covers farmers rights under PPV&FR."},
        {"chunk_id": "e", "text": "Trade secret confidentiality obligations arise under contract law."},
    ])
    results = hybrid_search("Section 3(d)", top_k=5)
    assert results
    assert results[0]["chunk_id"] == "a"


def test_hybrid_search_empty_query_does_not_crash():
    results = hybrid_search("", top_k=5)
    assert isinstance(results, list)
