"""
IP-SAKTI SAHAYAK
Config Module
=============

Central configuration for the application. All values are loaded from
environment variables (via a local .env file during development) so that
no secrets or environment-specific paths are ever hard-coded.

Import pattern used throughout the rest of the codebase:

    from config import settings

Never read os.environ directly outside this file.
"""

import os
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import List

from dotenv import load_dotenv

# =====================================================
# ENVIRONMENT LOADING
# =====================================================

BASE_DIR = Path(__file__).resolve().parent

# Load .env if present. In production, real environment variables should
# be set by the host/platform instead — load_dotenv() will simply no-op
# if there is no .env file.
load_dotenv(BASE_DIR / ".env")


def _get_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _get_float(name: str, default: float) -> float:
    val = os.getenv(name)
    if val is None:
        return default
    try:
        return float(val)
    except ValueError:
        logging.warning("Invalid float for %s=%r, using default %.3f", name, val, default)
        return default


def _get_int(name: str, default: int) -> int:
    val = os.getenv(name)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        logging.warning("Invalid int for %s=%r, using default %d", name, val, default)
        return default


def _get_list(name: str, default: List[str]) -> List[str]:
    val = os.getenv(name)
    if val is None or not val.strip():
        return default
    return [item.strip() for item in val.split(",") if item.strip()]


# =====================================================
# CLASS
# =====================================================

