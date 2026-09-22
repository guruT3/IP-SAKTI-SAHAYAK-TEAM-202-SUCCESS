"""
IP-SAKTI SAHAYAK
Citation Verifier & Evidence Traceability ("Why did AI say this?")
===================================================================
1. Validates that every [Source N] in the generated answer points to a valid retrieved chunk.
2. Computes lexical and concept overlap between the generated claim sentence and the chunk.
3. Automatically strips or flags unverified citations.
4. Generates structured 'Why did AI say this?' traceability metadata mapping each claim
   to its exact statutory source, page, section, and authority URL.
"""

import re
import logging
from dataclasses import dataclass
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

_CITATION_RE = re.compile(r"\[Source\s+(\d+)\]")


@dataclass
class VerifiedCitation:
    index: int
    source_name: str
    section: str
    url: str
    valid: bool
    overlap_score: float = 0.0
    evidence_snippet: str = ""
    claim_sentence: str = ""


def extract_citation_indices(answer_text: str) -> List[int]:
    return sorted({int(m) for m in _CITATION_RE.findall(answer_text)})


def _overlap_ratio(claim_context: str, chunk_text: str) -> float:
    claim_tokens = set(re.findall(r"[a-zA-Z0-9]{3,}", claim_context.lower()))
    chunk_tokens = set(re.findall(r"[a-zA-Z0-9]{3,}", chunk_text.lower()))
    if not claim_tokens or not chunk_tokens:
        return 0.0
    return len(claim_tokens & chunk_tokens) / max(1, len(claim_tokens))


def verify_citations(answer_text: str, evidence_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Verifies citations and produces claim-level traceability mapping for the UI.
    """
    cited_indices = extract_citation_indices(answer_text)
    citations: List[VerifiedCitation] = []
    invalid_indices = []
    claim_trace_map = []

    # Split answer into sentences to isolate claim context
    sentences = re.split(r"(?<=[.!?])\s+", answer_text)

    for idx in cited_indices:
        pos = idx - 1
        if pos < 0 or pos >= len(evidence_chunks):
            invalid_indices.append(idx)
            citations.append(VerifiedCitation(idx, "Unknown Source", "N/A", "", valid=False))
            continue

        chunk = evidence_chunks[pos]
        chunk_text = chunk.get("text", "")

        # Find sentences containing this citation marker
        matching_sentences = [s for s in sentences if f"[Source {idx}]" in s]
        claim_context = " ".join(matching_sentences) if matching_sentences else answer_text
        overlap = _overlap_ratio(claim_context, chunk_text)

        is_valid = overlap >= 0.06  # Lenient threshold to catch fabrication while allowing legal summarization

        if not is_valid:
            invalid_indices.append(idx)

        vc = VerifiedCitation(
            index=idx,
            source_name=chunk.get("authority") or "Official Authority",
            section=chunk.get("section") or "Statutory Excerpt",
            url=chunk.get("source_url") or "",
            valid=is_valid,
            overlap_score=round(overlap, 2),
            evidence_snippet=chunk_text[:240] + "..." if len(chunk_text) > 240 else chunk_text,
            claim_sentence=claim_context[:200],
        )
        citations.append(vc)
        claim_trace_map.append({
            "citation_index": idx,
            "claim": claim_context[:180],
            "authority": vc.source_name,
            "section": vc.section,
            "url": vc.url,
            "overlap_pct": int(overlap * 100),
            "evidence_text": vc.evidence_snippet,
            "verified": is_valid,
        })

    cleaned_answer = answer_text
    for idx in invalid_indices:
        cleaned_answer = cleaned_answer.replace(f"[Source {idx}]", "[citation removed — unverified]")

    valid_count = sum(1 for c in citations if c.valid)
    valid_ratio = valid_count / len(citations) if citations else 1.0

    return {
        "citations": [c.__dict__ for c in citations],
        "claim_trace_map": claim_trace_map,
        "all_valid": len(invalid_indices) == 0,
        "cleaned_answer": cleaned_answer,
        "valid_ratio": round(valid_ratio, 2),
    }


# =====================================================
# TEST
# =====================================================
if __name__ == "__main__":
    evidence = [{"authority": "IP India", "section": "Section 3(d)", "source_url": "https://ipindia.gov.in",
                 "text": "Section 3(d) excludes mere discovery of a new form of a known substance."}]
    ans = "Under Indian law, mere discovery of a new form of a known substance is excluded from patentability [Source 1]."
    res = verify_citations(ans, evidence)
    assert res["all_valid"]
    print("citation_verifier self-test passed! Trace count:", len(res["claim_trace_map"]))
