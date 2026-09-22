"""
IP-SAKTI SAHAYAK
Unified Query Router & Multi-Engine Decomposer
================================================
Intelligently routes and synthesizes queries across:
1. Pure IP Law queries -> IP-RAG Engine (rag/rag_pipeline.py)
2. Pure Regulatory & Compliance queries -> Regulatory RAG Engine (regulatory/pipeline.py)
3. Hybrid Questions (IP + Regulatory) -> Query Decomposition Engine:
   Splits query into IP sub-question and Regulatory sub-question, executes parallel
   retrieval across both isolated knowledge stores, and fuses evidence into a unified dossier.
"""

import logging
import re
from typing import Dict, Any, Optional

from rag.rag_pipeline import answer_query as answer_ip_query
from regulatory.pipeline import answer_regulatory_query
from ai.llm import llm_client

logger = logging.getLogger(__name__)

IP_KEYWORDS = [
    "patent", "patentability", "section 3(d)", "section 3(p)", "section 3(e)",
    "prior art", "tkdl", "trademark", "copyright", "geographical indication", "gi tag",
    "pct", "trips", "inventive step", "novelty", "patent infringement", "claim drafting",
]

REGULATORY_KEYWORDS = [
    "fssai", "cdsco", "ayush", "license", "licensing", "food safety", "nutraceutical",
    "selling in india", "commercialize", "can i sell", "approval pathway", "rule 158b",
    "schedule t", "gmp", "fda", "ema", "thmpd", "dshea", "labeling", "health claims",
    "heavy metal limit", "abs approval", "nba approval", "section 6 bda", "cosmetic",
    "medical device", "packaging requirement", "legal metrology",
]


def classify_query_type(query: str) -> str:
    """Classifies query as 'ip', 'regulatory', or 'hybrid'."""
    q_lower = query.lower()

    has_ip = any(kw in q_lower for kw in IP_KEYWORDS)
    has_reg = any(kw in q_lower for kw in REGULATORY_KEYWORDS)

    if has_ip and has_reg:
        return "hybrid"
    elif has_reg:
        return "regulatory"
    elif has_ip:
        return "ip"
    else:
        # Default based on context
        if any(w in q_lower for w in ["sell", "market", "approval", "safe", "product", "ingredient", "drink", "medicine"]):
            return "regulatory"
        return "ip"


