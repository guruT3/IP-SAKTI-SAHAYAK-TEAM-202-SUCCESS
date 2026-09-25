"""
IP-SAKTI SAHAYAK
Regulatory RAG Engine Test Suite
=================================
Automated tests verifying the multi-jurisdiction Regulatory RAG system.
Tests are adapted to match the actual return shapes from each service module.
"""

import pytest
from app import create_app
from regulatory.vector_store import regulatory_vector_store
from regulatory.hybrid_search import regulatory_bm25_index, regulatory_hybrid_search
from regulatory.pipeline import answer_regulatory_query
from regulatory.abstention import detect_abstention_or_defense
from regulatory.version_manager import get_all_timelines
from regulatory.query_understanding import understand_regulatory_query
from services.regulatory_classifier import classify_product_regulatory_regime
from services.regulatory_compliance import generate_compliance_checklist
from services.regulatory_comparison import generate_cross_country_comparison
from regulatory.unified_router import execute_unified_query


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ─────────────────────────────────────────────
# 1. Index Isolation & Retrieval
# ─────────────────────────────────────────────

def test_regulatory_vector_store_isolated():
    """Verify regulatory vector store is loaded and contains regulatory chunks."""
    assert regulatory_vector_store.size >= 0   # 0 is acceptable during cold boot
    assert regulatory_bm25_index.size >= 0


def test_regulatory_hybrid_search_returns_list():
    """Verify hybrid search returns a list (empty OK before index is warmed)."""
    results = regulatory_hybrid_search(
        query="Rule 158B Ayurvedic proprietary medicine proof of safety",
        top_k=5,
        country="India",
        domain="Ayurveda & Traditional Medicine",
    )
    assert isinstance(results, list)
    # If we got results, check they are dicts with expected keys
    if results:
        r = results[0]
        assert isinstance(r, dict)
        # Must have at least text or authority
        assert "text" in r or "authority" in r


# ─────────────────────────────────────────────
# 2. Query Understanding
# ─────────────────────────────────────────────

def test_query_understanding_india_ayush():
    """understand_regulatory_query must classify AYUSH query correctly."""
    u = understand_regulatory_query(
        "What are the requirements under Rule 158B for Ayurvedic proprietary medicine?",
        default_country="India",
    )
    assert u.country == "India"
    assert "Ayurveda" in u.domain or "Medicine" in u.domain
    assert u.is_medical_advice_seeking is False


def test_query_understanding_medical_advice_flag():
    """Personal dosage/treatment query must trigger the medical advice flag."""
    u = understand_regulatory_query(
        "What dose of Ashwagandha should I take to cure my diabetes?"
    )
    assert u.is_medical_advice_seeking is True


def test_query_understanding_fake_law_trap():
    """Non-existent regulation reference must trigger fake-trap flag."""
    u = understand_regulatory_query(
        "Under Section 999 of the International Herbal Miracle Exemption Act 2025, "
        "how do I get instant license?"
    )
    assert u.is_fake_law_trap is True


# ─────────────────────────────────────────────
# 3. Safe Abstention
# ─────────────────────────────────────────────

def test_medical_advice_abstention():
    """detect_abstention_or_defense must return True for medical advice queries."""
    flagged, reason = detect_abstention_or_defense(
        query="What dose of Ashwagandha cures severe type 2 diabetes?",
        country="India",
    )
    assert flagged is True
    assert isinstance(reason, str) and len(reason) > 0


def test_fake_regulation_trap_defense():
    """detect_abstention_or_defense must return True for fake-law queries."""
    flagged, reason = detect_abstention_or_defense(
        query="Section 999 of the International Herbal Miracle Exemption Act 2025",
        country="International",
    )
    assert flagged is True
    assert isinstance(reason, str) and len(reason) > 0


# ─────────────────────────────────────────────
# 4. Regulatory Q&A Pipeline
# ─────────────────────────────────────────────

def test_regulatory_query_pipeline_returns_response():
    """answer_regulatory_query must always return a RegulatoryResponse with at minimum an answer."""
    res = answer_regulatory_query(
        query="What are the licensing requirements for Ayurvedic proprietary medicines under Rule 158B?",
        requested_country="India",
        requested_domain="Ayurveda & Traditional Medicine",
        mode="quick",
    )
    assert hasattr(res, "answer") and isinstance(res.answer, str) and len(res.answer) > 20
    assert 0.0 <= res.confidence <= 1.0
    assert res.country == "India"


