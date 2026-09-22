"""
IP-SAKTI SAHAYAK
Search & Intelligence Routes
=============================
POST /api/analyze-innovation — flagship multi-stage innovation assessment.
POST /api/comparative-ip — India vs International comparative law matrix.
POST /api/prior-art — prior-art & TKDL concept search.
POST /api/compliance — preliminary regulatory guidance.
POST /api/search — raw evidence search.
"""

import logging
from flask import Blueprint, request, jsonify

from rag.hybrid_search import hybrid_search
from rag.reranker import reranker
from services.prior_art_search import search_prior_art
from services.compliance_engine import check_compliance
from services.innovation_analyzer import analyze_innovation
from services.comparative_ip import generate_comparative_matrix

logger = logging.getLogger(__name__)
search_bp = Blueprint("search", __name__)


@search_bp.route("/api/analyze-innovation", methods=["POST"])
def analyze_innovation_route():
    data = request.get_json(silent=True) or {}
    name = (data.get("innovation_name") or "").strip()
    ingredients = (data.get("ingredients") or "").strip()
    process = (data.get("preparation_process") or "").strip()
    intended_use = (data.get("intended_use") or "").strip()
    jurisdiction = data.get("target_jurisdiction") or "India"
    description = (data.get("optional_description") or "").strip()

    if not name and not ingredients:
        return jsonify({"success": False, "error": "Innovation name or ingredients are required."}), 400

    try:
        result = analyze_innovation(
            innovation_name=name or "Ayurvedic Herbal Innovation",
            ingredients=ingredients,
            preparation_process=process,
            intended_use=intended_use,
            target_jurisdiction=jurisdiction,
            optional_description=description,
        )
        return jsonify(result)
    except Exception as e:
        logger.exception("Innovation analysis failed")
        return jsonify({"success": False, "error": f"Innovation analysis failed: {str(e)}"}), 500


@search_bp.route("/api/comparative-ip", methods=["POST"])
def comparative_ip_route():
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    focus = data.get("domain_focus") or "All"

    if not query:
        return jsonify({"success": False, "error": "Query or innovation description is required."}), 400

    try:
        result = generate_comparative_matrix(query, domain_focus=focus)
        return jsonify(result)
    except Exception as e:
        logger.exception("Comparative IP analysis failed")
        return jsonify({"success": False, "error": "Comparative analysis failed."}), 500


@search_bp.route("/api/prior-art", methods=["POST"])
def prior_art():
    data = request.get_json(silent=True) or {}
    description = (data.get("description") or "").strip()
    jurisdiction = data.get("jurisdiction") or "India"
    if not description:
        return jsonify({"success": False, "error": "Invention description is required."}), 400

    try:
        result = search_prior_art(description, jurisdiction=jurisdiction)
        return jsonify({"success": True, **result})
    except Exception as e:
        logger.exception("Prior-art search failed")
        return jsonify({"success": False, "error": "Prior-art search failed."}), 500


@search_bp.route("/api/compliance", methods=["POST"])
def compliance():
    data = request.get_json(silent=True) or {}
    description = (data.get("description") or "").strip()
    if not description:
        return jsonify({"success": False, "error": "Description is required."}), 400
    try:
        result = check_compliance(description)
        return jsonify({"success": True, **result})
    except Exception as e:
        logger.exception("Compliance check failed")
        return jsonify({"success": False, "error": "Compliance check failed."}), 500


@search_bp.route("/api/search", methods=["POST"])
def search():
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    jurisdiction = data.get("jurisdiction") or None
    domain = data.get("domain") or None

    if not query:
        return jsonify({"success": False, "error": "Query text is required."}), 400

    try:
        candidates = hybrid_search(query, jurisdiction=jurisdiction, domain=domain)
        results = reranker.rerank(query, candidates, top_n=8)
        return jsonify({"success": True, "query": query, "results": results})
    except Exception as e:
        logger.exception("Search failed")
        return jsonify({"success": False, "error": "Search failed."}), 500
