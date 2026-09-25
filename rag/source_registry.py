"""
IP-SAKTI SAHAYAK
Centralized Authoritative Source Registry & Domain Router
=========================================================
Per spec Sections 15, 16, 17, 18, 42, 43, 44, 45:
Defines the authoritative source registry across 5 core domains:
- DOMAIN A: IP / PATENTS (IP India, WIPO, India Code, EPO, USPTO)
- DOMAIN B: MEDICAL / SCIENTIFIC (ICMR, PubMed, CDSCO, WHO, FDA, EMA)
- DOMAIN C: AYURVEDA / TRADITIONAL KNOWLEDGE (AYUSH, TKDL Public, PCIM&H, CCRAS, AYUSH Portal)
- DOMAIN D: REGULATORY / LEGAL (India Code, e-Gazette, FSSAI, CDSCO, AYUSH)
- DOMAIN E: BIODIVERSITY / ABS (National Biodiversity Authority NBA, India Code, WIPO TK)

Tracks authority tiers (Tier 1 Statutory vs Tier 2 Scientific/Secondary),
freshness policies, and technical availability.
"""

from typing import Dict, Any, List, Optional

SOURCE_REGISTRY: Dict[str, Dict[str, Any]] = {
    # -------------------------------------------------------------------------
    # DOMAIN A — IP / PATENTS
    # -------------------------------------------------------------------------
    "ip_india": {
        "name": "IP India (CGPDTM)",
        "domain": "IP / Patents",
        "domain_code": "DOMAIN_A",
        "jurisdiction": "India",
        "authority_level": "Tier 1",
        "priority": 1,
        "source_type": "Statutory Authority",
        "url": "https://ipindia.gov.in",
        "supports_live": True,
        "supports_cache": True,
        "status": "active",
        "description": "Controller General of Patents, Designs and Trade Marks. Official statutory authority for Indian Patents Act 1970, Section 3(d), Section 3(p), Section 3(e), and public patent search.",
    },
    "india_code": {
        "name": "India Code",
        "domain": "Regulatory / Legal",
        "domain_code": "DOMAIN_D",
        "jurisdiction": "India",
        "authority_level": "Tier 1",
        "priority": 1,
        "source_type": "Statutory Authority",
        "url": "https://indiacode.nic.in",
        "supports_live": True,
        "supports_cache": True,
        "status": "active",
        "description": "Official repository of Central and State statutory Acts, enacted provisions, and legislative amendments.",
    },
    "wipo_patentscope": {
        "name": "WIPO PATENTSCOPE",
        "domain": "IP / Patents",
        "domain_code": "DOMAIN_A",
        "jurisdiction": "International",
        "authority_level": "Tier 1",
        "priority": 1,
        "source_type": "International Treaty Authority",
        "url": "https://patentscope.wipo.int",
        "supports_live": True,
        "supports_cache": True,
        "status": "active",
        "description": "World Intellectual Property Organization patent portal covering PCT international applications, WIPO 2024 Genetic Resources Treaty, and international patent documents.",
    },
    "epo_espacenet": {
        "name": "EPO Espacenet",
        "domain": "IP / Patents",
        "domain_code": "DOMAIN_A",
        "jurisdiction": "International",
        "authority_level": "Tier 2",
        "priority": 2,
        "source_type": "Patent Office Registry",
        "url": "https://worldwide.espacenet.com",
        "supports_live": True,
        "supports_cache": True,
        "status": "active",
        "description": "European Patent Office global patent database, prior art revocations (Neem patent case precedent), and European patent search.",
    },
    "uspto": {
        "name": "USPTO Public Search",
        "domain": "IP / Patents",
        "domain_code": "DOMAIN_A",
        "jurisdiction": "International",
        "authority_level": "Tier 2",
        "priority": 2,
        "source_type": "Patent Office Registry",
        "url": "https://ppubs.uspto.gov",
        "supports_live": True,
        "supports_cache": True,
        "status": "active",
        "description": "United States Patent and Trademark Office database, utility patent specifications, and Turmeric patent re-examination precedent history.",
    },

    # -------------------------------------------------------------------------
    # DOMAIN B — MEDICAL / SCIENTIFIC
    # -------------------------------------------------------------------------
    "icmr": {
        "name": "ICMR (Indian Council of Medical Research)",
        "domain": "Medical / Scientific",
        "domain_code": "DOMAIN_B",
        "jurisdiction": "India",
        "authority_level": "Tier 2",
        "priority": 2,
        "source_type": "Medical Research Authority",
        "url": "https://www.icmr.gov.in",
        "supports_live": True,
        "supports_cache": True,
        "status": "active",
        "description": "Apex Indian medical research body for clinical trial ethics, medical research guidelines, and indigenous health research.",
    },
    "pubmed": {
        "name": "PubMed / NLM (National Library of Medicine)",
        "domain": "Medical / Scientific",
        "domain_code": "DOMAIN_B",
        "jurisdiction": "International",
        "authority_level": "Tier 2",
        "priority": 2,
        "source_type": "Biomedical Literature Database",
        "url": "https://pubmed.ncbi.nlm.nih.gov",
        "supports_live": True,
        "supports_cache": True,
        "status": "active",
        "description": "Peer-reviewed biomedical literature covering phytochemistry, pharmacology, clinical trial results, and international medicinal plant research. Supports scientific evidence retrieval (distinct from statutory authority).",
    },
    "cdsco": {
        "name": "CDSCO (Central Drugs Standard Control Organisation)",
        "domain": "Medical / Scientific",
        "domain_code": "DOMAIN_B",
        "jurisdiction": "India",
        "authority_level": "Tier 1",
        "priority": 1,
        "source_type": "Statutory Regulatory Authority",
        "url": "https://cdsco.gov.in",
        "supports_live": True,
        "supports_cache": True,
        "status": "active",
        "description": "National drug regulatory authority for drug approval pathways, phytopharmaceuticals, clinical trials, and bio-equivalence standards.",
    },

    # -------------------------------------------------------------------------
    # DOMAIN C — AYURVEDA / TRADITIONAL KNOWLEDGE
    # -------------------------------------------------------------------------
    "ayush_ministry": {
        "name": "Ministry of AYUSH",
        "domain": "Ayurveda / Traditional Knowledge",
        "domain_code": "DOMAIN_C",
        "jurisdiction": "India",
        "authority_level": "Tier 1",
        "priority": 1,
        "source_type": "Statutory Ministry",
        "url": "https://ayush.gov.in",
        "supports_live": True,
        "supports_cache": True,
        "status": "active",
        "description": "Ministry of Ayurveda, Yoga & Naturopathy, Unani, Siddha and Homoeopathy. Governs Rule 158B licensing, Schedule T GMP, and AYUSH regulatory notifications.",
    },
    "pcimh": {
        "name": "PCIM&H (Pharmacopoeia Commission for Indian Medicine & Homoeopathy)",
        "domain": "Ayurveda / Traditional Knowledge",
        "domain_code": "DOMAIN_C",
        "jurisdiction": "India",
        "authority_level": "Tier 1",
        "priority": 1,
        "source_type": "Statutory Pharmacopoeia Authority",
        "url": "https://pcimh.gov.in",
        "supports_live": True,
        "supports_cache": True,
        "status": "active",
        "description": "Statutory body establishing official quality standards, monographs, Ayurvedic Pharmacopoeia of India (API), Ayurvedic Formulary of India (AFI), raw drug identification, and botanical nomenclature.",
    },
    "tkdl_public": {
        "name": "TKDL (Traditional Knowledge Digital Library — Public & Access Agreements)",
        "domain": "Ayurveda / Traditional Knowledge",
        "domain_code": "DOMAIN_C",
        "jurisdiction": "India",
        "authority_level": "Tier 1",
        "priority": 1,
        "source_type": "Traditional Knowledge Database",
        "url": "https://www.tkdl.res.in",
        "supports_live": True,
        "supports_cache": True,
        "status": "active",
        "description": "CSIR & Ministry of AYUSH repository mapping classical Sanskrit/Urdu medical formulations to international patent classifications (TKRC). System accesses public guidelines and authorized non-patent prior art.",
    },
    "ayush_research_portal": {
        "name": "AYUSH Research Portal & CCRAS",
        "domain": "Ayurveda / Traditional Knowledge",
        "domain_code": "DOMAIN_C",
        "jurisdiction": "India",
        "authority_level": "Tier 2",
        "priority": 2,
        "source_type": "Research Council Portal",
        "url": "https://ayushportal.nic.in",
        "supports_live": True,
        "supports_cache": True,
        "status": "active",
        "description": "Central Council for Research in Ayurvedic Sciences (CCRAS) publication database for clinical and preclinical Ayurveda research projects.",
    },

    # -------------------------------------------------------------------------
    # DOMAIN E — BIODIVERSITY / ABS
    # -------------------------------------------------------------------------
    "nba": {
        "name": "National Biodiversity Authority (NBA)",
        "domain": "Biodiversity / ABS",
        "domain_code": "DOMAIN_E",
        "jurisdiction": "India",
        "authority_level": "Tier 1",
        "priority": 1,
        "source_type": "Statutory Authority",
        "url": "https://nbaindia.gov.in",
        "supports_live": True,
        "supports_cache": True,
        "status": "active",
        "description": "Statutory body enforcing Biological Diversity Act 2002 & 2023 Amendment, Section 6 mandatory approval for patent grants, and Access & Benefit Sharing (ABS) regulations.",
    },
}


