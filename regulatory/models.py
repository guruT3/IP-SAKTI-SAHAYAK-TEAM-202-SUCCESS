"""
IP-SAKTI SAHAYAK
Regulatory Data Models & Schema
=================================
Data classes and schemas for the Regulatory RAG Engine.
Preserves complete legal provenance (document, section, subsection, clause,
authority, version, effective date, status, priority, and official source link).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class RegulatoryChunk:
    chunk_id: str
    document_id: str
    text: str
    section: Optional[str] = None
    chapter: Optional[str] = None
    clause: Optional[str] = None
    page: Optional[int] = None
    authority: Optional[str] = None
    jurisdiction: Optional[str] = None
    country: Optional[str] = None
    domain: Optional[str] = None
    source_url: Optional[str] = None
    source_priority: int = 1
    document_type: str = "REGULATION"  # STATUTE | REGULATION | RULE | NOTIFICATION | GUIDELINE | STANDARD | ADVISORY
    version: Optional[str] = None
    effective_date: Optional[str] = None
    status: str = "CURRENT"             # CURRENT | AMENDED | SUPERSEDED | DRAFT | PROPOSED | EXPIRED
    superseded_by: Optional[str] = None


@dataclass
class RegulatoryDocument:
    document_id: str
    title: str
    organization: str
    country: str
    jurisdiction: str
    domains: List[str]
    document_type: str                  # STATUTE | REGULATION | RULE | NOTIFICATION | GUIDELINE | STANDARD
    source_priority: int
    source_url: str
    official_source: bool = True
    publication_date: Optional[str] = None
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None
    version: str = "1.0"
    last_updated: Optional[str] = None
    language: str = "en"
    status: str = "CURRENT"             # CURRENT | AMENDED | SUPERSEDED | DRAFT | EXPIRED
    supersedes: Optional[str] = None
    superseded_by: Optional[str] = None
    content_hash: Optional[str] = None
    retrieved_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    chunks: List[RegulatoryChunk] = field(default_factory=list)


@dataclass
class EvidenceCard:
    index: int
    source_name: str
    authority: str
    jurisdiction: str
    country: str
    section: Optional[str]
    clause: Optional[str]
    page: Optional[int]
    version: Optional[str]
    effective_date: Optional[str]
    status: str
    document_type: str
    source_priority: int
    url: Optional[str]
    url_display: str
    text_snippet: str
    verified: bool = True
    overlap_score: float = 0.0


@dataclass
class RegulatoryClaimTrace:
    citation_index: int
    claim: str
    authority: str
    section: str
    url: str
    effective_date: str
    version: str
    status: str
    overlap_pct: int
    evidence_text: str
    verified: bool


@dataclass
class RegulatoryQueryUnderstanding:
    raw_query: str
    intent: str
    domain: str
    secondary_domains: List[str]
    country: str
    jurisdiction: str
    authority_hints: List[str]
    product_type: str
    regulatory_topic: str
    date_context: str
    language: str
    risk_level: str                    # HIGH | MEDIUM | LOW
    is_medical_advice_seeking: bool
    is_fake_law_trap: bool
    requires_clarification: bool
    clarification_prompt: Optional[str] = None


@dataclass
class RegulatoryResponse:
    success: bool
    answer: str
    confidence: float
    confidence_level: str              # HIGH | MEDIUM | LOW | VERY LOW
    country: str
    jurisdiction: str
    domain: str
    primary_authority: str
    applicable_regulation: Optional[str] = None
    relevant_provisions: List[str] = field(default_factory=list)
    effective_date: Optional[str] = None
    status: str = "CURRENT"
    evidence: List[EvidenceCard] = field(default_factory=list)
    citations: List[Dict[str, Any]] = field(default_factory=list)
    claim_trace_map: List[RegulatoryClaimTrace] = field(default_factory=list)
    abstained: bool = False
    abstain_reason: Optional[str] = None
    discrepancies: List[str] = field(default_factory=list)
    disclaimer: str = (
        "This is an evidence-grounded regulatory information system based on authentic official sources. "
        "It is not a substitute for formal legal, medical, or statutory regulatory advice."
    )
    latency_ms: int = 0
    mode: str = "quick"
    why_trace: Optional[Dict[str, Any]] = None
    freshness_audit: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