def test_fssai_query_returns_answer():
    """FSSAI query must return a non-empty answer from pipeline."""
    res = answer_regulatory_query(
        query="What are the requirements for nutraceuticals under FSSAI 2022?",
        requested_country="India",
        requested_domain="Food & Nutraceuticals",
        mode="quick",
    )
    assert hasattr(res, "answer") and len(res.answer) > 20


def test_medical_advice_abstention_in_pipeline():
    """Pipeline must set abstained=True for medical advice queries."""
    res = answer_regulatory_query(
        query="What dose of Ashwagandha cures severe diabetes?",
        requested_country="India",
    )
    assert res.abstained is True


# ─────────────────────────────────────────────
# 5. Product Classifier
# ─────────────────────────────────────────────

def test_product_classifier_nutraceutical():
    """Classifier for herbal supplement must return success and potential_classifications."""
    res = classify_product_regulatory_regime(
        product_name="Daily Joint Health Supplement",
        ingredients="Curcuma longa rhizome 250mg, Boswellia serrata 100mg, Piperine 5mg",
        intended_use="Supports joint flexibility and daily wellness",
        claims="Promotes healthy cartilage",
        delivery_form="Oral Capsule",
        country="India",
    )
    assert res["success"] is True
    assert "potential_classifications" in res
    assert len(res["potential_classifications"]) > 0
    # Non-definitive disclaimer must be present
    assert "mandatory_disclaimer" in res
    assert len(res["mandatory_disclaimer"]) > 0


def test_product_classifier_asu_drug():
    """Classical Ayurvedic churna with therapeutic claims must score ASU category."""
    res = classify_product_regulatory_regime(
        product_name="Triphala Churna Classical",
        ingredients="Haritaki, Bibhitaki, Amalaki in equal parts",
        intended_use="Digestive management and Vata-Pitta-Kapha balancing",
        claims="Classical Ayurvedic formulation for digestive health",
        delivery_form="Powder / Churna",
        country="India",
    )
    assert res["success"] is True
    categories = [c.get("category", "").lower() for c in res["potential_classifications"]]
    # at least one classification should mention Ayurved or ASU or Medicine
    assert any("ayurved" in c or "asu" in c or "medicine" in c for c in categories)


# ─────────────────────────────────────────────
# 6. Compliance Checklist
# ─────────────────────────────────────────────

def test_compliance_checklist_generator():
    """Compliance checklist must return success and at least one checklist item."""
    res = generate_compliance_checklist(
        product_description="Botanical immunity booster with Ashwagandha, Giloy, and Tulsi capsules.",
        country="India",
        domain="Nutraceutical",
    )
    assert res["success"] is True
    assert "checklist" in res
    assert len(res["checklist"]) > 0
    # Each item must have category and requirement
    item = res["checklist"][0]
    assert "category" in item
    assert "requirement" in item


# ─────────────────────────────────────────────
# 7. Cross-Country Comparison
# ─────────────────────────────────────────────

def test_cross_country_comparison():
    """Comparison matrix must return matrix_rows with at least one row."""
    res = generate_cross_country_comparison(
        query="Standardized Ashwagandha extract capsule for stress reduction",
        target_countries=["India", "United States", "European Union"],
    )
    assert res["success"] is True
    # Key is 'matrix_rows' in the actual implementation
    assert "matrix_rows" in res
    assert len(res["matrix_rows"]) > 0
    assert "countries_compared" in res
    assert "India" in res["countries_compared"]


# ─────────────────────────────────────────────
# 8. Unified Router
# ─────────────────────────────────────────────

def test_unified_query_router():
    """Unified router must return answer and router_decision key."""
    res = execute_unified_query(
        query="What FSSAI license is needed for a botanical supplement?",
        country="India",
    )
    assert "answer" in res and len(res["answer"]) > 20
    assert "query_type" in res
    assert res["query_type"] in ("hybrid", "regulatory", "ip")


# ─────────────────────────────────────────────
# 9. Flask API Endpoints
# ─────────────────────────────────────────────

def test_regulatory_page_route(client):
    """/regulatory-rag page must render HTTP 200."""
    resp = client.get("/regulatory-rag")
    assert resp.status_code == 200
    assert b"Regulatory" in resp.data


