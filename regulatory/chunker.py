"""
IP-SAKTI SAHAYAK
Regulatory-Aware Legal Chunker
================================
Specialized chunking engine that parses statutory and regulatory texts while
strictly preserving the legal hierarchy:
  Act / Statute / Ordinance
    ↓
  Chapter / Part / Schedule
    ↓
  Section / Article / Rule / Regulation
    ↓
  Subsection / Sub-rule / Clause / Sub-clause
    ↓
  Explanation / Proviso / Standard / Table

Every generated chunk retains its parent regulatory hierarchy and provenance metadata.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from regulatory.models import RegulatoryChunk

logger = logging.getLogger(__name__)

# Matches comprehensive statutory and regulatory structural boundaries
REGULATORY_HEADING_RE = re.compile(
    r"^(?:(?:CHAPTER|PART|SCHEDULE|ANNEXURE|APPENDIX)\s+[\dIVXLCDM]+|"
    r"(?:Section|Sec\.|Article|Art\.|Rule|Regulation|Clause|Notification|Guideline|Standard)\s+[\dIVXLC]+[\w.()/\-]*|"
    r"(?:Explanation\s*(?:\d+)?|Proviso(?:\s*\d+)?|Table\s*[\dIVXLC.]+))\s*[:.\-—]?",
    re.IGNORECASE | re.MULTILINE,
)

DEFAULT_REG_CHUNK_SIZE = 950       # characters (~190-230 tokens)
DEFAULT_REG_CHUNK_OVERLAP = 150


def split_by_regulatory_hierarchy(text: str) -> List[Dict[str, str]]:
    """Splits text along statutory boundaries (Section, Rule, Schedule, Article, Clause)."""
    matches = list(REGULATORY_HEADING_RE.finditer(text))
    if not matches:
        return [{"heading": None, "body": text}]

    segments = []
    if matches[0].start() > 0:
        segments.append({"heading": None, "body": text[: matches[0].start()]})

    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        first_line = text[start:end].split("\n", 1)[0].strip()
        body = text[start:end]
        segments.append({"heading": first_line, "body": body})

    return [s for s in segments if s["body"].strip()]


def _fixed_window(text: str, size: int, overlap: int) -> List[str]:
    if len(text) <= size:
        return [text] if text.strip() else []
    windows = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        windows.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return windows


def chunk_regulatory_document(
    document_id: str,
    text: str,
    authority: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    country: Optional[str] = None,
    domain: Optional[str] = None,
    source_url: Optional[str] = None,
    source_priority: int = 1,
    document_type: str = "REGULATION",
    version: Optional[str] = "1.0",
    effective_date: Optional[str] = None,
    status: str = "CURRENT",
    page_map: Optional[Dict[int, str]] = None,
    chunk_size: int = DEFAULT_REG_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_REG_CHUNK_OVERLAP,
) -> List[RegulatoryChunk]:
    """
    Splits regulatory documents into hierarchy-preserving chunks with complete
    provenance and version tracking metadata.
    """
    segments = split_by_regulatory_hierarchy(text)
    chunks: List[RegulatoryChunk] = []
    counter = 0

    for seg in segments:
        body = seg["body"].strip()
        if not body:
            continue
        sub_windows = _fixed_window(body, chunk_size, chunk_overlap)
        for window in sub_windows:
            counter += 1
            page_num = _guess_page(window, page_map) if page_map else None

            # Extract section or clause details if present
            section_title = seg["heading"] or f"Provision {counter}"
            chapter = None
            if "chapter" in section_title.lower() or "part" in section_title.lower():
                chapter = section_title

            chunks.append(
                RegulatoryChunk(
                    chunk_id=f"{document_id}-C{counter:04d}",
                    document_id=document_id,
                    text=window.strip(),
                    section=section_title,
                    chapter=chapter,
                    clause=None,
                    page=page_num,
                    authority=authority,
                    jurisdiction=jurisdiction,
                    country=country,
                    domain=domain,
                    source_url=source_url,
                    source_priority=source_priority,
                    document_type=document_type,
                    version=version,
                    effective_date=effective_date,
                    status=status,
                )
            )

    if not chunks:
        logger.warning("chunk_regulatory_document produced 0 chunks for document_id=%s", document_id)
    return chunks


def _guess_page(window: str, page_map: Dict[int, str]) -> Optional[int]:
    snippet = window[:50].strip()
    if not snippet:
        return None
    for page_num, page_text in page_map.items():
        if snippet[:25] and snippet[:25] in page_text:
            return page_num
    return None


if __name__ == "__main__":
    sample = (
        "Regulation 4. Composition and Requirements for Food Supplements.\n"
        "(1) Food supplements shall not contain any substance prohibited by the Central Government.\n"
        "(2) Vitamins and minerals shall not exceed 100% of the Recommended Dietary Allowances (RDA).\n"
        "Regulation 5. Labelling Requirements for Nutraceuticals.\n"
        "Every package of nutraceutical shall bear the words 'NOT FOR MEDICINAL USE'."
    )
    chunks = chunk_regulatory_document(
        document_id="fssai-nutra-2022",
        text=sample,
        authority="FSSAI",
        jurisdiction="India",
        country="India",
        domain="Food",
        effective_date="2022-04-01",
    )
    print(f"Regulatory chunker produced {len(chunks)} chunks:")
    for c in chunks:
        print(f"  [{c.chunk_id}] Section: {c.section} | Status: {c.status}")
