# IP-SAKTI SAHAYAK

**AI-Powered Intellectual Property & Traditional Knowledge Assistant**
SIH 2026 — Problem Statement PS26045

## Problem Statement

Inventors, researchers, and practitioners working with Ayurveda, Traditional Knowledge, and
Indian/international IP face a fragmented regulatory landscape spread across dozens of official
bodies (IP India, AYUSH, NBA, WIPO, WTO, etc.), with no single, trustworthy, citation-backed
place to ask questions and get grounded answers.

## Solution

IP-SAKTI SAHAYAK is a Retrieval-Augmented Generation (RAG) assistant that answers IP,
Traditional Knowledge, and Ayurveda-related questions **only from verified evidence** pulled from
a prioritized registry of official sources, with mandatory citations, a transparent confidence
score, and safe abstention when evidence is insufficient — rather than a general-purpose chatbot
that might hallucinate legal facts.

## Architecture

```
USER -> Flask App -> Domain Classifier + Jurisdiction Detector -> Source Selector
     -> Local Knowledge Cache (SQLite + FAISS/BM25) + Live Official Source Fetch
     -> Hybrid Retrieval (semantic + keyword) -> Reranker -> Evidence Verification
     -> Groq LLM (grounded generation) -> Citation Verification -> Confidence Scoring
     -> Safe Abstention Gate -> Final Answer + Sources -> Flask JSON API -> HTML/CSS/JS UI
```

See `config.py`, `rag/rag_pipeline.py`, and the module docstrings throughout the codebase for
the detailed data flow of each stage.

## Features

- **Hybrid RAG**: FAISS (BAAI/bge-m3 embeddings) + BM25 keyword search, weighted and
  auto-tuned toward exact statutory citations (e.g. "Section 3(d)").
- **Authoritative source registry**: IP India, India Code, AYUSH, NBA, TKDL, WIPO, WIPO Lex,
  WTO, WHO — prioritized by authority level, configurable and extensible.
- **Reranking**: cross-encoder reranking of top-20 candidates down to the top-5 evidence set.
- **Citation verification**: every `[Source N]` marker is checked against retrieved evidence
  before being shown to the user; unsupported citations are stripped, never trusted.
- **Confidence scoring**: 0–1 score (HIGH/MEDIUM/LOW/VERY LOW) from retrieval quality, source
  authority, citation validity, evidence agreement, and jurisdiction match.
- **Safe abstention**: the system explicitly refuses to answer confidently when evidence is
  missing, conflicting, or the question is out of domain — treated as a feature, not a failure.
- **Multilingual**: English, Hindi, Odia, with legal proper nouns (Patents Act, PCT, TRIPS, TKDL,
  ABS, Geographical Indication) preserved untranslated.
- **Prior-art search, compliance guidance, document analyzer, regulation monitor, knowledge
  graph**: secondary research tools built on the same retrieval core.
- **Graceful degradation everywhere**: every stage (reranker, FAISS, embeddings, LLM, live
  fetch) has a defined fallback so the app never crashes outright — see Section 52 of the
  original spec and `config.py::validate()`.

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Frontend | HTML5, CSS3, vanilla JavaScript |
| LLM | Groq API (OpenAI-compatible) |
| Embeddings | BAAI/bge-m3 (multilingual) |
| Vector DB | FAISS |
| Keyword search | BM25 (rank_bm25) |
| Reranker | Configurable cross-encoder (sentence-transformers) |
| Database | SQLite + SQLAlchemy |
| PDF handling | PyMuPDF / pypdf |
| Web extraction | BeautifulSoup, requests |
| Reports | ReportLab (PDF), Jinja-free HTML templates |

## Folder Structure

