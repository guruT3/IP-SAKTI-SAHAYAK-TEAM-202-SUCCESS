"""
IP-SAKTI SAHAYAK
Document Analyzer
===================
Optional secondary feature (spec Section 29): analyze an uploaded
legal/IP document and extract type, jurisdiction hints, key sections,
dates, and cited-law mentions using lightweight regex heuristics plus
domain classification — no fabricated legal conclusions.
"""

import re
import logging
from typing import Dict, Any, List

from rag.document_loader import load_document
from rag.text_cleaner import clean_text
from ai.domain_classifier import classify_domain
from ai.jurisdiction_detector import detect_jurisdiction

logger = logging.getLogger(__name__)

_DATE_RE = re.compile(r"\b(\d{1,2}[-/th|st|nd|rd\s]*\s*(?:January|February|March|April|May|June|July|"
                       r"August|September|October|November|December|\d{1,2})[-/,\s]*\d{2,4})\b", re.IGNORECASE)
_SECTION_RE = re.compile(r"\b(Section|Article|Chapter|Rule|Clause)\s+[\dIVXLC]+[\w.()]*", re.IGNORECASE)
_LAW_RE = re.compile(
    r"\b(Patents? Act|Trade Marks? Act|Copyright Act|Designs Act|Geographical Indications? .*?Act|"
    r"PCT|TRIPS|WIPO|Nagoya Protocol|Madrid Protocol|Biological Diversity Act)\b", re.IGNORECASE
)


def analyze_document(path: str) -> Dict[str, Any]:
    loaded = load_document(path)
    text = clean_text(loaded.text)

    if not text.strip():
        return {
            "document_name": loaded.document_name,
            "error": "No extractable text found in the uploaded document.",
        }

    domain_result = classify_domain(text[:4000])
    jurisdiction_result = detect_jurisdiction(text[:4000], domain=domain_result["domain"])

    sections = sorted(set(m.group(0) for m in _SECTION_RE.finditer(text)))[:25]
    dates = sorted(set(m.group(0) for m in _DATE_RE.finditer(text)))[:15]
    cited_laws = sorted(set(m.group(0) for m in _LAW_RE.finditer(text)), key=str.lower)

    return {
        "document_name": loaded.document_name,
        "document_type_guess": domain_result["domain"],
        "jurisdiction_guess": jurisdiction_result["jurisdiction"],
        "important_sections": sections,
        "dates_found": dates,
        "cited_laws_and_authorities": cited_laws,
        "character_count": len(text),
        "note": (
            "This is an automated structural extraction, not a legal interpretation of the "
            "document's rights or obligations."
        ),
    }


# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":
    print("document_analyzer module loaded — call analyze_document(path) with a real file to test.")
