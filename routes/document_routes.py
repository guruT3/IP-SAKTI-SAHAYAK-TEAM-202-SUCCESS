"""
IP-SAKTI SAHAYAK
Document & Report Routes
=========================
POST /api/analyze-document — upload & analyze legal/IP document.
POST /api/reports — generate a downloadable PDF/HTML report.
GET /api/reports/download/<filename> — download report file.
"""

import logging
import os
import uuid
from pathlib import Path

from flask import Blueprint, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

from config import settings
from services.document_analyzer import analyze_document
from services.report_generator import generate_report

logger = logging.getLogger(__name__)
document_bp = Blueprint("documents", __name__)


def _allowed_file(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in settings.ALLOWED_UPLOAD_EXTENSIONS


@document_bp.route("/api/analyze-document", methods=["POST"])
def analyze_document_route():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected."}), 400
    if not _allowed_file(file.filename):
        return jsonify({"success": False, "error": f"File type not allowed. Allowed: {settings.ALLOWED_UPLOAD_EXTENSIONS}"}), 400

    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    save_path = Path(settings.RAW_DATA_PATH) / unique_name

    file.seek(0, os.SEEK_END)
    size_mb = file.tell() / (1024 * 1024)
    file.seek(0)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        return jsonify({"success": False, "error": f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit."}), 400

    try:
        file.save(save_path)
        result = analyze_document(str(save_path))

        if "error" in result:
            return jsonify({"success": False, **result}), 422

        return jsonify({"success": True, **result})
    except Exception as e:
        logger.exception("Document analysis failed")
        return jsonify({"success": False, "error": f"Document analysis failed: {str(e)}"}), 500


@document_bp.route("/api/reports", methods=["POST"])
def create_report():
    data = request.get_json(silent=True) or {}
    message_id = data.get("message_id")
    fmt = (data.get("format") or "html").lower()
    if fmt not in ("html", "pdf"):
        return jsonify({"success": False, "error": "format must be 'html' or 'pdf'."}), 400

    try:
        result = generate_report(message_id=message_id, answer_payload=data.get("answer_payload"), fmt=fmt)
        return jsonify(result)
    except Exception as e:
        logger.exception("Report generation failed")
        return jsonify({"success": False, "error": f"Report generation failed: {str(e)}"}), 500


@document_bp.route("/api/reports/download/<filename>", methods=["GET"])
def download_report(filename):
    safe_name = secure_filename(filename)
    reports_dir = Path(settings.REPORTS_PATH)
    if not (reports_dir / safe_name).exists():
        return jsonify({"success": False, "error": "Report file not found."}), 404
    return send_from_directory(str(reports_dir), safe_name, as_attachment=True)
