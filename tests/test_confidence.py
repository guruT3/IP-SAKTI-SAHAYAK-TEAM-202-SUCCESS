"""Tests for confidence scoring and safe abstention."""
from ai.confidence import compute_confidence
from ai.abstention import check_abstention


def test_no_evidence_gives_very_low_confidence():
    result = compute_confidence([], citation_valid_ratio=1.0, jurisdiction_match=True)
    assert result.level == "VERY LOW"


def test_abstention_triggers_on_no_evidence():
    decision = check_abstention(
        query="What is Section 3(d)?",
        evidence_chunks=[],
        confidence_score=0.0,
        citation_all_valid=True,
        jurisdiction_ambiguous=False,
        out_of_domain=False,
    )
    assert decision.should_abstain


def test_no_abstention_with_strong_evidence():
    chunks = [
        {"rerank_score": 0.9, "priority": 1, "source_url": "https://ipindia.gov.in", "text": "Section 3(d)"},
        {"rerank_score": 0.85, "priority": 1, "source_url": "https://indiacode.nic.in", "text": "Patents Act"},
    ]
    conf = compute_confidence(chunks, citation_valid_ratio=1.0, jurisdiction_match=True)
    decision = check_abstention(
        query="What is Section 3(d)?",
        evidence_chunks=chunks,
        confidence_score=conf.score,
        citation_all_valid=True,
        jurisdiction_ambiguous=False,
        out_of_domain=False,
    )
    assert not decision.should_abstain