def execute_unified_query(
    query: str,
    country: Optional[str] = None,
    domain: Optional[str] = None,
    language: Optional[str] = None,
    mode: str = "quick",
) -> Dict[str, Any]:
    """
    Unified entry point that dispatches or decomposes questions seamlessly.
    """
    query_type = classify_query_type(query)
    logger.info("Unified Router classified query as: %s", query_type)

    if query_type == "regulatory":
        reg_res = answer_regulatory_query(
            query=query,
            requested_country=country,
            requested_domain=domain,
            requested_language=language,
            mode=mode,
        )
        return {
            "router_decision": "regulatory",
            "query_type": "regulatory",
            "success": True,
            "answer": reg_res.answer,
            "confidence": reg_res.confidence,
            "confidence_level": reg_res.confidence_level,
            "country": reg_res.country,
            "jurisdiction": reg_res.jurisdiction,
            "domain": reg_res.domain,
            "primary_authority": reg_res.primary_authority,
            "applicable_regulation": reg_res.applicable_regulation,
            "relevant_provisions": reg_res.relevant_provisions,
            "effective_date": reg_res.effective_date,
            "status": reg_res.status,
            "sources": [
                {
                    "index": e.index,
                    "source_name": e.source_name,
                    "authority": e.authority,
                    "jurisdiction": e.jurisdiction,
                    "country": e.country,
                    "section": e.section,
                    "version": e.version,
                    "effective_date": e.effective_date,
                    "status": e.status,
                    "url": e.url,
                    "url_display": e.url_display,
                    "text_snippet": e.text_snippet,
                    "source_priority": e.source_priority,
                }
                for e in reg_res.evidence
            ],
            "citations": reg_res.citations,
            "claim_trace_map": [ct.__dict__ for ct in reg_res.claim_trace_map],
            "abstained": reg_res.abstained,
            "abstain_reason": reg_res.abstain_reason,
            "discrepancies": reg_res.discrepancies,
            "latency_ms": reg_res.latency_ms,
            "mode": mode,
        }

    elif query_type == "ip":
        ip_res = answer_ip_query(
            query=query,
            requested_jurisdiction=country,
            requested_language=language,
            mode=mode,
        )
        return {
            "router_decision": "ip",
            "query_type": "ip",
            "success": True,
            "answer": ip_res.answer,
            "confidence": ip_res.confidence,
            "confidence_level": ip_res.confidence_level,
            "country": ip_res.jurisdiction,
            "jurisdiction": ip_res.jurisdiction,
            "domain": ip_res.domain,
            "primary_authority": ip_res.sources[0].get("authority", "IP India") if ip_res.sources else "IP India",
            "sources": ip_res.sources,
            "citations": ip_res.citations,
            "claim_trace_map": ip_res.claim_trace_map,
            "abstained": ip_res.abstained,
            "abstain_reason": ip_res.abstain_reason,
            "latency_ms": ip_res.latency_ms,
            "mode": mode,
        }

    else:
        # Hybrid Decomposition Mode
        logger.info("Executing Hybrid Decomposition on query: %s", query)
        ip_sub_query = f"{query} patentability novelty section 3d section 3p traditional knowledge"
        reg_sub_query = f"{query} regulatory approval licensing fssai ayush cdsco requirements"

        ip_res = answer_ip_query(query=ip_sub_query, requested_jurisdiction=country, requested_language=language)
        reg_res = answer_regulatory_query(query=reg_sub_query, requested_country=country, requested_domain=domain, requested_language=language)

        combined_answer = (
            f"### PART 1: INTELLECTUAL PROPERTY & PATENTABILITY ASSESSMENT\n\n"
            f"{ip_res.answer}\n\n"
            f"---\n\n"
            f"### PART 2: STATUTORY REGULATORY & COMMERCIAL COMPLIANCE\n\n"
            f"{reg_res.answer}"
        )

        all_sources = []
        for s in ip_res.sources:
            all_sources.append({**s, "subsystem": "IP Knowledge Base"})
        for e in reg_res.evidence:
            all_sources.append({
                "index": len(all_sources) + 1,
                "source_name": e.source_name,
                "authority": e.authority,
                "jurisdiction": e.jurisdiction,
                "country": e.country,
                "section": e.section,
                "version": e.version,
                "effective_date": e.effective_date,
                "status": e.status,
                "url": e.url,
                "url_display": e.url_display,
                "text_snippet": e.text_snippet,
                "subsystem": "Regulatory Knowledge Base",
            })

        avg_conf = round((ip_res.confidence + reg_res.confidence) / 2, 2)
        conf_level = "HIGH" if avg_conf >= 0.8 else "MEDIUM" if avg_conf >= 0.6 else "LOW"

        return {
            "router_decision": "hybrid",
            "query_type": "hybrid",
            "success": True,
            "answer": combined_answer,
            "confidence": avg_conf,
            "confidence_level": conf_level,
            "country": country or "India",
            "jurisdiction": country or "India",
            "domain": "Hybrid IP & Product Regulation",
            "primary_authority": f"IP India & {reg_res.primary_authority}",
            "sources": all_sources,
            "citations": ip_res.citations + reg_res.citations,
            "claim_trace_map": [ct.__dict__ if hasattr(ct, '__dict__') else ct for ct in reg_res.claim_trace_map],
            "abstained": ip_res.abstained and reg_res.abstained,
            "latency_ms": ip_res.latency_ms + reg_res.latency_ms,
            "mode": mode,
        }