def get_routed_sources(domain: str, query: str = "") -> List[Dict[str, Any]]:
    """
    Selects target source registries based on domain and query characteristics (Section 18).
    """
    q_lower = query.lower()
    selected_keys = set()

    # Domain A: IP / Patents
    if domain in ("Patent", "Trademark", "Copyright", "GI", "Design", "Trade Secret", "Plant Variety", "International IP", "General IP"):
        selected_keys.update(["ip_india", "india_code", "wipo_patentscope", "epo_espacenet"])

    # Domain C: Ayurveda / TK
    if domain in ("Ayurveda", "Traditional Knowledge") or any(k in q_lower for k in ["ayurveda", "ayurvedic", "tkdl", "herb", "plant", "classical"]):
        selected_keys.update(["ayush_ministry", "pcimh", "tkdl_public", "ayush_research_portal", "ip_india", "nba"])

    # Domain E: ABS / Biodiversity
    if domain in ("Biodiversity", "ABS") or any(k in q_lower for k in ["abs", "biodiversity", "nba", "biological resource"]):
        selected_keys.update(["nba", "india_code", "wipo_patentscope"])

    # Domain B: Medical / Scientific
    if domain in ("Medical", "Scientific") or any(k in q_lower for k in ["pubmed", "clinical", "pharmacology", "extract", "efficacy"]):
        selected_keys.update(["pubmed", "icmr", "cdsco"])

    # Domain D: Regulatory
    if domain in ("Regulatory",) or any(k in q_lower for k in ["rule 158b", "fssai", "ayush", "gmp", "schedule t"]):
        selected_keys.update(["ayush_ministry", "cdsco", "india_code", "pcimh"])

    # Default fallback: ensure Tier 1 statutory sources are included
    if not selected_keys:
        selected_keys.update(["ip_india", "india_code", "ayush_ministry", "tkdl_public", "nba"])

    return [SOURCE_REGISTRY[k] for k in selected_keys if k in SOURCE_REGISTRY]