```
IP_SAKTI_Sahayak/
├── app.py, config.py, ingestion.py, evaluation.py
├── ai/            # LLM client, prompts, classifiers, verifiers, confidence, abstention
├── rag/            # document loading, chunking, embeddings, vector store, hybrid search, reranker, web sources, pipeline
├── database/       # SQLAlchemy models, engine/session, cache helpers
├── services/       # prior-art search, regulation monitor, document analyzer, knowledge graph, compliance engine, report generator
├── routes/         # Flask blueprints (chat, search, sources, documents, admin)
├── templates/      # Jinja2 HTML pages
├── static/         # CSS + vanilla JS
├── data/           # raw/processed/index/cache/reports (gitignored except structure)
└── tests/          # pytest suite
```

## Installation

```bash
cd IP_SAKTI_Sahayak
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then fill in GROQ_API_KEY
```

## Environment Variables

See `.env.example` for the full list. Only `GROQ_API_KEY` is required; everything else has a
sensible default (models, thresholds, paths).

## Running Locally

```bash
python app.py
```

Visit `http://localhost:5000`. On first run the app automatically seeds the source registry and
ingests a small set of bootstrap legal passages into FAISS + BM25 (see `ingestion.py`) so there's
real content to query immediately — no manual PDF upload required to see it work.

## Building / Rebuilding the Knowledge Index

```bash
python ingestion.py          # re-run anytime to add more seed passages
```

## API Documentation

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/chat` | Main RAG query |
| POST | `/api/search` | Raw evidence search |
| POST | `/api/prior-art` | Prior-art search over an invention description |
| POST | `/api/compliance` | Preliminary compliance guidance |
| POST | `/api/analyze-document` | Uploaded document analysis |
| GET | `/api/sources`, `/api/sources/<id>` | Source registry |
| GET | `/api/regulations` | Regulation monitor feed |
| GET | `/api/knowledge-graph` | Graph data |
| POST | `/api/reports` | Generate PDF/HTML report |
| GET | `/api/health` | System health check |
| GET | `/api/admin/status` | Prototype-only admin status (no production auth) |

All responses follow `{success, ...}`; errors are `{success: false, error}` — no stack traces are
ever returned to the client.

## Testing

```bash
pytest tests/ -v
python evaluation.py     # runs the Section-49 example questions + the must-abstain safety check
```

## Security

Environment-variable secrets only, upload type/size validation, filename sanitization, HTML
escaping in templates, CORS enabled for the API, request size limits, and error handlers that
never leak internals. The `/admin` blueprint is explicitly prototype-only — **no production
authentication is implemented**; put a real auth layer in front of it before any real deployment.

## Deployment Notes

- **Local (Windows/Linux)**: `python app.py` as above.
- **Render/Railway-style**: set environment variables in the platform dashboard, use
  `gunicorn app:app` as the start command, and mount a persistent volume for `data/` and the
  SQLite file if you need the index to survive restarts.
- **Google Colab**: install `requirements.txt`, set `GROQ_API_KEY` via `os.environ`, and run
  `app.run()` with `use_reloader=False`; expose via `ngrok` or Colab's built-in tunneling.

## Limitations

- The seed knowledge base is a small illustrative set of passages, not a complete corpus of
  Indian/international IP law — production use requires a real ingestion pipeline against full
  statutory texts.
- `web_sources.py` fetches each configured source's base/landing page as a coarse relevance
  signal rather than using each authority's dedicated search API (tracked as future scope).
- BGE-M3 and the cross-encoder reranker require model downloads on first run; without network
  access to Hugging Face, the app automatically falls back to a lightweight keyword-weighted
  mode rather than failing.
- Prototype-only authentication on `/admin`.

## Future Scope

- Per-authority search API integration instead of landing-page fetches.
- Redis-backed distributed cache.
- Neo4j-backed knowledge graph (the current module's node/edge shape is already compatible).
- Scheduled regulation-monitor jobs with notification hooks.
- Real user authentication and per-user saved queries/history.

## SIH Relevance

Directly addresses PS26045 by combining authoritative-source-first retrieval, mandatory
citations, and safe abstention — prioritizing correctness and traceability over generic
chatbot-style fluency, which is the core requirement of a regulatory/legal research assistant.

---
*This tool is informational and does not constitute legal advice. Verify important matters with
the relevant authority or a qualified legal professional.*
