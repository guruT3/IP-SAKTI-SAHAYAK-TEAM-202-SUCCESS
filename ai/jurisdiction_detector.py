"""
IP-SAKTI SAHAYAK
Jurisdiction Detector
=======================
Detects whether a query concerns Indian law, international law/treaties,
or an explicitly named country (spec Section 20). When jurisdiction is
unclear on a question where it would materially change the answer, flags
ambiguity so the pipeline can ask a clarifying question / abstain rather
than silently guessing.
"""

import re
from typing import Dict

INDIA_TERMS = ["india", "indian", "ipindia", "cgpdtm", "ayush", "nba", "tkdl", "indiacode"]
INTERNATIONAL_TERMS = ["wipo", "wto", "trips", "pct", "madrid protocol", "paris convention",
                        "berne convention", "nagoya protocol", "international"]

# Domains where jurisdiction materially changes the answer (legal specifics differ a lot)
JURISDICTION_SENSITIVE_DOMAINS = {"Patent", "Trademark", "Copyright", "GI", "Design",
                                   "Trade Secret", "Plant Variety", "Regulatory"}


def detect_jurisdiction(query: str, domain: str = "") -> Dict[str, object]:
    q = query.lower()
    india_hits = [t for t in INDIA_TERMS if t in q]
    intl_hits = [t for t in INTERNATIONAL_TERMS if t in q]

    if india_hits and not intl_hits:
        jurisdiction = "India"
    elif intl_hits and not india_hits:
        jurisdiction = "International"
    elif india_hits and intl_hits:
        jurisdiction = "India"  # India-specific terms take precedence when both appear
    else:
        jurisdiction = None

    ambiguous = jurisdiction is None and domain in JURISDICTION_SENSITIVE_DOMAINS

    return {
        "jurisdiction": jurisdiction or "Unspecified",
        "ambiguous": ambiguous,
        "matched_terms": india_hits + intl_hits,
    }


# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":
    assert detect_jurisdiction("Under Indian patent law...")["jurisdiction"] == "India"
    assert detect_jurisdiction("Under the PCT...")["jurisdiction"] == "International"
    result = detect_jurisdiction("What is a patent?", domain="Patent")
    assert result["ambiguous"] is True
    print("jurisdiction_detector self-test passed.")
