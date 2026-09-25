"""
IP-SAKTI SAHAYAK
AI Copilot API Routes
======================
REST API endpoints for the AI Website Copilot:
- POST /api/copilot/chat — Main Copilot query & context processing
- POST /api/copilot/action — Perform supported UI workflow actions
- GET  /api/copilot/context — Get current page context & suggested prompts
- GET  /api/copilot/capabilities — Return available feature capability matrix
- POST /api/copilot/voice — Speech-to-text / Text-to-speech helper
"""

import logging
from flask import Blueprint, request, jsonify

from services.copilot_service import (
    process_copilot_request,
    execute_tool,
    WEBSITE_PAGES_REGISTRY,
    CAPABILITIES_REGISTRY
)

logger = logging.getLogger(__name__)
copilot_bp = Blueprint("copilot", __name__)


@copilot_bp.route("/api/copilot/chat", methods=["POST"])
def copilot_chat_route():
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    page_context = data.get("page_context") or {}
    history = data.get("history") or []
    language = data.get("language") or None

    if not query:
        return jsonify({"success": False, "error": "Query text is required for Copilot."}), 400

    if len(query) > 5000:
        return jsonify({"success": False, "error": "Query is too long (max 5000 characters)."}), 400

    try:
        res = process_copilot_request(
            query=query,
            page_context=page_context,
            conversation_history=history,
            requested_language=language
        )
        return jsonify(res)

    except Exception as e:
        logger.exception("Error processing Copilot request")
        return jsonify({
            "success": False,
            "error": "The Copilot assistant encountered an internal issue. Please try again.",
            "message": "The Copilot assistant encountered an internal issue. You can continue using standard page tools."
        }), 500


@copilot_bp.route("/api/copilot/action", methods=["POST"])
def copilot_action_route():
    data = request.get_json(silent=True) or {}
    action_name = data.get("action_name") or ""
    params = data.get("params") or {}
    page_context = data.get("page_context") or {}

    if not action_name:
        return jsonify({"success": False, "error": "action_name is required."}), 400

    try:
        tool_res = execute_tool(action_name, params, page_context)
        return jsonify(tool_res)

    except Exception as e:
        logger.exception("Error performing Copilot action")
        return jsonify({"success": False, "error": "Copilot action execution failed."}), 500


@copilot_bp.route("/api/copilot/context", methods=["GET"])
def copilot_context_route():
    route = request.args.get("route", "/")
    info = WEBSITE_PAGES_REGISTRY.get(route, WEBSITE_PAGES_REGISTRY["/"])
    return jsonify({
        "success": True,
        "route": route,
        "page_info": info,
        "all_pages": [{"route": r, "title": m["title"]} for r, m in WEBSITE_PAGES_REGISTRY.items()]
    })


@copilot_bp.route("/api/copilot/capabilities", methods=["GET"])
def copilot_capabilities_route():
    return jsonify({
        "success": True,
        "capabilities": CAPABILITIES_REGISTRY,
        "supported_languages": ["en", "hi", "or"],
        "version": "2.0.0-Copilot"
    })


@copilot_bp.route("/api/copilot/voice", methods=["POST"])
def copilot_voice_route():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    language = data.get("language") or "en"

    if not text:
        return jsonify({"success": False, "error": "Text is required for voice synthesis helper."}), 400

    return jsonify({
        "success": True,
        "text": text,
        "language": language,
        "voice_synthesis_supported": True,
        "notes": "Browser Web Speech API is utilized for zero-latency client-side speech synthesis."
    })
