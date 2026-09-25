"""
IP-SAKTI SAHAYAK
Ayurvedic Product & Formulation Classification Layer
=====================================================
Per spec Section 19: Classifies Ayurvedic product queries into statutory
categories before final IP/patentability analysis:
1. Classical / generic medicine (Shastriya Aushadhi)
2. Patent / proprietary medicine (Anubhuta / ASU Innovation)
3. New / non-classical drug
4. Phytopharmaceutical (CDSCO botanical extract drug)
5. Ayurveda-Aahar / nutraceutical (FSSAI AYUSH food category)
6. Cosmetic

Provides legal bar hints (Section 3(p), Section 3(d), Section 3(e), Rule 158B,
NBA Section 6, FSSAI) tailored to the classified category.
"""

import re
from typing import Dict, Any, List

CATEGORIES = {
    "classical_medicine": {
        "title": "Classical / Generic Medicine (Shastriya Aushadhi)",
        "keywords": ["classical", "shastriya", "charaka", "sushruta", "ayurvedic pharmacopoeia", "pharmacopoeia", "pharmacopoeial", "monograph", "api", "afi", "triphala", "trikatu", "chyawanprash", "bhasma", "asava", "arishta", "gutika", "churna", "taila", "ghrita", "haridra", "nimba", "shunthi", "pippali"],
        "governing_rules": "Drugs & Cosmetics Act First Schedule, Rule 158B(a), Section 3(p) Patents Act",
        "ip_status": "Statutorily excluded from patentability in India under Section 3(p) as traditional knowledge, unless non-obvious synergistic technical modification is proven. Prior art exists in classical texts and TKDL.",
        "regulatory_pathway": "AYUSH Manufacturing License under D&C Act Rule 158B(a) based on classical textual references; safety/efficacy clinical trials generally exempt.",
    },
    "proprietary_medicine": {
        "title": "Patent / Proprietary Medicine (Anubhuta / ASU Innovation)",
        "keywords": ["proprietary", "patent medicine", "new ratio", "herbal formulation", "synergistic", "extract combination", "bio-enhancer", "polyherbal capsule", "synergy", "standardized extract"],
        "governing_rules": "Drugs & Cosmetics Act Rule 158B(b), Section 3(e) & Section 3(d) Patents Act",
        "ip_status": "Patentable ONLY if applicant proves non-obvious technical synergy beyond mere aggregation (overcoming Section 3(e)) and enhanced therapeutic efficacy over known components (overcoming Section 3(d)).",
        "regulatory_pathway": "AYUSH License under Rule 158B(b) requiring published safety and acute toxicity study evidence plus proof of effectiveness.",
    },
    "phytopharmaceutical": {
        "title": "Phytopharmaceutical Drug (CDSCO Botanical Extract)",
        "keywords": ["phytopharmaceutical", "standardized botanical drug", "cdsco drug", "fractionated extract", "purified active", "clinical trial drug"],
        "governing_rules": "CDSCO New Drug Rules / D&C Rules 122E",
        "ip_status": "High patentability potential if novel purified fraction or novel therapeutic process is claimed. Requires rigorous patent drafting and clinical data.",
        "regulatory_pathway": "CDSCO approval as New Drug requiring Phase I, II, III clinical trials and strict chemical standardization (chromatographic profiling).",
    },
    "ayurveda_aahar": {
        "title": "Ayurveda-Aahar / Nutraceutical (Food Supplement)",
        "keywords": ["ayurveda aahar", "food", "dietary supplement", "health drink", "nutraceutical", "fssai", "herbal tea", "supplement", "functional food"],
        "governing_rules": "FSSAI (Ayurveda Aahara) Regulations, 2022",
        "ip_status": "Patentable as novel food composition or process if inventive step exists. Cannot claim disease cure on food labels.",
        "regulatory_pathway": "FSSAI registration/license under Ayurveda Aahara regulations. Must display 'AYURVEDA AAHARA' logo and mandatory disclaimers.",
    },
    "cosmetic": {
        "title": "Ayurvedic Cosmetic (Saundarya Kalpana)",
        "keywords": ["cosmetic", "cream", "lotion", "shampoo", "face wash", "skincare", "beauty", "saundarya"],
        "governing_rules": "Drugs & Cosmetics Act (Cosmetics Rules)",
        "ip_status": "Process or cosmetic composition may be patentable if novel and non-obvious. Subject to prior art in classical beauty preparations.",
        "regulatory_pathway": "Cosmetics manufacturing license; no medicinal or disease cure claims allowed on packaging.",
    },
}

AYURVEDA_TERMS = [
    "ayurved", "herbal", "plant", "botanical", "herb", "tkdl", "traditional medicine",
    "ashwagandha", "turmeric", "neem", "curcumin", "extract", "formulation", "shastriya",
    "aahar", "triphala", "trikatu", "pharmacopoeia", "pharmacopoeial", "monograph",
    "churna", "rasayana", "bhasma", "haridra", "pippali", "shunthi"
]


def classify_ayurvedic_formulation(query: str) -> Dict[str, Any]:
    """
    Determines formulation category or returns uncertain classification if evidence in query is insufficient.
    """
    q_lower = query.lower()

    # Check if query is actually about Ayurveda/Herbal products
    if not any(t in q_lower for t in AYURVEDA_TERMS):
        return {
            "applicable": False,
            "category": None,
            "title": "Not an Ayurvedic/Herbal Product Query",
            "reason": "Query does not refer to an Ayurvedic or botanical product formulation.",
        }

    scores = {}
    for cat_id, cat_info in CATEGORIES.items():
        hits = [kw for kw in cat_info["keywords"] if kw in q_lower]
        if hits:
            scores[cat_id] = len(hits)

    if not scores:
        return {
            "applicable": True,
            "category": "uncertain",
            "title": "Uncertain / Unclassified Formulation",
            "reason": "Available query evidence is insufficient to conclusively determine whether this is a Classical Shastriya medicine, Proprietary ASU medicine, Phytopharmaceutical, or Ayurveda-Aahara food product.",
            "clarification_prompt": "Please specify: Is this a classical formulation from traditional texts (e.g. Charaka Samhita/API), a proprietary herbal mixture with new ratios, a standardized phytopharmaceutical extract, or an Ayurveda-Aahara food supplement?",
            "ip_status": "Classification depends on product category. Classical preparations face Section 3(p) TK bars; proprietary mixtures face Section 3(e) admixture bars.",
        }

    best_cat_id = max(scores, key=scores.get)
    cat_info = CATEGORIES[best_cat_id]

    return {
        "applicable": True,
        "category": best_cat_id,
        "title": cat_info["title"],
        "reason": f"Matched formulation classification keywords: {', '.join(cat_info['keywords'][:3])}",
        "governing_rules": cat_info["governing_rules"],
        "ip_status": cat_info["ip_status"],
        "regulatory_pathway": cat_info["regulatory_pathway"],
    }
