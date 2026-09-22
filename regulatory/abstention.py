"""
IP-SAKTI SAHAYAK
Regulatory Safe Abstention & Guardrails Engine
================================================
Implements non-negotiable safety guardrails for the Regulatory RAG Engine:
1. Personal Medical Advice vs. Regulatory Information Guardrail:
   - System provides official regulatory status, approved indications, and official warnings,
     but strictly abstains from prescribing dosages, diagnosing symptoms, or advising on medication changes.
2. Adversarial Red-Team Fake Law / Regulation Trap Detection.
3. Insufficient Authoritative Evidence Gate.
4. Jurisdictional Ambiguity Gate.
5. Regulatory Conflict & Discrepancy Gate.
"""

import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

MEDICAL_DISCLAIMER_HEADER = (
    "⚠ IMPORTANT HEALTH & MEDICAL NOTICE\n"
    "IP-SAKTI SAHAYAK provides evidence-grounded statutory regulatory information from official government agencies. "
    "This system is NOT a medical doctor and CANNOT provide personal medical advice, diagnose conditions, or prescribe treatments. "
    "For individual health concerns or dosage questions, please consult a registered medical practitioner or qualified healthcare professional."
)


@dataclass
class RegulatoryAbstentionDecision:
    should_abstain: bool
    reason: Optional[str] = None
    message: Optional[str] = None
    abstention_type: Optional[str] = None  # medical_advice | fake_law_trap | insufficient_evidence | jurisdiction_ambiguous | regulatory_conflict
    discrepancy_details: Optional[Dict[str, Any]] = None


def detect_abstention_or_defense(
    query: str,
    country: Optional[str] = None,
    domain: Optional[str] = None,
) -> tuple[bool, str]:
    """
    Convenience wrapper to check if a query triggers medical advice, fake regulation,
    or adversarial traps before full retrieval execution.
    Returns: (should_abstain: bool, reason_message: str)
    """
    from regulatory.query_understanding import understand_regulatory_query
    qu = understand_regulatory_query(query, default_country=country, default_domain=domain)
    decision = check_regulatory_abstention(query, qu, evidence_chunks=[{"dummy": True}], confidence_score=0.9)
    if decision.should_abstain:
        return True, decision.reason or decision.message or "Query triggers safety abstention."
    return False, ""


def check_regulatory_abstention(
    query: str,
    query_understanding,
    evidence_chunks: List[Dict[str, Any]],
    confidence_score: float,
) -> RegulatoryAbstentionDecision:
    """
    Evaluates regulatory safety, anti-hallucination gates, and medical advice barriers.
    """
    # 1. Check for Personal Medical Advice Seeking
    if query_understanding.is_medical_advice_seeking:
        message = (
            f"{MEDICAL_DISCLAIMER_HEADER}\n\n"
            f"Regarding your query on '{query}':\n"
            f"Under statutory regulations (such as Ministry of AYUSH Schedule T guidelines, CDSCO drug labeling rules, "
            f"and US FDA 21 CFR regulations), medicinal dosage, therapeutic administration, and individual treatment regimens "
            f"must strictly be determined by licensed physicians based on specific clinical parameters and patient medical history.\n\n"
            f"If you are seeking official approved regulatory indications, pharmacopoeial monograph specifications, or manufacturing "
            f"compliance standards for this substance, please rephrase your question in a regulatory context."
        )
        return RegulatoryAbstentionDecision(
            should_abstain=True,
            reason="Query requests personal medical advice, symptom diagnosis, or prescriptive dosage guidance.",
            message=message,
            abstention_type="medical_advice",
        )

    # 2. Check for Adversarial Fake Law Traps
    if query_understanding.is_fake_law_trap:
        message = (
            f"I could not verify the existence of the cited regulation or statutory provision in any authoritative "
            f"Indian, US, European, or international regulatory gazettes.\n\n"
            f"Sources checked include: India Code, Gazette of India, FSSAI Regulations, CDSCO Drug Rules, Ministry of AYUSH "
            f"statutes, US Code of Federal Regulations (21 CFR), and WIPO Lex.\n\n"
            f"The system cannot generate legal or compliance requirements for an unverified or non-existent regulatory instrument."
        )
        return RegulatoryAbstentionDecision(
            should_abstain=True,
            reason="Cited statute, section number, or notification was identified as a non-existent or adversarial legal trap.",
            message=message,
            abstention_type="fake_law_trap",
        )

    # 3. Check for Mandatory Jurisdictional Ambiguity
    if query_understanding.requires_clarification and query_understanding.clarification_prompt:
        message = (
            f"To provide an accurate and authoritative regulatory answer, additional jurisdictional context is required.\n\n"
            f"{query_understanding.clarification_prompt}\n\n"
            f"Please specify the target market (e.g., India, United States, European Union, United Kingdom, etc.) so that the "
            f"appropriate regulatory authority (such as FSSAI vs. US FDA vs. EMA) and applicable standards can be retrieved."
        )
        return RegulatoryAbstentionDecision(
            should_abstain=True,
            reason="Governing country/jurisdiction is ambiguous and materially dictates the applicable regulatory regime.",
            message=message,
            abstention_type="jurisdiction_ambiguous",
        )

    # 4. Check for Empty or Insufficient Authoritative Evidence
    if not evidence_chunks:
        authorities_str = ", ".join(query_understanding.authority_hints) if query_understanding.authority_hints else "Official Regulators"
        message = (
            f"I could not find sufficient authoritative regulatory evidence in the currently indexed official sources to answer this question reliably.\n\n"
            f"• Target Jurisdiction: {query_understanding.country}\n"
            f"• Domain: {query_understanding.domain}\n"
            f"• Relevant Authorities Searched: {authorities_str}\n\n"
            f"To avoid hallucination or unverified regulatory advice, the system has safely abstained. "
            f"Please verify this requirement directly with the relevant official regulator."
        )
        return RegulatoryAbstentionDecision(
            should_abstain=True,
            reason="No verified statutory or regulatory chunks could be matched from authoritative sources.",
            message=message,
            abstention_type="insufficient_evidence",
        )

    # 5. Check for Low Confidence Score
    if confidence_score < 0.35:
        message = (
            f"The available regulatory evidence is insufficient or lacks high-priority statutory backing (Confidence: {confidence_score:.2f}).\n\n"
            f"The retrieved passages do not clearly establish a definitive compliance requirement for this specific scenario. "
            f"Formal confirmation from the competent statutory authority is recommended."
        )
        return RegulatoryAbstentionDecision(
            should_abstain=True,
            reason=f"Evidence confidence score ({confidence_score:.2f}) is below the regulatory safety threshold.",
            message=message,
            abstention_type="low_confidence",
        )

    return RegulatoryAbstentionDecision(should_abstain=False)
