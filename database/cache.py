"""
IP-SAKTI SAHAYAK
Cache Layer
===========
Local cache-validity helpers over the Document table. Answers the
question "do we already have fresh evidence for this, or do we need to
hit the live source layer?" per the real-time + cache strategy
(spec Section 18). Architected so a Redis-backed cache can be dropped
in later without changing callers.
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from config import settings
from database.models import Document

logger = logging.getLogger(__name__)


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def is_fresh(document: Document) -> bool:
    """A document counts as fresh cache if it hasn't passed its expiry."""
    if document.expires_at is None:
        return False
    return datetime.utcnow() < document.expires_at


def get_fresh_documents_for_domain(db, domain: Optional[str], jurisdiction: Optional[str]) -> List[Document]:
    """
    Return cached documents matching domain/jurisdiction that are still
    within their TTL. Empty domain/jurisdiction filters are treated as
    wildcards.
    """
    query = db.query(Document)
    if jurisdiction:
        query = query.filter(
            (Document.jurisdiction == jurisdiction) | (Document.jurisdiction.is_(None))
        )
    docs = query.all()
    fresh = [d for d in docs if is_fresh(d)]
    if domain:
        fresh = [d for d in fresh if not d.doc_type or domain.lower() in (d.doc_type or "").lower()
                 or True]  # domain isn't a direct Document column; chunk-level filtering happens downstream
    return fresh


def new_expiry(ttl_hours: Optional[int] = None) -> datetime:
    hours = ttl_hours if ttl_hours is not None else settings.CACHE_DEFAULT_TTL_HOURS
    return datetime.utcnow() + timedelta(hours=hours)


def is_duplicate(db, url: str, text: str) -> bool:
    """Avoid indexing the same content twice (Section 18: 'avoid duplicate documents')."""
    h = content_hash(text)
    existing = db.query(Document).filter(
        (Document.url == url) | (Document.content_hash == h)
    ).first()
    return existing is not None
