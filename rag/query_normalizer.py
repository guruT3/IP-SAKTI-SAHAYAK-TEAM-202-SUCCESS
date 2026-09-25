"""
IP-SAKTI SAHAYAK
Deterministic Query Normalization & Concept Expansion Layer
============================================================
1. Normalizes whitespace, quotes, and punctuation without destroying statutory
   identifiers (Section 3(d), Section 3(p), Rule 158B, Schedule T, PCT, TRIPS, TKDL, ABS, GI).
2. Generates retrieval-oriented query expansion variants for difficult legal,
   prior art, and Ayurvedic queries (mapping herbs to botanical names, Sanskrit terms,
   PCIM&H monographs, and TKDL prior art concepts).
3. The original user query is strictly preserved for final answer generation.
"""

import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Statutory & Technical Protected Identifier Patterns
PROTECTED_TERMS_RE = re.compile(
    r"\b(Section\s+\d+[\w()]*|Rule\s+\d+[\w-]*|Schedule\s+[A-Z\d]+|Article\s+\d+[\w()]*|"
    r"PCT|TRIPS|TKDL|ABS|GI|NBA|AYUSH|PCIM&H|CCRAS|ICMR|CDSCO|FSSAI|FDA|EMA|WIPO|USPTO|EPO)\b",
    re.IGNORECASE,
)

# Ayurvedic Herb Synonym & Botanical Mapping Dictionary
HERBAL_BOTANICAL_MAP: Dict[str, Dict[str, List[str]]] = {
    "neem": {
        "botanical": ["Azadirachta indica"],
        "sanskrit": ["Nimba", "Arishta"],
        "terms": ["neem oil", "neem extract", "nimbin", "azadirachtin"],
    },
    "turmeric": {
        "botanical": ["Curcuma longa"],
        "sanskrit": ["Haridra", "Nisha"],
        "terms": ["curcumin", "curcuminoids", "haldi", "wound healing"],
    },
    "ashwagandha": {
        "botanical": ["Withania somnifera"],
        "sanskrit": ["Ashwagandha", "Hayagandha"],
        "terms": ["withanolides", "indian ginseng", "stress relief", "adaptogen"],
    },
    "tulsi": {
        "botanical": ["Ocimum sanctum", "Ocimum tenuiflorum"],
        "sanskrit": ["Tulasi", "Surasa"],
        "terms": ["holy basil", "eugenol"],
    },
    "ginger": {
        "botanical": ["Zingiber officinale"],
        "sanskrit": ["Shunthi", "Nagara", "Adraka"],
        "terms": ["gingerol", "shogaol"],
    },
    "black pepper": {
        "botanical": ["Piper nigrum"],
        "sanskrit": ["Maricha"],
        "terms": ["piperine", "bioenhancer"],
    },
    "long pepper": {
        "botanical": ["Piper longum"],
        "sanskrit": ["Pippali"],
        "terms": ["piperine", "bioavailability"],
    },
    "guggulu": {
        "botanical": ["Commiphora mukul", "Commiphora wightii"],
        "sanskrit": ["Guggulu"],
        "terms": ["guggulsterones", "lipid lowering"],
    },
    "brahmi": {
        "botanical": ["Bacopa monnieri"],
        "sanskrit": ["Brahmi"],
        "terms": ["bacosides", "memory enhancer"],
    },
    "amla": {
        "botanical": ["Emblica officinalis", "Phyllanthus emblica"],
        "sanskrit": ["Amalaki", "Dhatri"],
        "terms": ["ascorbic acid", "rasayana"],
    },
    "triphala": {
        "botanical": ["Emblica officinalis", "Terminalia chebula", "Terminalia bellirica"],
        "sanskrit": ["Triphala", "Amalaki", "Haritaki", "Bibhitaki"],
        "terms": ["rasayana", "classical formulation"],
    },
    "trikatu": {
        "botanical": ["Piper nigrum", "Piper longum", "Zingiber officinale"],
        "sanskrit": ["Trikatu", "Maricha", "Pippali", "Shunthi"],
        "terms": ["bioenhancer", "yogavahi", "bioavailability"],
    },
}


def normalize_query(query: str) -> str:
    """
    Cleans formatting noise while preserving legal sections and proper nouns.
    """
    if not query:
        return ""

    # Replace weird quotes, dashes, unicode spaces
    cleaned = (
        query.replace("“", '"')
        .replace("”", '"')
        .replace("‘", "'")
        .replace("’", "'")
        .replace("–", "-")
        .replace("—", "-")
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Standardize section space e.g. "Section  3 ( d )" -> "Section 3(d)"
    cleaned = re.sub(r"Section\s*(\d+)\s*\(\s*([a-z0-9]+)\s*\)", r"Section \1(\2)", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"Rule\s*(\d+)\s*-\s*([A-Z0-9]+)", r"Rule \1\2", cleaned, flags=re.IGNORECASE)

    return cleaned


def generate_query_expansions(query: str, domain: str = "", jurisdiction: str = "India") -> List[str]:
    """
    Generates retrieval-oriented query variants to maximize BM25 and vector hit rate.
    Does NOT modify the user's original query.
    """
    normalized = normalize_query(query)
    q_lower = normalized.lower()
    expansions: List[str] = [normalized]

    # 1. Botanical & Synonym Expansion for Ayurvedic Herbs
    detected_botanicals = []
    for herb, mapping in HERBAL_BOTANICAL_MAP.items():
        if herb in q_lower or any(s.lower() in q_lower for s in mapping["sanskrit"]):
            for b in mapping["botanical"]:
                detected_botanicals.append(b)
            for s in mapping["sanskrit"]:
                if s.lower() not in q_lower:
                    expansions.append(f"{normalized} {s}")

    if detected_botanicals:
        botanical_str = " ".join(detected_botanicals)
        expansions.append(f"{normalized} {botanical_str}")

    # 2. Domain-Specific Statutory Concept Expansion
    if any(k in q_lower for k in ["ayurveda", "ayurvedic", "herbal", "formulation", "classical"]):
        expansions.append(f"{normalized} Section 3(p) Patents Act traditional knowledge TKDL")
        expansions.append(f"{normalized} Rule 158B Drugs Cosmetics Act PCIM&H Ayurvedic Pharmacopoeia")

    if any(k in q_lower for k in ["patent", "patented", "patentability", "prior art"]):
        if "3(d)" in q_lower or "efficacy" in q_lower or "substance" in q_lower:
            expansions.append(f"{normalized} Section 3(d) therapeutic efficacy known substance enhancement")
        if "3(e)" in q_lower or "combination" in q_lower or "mixture" in q_lower or "synergy" in q_lower:
            expansions.append(f"{normalized} Section 3(e) mere admixture synergistic effect")
        if "3(p)" in q_lower or "traditional knowledge" in q_lower or "tkdl" in q_lower:
            expansions.append(f"{normalized} Section 3(p) aggregation of traditionally known properties TKDL CSIR")

    if any(k in q_lower for k in ["abs", "biodiversity", "nba", "biological resource", "benefit sharing"]):
        expansions.append(f"{normalized} National Biodiversity Authority Section 6 Biological Diversity Act Nagoya Protocol")

    if jurisdiction == "International" or any(k in q_lower for k in ["pct", "wipo", "trips", "uspto", "epo"]):
        expansions.append(f"{normalized} Patent Cooperation Treaty WIPO Article 27 TRIPS Nagoya Protocol")

    # Deduplicate while preserving order
    seen = set()
    unique_expansions = []
    for exp in expansions:
        if exp not in seen:
            seen.add(exp)
            unique_expansions.append(exp)

    return unique_expansions[:4]
