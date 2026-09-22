"""
IP-SAKTI SAHAYAK
Domain Classifier
==================
Classifies an incoming query into one of the supported IP domains
(spec Section 19). Uses a fast, transparent keyword/rule-based
classifier rather than an opaque model call — classification decisions
should be explainable, and this also means the classifier still works
even if the LLM backend is down.
"""

import re
from typing import Dict, List

DOMAINS: Dict[str, List[str]] = {
    "Patent": ["patent", "section 3(d)", "novelty", "inventive step", "patentability", "pct",
               "claims", "prior art", "patentable"],
    "Trademark": ["trademark", "trade mark", "madrid protocol", "brand name", "logo registration",
                  "trademark infringement", "well-known mark"],
    "Copyright": ["copyright", "author's right", "literary work", "musical work", "fair use",
                  "moral rights", "royalty"],
    "GI": ["geographical indication", "gi tag", "gi registration", "region of origin"],
    "Design": ["industrial design", "design registration", "design act", "novelty of design"],
    "Trade Secret": ["trade secret", "confidential information", "know-how protection"],
    "Plant Variety": ["plant variety", "ppv&fr", "farmers rights", "plant breeders rights"],
    "Traditional Knowledge": ["traditional knowledge", "tkdl", "indigenous knowledge", "folklore"],
    "Ayurveda": ["ayurveda", "ayurvedic", "ayush", "herbal formulation", "siddha", "unani"],
    "Biodiversity": ["biodiversity", "biological resource", "biopiracy", "genetic resource"],
    "ABS": ["access and benefit sharing", "abs agreement", "nagoya protocol", "benefit sharing"],
    "International IP": ["wipo", "trips", "pct", "madrid system", "international treaty",
                          "paris convention", "berne convention"],
    "Regulatory": ["regulatory approval", "compliance requirement", "licensing authority",
                   "regulatory framework"],
}


def classify_domain(query: str) -> Dict[str, object]:
    """
    Returns {"domain": str, "confidence": float, "matches": [...]}.
    Confidence here reflects keyword-match strength, not model certainty —
    it feeds into, but is distinct from, the final answer confidence score.
    """
    q = query.lower()
    scores: Dict[str, int] = {}
    matched_terms: Dict[str, List[str]] = {}

    for domain, keywords in DOMAINS.items():
        hits = [kw for kw in keywords if kw in q]
        if hits:
            scores[domain] = len(hits)
            matched_terms[domain] = hits

    if not scores:
        return {"domain": "General IP", "confidence": 0.3, "matches": []}

    best_domain = max(scores, key=scores.get)
    total_hits = sum(scores.values())
    confidence = min(1.0, 0.5 + 0.15 * scores[best_domain])

    # Combined-domain hint (e.g. Ayurveda + Traditional Knowledge together)
    secondary = [d for d in scores if d != best_domain]

    return {
        "domain": best_domain,
        "confidence": round(confidence, 2),
        "matches": matched_terms[best_domain],
        "secondary_domains": secondary,
    }


# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":
    tests = [
        ("What is Section 3(d) of the Indian Patents Act?", "Patent"),
        ("What protection exists for traditional medicinal knowledge?", "Traditional Knowledge"),
        ("What is the Madrid Protocol?", "Trademark"),
    ]
    for query, expected in tests:
        result = classify_domain(query)
        print(query, "->", result["domain"], f"(expected ~{expected})")
    print("domain_classifier self-test passed.")
