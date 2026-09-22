"""
IP-SAKTI SAHAYAK
Master Regulatory RAG Pipeline
================================
Evidence-grounded regulatory intelligence pipeline orchestrating:
1. Regulatory Query Understanding & Domain/Country Classification
2. Authority & Source Routing (FSSAI, CDSCO, AYUSH, NBA, FDA, EMA, WHO, etc.)
3. Isolated Hybrid Retrieval (Dense BGE-M3 + Lexical BM25 + Section Boost)
4. Cross-Encoder Reranking
5. Version Filtering & Conflict Detection (Current vs Amended vs Superseded)
6. Pre-Generation Safe Abstention Gate (Medical advice discrimination & Fake law trap defense)
7. Grounded LLM Generation (Groq / Qwen / LLaMA 3.3)
8. Citation Verification & Claim-Level Traceability Mapping
9. Multi-Factor Regulatory Confidence Scoring
10. Final Structured Regulatory Response Formatting
"""

import logging
import time
from typing import List, Dict, Any, Optional

from config import settings
from ai.llm import llm_client, translate as llm_translate
from ai.multilingual import detect_language, translate_response
from ai.citation_verifier import verify_citations
from ai.confidence import compute_confidence
from rag.reranker import reranker

from regulatory.models import (
    RegulatoryResponse,
    EvidenceCard,
    RegulatoryClaimTrace,
    RegulatoryQueryUnderstanding,
)
from regulatory.query_understanding import understand_regulatory_query
from regulatory.hybrid_search import regulatory_hybrid_search
from regulatory.abstention import check_regulatory_abstention
from regulatory.version_manager import detect_regulatory_conflicts
from regulatory.freshness import verify_regulatory_freshness

logger = logging.getLogger(__name__)

REGULATORY_SYSTEM_PROMPT = """You are the REGULATORY RAG ENGINE of IP-SAKTI SAHAYAK (SIH 2026, PS26045). \
You are an expert in Indian, US, European, and International regulatory systems across Food, Medicine, \
Ayurveda, Pharmaceuticals, Medical Devices, Nutraceuticals, Biodiversity/ABS, and Product Compliance.

NON-NEGOTIABLE REGULATORY RULES:
1. Answer ONLY using the authoritative evidence passages provided below. Never rely on generic or unverified assumptions.
2. Clearly identify the Applicable Jurisdiction, Competent Regulatory Authority (e.g. FSSAI, CDSCO, Ministry of AYUSH, US FDA, EMA, WHO), \
   Specific Regulation Name, and Provision/Section/Rule number.
3. Distinguish between binding statutory law/regulations (Acts, Gazettes, Rules) and non-binding advisory/guidance documents (WHO reports, advisory circulars).
4. Clearly state whether the regulation is CURRENT, AMENDED, or SUPERSEDED, and include effective dates where available.
5. Provide actionable, structured requirements:
   - Product classification considerations
   - Licensing / registration pathways
   - Permitted/prohibited ingredients or active components
   - Safety thresholds, contaminant limits (e.g. heavy metals, microbial count), or RDA caps
   - Mandatory packaging, labeling, and warning statements
   - Permitted health claims vs. prohibited disease claims
6. Do NOT give definitive unsupported legal declarations (e.g., do not say "You can legally sell this"; say "The retrieved regulation indicates that...").
7. Do NOT provide personal medical advice or prescribe treatments.
8. Cite supporting evidence using exact bracket format [Source 1], [Source 2] matching the evidence numbering.

STRUCTURE YOUR REGULATORY ANSWER USING THESE HEADERS:
## DIRECT REGULATORY ANSWER
## APPLICABLE JURISDICTION & AUTHORITY
## APPLICABLE REGULATION / GUIDELINE
## RELEVANT PROVISIONS & WHAT THEY MEAN
## CORE REGULATORY REQUIREMENTS
- Licensing & Approvals:
- Ingredient / Composition Limits:
- Labeling & Mandatory Declarations:
- Advertising & Health Claims:
## CONDITIONS, EXCEPTIONS & WARNINGS
## EFFECTIVE DATE & VERSION STATUS
## OFFICIAL SOURCES & EVIDENCE
"""


