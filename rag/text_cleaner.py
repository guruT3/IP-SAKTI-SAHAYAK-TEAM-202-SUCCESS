"""
IP-SAKTI SAHAYAK
Text Cleaner
============
Normalizes raw extracted text (PDF/HTML) and provides robust HTML
extraction via BeautifulSoup, respecting the "never bypass access
controls" constraint — this module only cleans text already fetched
lawfully by web_sources.py, it does not fetch anything itself.
"""

import re
import logging

logger = logging.getLogger(__name__)

_WHITESPACE_RE = re.compile(r"[ \t]+")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
_HYPHEN_LINEBREAK_RE = re.compile(r"(\w)-\n(\w)")


def clean_text(raw: str) -> str:
    if not raw:
        return ""
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    text = _HYPHEN_LINEBREAK_RE.sub(r"\1\2", text)   # rejoin hyphenated line-wraps
    text = _WHITESPACE_RE.sub(" ", text)
    text = _MULTI_NEWLINE_RE.sub("\n\n", text)
    lines = [ln.strip() for ln in text.split("\n")]
    return "\n".join(ln for ln in lines if ln != "").strip()


def extract_text_from_html(html: str) -> str:
    """
    Extract readable body text from HTML using BeautifulSoup, stripping
    nav/script/style/footer noise so downstream chunking sees content,
    not markup.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.error("beautifulsoup4 not installed; returning raw HTML string.")
        return clean_text(html)

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "form"]):
        tag.decompose()

    main = soup.find("main") or soup.find("article") or soup.body or soup
    text = main.get_text(separator="\n")
    return clean_text(text)


def normalize_legal_text(text: str) -> str:
    """
    Light legal-specific normalization: standardize section markers like
    'Sec.' / 'sec' -> 'Section', and collapse spaced-out sub-clause
    numbering ('3 (d)' -> '3(d)') so keyword search matches consistently.
    """
    text = re.sub(r"\bSec\.\s*", "Section ", text, flags=re.IGNORECASE)
    text = re.sub(r"(\d)\s+\(([a-zA-Z0-9]+)\)", r"\1(\2)", text)
    return text


# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":
    sample = "Patent-\nability under  Section 3 (d)   is limited.\n\n\n\nSee also Sec. 2(1)(j)."
    cleaned = normalize_legal_text(clean_text(sample))
    assert "Section 3(d)" in cleaned
    assert "Section 2(1)(j)" in cleaned
    print("text_cleaner self-test passed:", cleaned)
