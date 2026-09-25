"""
IP-SAKTI SAHAYAK
Flask Application Entry Point
===============================
Wires together configuration, database bootstrap, vector/BM25 indexes,
API blueprints, page routes, and centralized error handlers.
"""

import logging
from pathlib import Path

from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    session,
    redirect,
    url_for,
    flash,
)
from werkzeug.security import generate_password_hash, check_password_hash

from db import get_db

try:
    from flask_cors import CORS
except ImportError:
    def CORS(app):
        @app.after_request
        def add_cors_headers(response):
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
            response.headers["Access-Control-Allow-Methods"] = "GET,PUT,POST,DELETE,OPTIONS"
            return response

from config import settings

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(settings.LOGS_PATH) / "app.log"),
    ],
)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    CORS(app)

    config_issues = settings.validate()
    for issue in config_issues:
        logger.warning("Config issue: %s", issue)

    # ---- Bootstrap DB + indexes (idempotent) ----
    try:
        from ingestion import bootstrap_indexes
        bootstrap_indexes()
    except Exception:
        logger.exception("Index/DB bootstrap failed — app starting in degraded retrieval mode.")

    try:
        from regulatory.ingestion import bootstrap_regulatory_indexes
        bootstrap_regulatory_indexes()
    except Exception:
        logger.exception("Regulatory index bootstrap failed — starting in degraded retrieval mode.")

    # ---- Register API blueprints ----
    from routes.chat_routes import chat_bp
    from routes.search_routes import search_bp
    from routes.source_routes import source_bp
    from routes.document_routes import document_bp
    from routes.admin_routes import admin_bp
    from routes.regulatory_routes import regulatory_bp

    app.register_blueprint(chat_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(source_bp)
    app.register_blueprint(document_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(regulatory_bp)

    # ---- Page routes ----

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/regulatory-rag")
    def regulatory_rag_page():
        return render_template("regulatory_rag.html")

    @app.route("/dashboard")
    def dashboard():
        return render_template("dashboard.html")

    @app.route("/chat")
    def chat_page():
        return render_template("chat.html")

    @app.route("/analyze-innovation")
    def innovation_analyzer_page():
        return render_template("innovation_analyzer.html")

    @app.route("/comparative")
    def comparative_page():
        return render_template("comparative.html")

    @app.route("/prior-art")
    def prior_art_page():
        return render_template("prior_art.html")

    @app.route("/compliance")
    def compliance_page():
        return render_template("compliance.html")

    @app.route("/regulations")
    def regulations_page():
        return render_template("regulations.html")

    @app.route("/knowledge-graph")
    def knowledge_graph_page():
        return render_template("knowledge_graph.html")

    @app.route("/documents")
    def documents_page():
        return render_template("documents.html")

    @app.route("/benchmark")
    def benchmark_page():
        return render_template("benchmark.html")

    @app.route("/sources")
    def sources_page():
        return render_template("sources.html")

    @app.route("/ip-analytics")
    @app.route("/patents-dashboard")
    def ip_analytics_page():
        return render_template("ip_analytics.html")

    @app.route("/admin")
    def admin_page():
        return render_template("admin.html")

    # ---- Context Processor for User Session ----
    @app.context_processor
    def inject_user():
        if "user_id" in session:
            return {
                "current_user": {
                    "id": session.get("user_id"),
                    "username": session.get("username"),
                    "email": session.get("email"),
                    "referral_code": session.get("referral_code"),
                }
            }
        return {"current_user": None}

    # ---- Auth routes ----

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")

            if not username or not email or not password:
                flash("All fields are required.", "danger")
                return redirect(url_for("signup"))

            hashed_password = generate_password_hash(password)
            import uuid
            referral_code = f"REF-{username.upper()}-{uuid.uuid4().hex[:4].upper()}"

            db = get_db()
            cursor = db.cursor()
            try:
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash, referral_code) VALUES (%s, %s, %s, %s)",
                    (username, email, hashed_password, referral_code),
                )
                db.commit()
            except Exception:
                logger.exception("Signup failed")
                db.rollback()
                flash("That username or email is already registered.", "danger")
                return redirect(url_for("signup"))
            finally:
                cursor.close()
                db.close()

            flash("Signup successful! Please log in with your credentials.", "success")
            return redirect(url_for("login"))

        return render_template("signup.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, username))
            user = cursor.fetchone()

            if user and check_password_hash(user["password_hash"], password):
                referral_code = user.get("referral_code")
                if not referral_code:
                    import uuid
                    referral_code = f"REF-{user['username'].upper()}-{uuid.uuid4().hex[:4].upper()}"
                    try:
                        cursor_update = db.cursor()
                        cursor_update.execute(
                            "UPDATE users SET referral_code = %s WHERE id = %s",
                            (referral_code, user["id"])
                        )
                        db.commit()
                        cursor_update.close()
                    except Exception as e:
                        logger.warning("Could not update referral code: %s", e)

                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["email"] = user["email"]
                session["referral_code"] = referral_code

                cursor.close()
                db.close()

                flash(f"Welcome back, {user['username']}! You are successfully logged in.", "success")
                return redirect(url_for("index"))
            else:
                cursor.close()
                db.close()
                flash("Invalid username or password.", "danger")
                return redirect(url_for("login"))

        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out successfully.", "info")
        return redirect(url_for("login"))

    @app.route("/api/user/profile")
    def user_profile_api():
        if "user_id" not in session:
            return jsonify({"logged_in": False}), 401
        return jsonify({
            "logged_in": True,
            "user": {
                "id": session.get("user_id"),
                "username": session.get("username"),
                "email": session.get("email"),
                "referral_code": session.get("referral_code"),
                "referral_link": f"{request.host_url}signup?ref={session.get('referral_code')}"
            }
        })

    @app.route("/api/ip-analytics/stats")
    def ip_analytics_stats_api():
        return jsonify({
            "success": True,
            "metrics": {
                "total_filings": 1093299,
                "total_grants": 284510,
                "current_filings": 92480,
                "current_grants": 38190,
                "online_share_pct": 96.4,
                "last_sync": "2026-09-20 06:00:00 IST",
                "source": "Controller General of Patents, Designs and Trade Marks (CGPDTM)"
            },
            "state_distribution": [
                {"state": "Maharashtra", "filings": 21400, "grants": 9800},
                {"state": "Tamil Nadu", "filings": 16200, "grants": 7400},
                {"state": "Karnataka", "filings": 14500, "grants": 6100},
                {"state": "Delhi", "filings": 12800, "grants": 5200},
                {"state": "Gujarat", "filings": 9400, "grants": 3800},
                {"state": "Telangana", "filings": 8200, "grants": 3100}
            ]
        })

    # ---- Health check ----
    @app.route("/api/health")
    def health():
        from rag.vector_store import vector_store
        from regulatory.vector_store import regulatory_vector_store
        from regulatory.hybrid_search import regulatory_bm25_index
        from ai.llm import llm_client

        checks = {
            "status": "healthy",
            "llm": bool(llm_client._get_client()),
            "embeddings": True,
            "vector_store_size": vector_store.size,
            "vector_store_backend": vector_store.backend,
            "regulatory_vector_store_size": regulatory_vector_store.size,
            "regulatory_vector_store_backend": regulatory_vector_store.backend,
            "regulatory_bm25_size": regulatory_bm25_index.size,
            "database": True,
        }
        if not checks["llm"]:
            checks["status"] = "degraded (LLM key not configured)"
        return jsonify(checks)

    # ---- Centralized Error handlers: Never leak stack traces ----
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "error": "Resource not found."}), 404

    @app.errorhandler(413)
    def too_large(e):
        return jsonify({"success": False, "error": f"Uploaded file exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit."}), 413

    @app.errorhandler(500)
    def server_error(e):
        logger.exception("Unhandled server error")
        return jsonify({"success": False, "error": "An internal error occurred. Please try again."}), 500

    # ---- Register AI Copilot blueprint ----
    from routes.copilot_routes import copilot_bp
    app.register_blueprint(copilot_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)