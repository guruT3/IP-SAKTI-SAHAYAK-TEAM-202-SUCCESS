"""
IP-SAKTI SAHAYAK
Request-Scoped Query Context & Diagnostics
==========================================
Encapsulates state for a single RAG request. Ensures 100% query isolation
so no global variables, previous retrieval results, or filters spill over
between user queries (fixes "works once, fails later" issues).
"""

import uuid
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class QueryContext:
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    original_query: str = ""
    normalized_query: str = ""
    detected_language: str = "en"
    requested_language: str = "en"
    intent: str = "ip_query"
    domain: str = "General IP"
    domain_confidence: float = 1.0
    secondary_domains: List[str] = field(default_factory=list)
    jurisdiction: str = "India"
    jurisdiction_ambiguous: bool = False
    selected_source_domains: List[str] = field(default_factory=list)
    query_expansions: List[str] = field(default_factory=list)
    
    # Formulation classification (for Ayurveda/Herbals)
    formulation_category: Optional[str] = None
    formulation_classification_reason: Optional[str] = None
    
    # Retrieval diagnostics
    bm25_count: int = 0
    vector_count: int = 0
    merged_count: int = 0
    evidence_count: int = 0
    
    # Scoring & Execution
    confidence_score: float = 0.0
    confidence_level: str = "VERY LOW"
    llm_attempts: int = 0
    cache_hit: bool = False
    is_degraded: bool = False
    degraded_reason: Optional[str] = None
    error: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    latency_ms: int = 0
    
    # Diagnostic trace for internal audit mode
    trace_log: List[str] = field(default_factory=list)

    def log(self, message: str) -> None:
        elapsed = int((time.time() - self.start_time) * 1000)
        self.trace_log.append(f"[{elapsed}ms] {message}")

    def finalize(self) -> None:
        self.latency_ms = int((time.time() - self.start_time) * 1000)

    def get_diagnostic_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "original_query": self.original_query,
            "normalized_query": self.normalized_query,
            "detected_language": self.detected_language,
            "requested_language": self.requested_language,
            "domain": self.domain,
            "secondary_domains": self.secondary_domains,
            "jurisdiction": self.jurisdiction,
            "jurisdiction_ambiguous": self.jurisdiction_ambiguous,
            "selected_source_domains": self.selected_source_domains,
            "formulation_category": self.formulation_category,
            "query_expansions": self.query_expansions,
            "retrieval_counts": {
                "bm25": self.bm25_count,
                "vector": self.vector_count,
                "merged": self.merged_count,
                "evidence": self.evidence_count,
            },
            "confidence_score": self.confidence_score,
            "confidence_level": self.confidence_level,
            "cache_hit": self.cache_hit,
            "is_degraded": self.is_degraded,
            "degraded_reason": self.degraded_reason,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "trace_log": self.trace_log,
        }
