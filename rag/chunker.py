"""
IP-SAKTI SAHAYAK
Legal-Aware Chunker
====================
Splits cleaned document text into retrieval-sized chunks while trying
to respect legal document structure (Acts, Chapters, Sections, Articles,
Rules, clauses) instead of blind fixed-width splitting, per spec
Section 11. Every chunk carries full provenance metadata.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

# Matches common legal heading patterns: "Section 3.", "Section 3(d)",
# "Article 27", "Chapter IV", "Rule 12", "Clause 5.2"
_HEADING_RE = re.compile(
    r"^(Section|Article|Chapter|Rule|Clause|Regulation)\s+[\dIVXLC]+[\w.()]*",
    re.IGNORECASE | re.MULTILINE,
)

DEFAULT_CHUNK_SIZE = 900       # characters, approx ~180-220 tokens
DEFAULT_CHUNK_OVERLAP = 150


@dataclass
class Chunk:
    document_id: str
    chunk_id: str
    text: str
    section: Optional[str] = None
    page: Optional[int] = None
    authority: Optional[str] = None
    jurisdiction: Optional[str] = None
    source_url: Optional[str] = None
    version: Optional[str] = None
    effective_date: Optional[str] = None


def _split_by_headings(text: str) -> List[Dict[str, str]]:
    """Split text into (heading, body) segments at legal heading boundaries."""
    matches = list(_HEADING_RE.finditer(text))
    if not matches:
        return [{"heading": None, "body": text}]

    segments = []
    if matches[0].start() > 0:
        segments.append({"heading": None, "body": text[: matches[0].start()]})

    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        heading_line = text[start:end].split("\n", 1)[0].strip()
        body = text[start:end]
        segments.append({"heading": heading_line, "body": body})

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


def chunk_document(
    document_id: str,
    text: str,
    authority: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    source_url: Optional[str] = None,
    version: Optional[str] = None,
    effective_date: Optional[str] = None,
    page_map: Optional[Dict[int, str]] = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[Chunk]:
    """
    Produce legal-aware chunks: first split on Section/Article/Chapter/
    Rule/Clause headings, then sub-split any oversized segment with a
    sliding window so no chunk blows past the embedding model's
    effective context.
    """
    segments = _split_by_headings(text)
    chunks: List[Chunk] = []
    counter = 0

    for seg in segments:
        body = seg["body"].strip()
        if not body:
            continue
        sub_windows = _fixed_window(body, chunk_size, chunk_overlap)
        for window in sub_windows:
            counter += 1
            page_number = _guess_page(window, page_map) if page_map else None
            chunks.append(
                Chunk(
                    document_id=document_id,
                    chunk_id=f"{document_id}-{counter:04d}",
                    text=window.strip(),
                    section=seg["heading"],
                    page=page_number,
                    authority=authority,
                    jurisdiction=jurisdiction,
                    source_url=source_url,
                    version=version,
                    effective_date=effective_date,
                )
            )

    if not chunks:
        logger.warning("chunk_document produced 0 chunks for document_id=%s", document_id)
    return chunks


def _guess_page(window: str, page_map: Dict[int, str]) -> Optional[int]:
    snippet = window[:60].strip()
    if not snippet:
        return None
    for page_num, page_text in page_map.items():
        if snippet[:30] and snippet[:30] in page_text:
            return page_num
    return None


# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":
    sample = (
        "Section 3. What are not inventions.\n"
        "The following are not inventions within the meaning of this Act -\n"
        "Section 3(d) the mere discovery of a new form of a known substance...\n"
        "Section 4. Inventions relating to atomic energy not patentable.\n"
        "No patent shall be granted in respect of an invention relating to atomic energy."
    )
    result = chunk_document("act-1970", sample, authority="IP India", jurisdiction="India")
    assert len(result) >= 2
    assert any("3(d)" in c.section or "" for c in result if c.section)
    print(f"chunker self-test passed: {len(result)} chunks produced.")
