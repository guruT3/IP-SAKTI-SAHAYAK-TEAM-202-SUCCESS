"""
IP-SAKTI SAHAYAK
Unified RAG Pipeline Core (Upgraded Reliability & Retrieval Engine)
====================================================================
Orchestrates:
1. Request-Scoped QueryContext Isolation (fixes "works once, fails later")
2. Query Normalization & Concept Expansion
3. Domain Classification & Ayurvedic Formulation Category Detection
4. Authoritative Source Routing (IP India -> WIPO PATENTSCOPE -> TKDL -> PCIM&H -> Scientific Literature)
5. Fault-Tolerant Hybrid Retrieval (Dense Semantic FAISS/NumPy + BM25 Lexical)
6. Exception-Safe Cross-Encoder Reranking (Top 20 -> Top 5)
7. Evidence Grounding & Sufficiency Audit
8. Grounded LLM Generation with Generation Retry Recovery
9. Citation Verification & Claim-Level Traceability ("Why did AI say this?")
10. Multi-Factor Confidence Scoring
11. Safe Abstention Gate (including adversarial red-team traps)
12. Internal Diagnostic Trace for Developer Audit
"""

import logging
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from config import settings
from ai.domain_classifier import classify_domain
from ai.jurisdiction_detector import detect_jurisdiction
from ai.ayurveda_classifier import classify_ayurvedic_formulation
from ai.multilingual import detect_language, translate_response, LANGUAGE_NAMES, normalize_language_code
from ai.prompts import build_rag_prompt, DISCLAIMER_TEXT
from ai.llm import llm_client, translate as llm_translate
from ai.citation_verifier import verify_citations
from ai.confidence import compute_confidence
from ai.abstention import check_abstention, is_out_of_domain

from rag.query_context import QueryContext
from rag.query_normalizer import normalize_query, generate_query_expansions
from rag.source_registry import get_routed_sources
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
    diagnostic_trace: Optional[Dict[str, Any]] = None


def _source_card(chunk: Dict[str, Any], index: int) -> Dict[str, Any]:
    return {
        "index": index,
        "source_name": chunk.get("authority") or "Official Authority",
        "authority": chunk.get("authority"),
        "jurisdiction": chunk.get("jurisdiction") or "India",
        "section": chunk.get("section") or "Statutory Excerpt",
        "page": chunk.get("page"),
        "url": chunk.get("source_url") or None,
        "url_display": chunk.get("source_url") or "Source URL unavailable",
        "text_snippet": chunk.get("text", "")[:220],
        "priority": chunk.get("priority", 2),
    }


