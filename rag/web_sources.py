"""
IP-SAKTI SAHAYAK
Real-Time Web Source Layer
===========================
Fetches and extracts content from the authoritative source registry
only (never arbitrary sites — spec Section 17). Respects robots.txt,
never bypasses auth/CAPTCHA/paywalls, times out politely, and never
leaks stack traces to callers.
"""

import logging
import urllib.robotparser as robotparser
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

import requests

from config import settings
from rag.text_cleaner import extract_text_from_html

logger = logging.getLogger(__name__)

USER_AGENT = "IP-SAKTI-SAHAYAK-Research-Bot/1.0 (+educational SIH prototype)"


@dataclass
class FetchedSource:
    url: str
    title: str
    text: str
    authority: Optional[str] = None
    jurisdiction: Optional[str] = None
    document_type: Optional[str] = None
    status: str = "ok"          # ok | blocked_by_robots | timeout | http_error | empty | malformed
    error: Optional[str] = None


def _robots_allowed(url: str) -> bool:
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(USER_AGENT, url)
    except Exception as e:
        # If robots.txt can't be read, default to allow but log it — do not
        # treat this as license to bypass anything requiring auth.
        logger.info("robots.txt check failed for %s (%s); defaulting to allow.", url, e)
        return True


def fetch_source(url: str) -> FetchedSource:
    """Fetch a single URL, honoring robots.txt and handling errors safely."""
    if not _robots_allowed(url):
        return FetchedSource(url=url, title="", text="", status="blocked_by_robots",
                              error="Disallowed by robots.txt")
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=settings.REQUEST_TIMEOUT_SECONDS,
        )
    except requests.Timeout:
        return FetchedSource(url=url, title="", text="", status="timeout", error="Request timed out")
    except requests.RequestException as e:
        return FetchedSource(url=url, title="", text="", status="http_error", error=str(e))

    if resp.status_code >= 400:
        return FetchedSource(url=url, title="", text="", status="http_error",
                              error=f"HTTP {resp.status_code}")

    try:
        text = extract_text_from_html(resp.text)
        title = _extract_title(resp.text) or url
    except Exception as e:
        logger.error("Content extraction failed for %s: %s", url, e)
        return FetchedSource(url=url, title="", text="", status="malformed", error="Extraction failed")

    if not text.strip():
        return FetchedSource(url=url, title=title, text="", status="empty", error="No extractable content")

    return FetchedSource(url=url, title=title, text=text, status="ok")


def _extract_title(html: str) -> Optional[str]:
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        if soup.title and soup.title.string:
            return soup.title.string.strip()
    except Exception:
        pass
    return None


def search_official_sources(query: str, sources: List[Dict[str, Any]]) -> List[FetchedSource]:
    """
    Given the enabled rows from the Source registry (already filtered by
    domain/jurisdiction upstream), fetch each source's base_url as a
    coarse "does this source currently say anything relevant" pass.

    NOTE: this hits each configured source's landing/base page. A
    production version would use each authority's own search endpoint
    where available (tracked as future scope) — this keeps the prototype
    within "never bypass access controls" and "no arbitrary scraping".
    """
    results = []
    for src in sources:
        fetched = fetch_source(src["base_url"])
        fetched.authority = src.get("authority")
        fetched.jurisdiction = src.get("jurisdiction")
        fetched.document_type = src.get("source_type")
        if fetched.status != "ok":
            logger.info("Source fetch non-ok for %s: %s (%s)", src.get("source_name"), fetched.status, fetched.error)
        results.append(fetched)
    return results


def build_source_metadata(fetched: FetchedSource, source_row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "title": fetched.title,
        "url": fetched.url,
        "authority": source_row.get("authority"),
        "jurisdiction": source_row.get("jurisdiction"),
        "source_type": source_row.get("source_type"),
        "priority": source_row.get("priority"),
    }


def validate_source(fetched: FetchedSource) -> bool:
    return fetched.status == "ok" and bool(fetched.text.strip())


# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = fetch_source("https://example.com")
    print("web_sources self-test:", result.status, result.title)
