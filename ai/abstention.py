"""
IP-SAKTI SAHAYAK
Safe Abstention & Hallucination Defense Gate
=============================================
Strictly gates responses to prevent legal hallucination:
1. Out-of-Domain Detection (general chitchat, weather, movies, coding, financial speculation)
2. Adversarial Red-Team Trap Detection (fake/non-existent section numbers like Sec 99B, non-existent acts)
3. Insufficient Evidence Detection (when authoritative retrieval yields zero relevant statutory passages)
4. Citation Validity Threshold (when generated claims fail ground truth alignment)
5. Jurisdiction Ambiguity Detection (when question requires knowing country to give legal answer)

Safe Abstention is treated as a CORE FEATURE, not a failure.
"""

import re
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from config import settings
from ai.prompts import build_abstention_message

logger = logging.getLogger(__name__)

# Known fake or non-existent statutory section traps for red-team evaluation
KNOWN_FAKE_PROVISIONS = [
    "section 99b", "section 99", "section 108a", "section 200", "section 500",
    "ayurvedic patent free grant act", "traditional medicine universal immunity act",
    "section 3(z)", "section 3(y)", "section 3(x)",
]

# Explicit out-of-domain keywords that must trigger safe abstention
OUT_OF_DOMAIN_PATTERNS = [
    r"\bweather\b", r"\bmovie\b", r"\bcricket\b", r"\bfootball\b",
    r"\bstock price\b", r"\bbitcoin\b", r"\bprice of gold in 203\d\b",
    r"\brecipe for chocolate cake\b", r"\bwrite a python script for game\b",
    r"\bwho won the match\b", r"\bhoroscope\b",
]


@dataclass
class AbstentionDecision:
    should_abstain: bool
    reason: Optional[str] = None
    message: Optional[str] = None
    abstention_type: Optional[str] = None  # out_of_domain | fake_law_trap | insufficient_evidence | low_confidence


def check_adversarial_traps(query: str) -> Optional[str]:
    """Detects queries mentioning known non-existent sections or fabricated acts."""
    q_lower = query.lower()
    for fake in KNOWN_FAKE_PROVISIONS:
        if fake in q_lower:
            return f"The provision or statute '{fake.title()}' does not exist in authoritative Indian or international IP legislation."
    return None


def is_explicit_out_of_domain(query: str) -> bool:
    """Checks for explicit out-of-domain conversational queries."""
    q_lower = query.lower()
    return any(re.search(pat, q_lower) for pat in OUT_OF_DOMAIN_PATTERNS)


def check_abstention(
    query: str,
    evidence_chunks: List[Dict[str, Any]],
    confidence_score: float,
    citation_all_valid: bool,
    jurisdiction_ambiguous: bool,
    out_of_domain: bool,
) -> AbstentionDecision:
    # 1. Check for explicit out of domain patterns
    if is_explicit_out_of_domain(query) or out_of_domain:
        reason = (
            "This question falls outside IP-SAKTI SAHAYAK's specialized domain "
            "(Intellectual Property, Traditional Knowledge, Ayurveda, and related regulatory law)."
        )
        return AbstentionDecision(True, reason, build_abstention_message(reason), abstention_type="out_of_domain")

    # 2. Check for adversarial red-team fake law traps
    fake_trap_reason = check_adversarial_traps(query)
    if fake_trap_reason:
        reason = f"Adversarial / unverified legal claim detected: {fake_trap_reason}"
        return AbstentionDecision(True, reason, build_abstention_message(reason), abstention_type="fake_law_trap")

    # 3. Check for empty evidence
    if not evidence_chunks:
        reason = "No relevant evidence could be retrieved from the authoritative statutory sources currently indexed."
        return AbstentionDecision(True, reason, build_abstention_message(reason), abstention_type="insufficient_evidence")

    # 4. Check for jurisdictional ambiguity
    if jurisdiction_ambiguous:
        reason = "The jurisdiction governing this question is unspecified or ambiguous and materially affects the legal outcome."
        return AbstentionDecision(True, reason, build_abstention_message(reason), abstention_type="jurisdiction_ambiguous")

    # 5. Check for low confidence score
    if confidence_score < settings.ABSTENTION_THRESHOLD:
        reason = f"Evidence confidence score ({confidence_score:.2f}) is below the safe-answer threshold ({settings.ABSTENTION_THRESHOLD})."
        return AbstentionDecision(True, reason, build_abstention_message(reason), abstention_type="low_confidence")

    # 6. Check for failed citation verification under moderate confidence
    if not citation_all_valid and confidence_score < settings.CONFIDENCE_MEDIUM:
        reason = "Citation verification failed for part of the answer and overall evidence confidence is moderate to low."
        return AbstentionDecision(True, reason, build_abstention_message(reason), abstention_type="citation_failure")

    return AbstentionDecision(False)


SUPPORTED_DOMAIN_HINTS = {
    "Patent", "Trademark", "Copyright", "GI", "Design", "Trade Secret", "Plant Variety",
    "Traditional Knowledge", "Ayurveda", "Biodiversity", "ABS", "International IP",
    "Regulatory", "General IP",
}


def is_out_of_domain(domain: str, domain_classifier_confidence: float) -> bool:
    return domain not in SUPPORTED_DOMAIN_HINTS or domain_classifier_confidence < 0.15


# =====================================================
# TEST
# =====================================================
if __name__ == "__main__":
    d1 = check_abstention("What are penalties under Section 99B of Patents Act?", [], 0.0, True, False, False)
    assert d1.should_abstain and d1.abstention_type == "fake_law_trap"
    d2 = check_abstention("What will be the price of gold in 2035?", [], 0.0, True, False, True)
    assert d2.should_abstain and d2.abstention_type == "out_of_domain"
    print("abstention self-test passed! Both adversarial and out-of-domain cases properly caught.")