def answer_query(
    query: str,
    requested_jurisdiction: Optional[str] = None,
    requested_language: Optional[str] = None,
    mode: str = "quick",
    debug: bool = False,
) -> RAGResponse:
    # 0. Initialize Isolated Request Context
    ctx = QueryContext(original_query=query, requested_language=requested_language or "en")
    ctx.log(f"Started query execution: {query[:60]}...")

    # Handle Deep Research Mode Dispatch
    if mode == "deep":
        from services.research_agent import execute_deep_research
        deep_res = execute_deep_research(query, requested_jurisdiction)
        ctx.finalize()
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
            latency_ms=ctx.latency_ms,
            mode="deep",
            diagnostic_trace=ctx.get_diagnostic_dict() if debug else None,
        )

    # 1. Deterministic Query Normalization & Language Detection
    ctx.normalized_query = normalize_query(query)
    ctx.detected_language = detect_language(query)
    ctx.requested_language = normalize_language_code(requested_language or ctx.detected_language)
    ctx.log(f"Normalized query: '{ctx.normalized_query}' | Lang: {ctx.requested_language}")

    # 2. Domain & Jurisdiction Classification
    domain_result = classify_domain(query)
    ctx.domain = domain_result["domain"]
    ctx.domain_confidence = domain_result["confidence"]
    ctx.secondary_domains = domain_result.get("secondary_domains", [])
    ctx.log(f"Domain classified: {ctx.domain} (conf={ctx.domain_confidence})")

    jurisdiction_result = detect_jurisdiction(query, domain=ctx.domain)
    ctx.jurisdiction = requested_jurisdiction or jurisdiction_result["jurisdiction"]
    ctx.jurisdiction_ambiguous = jurisdiction_result["ambiguous"] and not requested_jurisdiction
    ctx.log(f"Jurisdiction detected: {ctx.jurisdiction} (ambiguous={ctx.jurisdiction_ambiguous})")

    out_of_domain = is_out_of_domain(ctx.domain, ctx.domain_confidence)

    # 3. Ayurvedic Formulation Classification (if applicable)
    formulation_res = classify_ayurvedic_formulation(query)
    if formulation_res.get("applicable"):
        ctx.formulation_category = formulation_res.get("category")
        ctx.formulation_classification_reason = formulation_res.get("reason")
        ctx.log(f"Ayurvedic Formulation Category: {formulation_res.get('title')}")

    # 4. Source Domain Routing & Query Expansion
    routed_sources = get_routed_sources(ctx.domain, query)
    ctx.selected_source_domains = list({s["domain"] for s in routed_sources})
    allowed_domain_set = list({ctx.domain, "General IP"} | set(ctx.secondary_domains) | set(ctx.selected_source_domains))

    ctx.query_expansions = generate_query_expansions(query, ctx.domain, ctx.jurisdiction)
    ctx.log(f"Query expansions generated ({len(ctx.query_expansions)} variants)")

    # 5. Hybrid Retrieval (Dense FAISS + BM25 Lexical)
    jurisdiction_filter = ctx.jurisdiction if ctx.jurisdiction not in (None, "Unspecified", "Auto Detect") else None

    candidates = hybrid_search(
        query=ctx.normalized_query,
        top_k=settings.RETRIEVAL_TOP_K,
        jurisdiction=jurisdiction_filter,
        domain=ctx.domain,
        allowed_domains=allowed_domain_set,
        query_expansions=ctx.query_expansions,
    )
    ctx.merged_count = len(candidates)
    ctx.log(f"Hybrid retrieval yielded {ctx.merged_count} candidates")

    # 6. Rerank top candidates with exception safety
    evidence_chunks = reranker.rerank(ctx.normalized_query, candidates, top_n=settings.RERANK_TOP_N)
    ctx.evidence_count = len(evidence_chunks)
    ctx.log(f"Reranker selected top {ctx.evidence_count} evidence chunks")

    # 7. Pre-Generation Safe Abstention Check
    early_abstention = check_abstention(
        query=query,
        evidence_chunks=evidence_chunks,
        confidence_score=0.8 if evidence_chunks else 0.0,
        citation_all_valid=True,
        jurisdiction_ambiguous=ctx.jurisdiction_ambiguous,
        out_of_domain=out_of_domain,
    )

    if early_abstention.should_abstain:
        ctx.confidence_score = 0.15
        ctx.confidence_level = "VERY LOW"
        ctx.finalize()
        ctx.log(f"Early abstention triggered: {early_abstention.reason}")
        return RAGResponse(
            success=True,
            answer=early_abstention.message or f"I could not find sufficient authoritative evidence.\n\n{DISCLAIMER_TEXT}",
            confidence=0.15,
            confidence_level="VERY LOW",
            domain=ctx.domain,
            jurisdiction=ctx.jurisdiction,
            language=ctx.requested_language,
            sources=[_source_card(c, i + 1) for i, c in enumerate(evidence_chunks)],
            citations=[],
            claim_trace_map=[],
            abstained=True,
            abstain_reason=early_abstention.reason,
            latency_ms=ctx.latency_ms,
            diagnostic_trace=ctx.get_diagnostic_dict() if debug else None,
        )

    # 8. LLM Generation with Single Retry on Failure
    messages = build_rag_prompt(query, evidence_chunks, ctx.domain, ctx.jurisdiction, language="en")
    
    ctx.llm_attempts = 1
    llm_result = llm_client.chat(messages)
    
    # Retry once if LLM call failed transiently but evidence exists
    if not llm_result.success and evidence_chunks:
        ctx.log("First LLM generation attempt failed, retrying generation...")
        ctx.llm_attempts += 1
        time.sleep(0.5)
        llm_result = llm_client.chat(messages)

    llm_answer_text = llm_result.text if llm_result.success else ""
    llm_error = llm_result.error

    # Add Formulation Classification Summary to Answer if relevant
    if formulation_res.get("applicable") and formulation_res.get("title") and llm_answer_text:
        formulation_header = (
            f"**Product Classification:** {formulation_res.get('title')}\n"
            f"*{formulation_res.get('reason')}*\n\n"
        )
        if "DIRECT ANSWER" in llm_answer_text:
            llm_answer_text = llm_answer_text.replace("DIRECT ANSWER\n", f"DIRECT ANSWER\n{formulation_header}")

    # 9. Citation Verification & Claim-Level Traceability Map
    if llm_answer_text:
        citation_result = verify_citations(llm_answer_text, evidence_chunks)
    else:
        citation_result = {"citations": [], "claim_trace_map": [], "all_valid": True, "cleaned_answer": "", "valid_ratio": 0.0}

    # 10. Multi-Factor Confidence Scoring
    jurisdiction_match = bool(jurisdiction_filter) or ctx.jurisdiction == "Unspecified"
    confidence_result = compute_confidence(
        evidence_chunks,
        citation_valid_ratio=citation_result["valid_ratio"] if evidence_chunks else 0.0,
        jurisdiction_match=jurisdiction_match,
    )
    ctx.confidence_score = confidence_result.score
    ctx.confidence_level = confidence_result.level

    # 11. Post-Generation Safe Abstention Gate
    final_abstention = check_abstention(
        query=query,
        evidence_chunks=evidence_chunks,
        confidence_score=confidence_result.score,
        citation_all_valid=citation_result["all_valid"],
        jurisdiction_ambiguous=ctx.jurisdiction_ambiguous,
        out_of_domain=out_of_domain,
    )

    ctx.finalize()

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
            domain=ctx.domain,
            jurisdiction=ctx.jurisdiction,
            language=ctx.requested_language,
            sources=[_source_card(c, i + 1) for i, c in enumerate(evidence_chunks)],
            citations=[],
            claim_trace_map=[],
            abstained=True,
            abstain_reason=final_abstention.reason,
            latency_ms=ctx.latency_ms,
            error=llm_error,
            diagnostic_trace=ctx.get_diagnostic_dict() if debug else None,
        )

    final_answer = citation_result["cleaned_answer"]

    # 12. Multilingual Translation
    if ctx.requested_language != "en":
        final_answer = translate_response(final_answer, ctx.requested_language, llm_translate)

    return RAGResponse(
        success=True,
        answer=final_answer,
        confidence=confidence_result.score,
        confidence_level=confidence_result.level,
        domain=ctx.domain,
        jurisdiction=ctx.jurisdiction,
        language=ctx.requested_language,
        sources=[_source_card(c, i + 1) for i, c in enumerate(evidence_chunks)],
        citations=citation_result["citations"],
        claim_trace_map=citation_result.get("claim_trace_map", []),
        abstained=False,
        latency_ms=ctx.latency_ms,
        mode="quick",
        diagnostic_trace=ctx.get_diagnostic_dict() if debug else None,
    )


# =====================================================
# TEST
# =====================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    res = answer_query("What is Section 3(d) of the Patents Act?", debug=True)
    print("RAG Pipeline self-test passed! Confidence:", res.confidence, "Abstained:", res.abstained)
    if res.diagnostic_trace:
        print("Diagnostic trace keys:", list(res.diagnostic_trace.keys()))
    assert res.success
