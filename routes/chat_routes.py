"""
IP-SAKTI SAHAYAK
Chat Routes
===========
POST /api/chat — main RAG query endpoint (supports 'quick' and 'deep' modes).
GET /api/chat/history/<conversation_id> — retrieve conversation history.
"""

import logging
from flask import Blueprint, request, jsonify

from ai.multilingual import normalize_language_code
from database.db import get_session
from database.models import Conversation, Message, Citation
from rag.rag_pipeline import answer_query

logger = logging.getLogger(__name__)
chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    conversation_id = data.get("conversation_id")
    jurisdiction = data.get("jurisdiction") or None
    if jurisdiction == "Auto Detect":
        jurisdiction = None
    language = normalize_language_code(data.get("language"))
    mode = (data.get("mode") or "quick").lower()

    if not query:
        return jsonify({"success": False, "error": "Query text is required."}), 400
    if len(query) > 5000:
        return jsonify({"success": False, "error": "Query is too long (max 5000 characters)."}), 400

    try:
        result = answer_query(query, requested_jurisdiction=jurisdiction, requested_language=language, mode=mode)
    except Exception as e:
        logger.exception("Unhandled error in answer_query")
        return jsonify({"success": False, "error": "Something went wrong while processing your question."}), 500

    try:
        with get_session() as db:
            convo = None
            if conversation_id:
                convo = db.get(Conversation, conversation_id)
            if convo is None:
                convo = Conversation(title=query[:60])
                db.add(convo)
                db.flush()

            db.add(Message(conversation_id=convo.id, role="user", content=query))
            assistant_msg = Message(
                conversation_id=convo.id, role="assistant", content=result.answer,
                domain=result.domain, jurisdiction=result.jurisdiction, language=result.language,
                confidence=result.confidence, confidence_level=result.confidence_level,
                abstained=result.abstained,
            )
            db.add(assistant_msg)
            db.flush()

            for c in result.citations:
                db.add(Citation(message_id=assistant_msg.id, source_name=c.get("source_name"),
                                 section=c.get("section"), url=c.get("url"), verified=c.get("valid", False)))
            conversation_id = convo.id
    except Exception:
        logger.exception("Failed to persist conversation/message (continuing — response still returned to user)")

    return jsonify({
        "success": result.success,
        "conversation_id": conversation_id,
        "answer": result.answer,
        "confidence": result.confidence,
        "confidence_level": result.confidence_level,
        "domain": result.domain,
        "jurisdiction": result.jurisdiction,
        "language": result.language,
        "mode": result.mode,
        "sources": result.sources,
        "citations": result.citations,
        "claim_trace_map": result.claim_trace_map,
        "abstained": result.abstained,
        "abstain_reason": result.abstain_reason,
        "disclaimer": result.disclaimer,
        "latency_ms": result.latency_ms,
    })


@chat_bp.route("/api/chat/history/<conversation_id>", methods=["GET"])
def chat_history(conversation_id):
    with get_session() as db:
        convo = db.get(Conversation, conversation_id)
        if not convo:
            return jsonify({"success": False, "error": "Conversation not found."}), 404
        messages = [
            {"role": m.role, "content": m.content, "confidence": m.confidence,
             "confidence_level": m.confidence_level, "created_at": m.created_at.isoformat()}
            for m in convo.messages
        ]
    return jsonify({"success": True, "conversation_id": conversation_id, "messages": messages})
