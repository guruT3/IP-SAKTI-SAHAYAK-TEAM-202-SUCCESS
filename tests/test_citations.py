"""Tests for citation verification."""
from ai.citation_verifier import verify_citations


def test_valid_citation_passes():
    evidence = [{"authority": "IP India", "section": "Section 3(d)", "source_url": "https://ipindia.gov.in",
                 "text": "Section 3(d) excludes mere discovery of a new form of a known substance."}]
    answer = "Mere discovery of a new form of a known substance is excluded [Source 1]."
    result = verify_citations(answer, evidence)
    assert result["all_valid"]


def test_fabricated_citation_is_stripped():
    evidence = [{"authority": "IP India", "section": "Section 3(d)", "source_url": "https://ipindia.gov.in",
                 "text": "Section 3(d) excludes mere discovery of a new form of a known substance."}]
    answer = "Gold prices will hit an all-time high in 2035 [Source 9]."
    result = verify_citations(answer, evidence)
    assert not result["all_valid"]
    assert "[citation removed" in result["cleaned_answer"]
