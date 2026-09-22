"""
IP-SAKTI SAHAYAK
Unified RAG Pipeline Core
==========================
Orchestrates:
1. Language Detection & Term Protection
2. Domain Classification & Jurisdiction Ambiguity Detection
3. Hybrid Retrieval (Semantic Dense + BM25 Lexical + Dynamic Section Boost)
4. Cross-Encoder Reranking
5. Grounded LLM Generation (Groq LLaMA 3.3 70B)
6. Citation Verification & Claim-Level Traceability ("Why did AI say this?")
7. Multi-Factor Confidence Scoring
8. Safe Abstention Gate (including adversarial red-team traps)
9. Quick Mode vs Deep Agentic Research Mode
"""

import logging
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from ai.domain_classifier import classify_domain
from ai.jurisdiction_detector import detect_jurisdiction
from ai.multilingual import detect_language, translate_response, LANGUAGE_NAMES
from ai.prompts import build_rag_prompt, DISCLAIMER_TEXT
from ai.llm import llm_client, translate as llm_translate
from ai.citation_verifier import verify_citations
from ai.confidence import compute_confidence
from ai.abstention import check_abstention, is_out_of_domain

from rag.hybrid_search import hybrid_search
from rag.reranker import reranker

logger = logging.getLogger(__name__)


@dataclass
class RAGResponse:
    success: bool
    answer: str
    confidence: float
    confidence_level: str
    domain: str
    jurisdiction: str
    language: str
    sources: List[Dict[str, Any]] = field(default_factory=list)
    citations: List[Dict[str, Any]] = field(default_factory=list)
    claim_trace_map: List[Dict[str, Any]] = field(default_factory=list)
    abstained: bool = False
    abstain_reason: Optional[str] = None
    disclaimer: str = DISCLAIMER_TEXT
    latency_ms: int = 0
    error: Optional[str] = None
    mode: str = "quick"


def _source_card(chunk: Dict[str, Any], index: int) -> Dict[str, Any]:
    return {
        "index": index,
        "source_name": chunk.get("authority") or "Unknown source",
        "authority": chunk.get("authority"),
        "jurisdiction": chunk.get("jurisdiction"),
        "section": chunk.get("section"),
        "page": chunk.get("page"),
        "url": chunk.get("source_url") or None,
        "url_display": chunk.get("source_url") or "Source URL unavailable",
        "text_snippet": chunk.get("text", "")[:220],
    }


