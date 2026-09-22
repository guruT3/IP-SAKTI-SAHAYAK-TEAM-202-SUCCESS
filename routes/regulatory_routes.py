"""
IP-SAKTI SAHAYAK
Regulatory RAG API Routes
===========================
REST API Endpoints for the Regulatory Intelligence Subsystem:
- POST /api/regulatory/query — Main Regulatory RAG Query Endpoint
- POST /api/regulatory/classify — Product Classification Engine
- POST /api/regulatory/compliance — Evidence-Backed Compliance Checklist
- POST /api/regulatory/compare — Cross-Country Regulatory Comparison Matrix
- GET  /api/regulatory/sources — Authoritative Regulatory Source Registry
- GET  /api/regulatory/sources/<id> — Specific Regulatory Source Details
- GET  /api/regulatory/timelines — Regulatory Amendment Timelines Feed
- GET  /api/regulatory/timeline/<id> — Specific Regulatory Timeline Record
- GET  /api/regulatory/status — Regulatory Knowledge Base & Vector Index Health
- POST /api/unified/query — Unified Query Router (IP vs Regulatory vs Decomposed Hybrid)
"""

import logging
from flask import Blueprint, request, jsonify

from ai.multilingual import normalize_language_code
from regulatory.pipeline import answer_regulatory_query
from regulatory.unified_router import execute_unified_query
from regulatory.registry import get_all_regulatory_sources, get_source_by_id, filter_sources
from regulatory.version_manager import get_all_timelines, get_timeline_by_id
from regulatory.vector_store import regulatory_vector_store
from regulatory.hybrid_search import regulatory_bm25_index
from services.regulatory_classifier import classify_product_regulatory_regime
from services.regulatory_compliance import generate_compliance_checklist
from services.regulatory_comparison import generate_cross_country_comparison

logger = logging.getLogger(__name__)
regulatory_bp = Blueprint("regulatory", __name__)


@regulatory_bp.route("/api/regulatory/query", methods=["POST"])
def regulatory_query_route():
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    country = data.get("country") or None
    if country in ("Auto Detect", "All"):
        country = None
    domain = data.get("domain") or None
    if domain in ("Auto Detect", "All"):
        domain = None
    language = normalize_language_code(data.get("language"))
    mode = (data.get("mode") or "quick").lower()

    if not query:
        return jsonify({"success": False, "error": "Query text is required."}), 400
    if len(query) > 5000:
        return jsonify({"success": False, "error": "Query is too long (max 5000 characters)."}), 400

    try:
        res = answer_regulatory_query(
            query=query,
            requested_country=country,
            requested_domain=domain,
            requested_language=language,
            mode=mode,
        )

        return jsonify({
            "success": res.success,
            "answer": res.answer,
            "confidence": res.confidence,
            "confidence_level": res.confidence_level,
            "country": res.country,
            "jurisdiction": res.jurisdiction,
            "domain": res.domain,
            "primary_authority": res.primary_authority,
            "applicable_regulation": res.applicable_regulation,
            "relevant_provisions": res.relevant_provisions,
            "effective_date": res.effective_date,
            "status": res.status,
            "evidence": [
                {
                    "index": e.index,
                    "source_name": e.source_name,
                    "authority": e.authority,
                    "jurisdiction": e.jurisdiction,
                    "country": e.country,
                    "section": e.section,
                    "clause": e.clause,
                    "page": e.page,
                    "version": e.version,
                    "effective_date": e.effective_date,
                    "status": e.status,
                    "document_type": e.document_type,
                    "source_priority": e.source_priority,
                    "url": e.url,
                    "url_display": e.url_display,
                    "text_snippet": e.text_snippet,
                    "verified": e.verified,
                    "overlap_score": e.overlap_score,
                }
                for e in res.evidence
            ],
            "citations": res.citations,
            "claim_trace_map": [
                {
                    "citation_index": ct.citation_index,
                    "claim": ct.claim,
                    "authority": ct.authority,
                    "section": ct.section,
                    "url": ct.url,
                    "effective_date": ct.effective_date,
                    "version": ct.version,
                    "status": ct.status,
                    "overlap_pct": ct.overlap_pct,
                    "evidence_text": ct.evidence_text,
                    "verified": ct.verified,
                }
                for ct in res.claim_trace_map
            ],
            "abstained": res.abstained,
            "abstain_reason": res.abstain_reason,
            "discrepancies": res.discrepancies,
            "disclaimer": res.disclaimer,
            "latency_ms": res.latency_ms,
            "mode": res.mode,
            "why_trace": res.why_trace,
            "freshness_audit": res.freshness_audit,
            "error": res.error,
        })
    except Exception as e:
        logger.exception("Regulatory query processing failed")
        return jsonify({"success": False, "error": "An error occurred while querying the regulatory knowledge base."}), 500