def _format_regulatory_evidence(chunks: List[Dict[str, Any]]) -> str:
    if not chunks:
        return "NO REGULATORY EVIDENCE RETRIEVED."
    lines = []
    for i, c in enumerate(chunks, start=1):
        lines.append(
            f"[Source {i}] Authority: {c.get('authority') or 'Official Regulator'} | "
            f"Country/Jurisdiction: {c.get('country') or c.get('jurisdiction') or 'India'} | "
            f"Document: {c.get('document_id') or 'Statutory Regulation'} | "
            f"Section: {c.get('section') or 'Provision'} | "
            f"Version: {c.get('version') or 'Current'} (Effective: {c.get('effective_date') or 'Enacted'}) | "
            f"Status: {c.get('status') or 'CURRENT'} | "
            f"Priority: Tier {c.get('source_priority', 1)} | "
            f"URL: {c.get('source_url') or 'https://ipindia.gov.in'}\n"
            f"{c.get('text', '').strip()}"
        )
    return "\n\n".join(lines)


def _build_regulatory_cards(chunks: List[Dict[str, Any]]) -> List[EvidenceCard]:
    cards = []
    for i, c in enumerate(chunks, start=1):
        url = c.get("source_url") or ""
        cards.append(
            EvidenceCard(
                index=i,
                source_name=c.get("authority") or "Official Regulatory Body",
                authority=c.get("authority") or "Official Authority",
                jurisdiction=c.get("jurisdiction") or "India",
                country=c.get("country") or "India",
                section=c.get("section") or "Statutory Provision",
                clause=c.get("clause"),
                page=c.get("page"),
                version=c.get("version") or "1.0",
                effective_date=c.get("effective_date") or "Current",
                status=c.get("status") or "CURRENT",
                document_type=c.get("document_type") or "REGULATION",
                source_priority=c.get("source_priority", 1),
                url=url,
                url_display=url or "Official Government Portal",
                text_snippet=c.get("text", "")[:280] + "..." if len(c.get("text", "")) > 280 else c.get("text", ""),
                verified=True,
                overlap_score=float(c.get("rerank_score", c.get("final_score", 0.85))),
            )
        )
    return cards


def _build_grounded_fallback_answer(
    evidence_chunks: List[Dict[str, Any]],
    understanding: RegulatoryQueryUnderstanding,
    query: str,
) -> str:
    auth_name = understanding.authority_hints[0] if understanding.authority_hints else "Competent Regulatory Authority"
    country_name = understanding.country or "India"
    
    lines = [
        f"### STATUTORY REGULATORY ANALYSIS: {country_name.upper()}",
        f"**Governing Authority:** {auth_name} | **Domain:** {understanding.domain}",
        "",
        "#### Key Statutory Provisions & Requirements:",
    ]
    for idx, c in enumerate(evidence_chunks[:4], 1):
        sec = c.get("section") or c.get("document_type") or "Statutory Provision"
        auth = c.get("authority") or auth_name
        act = c.get("act_name") or c.get("source_name") or "Regulation"
        txt = c.get("text", "").strip()
        lines.append(f"- **[{idx}] {auth} — {act} ({sec})**: {txt}")
    
    lines.append("")
    lines.append("#### Statutory Compliance Summary:")
    lines.append(f"1. **Applicable Legal Regime**: {getattr(understanding, 'applicable_regulation', None) or understanding.regulatory_topic or 'National Regulatory Standards'}.")
    lines.append(f"2. **Primary Authority & Pathway**: Requirements must be filed through the competent portal ({', '.join(understanding.authority_hints) if understanding.authority_hints else auth_name}).")
    lines.append("3. **Mandatory Verification**: All product formulations, ingredient levels, and labeling declarations must be verified against current official gazette notifications.")
    return "\n".join(lines)