def answer_query(
    query: str,
    requested_jurisdiction: Optional[str] = None,
    requested_language: Optional[str] = None,
    mode: str = "quick",
) -> RAGResponse:
    start = time.time()

    # If user selected Deep Research mode, dispatch to agentic multi-track research engine
    if mode == "deep":
        from services.research_agent import execute_deep_research
        deep_res = execute_deep_research(query, requested_jurisdiction)
        return RAGResponse(
            success=deep_res.success,
            answer=deep_res.dossier,
            confidence=deep_res.confidence,
            confidence_level=deep_res.confidence_level,
            domain="Deep IP Research",
            jurisdiction=requested_jurisdiction or "India & International",
            language=requested_language or "en",
            sources=deep_res.sources,
            citations=[],
            claim_trace_map=[],
            abstained=False,
            latency_ms=deep_res.latency_ms,
            mode="deep",
        )

    # 1. Language Detection
    language = requested_language or detect_language(query)

    # 2. Domain Classification
    domain_result = classify_domain(query)
    domain = domain_result["domain"]

    # 3. Jurisdiction Detection
    jurisdiction_result = detect_jurisdiction(query, domain=domain)
    jurisdiction = requested_jurisdiction or jurisdiction_result["jurisdiction"]
    jurisdiction_ambiguous = jurisdiction_result["ambiguous"] and not requested_jurisdiction

    out_of_domain = is_out_of_domain(domain, domain_result["confidence"])

    # 4. Hybrid Retrieval
    jurisdiction_filter = jurisdiction if jurisdiction not in (None, "Unspecified", "Auto Detect") else None
    candidates = hybrid_search(query, jurisdiction=jurisdiction_filter, domain=domain)

    # 5. Rerank top candidates
    evidence_chunks = reranker.rerank(query, candidates, top_n=5)

    # 6. Check Abstention BEFORE generation if out of domain or adversarial trap
    early_abstention = check_abstention(
        query=query,
        evidence_chunks=evidence_chunks,
        confidence_score=0.8 if evidence_chunks else 0.0,
        citation_all_valid=True,
        jurisdiction_ambiguous=jurisdiction_ambiguous,
        out_of_domain=out_of_domain,
    )

    if early_abstention.should_abstain:
        latency_ms = int((time.time() - start) * 1000)
        return RAGResponse(
            success=True,
            answer=early_abstention.message or f"I could not find sufficient authoritative evidence.\n\n{DISCLAIMER_TEXT}",
            confidence=0.15,
            confidence_level="VERY LOW",
            domain=domain,
            jurisdiction=jurisdiction,
            language=language,
            sources=[_source_card(c, i + 1) for i, c in enumerate(evidence_chunks)],
            citations=[],
            claim_trace_map=[],
            abstained=True,
            abstain_reason=early_abstention.reason,
            latency_ms=latency_ms,
        )

    # 7. LLM Generation
    messages = build_rag_prompt(query, evidence_chunks, domain, jurisdiction, language="en")
    llm_result = llm_client.chat(messages)
    llm_answer_text = llm_result.text if llm_result.success else ""
    llm_error = llm_result.error

    # 8. Citation Verification & Claim-Level Traceability Map
    if llm_answer_text:
        citation_result = verify_citations(llm_answer_text, evidence_chunks)
    else:
        citation_result = {"citations": [], "claim_trace_map": [], "all_valid": True, "cleaned_answer": "", "valid_ratio": 0.0}

    # 9. Confidence Calculation
    jurisdiction_match = bool(jurisdiction_filter) or jurisdiction == "Unspecified"
    confidence_result = compute_confidence(
        evidence_chunks,
        citation_valid_ratio=citation_result["valid_ratio"] if evidence_chunks else 0.0,
        jurisdiction_match=jurisdiction_match,
    )

    # 10. Post-generation Safe Abstention Gate
    final_abstention = check_abstention(
        query=query,
        evidence_chunks=evidence_chunks,
        confidence_score=confidence_result.score,
        citation_all_valid=citation_result["all_valid"],
        jurisdiction_ambiguous=jurisdiction_ambiguous,
        out_of_domain=out_of_domain,
    )

    latency_ms = int((time.time() - start) * 1000)

    if final_abstention.should_abstain or not llm_answer_text:
        final_text = final_abstention.message or (
            f"I could not find sufficient authoritative evidence to answer this reliably."
            f"{(' Reason: ' + llm_error) if llm_error else ''}\n\n{DISCLAIMER_TEXT}"
        )
        return RAGResponse(
            success=True,
            answer=final_text,
            confidence=confidence_result.score,
            confidence_level=confidence_result.level,
            domain=domain,
            jurisdiction=jurisdiction,
            language=language,
            sources=[_source_card(c, i + 1) for i, c in enumerate(evidence_chunks)],
            citations=[],
            claim_trace_map=[],
            abstained=True,
            abstain_reason=final_abstention.reason,
            latency_ms=latency_ms,
            error=llm_error,
        )

    final_answer = citation_result["cleaned_answer"]

    # 11. Multilingual translation
    if language != "en":
        final_answer = translate_response(final_answer, language, llm_translate)

    return RAGResponse(
        success=True,
        answer=final_answer,
        confidence=confidence_result.score,
        confidence_level=confidence_result.level,
        domain=domain,
        jurisdiction=jurisdiction,
        language=language,
        sources=[_source_card(c, i + 1) for i, c in enumerate(evidence_chunks)],
        citations=citation_result["citations"],
        claim_trace_map=citation_result.get("claim_trace_map", []),
        abstained=False,
        latency_ms=latency_ms,
        mode="quick",
    )


# =====================================================
# TEST
# =====================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    res = answer_query("What is Section 3(d) of the Patents Act?")
    print("RAG Pipeline self-test passed! Confidence:", res.confidence, "Abstained:", res.abstained)
    assert res.success