@regulatory_bp.route("/api/regulatory/classify", methods=["POST"])
def regulatory_classify_route():
    data = request.get_json(silent=True) or {}
    product_name = (data.get("product_name") or "Herbal Product").strip()
    ingredients = (data.get("ingredients") or "").strip()
    intended_use = (data.get("intended_use") or "").strip()
    claims = (data.get("claims") or "").strip()
    delivery_form = (data.get("delivery_form") or "Oral Tablet/Capsule").strip()
    country = data.get("country") or "India"

    if not ingredients and not intended_use:
        return jsonify({"success": False, "error": "Ingredients or intended use is required for classification."}), 400

    try:
        result = classify_product_regulatory_regime(
            product_name=product_name,
            ingredients=ingredients,
            intended_use=intended_use,
            claims=claims,
            delivery_form=delivery_form,
            country=country,
        )
        return jsonify(result)
    except Exception as e:
        logger.exception("Product classification failed")
        return jsonify({"success": False, "error": "Product classification analysis failed."}), 500


@regulatory_bp.route("/api/regulatory/compliance", methods=["POST"])
def regulatory_compliance_route():
    data = request.get_json(silent=True) or {}
    description = (data.get("description") or "").strip()
    country = data.get("country") or "India"
    domain = data.get("domain") or "Nutraceutical"

    if not description:
        return jsonify({"success": False, "error": "Product description is required."}), 400

    try:
        result = generate_compliance_checklist(
            product_description=description,
            country=country,
            domain=domain,
        )
        return jsonify(result)
    except Exception as e:
        logger.exception("Regulatory compliance checklist failed")
        return jsonify({"success": False, "error": "Compliance checklist generation failed."}), 500


@regulatory_bp.route("/api/regulatory/compare", methods=["POST"])
def regulatory_compare_route():
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    countries = data.get("countries") or ["India", "USA", "European Union"]

    if not query:
        return jsonify({"success": False, "error": "Query or product description is required."}), 400

    try:
        result = generate_cross_country_comparison(
            query=query,
            target_countries=countries,
        )
        return jsonify(result)
    except Exception as e:
        logger.exception("Cross-country comparison failed")
        return jsonify({"success": False, "error": "Comparison analysis failed."}), 500


@regulatory_bp.route("/api/regulatory/sources", methods=["GET"])
def regulatory_sources_route():
    country = request.args.get("country")
    domain = request.args.get("domain")
    priority = request.args.get("priority", type=int)

    sources = filter_sources(country=country, domain=domain, max_priority=priority)
    return jsonify({
        "success": True,
        "count": len(sources),
        "sources": sources,
    })


@regulatory_bp.route("/api/regulatory/sources/<source_id>", methods=["GET"])
def regulatory_source_detail_route(source_id):
    s = get_source_by_id(source_id)
    if not s:
        return jsonify({"success": False, "error": "Regulatory source not found."}), 404
    return jsonify({"success": True, "source": s})


@regulatory_bp.route("/api/regulatory/timelines", methods=["GET"])
def regulatory_timelines_route():
    timelines = get_all_timelines()
    return jsonify({
        "success": True,
        "count": len(timelines),
        "timelines": timelines,
    })


@regulatory_bp.route("/api/regulatory/timeline/<regulation_id>", methods=["GET"])
def regulatory_timeline_detail_route(regulation_id):
    t = get_timeline_by_id(regulation_id)
    if not t:
        return jsonify({"success": False, "error": "Regulatory timeline not found."}), 404
    return jsonify({"success": True, "timeline": t})


@regulatory_bp.route("/api/regulatory/status", methods=["GET"])
def regulatory_status_route():
    return jsonify({
        "success": True,
        "vector_index_size": regulatory_vector_store.size,
        "vector_backend": regulatory_vector_store.backend,
        "bm25_index_size": regulatory_bm25_index.size,
        "total_sources_registered": len(get_all_regulatory_sources()),
        "timelines_tracked": len(get_all_timelines()),
    })


@regulatory_bp.route("/api/unified/query", methods=["POST"])
def unified_query_route():
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    country = data.get("country") or None
    domain = data.get("domain") or None
    language = data.get("language") or None
    mode = (data.get("mode") or "quick").lower()

    if not query:
        return jsonify({"success": False, "error": "Query text is required."}), 400

    try:
        result = execute_unified_query(
            query=query,
            country=country,
            domain=domain,
            language=language,
            mode=mode,
        )
        return jsonify(result)
    except Exception as e:
        logger.exception("Unified query routing failed")
        return jsonify({"success": False, "error": "Unified query processing failed."}), 500