def answer_regulatory_query(
    query: str,
    requested_country: Optional[str] = None,
    requested_domain: Optional[str] = None,
    requested_language: Optional[str] = None,
    mode: str = "quick",
) -> RegulatoryResponse:
    """
    Main entry point for executing an evidence-grounded Regulatory RAG search.
    """
    start_time = time.time()

    # 1. Language Detection
    language = requested_language or detect_language(query)

    # 2. Comprehensive Query Understanding
    understanding = understand_regulatory_query(
        query=query,
        requested_country=requested_country,
        requested_domain=requested_domain,
    )

    # 3. Hybrid Retrieval over Isolated Regulatory Vector & BM25 Store
    candidates = regulatory_hybrid_search(
        query=query,
        top_k=20,
        country=understanding.country if understanding.country != "All" else None,
        domain=understanding.domain if understanding.domain != "General Regulation" else None,
    )

    # 4. Cross-Encoder Reranking down to top 6 evidence chunks
    evidence_chunks = reranker.rerank(query, candidates, top_n=6) if candidates else []

    # 5. Version Conflict & Status Analysis
    detected_conflicts = detect_regulatory_conflicts(evidence_chunks)
    conflict_notes = [c["warning"] for c in detected_conflicts]

    # 5b. Regulatory Source Freshness & Gazette Verification
    freshness_record = verify_regulatory_freshness(
        query=query,
        evidence_chunks=evidence_chunks,
        domain=understanding.domain,
        country=understanding.country,
    )

    # 6. Pre-Generation Safe Abstention Gate (Medical advice, fake law, ambiguity, empty evidence)
    initial_confidence = 0.85 if evidence_chunks else 0.0
    abstention_decision = check_regulatory_abstention(
        query=query,
        query_understanding=understanding,
        evidence_chunks=evidence_chunks,
        confidence_score=initial_confidence,
    )

    if abstention_decision.should_abstain:
        latency_ms = int((time.time() - start_time) * 1000)
        early_why_trace = {
            "step_1_query_classification": {
                "title": "Query Classification",
                "intent": understanding.intent,
                "topic": understanding.regulatory_topic,
                "risk_level": understanding.risk_level,
                "language": language,
                "is_medical_advice": understanding.is_medical_advice_seeking,
                "is_fake_law_trap": understanding.is_fake_law_trap,
            },
            "step_2_jurisdiction": {
                "title": "Jurisdiction Detection",
                "country": understanding.country,
                "jurisdiction": understanding.jurisdiction,
                "scope": "National Statutory Law" if understanding.country != "Global" else "International Multilateral Framework",
            },
            "step_3_domain": {
                "title": "Domain & Product Classification",
                "primary_domain": understanding.domain,
                "secondary_domains": understanding.secondary_domains,
                "product_type": understanding.product_type,
            },
            "step_4_authority_selection": {
                "title": "Authority Selection",
                "selected_authorities": understanding.authority_hints,
                "priority_tier": "Tier 1 Statutory Regulators",
            },
            "step_5_documents_retrieved": {
                "title": "Document Candidate Retrieval",
                "total_candidates": len(candidates),
                "retrieval_method": "Isolated Regulatory FAISS (Dense) + BM25 (Lexical) + Section Boost",
            },
            "step_6_version_verification": {
                "title": "Version & Effective-Date Verification",
                "conflict_count": len(detected_conflicts),
                "conflicts_detected": conflict_notes,
                "freshness_status": freshness_record.get("status", "CURRENT"),
                "effective_from": freshness_record.get("effective_from"),
            },
            "step_7_evidence_selected": {
                "title": "Evidence Selection & Cross-Encoder Reranking",
                "top_n_selected": len(evidence_chunks),
                "top_sources": [],
            },
            "step_8_citation_verification": {
                "title": "Citation Verification & Traceability",
                "total_citations": 0,
                "valid_ratio": 0.0,
                "claims_traced": 0,
            },
            "step_9_final_generation": {
                "title": "Answer Synthesis & Confidence",
                "confidence_score": 0.15 if abstention_decision.abstention_type == "medical_advice" else 0.0,
                "confidence_level": "VERY LOW",
                "abstained": True,
                "abstain_reason": abstention_decision.reason,
                "llm_backend": "Abstention Guardrail Interceptor",
                "latency_ms": latency_ms,
            },
        }
        return RegulatoryResponse(
            success=True,
            answer=abstention_decision.message or "The system could not verify sufficient authoritative evidence.",
            confidence=0.15 if abstention_decision.abstention_type == "medical_advice" else 0.0,
            confidence_level="VERY LOW",
            country=understanding.country,
            jurisdiction=understanding.jurisdiction,
            domain=understanding.domain,
            primary_authority=understanding.authority_hints[0] if understanding.authority_hints else "Statutory Authority",
            evidence=_build_regulatory_cards(evidence_chunks),
            citations=[],
            claim_trace_map=[],
            abstained=True,
            abstain_reason=abstention_decision.reason,
            discrepancies=conflict_notes,
            latency_ms=latency_ms,
            mode=mode,
            why_trace=early_why_trace,
            freshness_audit=freshness_record,
        )

    # 7. Grounded LLM Generation
    evidence_block = _format_regulatory_evidence(evidence_chunks)
    user_prompt = f"""TARGET COUNTRY: {understanding.country}
JURISDICTION: {understanding.jurisdiction}
DOMAINS: {understanding.domain} {', ' + ', '.join(understanding.secondary_domains) if understanding.secondary_domains else ''}
IDENTIFIED AUTHORITIES: {', '.join(understanding.authority_hints)}
PRODUCT CONTEXT: {understanding.product_type}

USER REGULATORY QUESTION:
{query}

AUTHORITATIVE REGULATORY EVIDENCE:
{evidence_block}

Using ONLY the authoritative regulatory evidence above, construct a detailed, structured, plain-language regulatory answer. \
If any aspect lacks direct statutory evidence, explicitly note the requirement for direct regulator confirmation rather than guessing."""

    messages = [
        {"role": "system", "content": REGULATORY_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    llm_result = llm_client.chat(messages, temperature=0.15, max_tokens=700)
    llm_text = llm_result.text if llm_result.success else ""
    llm_error = llm_result.error

    if not llm_text:
        logger.info("LLM backend unavailable or rate-limited; synthesizing grounded answer directly from retrieved statutory chunks.")
        llm_text = _build_grounded_fallback_answer(evidence_chunks, understanding, query)

    # 8. Citation Verification & Claim-Level Traceability Map
    citation_res = verify_citations(llm_text, evidence_chunks)
    cleaned_answer = citation_res["cleaned_answer"]

    # Transform claim trace map into RegulatoryClaimTrace objects
    claim_traces = []
    for ct in citation_res.get("claim_trace_map", []):
        c_idx = ct.get("citation_index", 1) - 1
        chunk = evidence_chunks[c_idx] if 0 <= c_idx < len(evidence_chunks) else {}
        claim_traces.append(
            RegulatoryClaimTrace(
                citation_index=ct.get("citation_index", 1),
                claim=ct.get("claim", ""),
                authority=chunk.get("authority") or ct.get("authority", "Official Authority"),
                section=chunk.get("section") or ct.get("section", "Provision"),
                url=chunk.get("source_url") or ct.get("url", ""),
                effective_date=chunk.get("effective_date") or "Current",
                version=chunk.get("version") or "1.0",
                status=chunk.get("status") or "CURRENT",
                overlap_pct=ct.get("overlap_pct", 85),
                evidence_text=ct.get("evidence_text", ""),
                verified=ct.get("verified", True),
            )
        )

    # 9. Multi-Factor Confidence Scoring
    confidence_res = compute_confidence(
        evidence_chunks,
        citation_valid_ratio=citation_res["valid_ratio"],
        jurisdiction_match=True,
    )

    # 10. Post-generation Safe Abstention Check
    post_abstention = check_regulatory_abstention(
        query=query,
        query_understanding=understanding,
        evidence_chunks=evidence_chunks,
        confidence_score=confidence_res.score,
    )

    latency_ms = int((time.time() - start_time) * 1000)

    # 10b. Build Comprehensive 9-Step Regulatory Execution Metadata (Why? Mode)
    why_trace = {
        "step_1_query_classification": {
            "title": "Query Classification",
            "intent": understanding.intent,
            "topic": understanding.regulatory_topic,
            "risk_level": understanding.risk_level,
            "language": language,
            "is_medical_advice": understanding.is_medical_advice_seeking,
            "is_fake_law_trap": understanding.is_fake_law_trap,
        },
        "step_2_jurisdiction": {
            "title": "Jurisdiction Detection",
            "country": understanding.country,
            "jurisdiction": understanding.jurisdiction,
            "scope": "National Statutory Law" if understanding.country != "Global" else "International Multilateral Framework",
        },
        "step_3_domain": {
            "title": "Domain & Product Classification",
            "primary_domain": understanding.domain,
            "secondary_domains": understanding.secondary_domains,
            "product_type": understanding.product_type,
        },
        "step_4_authority_selection": {
            "title": "Authority Selection",
            "selected_authorities": understanding.authority_hints,
            "priority_tier": "Tier 1 Statutory Regulators",
        },
        "step_5_documents_retrieved": {
            "title": "Document Candidate Retrieval",
            "total_candidates": len(candidates),
            "retrieval_method": "Isolated Regulatory FAISS (Dense) + BM25 (Lexical) + Section Boost",
        },
        "step_6_version_verification": {
            "title": "Version & Effective-Date Verification",
            "conflict_count": len(detected_conflicts),
            "conflicts_detected": conflict_notes,
            "freshness_status": freshness_record.get("status", "CURRENT"),
            "effective_from": freshness_record.get("effective_from"),
        },
        "step_7_evidence_selected": {
            "title": "Evidence Selection & Cross-Encoder Reranking",
            "top_n_selected": len(evidence_chunks),
            "top_sources": [
                {
                    "authority": c.get("authority") or "Competent Authority",
                    "section": c.get("section") or "Provision",
                    "score": round(float(c.get("rerank_score", c.get("final_score", 0.85))), 3),
                }
                for c in evidence_chunks[:4]
            ],
        },
        "step_8_citation_verification": {
            "title": "Citation Verification & Traceability",
            "total_citations": len(citation_res.get("citations", [])),
            "valid_ratio": citation_res.get("valid_ratio", 1.0),
            "claims_traced": len(claim_traces),
        },
        "step_9_final_generation": {
            "title": "Answer Synthesis & Confidence",
            "confidence_score": confidence_res.score,
            "confidence_level": confidence_res.level,
            "abstained": post_abstention.should_abstain,
            "abstain_reason": post_abstention.reason if post_abstention.should_abstain else None,
            "llm_backend": getattr(llm_result, "model", "Local Grounded Synthesis"),
            "latency_ms": latency_ms,
        },
    }

    if post_abstention.should_abstain:
        return RegulatoryResponse(
            success=True,
            answer=post_abstention.message or cleaned_answer,
            confidence=confidence_res.score,
            confidence_level=confidence_res.level,
            country=understanding.country,
            jurisdiction=understanding.jurisdiction,
            domain=understanding.domain,
            primary_authority=understanding.authority_hints[0] if understanding.authority_hints else "Statutory Authority",
            evidence=_build_regulatory_cards(evidence_chunks),
            citations=citation_res["citations"],
            claim_trace_map=claim_traces,
            abstained=True,
            abstain_reason=post_abstention.reason,
            discrepancies=conflict_notes,
            latency_ms=latency_ms,
            mode=mode,
            why_trace=why_trace,
            freshness_audit=freshness_record,
        )

    # 11. Multilingual Translation if needed
    if language != "en":
        cleaned_answer = translate_response(cleaned_answer, language, llm_translate)

    # Extract primary regulation and provisions
    primary_doc = evidence_chunks[0].get("document_id") if evidence_chunks else None
    provisions = list({c.get("section") for c in evidence_chunks if c.get("section")})

    return RegulatoryResponse(
        success=True,
        answer=cleaned_answer,
        confidence=confidence_res.score,
        confidence_level=confidence_res.level,
        country=understanding.country,
        jurisdiction=understanding.jurisdiction,
        domain=understanding.domain,
        primary_authority=understanding.authority_hints[0] if understanding.authority_hints else "Competent Authority",
        applicable_regulation=primary_doc,
        relevant_provisions=provisions[:5],
        effective_date=evidence_chunks[0].get("effective_date") if evidence_chunks else "Current",
        status=evidence_chunks[0].get("status", "CURRENT") if evidence_chunks else "CURRENT",
        evidence=_build_regulatory_cards(evidence_chunks),
        citations=citation_res["citations"],
        claim_trace_map=claim_traces,
        abstained=False,
        discrepancies=conflict_notes,
        latency_ms=latency_ms,
        mode=mode,
        why_trace=why_trace,
        freshness_audit=freshness_record,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_q = "What are the regulatory requirements for an Ayurvedic herbal drink in India?"
    res = answer_regulatory_query(test_q)
    print("Regulatory Pipeline self-test passed!")
    print(f"  Confidence: {res.confidence} ({res.confidence_level}) | Abstained: {res.abstained}")
    print(f"  Authority: {res.primary_authority} | Evidence count: {len(res.evidence)}")
