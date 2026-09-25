"""
IP-SAKTI SAHAYAK
Comprehensive IP-RAG Reliability, State Isolation & Source Regression Test Suite
==================================================================================
Tests:
1. Query Isolation & Repeatability ("Works once, fails later" state contamination prevention)
2. Domain Classification & Source Routing
3. Ayurvedic Formulation Classification (Classical vs Proprietary vs Phytopharmaceutical)
4. PCIM&H, PubMed, AYUSH & Statutory Corpus Retrieval
5. Multilingual Query Processing & Protected Term Restoration
6. Safe Abstention Gate & Adversarial Red-Team Traps
7. Diagnostic Trace Output
"""

import pytest
from rag.rag_pipeline import answer_query
from ai.ayurveda_classifier import classify_ayurvedic_formulation
from ai.domain_classifier import classify_domain
from ai.jurisdiction_detector import detect_jurisdiction
from ai.multilingual import protect_terms, restore_terms, detect_language


def test_repeatability_and_state_isolation():
    """
    HIGH PRIORITY TEST: Ensures that repeating the exact same query multiple times,
    interspersed with different queries, language changes, or jurisdiction changes,
    does NOT poison state or cause 'works once, fails later' regression.
    """
    query_a = "What is Section 3(d) of the Indian Patents Act?"
    query_b = "Can an Ayurvedic formulation made from neem and turmeric be patented?"
    query_c = "What are penalties under Section 99B of Patents Act?"  # Fake law trap

    # Turn 1: Query A
    res1 = answer_query(query_a)
    assert res1.success is True
    assert len(res1.sources) > 0
    assert res1.domain in ("Patent", "General IP")

    # Turn 2: Query B (Ayurveda patent question)
    res2 = answer_query(query_b)
    assert res2.success is True
    assert res2.domain in ("Ayurveda", "Traditional Knowledge", "Patent", "General IP")

    # Turn 3: Query C (Fake law trap - should abstain)
    res3 = answer_query(query_c)
    assert res3.success is True
    assert res3.abstained is True
    assert "fake_law_trap" in (res3.abstain_reason or "") or "Section 99B" in (res3.abstain_reason or "")

    # Turn 4: Query A AGAIN (Must succeed identically and not be poisoned by Turn 2 or Turn 3)
    res4 = answer_query(query_a)
    assert res4.success is True
    assert len(res4.sources) == len(res1.sources)
    assert res4.domain == res1.domain
    assert res4.jurisdiction == res1.jurisdiction

    # Turn 5: Query A with Hindi language setting
    res5 = answer_query(query_a, requested_language="hi")
    assert res5.success is True
    assert res5.language == "hi"

    # Turn 6: Query A AGAIN in English (Must succeed with English output & clean state)
    res6 = answer_query(query_a, requested_language="en")
    assert res6.success is True
    assert res6.language == "en"
    assert res6.domain == res1.domain


def test_ayurvedic_formulation_classification():
    """Tests formulation classification layer for classical vs proprietary ASU drugs."""
    # Classical formulation
    res_classical = classify_ayurvedic_formulation("What is the pharmacopoeial standard for Triphala Churna?")
    assert res_classical["applicable"] is True
    assert res_classical["category"] == "classical_medicine"

    # Proprietary formulation
    res_prop = classify_ayurvedic_formulation("Is a novel synergistic polyherbal capsule combining curcumin and piperine patentable?")
    assert res_prop["applicable"] is True
    assert res_prop["category"] == "proprietary_medicine"

    # Uncertain formulation
    res_unc = classify_ayurvedic_formulation("How do I sell my herb product?")
    assert res_unc["applicable"] is True
    assert res_unc["category"] == "uncertain"


def test_pcimh_and_pharmacopoeia_retrieval():
    """Tests retrieval of PCIM&H pharmacopoeial standards and raw drug identity."""
    res = answer_query("What is the standard identity for Haridra in the Ayurvedic Pharmacopoeia?")
    assert res.success is True
    assert len(res.sources) > 0
    assert any("PCIM&H" in s.get("authority", "") or "Pharmacopoeia" in s.get("source_name", "") or "Curcuma" in s.get("text_snippet", "") for s in res.sources)


def test_pubmed_medical_vs_ip_distinction():
    """Tests that PubMed scientific literature is retrieved without confusing legal authority."""
    res = answer_query("What scientific evidence exists for curcumin bio-enhancement by piperine in PubMed?")
    assert res.success is True
    assert len(res.sources) > 0
    assert any("PubMed" in s.get("authority", "") or "PubMed" in s.get("source_name", "") or "bioavailability" in s.get("text_snippet", "").lower() for s in res.sources)


def test_abs_and_biodiversity_routing():
    """Tests routing toward National Biodiversity Authority for Section 6 BDA queries."""
    res = answer_query("Does an invention using Indian biological resources require ABS approval from NBA?")
    assert res.success is True
    assert res.domain in ("ABS", "Biodiversity", "Patent", "General IP")
    assert len(res.sources) > 0
    assert any("National Biodiversity Authority" in s.get("authority", "") or "NBA" in s.get("source_name", "") or "Section 6" in s.get("text_snippet", "") for s in res.sources)


def test_multilingual_protected_terms():
    """Tests term protection for legal proper nouns during translation."""
    sample = "Under the Patents Act, Section 3(d) and Rule 158B apply to TKDL formulations."
    protected, placeholders = protect_terms(sample)
    assert "__PROTECTED_" in protected
    restored = restore_terms(protected, placeholders)
    assert restored == sample


def test_diagnostic_mode_output():
    """Tests internal diagnostic trace output when debug=True."""
    res = answer_query("Has a similar Ayurvedic formulation already been patented in India?", debug=True)
    assert res.success is True
    assert res.diagnostic_trace is not None
    assert "request_id" in res.diagnostic_trace
    assert "retrieval_counts" in res.diagnostic_trace
    assert "trace_log" in res.diagnostic_trace