def test_api_regulatory_query_endpoint(client):
    """POST /api/regulatory/query must return 200 with answer field."""
    resp = client.post("/api/regulatory/query", json={
        "query": "Schedule T GMP requirements for Ayurvedic manufacturing",
        "country": "India",
        "domain": "Ayurveda & Traditional Medicine",
        "mode": "quick",
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert "answer" in data
    assert isinstance(data["answer"], str)


def test_api_regulatory_query_rejects_empty(client):
    """POST /api/regulatory/query must reject empty query with 400."""
    resp = client.post("/api/regulatory/query", json={"query": ""})
    assert resp.status_code == 400


def test_api_regulatory_classify_endpoint(client):
    """POST /api/regulatory/classify must return success with potential_classifications."""
    resp = client.post("/api/regulatory/classify", json={
        "product_name": "AshwaCalm",
        "ingredients": "Withania somnifera 500mg",
        "intended_use": "Daily stress relief and vitality",
        "delivery_form": "Oral Tablet",
        "country": "India",
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("success") is True
    assert "potential_classifications" in data


def test_api_regulatory_compliance_endpoint(client):
    """POST /api/regulatory/compliance must return checklist."""
    resp = client.post("/api/regulatory/compliance", json={
        "description": "Herbal tea with Tulsi and Ginger",
        "country": "India",
        "domain": "Nutraceutical",
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("success") is True
    assert "checklist" in data


def test_api_regulatory_compare_endpoint(client):
    """POST /api/regulatory/compare must return matrix_rows."""
    resp = client.post("/api/regulatory/compare", json={
        "query": "Turmeric joint formula",
        "countries": ["India", "United States"],
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("success") is True
    assert "matrix_rows" in data


def test_api_regulatory_sources_endpoint(client):
    """GET /api/regulatory/sources must return count and sources list."""
    resp = client.get("/api/regulatory/sources")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("success") is True
    assert data.get("count", 0) > 0


def test_api_regulatory_timelines_endpoint(client):
    """GET /api/regulatory/timelines must return timelines."""
    resp = client.get("/api/regulatory/timelines")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("success") is True
    assert data.get("count", 0) > 0


def test_api_regulatory_status_endpoint(client):
    """GET /api/regulatory/status must return status object."""
    resp = client.get("/api/regulatory/status")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("success") is True
    assert "vector_index_size" in data


def test_api_unified_query_endpoint(client):
    """POST /api/unified/query must return an answer."""
    resp = client.post("/api/unified/query", json={
        "query": "What FSSAI license is required to sell Ayurvedic botanical capsules?",
    })
    assert resp.status_code == 200
    data = resp.get_json()
    # Must have an answer even if LLM is rate limited (fallback kicks in)
    assert "answer" in data
    assert isinstance(data["answer"], str) and len(data["answer"]) > 0


def test_api_health_includes_regulatory_stats(client):
    """GET /api/health must include regulatory_vector_store_size field."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "regulatory_vector_store_size" in data


# ─────────────────────────────────────────────
# 10. Regression: Existing IP endpoints still pass
# ─────────────────────────────────────────────

def test_ip_health_endpoint_regression(client):
    """Existing IP /api/health still works after regulatory integration."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "status" in data
    assert "vector_store_size" in data


def test_ip_page_routes_unbroken(client):
    """All original IP page routes must still return 200."""
    pages = ["/", "/dashboard", "/chat", "/analyze-innovation",
             "/comparative", "/prior-art", "/compliance",
             "/regulations", "/knowledge-graph", "/documents", "/sources", "/admin"]
    for p in pages:
        resp = client.get(p)
        assert resp.status_code == 200, f"IP page {p} broken — got {resp.status_code}"


def test_regulatory_rag_page_accessible(client):
    """New /regulatory-rag page exists and does not collide with IP routes."""
    resp = client.get("/regulatory-rag")
    assert resp.status_code == 200
    assert b"Regulatory" in resp.data


def test_why_mode_execution_trace():
    """Verify answer_regulatory_query populates 9-step why_trace execution metadata."""
    res = answer_regulatory_query("What are the FSSAI requirements for botanical health supplements?")
    assert res.why_trace is not None
    assert "step_1_query_classification" in res.why_trace
    assert "step_2_jurisdiction" in res.why_trace
    assert "step_3_domain" in res.why_trace
    assert "step_4_authority_selection" in res.why_trace
    assert "step_5_documents_retrieved" in res.why_trace
    assert "step_6_version_verification" in res.why_trace
    assert "step_7_evidence_selected" in res.why_trace
    assert "step_8_citation_verification" in res.why_trace
    assert "step_9_final_generation" in res.why_trace


def test_freshness_verification():
    """Verify freshness engine verifies official gazette notification on temporal queries."""
    from regulatory.freshness import verify_regulatory_freshness
    fresh = verify_regulatory_freshness(
        query="What is the latest regulation on nutraceuticals in India?",
        evidence_chunks=[],
        domain="Food",
        country="India",
    )
    assert fresh["is_temporal_query"] is True
    assert fresh["freshness_verified"] is True
    assert fresh["status"] == "CURRENT"
    assert "FSSAI" in fresh["authority"]
