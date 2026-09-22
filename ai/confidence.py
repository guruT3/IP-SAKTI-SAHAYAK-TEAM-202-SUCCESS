"""
IP-SAKTI SAHAYAK
Confidence Scoring
===================
Combines retrieval quality, source authority, citation validity, and
evidence agreement into a single 0-1 confidence score plus a
HIGH/MEDIUM/LOW/VERY LOW label (spec Section 25). Thresholds come from
config so they're tunable without code changes.
"""

from dataclasses import dataclass
from typing import List, Dict, Any

from config import settings

# Lower priority number = higher authority (matches Source.priority, 1=best)
_MAX_PRIORITY = 5


@dataclass
class ConfidenceResult:
    score: float
    level: str
    explanation: str


def _authority_score(chunks: List[Dict[str, Any]]) -> float:
    if not chunks:
        return 0.0
    priorities = [c.get("priority", 3) for c in chunks]
    avg_priority = sum(priorities) / len(priorities)
    return max(0.0, (_MAX_PRIORITY - avg_priority) / (_MAX_PRIORITY - 1))


def _agreement_score(chunks: List[Dict[str, Any]]) -> float:
    """Crude proxy: more distinct supporting sources -> more agreement, capped."""
    if not chunks:
        return 0.0
    distinct_sources = len({c.get("source_url") or c.get("authority") for c in chunks})
    return min(1.0, distinct_sources / 3)


def compute_confidence(
    evidence_chunks: List[Dict[str, Any]],
    citation_valid_ratio: float,
    jurisdiction_match: bool,
) -> ConfidenceResult:
    if not evidence_chunks:
        return ConfidenceResult(0.0, "VERY LOW", "No supporting evidence was retrieved.")

    retrieval_scores = [c.get("rerank_score", c.get("final_score", c.get("score", 0))) for c in evidence_chunks]
    # rerank/hybrid scores aren't guaranteed to be 0-1 (cross-encoder logits
    # in particular can be negative/large); squash defensively.
    norm_retrieval = min(1.0, max(0.0, (sum(retrieval_scores) / len(retrieval_scores) + 1) / 2))

    authority = _authority_score(evidence_chunks)
    agreement = _agreement_score(evidence_chunks)
    jurisdiction_factor = 1.0 if jurisdiction_match else 0.6

    score = (
        0.30 * norm_retrieval +
        0.25 * authority +
        0.20 * citation_valid_ratio +
        0.15 * agreement +
        0.10 * jurisdiction_factor
    )
    score = round(min(1.0, max(0.0, score)), 3)

    if score >= settings.CONFIDENCE_HIGH:
        level = "HIGH"
    elif score >= settings.CONFIDENCE_MEDIUM:
        level = "MEDIUM"
    elif score >= settings.CONFIDENCE_LOW:
        level = "LOW"
    else:
        level = "VERY LOW"

    explanation = (
        f"retrieval={norm_retrieval:.2f}, authority={authority:.2f}, "
        f"citation_validity={citation_valid_ratio:.2f}, agreement={agreement:.2f}, "
        f"jurisdiction_match={jurisdiction_match}"
    )
    return ConfidenceResult(score=score, level=level, explanation=explanation)


# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":
    chunks = [
        {"rerank_score": 0.8, "priority": 1, "source_url": "https://ipindia.gov.in"},
        {"rerank_score": 0.7, "priority": 1, "source_url": "https://indiacode.nic.in"},
    ]
    result = compute_confidence(chunks, citation_valid_ratio=1.0, jurisdiction_match=True)
    print(result)
    assert result.level in ("HIGH", "MEDIUM")
    empty = compute_confidence([], 1.0, True)
    assert empty.level == "VERY LOW"
    print("confidence self-test passed.")
