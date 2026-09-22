"""Comprehensive smoke and regression tests for Flask API and Page endpoints."""
import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_health_endpoint(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "status" in data


def test_page_routes_render_200(client):
    pages = [
        "/",
        "/dashboard",
        "/chat",
        "/analyze-innovation",
        "/comparative",
        "/prior-art",
        "/compliance",
        "/regulations",
        "/knowledge-graph",
        "/documents",
        "/benchmark",
        "/sources",
        "/admin",
    ]
    for p in pages:
        resp = client.get(p)
        assert resp.status_code == 200, f"Page {p} returned status {resp.status_code}"


def test_chat_endpoint_rejects_empty_query(client):
    resp = client.post("/api/chat", json={"query": ""})
    assert resp.status_code == 400


def test_sources_endpoint(client):
    resp = client.get("/api/sources")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("success") is True


def test_knowledge_graph_endpoint(client):
    resp = client.get("/api/knowledge-graph")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("success") is True
    assert "nodes" in data.get("graph", {})


def test_regulations_endpoint(client):
    resp = client.get("/api/regulations")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("success") is True
    assert len(data.get("updates", [])) >= 3


def test_regulation_diff_endpoint(client):
    resp = client.get("/api/regulations/diff/bda-2023-amendment")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("success") is True
    assert "Biological Diversity" in data.get("diff", {}).get("title", "")


def test_analyze_innovation_api(client):
    payload = {
        "innovation_name": "Herbo-Joint Gel",
        "ingredients": "Curcuma longa and Withania somnifera with Piperine",
        "preparation_process": "Micro-emulsion",
        "intended_use": "Osteoarthritis joint pain relief",
        "target_jurisdiction": "India",
    }
    resp = client.post("/api/analyze-innovation", json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("success") is True
    assert "risk_radar" in data
    assert len(data.get("extracted_botanicals", [])) >= 2


def test_comparative_ip_api(client):
    payload = {
        "query": "Herbal formulation patentability",
        "domain_focus": "Patentability",
    }
    resp = client.post("/api/comparative-ip", json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("success") is True
    assert "topics" in data


def test_prior_art_api(client):
    payload = {
        "description": "Herbal formulation using Ashwagandha and Turmeric for joint pain relief",
        "jurisdiction": "India",
    }
    resp = client.post("/api/prior-art", json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("success") is True
    assert len(data.get("results", [])) > 0


def test_compliance_api(client):
    resp = client.post("/api/compliance", json={"description": "I want to commercialize an Ayurvedic formulation."})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("success") is True


def test_report_generation_api(client):
    payload = {
        "format": "html",
        "answer_payload": {
            "query": "Test query",
            "answer": "Test answer",
            "sources": [{"authority": "IP India", "section": "Section 3(d)", "source_url": "https://ipindia.gov.in"}],
        },
    }
    resp = client.post("/api/reports", json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("success") is True
    assert "download_url" in data