@dataclass
class Settings:
    # ---- Core / secrets ----
    GROQ_API_KEY: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    GROQ_MODEL: str = field(default_factory=lambda: os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b"))

    # ---- AI / RAG models ----
    EMBEDDING_MODEL: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3"))
    RERANKER_MODEL: str = field(
        default_factory=lambda: os.getenv("RERANKER_MODEL", "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")
    )
    EMBEDDING_DIMENSION: int = field(default_factory=lambda: _get_int("EMBEDDING_DIMENSION", 1024))

    # ---- Retrieval tuning ----
    HYBRID_SEMANTIC_WEIGHT: float = field(default_factory=lambda: _get_float("HYBRID_SEMANTIC_WEIGHT", 0.6))
    HYBRID_KEYWORD_WEIGHT: float = field(default_factory=lambda: _get_float("HYBRID_KEYWORD_WEIGHT", 0.4))
    RETRIEVAL_TOP_K: int = field(default_factory=lambda: _get_int("RETRIEVAL_TOP_K", 20))
    RERANK_TOP_N: int = field(default_factory=lambda: _get_int("RERANK_TOP_N", 5))

    # ---- Confidence thresholds ----
    CONFIDENCE_HIGH: float = field(default_factory=lambda: _get_float("CONFIDENCE_HIGH", 0.80))
    CONFIDENCE_MEDIUM: float = field(default_factory=lambda: _get_float("CONFIDENCE_MEDIUM", 0.60))
    CONFIDENCE_LOW: float = field(default_factory=lambda: _get_float("CONFIDENCE_LOW", 0.40))
    ABSTENTION_THRESHOLD: float = field(default_factory=lambda: _get_float("ABSTENTION_THRESHOLD", 0.40))

    # ---- Database ----
    DATABASE_URL: str = field(
        default_factory=lambda: os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'ip_sakti.db'}")
    )

    # ---- Paths ----
    VECTOR_DB_PATH: str = field(
        default_factory=lambda: os.getenv("VECTOR_DB_PATH", str(BASE_DIR / "data" / "index" / "faiss.index"))
    )
    BM25_INDEX_PATH: str = field(
        default_factory=lambda: os.getenv("BM25_INDEX_PATH", str(BASE_DIR / "data" / "index" / "bm25.pkl"))
    )
    CACHE_PATH: str = field(
        default_factory=lambda: os.getenv("CACHE_PATH", str(BASE_DIR / "data" / "cache"))
    )
    RAW_DATA_PATH: str = field(default_factory=lambda: str(BASE_DIR / "data" / "raw"))
    PROCESSED_DATA_PATH: str = field(default_factory=lambda: str(BASE_DIR / "data" / "processed"))
    REPORTS_PATH: str = field(default_factory=lambda: str(BASE_DIR / "data" / "reports"))
    LOGS_PATH: str = field(default_factory=lambda: str(BASE_DIR / "logs"))

    # ---- Regulatory Isolation Paths ----
    REGULATORY_RAW_PATH: str = field(default_factory=lambda: str(BASE_DIR / "data" / "regulatory" / "raw"))
    REGULATORY_PROCESSED_PATH: str = field(default_factory=lambda: str(BASE_DIR / "data" / "regulatory" / "processed"))
    REGULATORY_METADATA_PATH: str = field(default_factory=lambda: str(BASE_DIR / "data" / "regulatory" / "metadata"))
    REGULATORY_INDEX_PATH: str = field(
        default_factory=lambda: os.getenv("REGULATORY_INDEX_PATH", str(BASE_DIR / "data" / "regulatory" / "index" / "regulatory_faiss.index"))
    )
    REGULATORY_BM25_PATH: str = field(
        default_factory=lambda: str(BASE_DIR / "data" / "regulatory" / "index" / "regulatory_bm25.pkl")
    )
    REGULATORY_CACHE_PATH: str = field(default_factory=lambda: str(BASE_DIR / "data" / "regulatory" / "cache"))
    REGULATORY_VERSIONS_PATH: str = field(default_factory=lambda: str(BASE_DIR / "data" / "regulatory" / "versions"))

    # ---- Cache behaviour ----
    CACHE_DEFAULT_TTL_HOURS: int = field(default_factory=lambda: _get_int("CACHE_DEFAULT_TTL_HOURS", 24 * 7))

    # ---- Language support ----
    SUPPORTED_LANGUAGES: List[str] = field(default_factory=lambda: _get_list("SUPPORTED_LANGUAGES", ["en", "hi", "or"]))
    DEFAULT_LANGUAGE: str = field(default_factory=lambda: os.getenv("DEFAULT_LANGUAGE", "en"))

    # ---- Networking ----
    REQUEST_TIMEOUT_SECONDS: int = field(default_factory=lambda: _get_int("REQUEST_TIMEOUT_SECONDS", 15))
    MAX_UPLOAD_SIZE_MB: int = field(default_factory=lambda: _get_int("MAX_UPLOAD_SIZE_MB", 10))
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = field(
        default_factory=lambda: _get_list("ALLOWED_UPLOAD_EXTENSIONS", ["pdf", "txt", "docx"])
    )

    # ---- Flask ----
    SECRET_KEY: str = field(default_factory=lambda: os.getenv("SECRET_KEY", "dev-secret-change-me"))
    DEBUG: bool = field(default_factory=lambda: _get_bool("DEBUG", False))
    HOST: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    PORT: int = field(default_factory=lambda: _get_int("PORT", 5000))

    def validate(self) -> List[str]:
        """
        Validate required configuration. Returns a list of warning/error
        strings rather than raising, so the app can still boot in a
        degraded state (per the fallback-design requirement) and surface
        problems via /api/health instead of crashing on import.
        """
        issues: List[str] = []

        if not self.GROQ_API_KEY:
            issues.append("GROQ_API_KEY is not set — LLM generation will be unavailable.")

        weight_sum = round(self.HYBRID_SEMANTIC_WEIGHT + self.HYBRID_KEYWORD_WEIGHT, 3)
        if weight_sum != 1.0:
            issues.append(
                f"HYBRID_SEMANTIC_WEIGHT + HYBRID_KEYWORD_WEIGHT = {weight_sum}, expected 1.0."
            )

        if not (0.0 <= self.ABSTENTION_THRESHOLD <= 1.0):
            issues.append("ABSTENTION_THRESHOLD must be between 0.0 and 1.0.")

        if self.SECRET_KEY == "dev-secret-change-me" and not self.DEBUG:
            issues.append("Using default SECRET_KEY outside DEBUG mode — set SECRET_KEY in production.")

        return issues

    def ensure_directories(self) -> None:
        """Create local data/log directories if they don't already exist."""
        for path in [
            self.RAW_DATA_PATH,
            self.PROCESSED_DATA_PATH,
            self.REPORTS_PATH,
            self.CACHE_PATH,
            self.LOGS_PATH,
            str(Path(self.VECTOR_DB_PATH).parent),
            self.REGULATORY_RAW_PATH,
            self.REGULATORY_PROCESSED_PATH,
            self.REGULATORY_METADATA_PATH,
            self.REGULATORY_CACHE_PATH,
            self.REGULATORY_VERSIONS_PATH,
            str(Path(self.REGULATORY_INDEX_PATH).parent),
        ]:
            Path(path).mkdir(parents=True, exist_ok=True)


# =====================================================
# SINGLETON
# =====================================================

settings = Settings()
settings.ensure_directories()

# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    problems = settings.validate()
    print("Loaded settings:")
    for key, value in settings.__dict__.items():
        display = "***" if "KEY" in key or "SECRET" in key else value
        print(f"  {key} = {display}")
    if problems:
        print("\nConfiguration warnings:")
        for p in problems:
            print(f"  - {p}")
    else:
        print("\nNo configuration issues detected.")
