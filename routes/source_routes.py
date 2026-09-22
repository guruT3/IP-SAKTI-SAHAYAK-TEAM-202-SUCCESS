"""
IP-SAKTI SAHAYAK
Source & Regulation Routes
===========================
GET /api/sources — authoritative source registry.
GET /api/sources/<id> — source details.
GET /api/regulations — structured regulatory amendments feed.
GET /api/regulations/diff/<id> — side-by-side provision diff.
GET /api/knowledge-graph — base domain knowledge graph.
GET /api/knowledge-graph/dynamic — query-specific entity subgraph.
"""

import logging
from flask import Blueprint, jsonify, request

from database.db import get_session
from database.models import Source, RegulationUpdate
from services.knowledge_graph import get_knowledge_graph, get_dynamic_subgraph
from services.regulation_monitor import get_all_regulatory_updates, get_regulation_diff

logger = logging.getLogger(__name__)
source_bp = Blueprint("sources", __name__)


@source_bp.route("/api/sources", methods=["GET"])
def list_sources():
    with get_session() as db:
        sources = db.query(Source).order_by(Source.priority.asc()).all()
        data = [
            {
                "id": s.id, "source_name": s.source_name, "base_url": s.base_url,
                "jurisdiction": s.jurisdiction, "domain": s.domain, "authority": s.authority,
                "source_type": s.source_type, "priority": s.priority, "enabled": s.enabled,
                "update_frequency": s.update_frequency,
                "last_checked": s.last_checked.isoformat() if s.last_checked else None,
            }
            for s in sources
        ]
    return jsonify({"success": True, "sources": data, "count": len(data)})


@source_bp.route("/api/sources/<source_id>", methods=["GET"])
def get_source(source_id):
    with get_session() as db:
        s = db.get(Source, source_id)
        if not s:
            return jsonify({"success": False, "error": "Source not found."}), 404
        data = {
            "id": s.id, "source_name": s.source_name, "base_url": s.base_url,
            "jurisdiction": s.jurisdiction, "domain": s.domain, "authority": s.authority,
            "source_type": s.source_type, "priority": s.priority, "enabled": s.enabled,
            "document_count": len(s.documents),
        }
    return jsonify({"success": True, "source": data})


@source_bp.route("/api/regulations", methods=["GET"])
def regulations():
    amendments = get_all_regulatory_updates()
    return jsonify({"success": True, "updates": amendments, "count": len(amendments)})


@source_bp.route("/api/regulations/diff/<regulation_id>", methods=["GET"])
def regulation_diff(regulation_id):
    diff = get_regulation_diff(regulation_id)
    if not diff:
        return jsonify({"success": False, "error": "Regulation amendment record not found."}), 404
    return jsonify({"success": True, "diff": diff})


@source_bp.route("/api/knowledge-graph", methods=["GET"])
def knowledge_graph():
    return jsonify({"success": True, "graph": get_knowledge_graph()})


@source_bp.route("/api/knowledge-graph/dynamic", methods=["GET"])
def dynamic_knowledge_graph():
    query = request.args.get("q", "").strip()
    return jsonify({"success": True, "graph": get_dynamic_subgraph(query)})
