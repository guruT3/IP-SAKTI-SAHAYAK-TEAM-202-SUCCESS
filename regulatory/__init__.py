"""
IP-SAKTI SAHAYAK
Regulatory RAG Subsystem
"""
from regulatory.pipeline import answer_regulatory_query
from regulatory.unified_router import execute_unified_query
from regulatory.registry import get_all_regulatory_sources, get_source_by_id, filter_sources
from regulatory.ingestion import bootstrap_regulatory_indexes, run_regulatory_ingestion

__all__ = [
    "answer_regulatory_query",
    "execute_unified_query",
    "get_all_regulatory_sources",
    "get_source_by_id",
    "filter_sources",
    "bootstrap_regulatory_indexes",
    "run_regulatory_ingestion",
]
