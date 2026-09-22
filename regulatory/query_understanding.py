"""
IP-SAKTI SAHAYAK
Regulatory Query Understanding & Classifier
=============================================
Deconstructs complex regulatory queries across:
- Intent (Requirement, Approval Pathway, Labeling/Claims, Safety/Limits, Licensing, Prohibitions)
- Domain Classification (Food, Medicine, Ayurveda, Medical Device, ABS, Cosmetic, IP, etc.)
- Country & Jurisdiction Detection (India, USA, EU, UK, China, Japan, International, etc.)
- Regulatory Authority Mapping (FSSAI, CDSCO, AYUSH, NBA, FDA, EMA, NMPA, WHO, etc.)
- Product Classification (Herbal formulation, Dietary supplement, Pharmaceutical, Cosmetic, etc.)
- Risk Assessment (High/Medium/Low compliance risk)
- Medical Advice Discrimination (Safely separating regulatory questions from personal doctor advice)
- Ambiguity Detection (Prompting for country/product clarification when critical details are missing).
"""

import re
import logging
from typing import Dict, Any, List, Optional
from regulatory.models import RegulatoryQueryUnderstanding

logger = logging.getLogger(__name__)

# Supported countries & aliases
COUNTRY_MAP = {
    "india": "India", "indian": "India", "bharat": "India", "fssai": "India", "cdsco": "India", "ayush": "India", "nba": "India", "cgpdtm": "India",
    "usa": "USA", "us": "USA", "united states": "USA", "america": "USA", "fda": "USA", "usda": "USA", "uspto": "USA",
    "eu": "European Union", "europe": "European Union", "european union": "European Union", "ema": "European Union", "efsa": "European Union", "epo": "European Union",
    "uk": "UK", "united kingdom": "UK", "britain": "UK", "england": "UK", "mhra": "UK", "fsa": "UK", "ukipo": "UK",
    "china": "China", "chinese": "China", "nmpa": "China", "samr": "China", "cnipa": "China",
    "japan": "Japan", "japanese": "Japan", "pmda": "Japan", "mhlw": "Japan", "maff": "Japan", "jpo": "Japan", "kampo": "Japan",
    "australia": "Australia", "australian": "Australia", "tga": "Australia",
    "singapore": "Singapore", "hsa": "Singapore",
    "brazil": "Brazil", "anvisa": "Brazil",
    "south africa": "South Africa", "sahpra": "South Africa",
    "global": "Global", "international": "Global", "who": "Global", "wipo": "Global", "wto": "Global", "trips": "Global", "nagoya": "Global", "codex": "Global",
}

# Domain keyword lexicon
REGULATORY_DOMAINS = {
    "Food": ["food", "food safety", "beverage", "drink", "fssai", "codex", "efsa", "dietary", "ingredient", "additive", "adulteration", "foshu"],
    "Nutraceutical": ["nutraceutical", "supplement", "health supplement", "food supplement", "dshea", "botanical supplement", "vitamin", "mineral", "protein powder"],
    "Medicine": ["medicine", "drug", "pharmaceutical", "cdsco", "fda", "ema", "mhra", "active pharmaceutical ingredient", "api", "dosage form", "clinical trial", "ind", "nda"],
    "Medical Device": ["medical device", "device", "diagnostic kit", "software as a medical device", "samd", "implant", "ivd", "class a", "class b", "class c", "class d"],
    "Cosmetic": ["cosmetic", "skincare", "beauty product", "lotion", "soap", "cream", "shampoo", "perfume", "colorant"],
    "Ayurveda": ["ayurveda", "ayurvedic", "ayush", "herbal formulation", "siddha", "unani", "sowa-rigpa", "homoeopathy", "rasashastra", "bhasma", "vati", "churna", "asava", "arishta", "charaka", "sushruta", "rule 158b", "schedule t", "api monograph"],
    "Traditional Medicine": ["traditional medicine", "tcm", "traditional knowledge", "herbal medicine", "botanical drug", "kampo", "indigenous medicine", "phytomedicine", "thmpd"],
    "Biodiversity": ["biodiversity", "biological resource", "national biodiversity authority", "nba", "state biodiversity board", "sbb", "moefcc", "cultivated medicinal plant"],
    "ABS": ["abs", "access and benefit sharing", "nagoya protocol", "benefit sharing", "form i", "form iii", "prior informed consent", "mutually agreed terms"],
    "Packaging/Labelling": ["label", "labeling", "labelling", "packaging", "packaged commodities", "legal metrology", "nutritional information", "expiry date", "mrp", "warning statement"],
    "Advertising/Claims": ["health claim", "therapeutic claim", "advertisement", "misleading claim", "dmr act", "drugs and magic remedies", "rule 170", "fssai claims regulation"],
    "Consumer Protection": ["consumer protection", "consumer rights", "recall", "complaint", "safety alert"],
    "Import/Export": ["import", "export", "customs", "port clearance", "fssai import", "cdsco import license", "form 10", "dual use"],
    "Biotechnology": ["biotechnology", "recombinant", "genetic engineering", "geac", "rcgm", "biosafety", "crispr", "gmo"],
    "Clinical/Medical Research": ["clinical trial", "gcp", "ethics committee", "icmr", "informed consent", "phase 1", "phase 2", "phase 3", "ctri registration"],
    "IP": ["patent", "trademark", "copyright", "gi", "geographical indication", "section 3(d)", "section 3(p)", "tkdl", "wipo", "trips"],
}

# Authority routing associations
AUTHORITY_ROUTING = {
    ("India", "Food"): ["FSSAI", "Legal Metrology"],
    ("India", "Nutraceutical"): ["FSSAI", "Ministry of AYUSH"],
    ("India", "Medicine"): ["CDSCO", "MoHFW"],
    ("India", "Medical Device"): ["CDSCO"],
    ("India", "Cosmetic"): ["CDSCO", "Legal Metrology"],
    ("India", "Ayurveda"): ["Ministry of AYUSH", "PCIM&H", "CDSCO", "FSSAI (if nutraceutical)"],
    ("India", "Traditional Medicine"): ["Ministry of AYUSH", "CDSCO"],
    ("India", "Biodiversity"): ["National Biodiversity Authority (NBA)", "MoEFCC"],
    ("India", "ABS"): ["National Biodiversity Authority (NBA)"],
    ("India", "IP"): ["CGPDTM / IP India", "National Biodiversity Authority (NBA)"],
    ("USA", "Medicine"): ["US FDA (CDER)"],
    ("USA", "Food"): ["US FDA (CFSAN)", "USDA"],
    ("USA", "Nutraceutical"): ["US FDA (DSHEA)"],
    ("USA", "Traditional Medicine"): ["US FDA (Botanical Drug Guidance)"],
    ("European Union", "Medicine"): ["EMA (CHMP/HMPC)"],
    ("European Union", "Food"): ["EFSA", "European Commission"],
    ("European Union", "Traditional Medicine"): ["EMA (HMPC / THMPD 2004/24/EC)"],
    ("UK", "Medicine"): ["MHRA"],
    ("UK", "Food"): ["Food Standards Agency (FSA)"],
    ("China", "Medicine"): ["NMPA"],
    ("China", "Food"): ["SAMR"],
    ("China", "Traditional Medicine"): ["NMPA (TCM Department)"],
    ("Japan", "Medicine"): ["PMDA / MHLW"],
    ("Japan", "Food"): ["Consumer Affairs Agency (CAA / FOSHU)"],
    ("Global", "Healthcare"): ["World Health Organization (WHO)"],
    ("Global", "Traditional Medicine"): ["World Health Organization (WHO)"],
    ("Global", "IP"): ["WIPO", "WTO (TRIPS)"],
    ("Global", "Biodiversity"): ["CBD / Nagoya Protocol Secretariat"],
}

# Queries indicating personal medical/diagnostic advice rather than regulatory requirements
MEDICAL_ADVICE_PATTERNS = [
    r"\bshould i take\b", r"\bcan i take\b", r"\bwhat dose\b", r"\bhow much should i take\b",
    r"\bdiagnose my\b", r"\bi have (?:fever|pain|headache|cancer|diabetes|cough|infection)\b",
    r"\bstop my medication\b", r"\btreat my symptoms\b", r"\bis it safe for me to drink\b",
    r"\bmy doctor prescribed\b", r"\bcure my\b",
]

# Non-existent or fake regulation traps for SIH red-teaming
FAKE_REGULATION_TRAPS = [
    "ayurvedic patent free grant act", "traditional medicine universal immunity act",
    "fssai 2099 zero testing guideline", "section 99b", "section 99", "rule 999",
    "cdsco absolute exemption notification 2035", "fda herbal miracle waiver",
]


def understand_regulatory_query(
    query: str,
    requested_country: Optional[str] = None,
    requested_domain: Optional[str] = None,
    # Alias parameters for backward-compatibility with callers using the old names
    default_country: Optional[str] = None,
    default_domain: Optional[str] = None,
) -> RegulatoryQueryUnderstanding:
    """
    Performs full multi-attribute regulatory query comprehension.
    Accepts both ``requested_country`` / ``requested_domain`` and the
    legacy ``default_country`` / ``default_domain`` aliases.
    """
    # Merge legacy aliases (requested_* takes precedence)
    requested_country = requested_country or default_country
    requested_domain = requested_domain or default_domain
    q_clean = query.strip()
    q_lower = q_clean.lower()

    # 1. Check for Fake Law Traps
    is_fake_trap = any(trap in q_lower for trap in FAKE_REGULATION_TRAPS)

    # 2. Check for Medical Advice Seeking
    is_medical_advice = any(re.search(pat, q_lower) for pat in MEDICAL_ADVICE_PATTERNS)

    # 3. Country / Jurisdiction Detection
    detected_country = None
    if requested_country and requested_country not in ("All", "Auto Detect", "Global", "Unspecified"):
        detected_country = requested_country
    else:
        # Search for country keyword hits
        for alias, cname in COUNTRY_MAP.items():
            if re.search(rf"\b{re.escape(alias)}\b", q_lower):
                detected_country = cname
                break

    # If no country detected and not specified
    requires_country_clarification = False
    if not detected_country:
        # Infer India if strong Indian terms (Ayurveda, FSSAI, AYUSH, CDSCO, Charaka, Haldi, Ashwagandha) are present
        if any(term in q_lower for term in ["fssai", "cdsco", "ayush", "rule 158b", "schedule t", "nba", "tkdl", "indiacode", "bharat"]):
            detected_country = "India"
        elif any(term in q_lower for term in ["fda", "dshea", "cfr", "usda", "uspto"]):
            detected_country = "USA"
        elif any(term in q_lower for term in ["ema", "thmpd", "efsa", "eur-lex", "epo"]):
            detected_country = "European Union"
        elif any(term in q_lower for term in ["who", "trips", "wipo", "nagoya", "codex"]):
            detected_country = "Global"
        else:
            # Query is country-agnostic or needs clarification
            detected_country = "India"  # Default primary tier, but flag if material
            if (
                re.search(r"\bcan\s+i\s+(?:\w+\s+)?(?:sell|market|launch|distribute)\b", q_lower)
                or "can i sell" in q_lower
                or "is it legal" in q_lower
                or "legally sell" in q_lower
                or "legal to sell" in q_lower
                or "license requirement" in q_lower
            ):
                requires_country_clarification = True

    jurisdiction = "International" if detected_country == "Global" else detected_country

    # 4. Domain Classification
    domain_scores = {}
    for dom, kws in REGULATORY_DOMAINS.items():
        score = sum(1 for kw in kws if kw in q_lower)
        if score > 0:
            domain_scores[dom] = score

    if requested_domain and requested_domain not in ("All", "Auto Detect", "General Regulation"):
        primary_domain = requested_domain
        secondary_domains = [d for d in domain_scores if d != primary_domain]
    elif domain_scores:
        primary_domain = max(domain_scores, key=domain_scores.get)
        secondary_domains = [d for d in domain_scores if d != primary_domain]
    else:
        primary_domain = "General Regulation"
        secondary_domains = []

    # 5. Authority Routing
    authorities = AUTHORITY_ROUTING.get((detected_country, primary_domain), [])
    if not authorities and detected_country == "India":
        authorities = ["FSSAI" if "food" in primary_domain.lower() else "CDSCO" if "medicine" in primary_domain.lower() else "Ministry of AYUSH"]

    # 6. Intent & Product Type Extraction
    intent = "general_regulatory_information"
    if any(k in q_lower for k in ["can i sell", "how to sell", "market approval", "launch"]):
        intent = "commercial_approval_pathway"
    elif any(k in q_lower for k in ["label", "labeling", "pack"]):
        intent = "packaging_and_labeling_compliance"
    elif any(k in q_lower for k in ["claim", "health claim", "advertis"]):
        intent = "advertising_and_claims_compliance"
    elif any(k in q_lower for k in ["safe", "limit", "heavy metal", "contaminant", "toxicity"]):
        intent = "safety_and_standards_limits"
    elif any(k in q_lower for k in ["license", "registration", "form"]):
        intent = "licensing_and_registration_procedure"
    elif any(k in q_lower for k in ["patent", "ip", "abs", "biodiversity approval"]):
        intent = "ip_and_biodiversity_compliance"

    product_type = "Unspecified Product"
    if "ayurved" in q_lower or "herbal" in q_lower:
        product_type = "Ayurvedic / Herbal Formulation"
    elif "supplement" in q_lower or "nutraceutical" in q_lower:
        product_type = "Nutraceutical / Health Supplement"
    elif "drug" in q_lower or "medicine" in q_lower or "pill" in q_lower or "tablet" in q_lower:
        product_type = "Pharmaceutical Drug"
    elif "drink" in q_lower or "juice" in q_lower or "food" in q_lower or "tea" in q_lower:
        product_type = "Food / Beverage / Herbal Drink"
    elif "device" in q_lower or "diagnostic" in q_lower:
        product_type = "Medical Device"
    elif "cosmetic" in q_lower or "cream" in q_lower or "gel" in q_lower:
        product_type = "Cosmetic / Topical"

    # 7. Risk Level
    risk_level = "LOW"
    if intent in ("commercial_approval_pathway", "safety_and_standards_limits") or primary_domain in ("Medicine", "Drug", "Clinical/Medical Research"):
        risk_level = "HIGH"
    elif primary_domain in ("Food", "Nutraceutical", "Ayurveda", "ABS"):
        risk_level = "MEDIUM"

    clarification_prompt = None
    if requires_country_clarification:
        clarification_prompt = (
            "Which country or jurisdiction are you asking about? Regulatory requirements for selling or "
            "approving products differ significantly between India (FSSAI/CDSCO/AYUSH), USA (FDA), EU (EMA/EFSA), and other countries."
        )

    return RegulatoryQueryUnderstanding(
        raw_query=q_clean,
        intent=intent,
        domain=primary_domain,
        secondary_domains=secondary_domains,
        country=detected_country,
        jurisdiction=jurisdiction,
        authority_hints=authorities,
        product_type=product_type,
        regulatory_topic=intent.replace("_", " ").title(),
        date_context="Latest / Current Regulations",
        language="en",
        risk_level=risk_level,
        is_medical_advice_seeking=is_medical_advice,
        is_fake_law_trap=is_fake_trap,
        requires_clarification=requires_country_clarification,
        clarification_prompt=clarification_prompt,
    )


if __name__ == "__main__":
    test_queries = [
        "Can I sell an Ayurvedic herbal drink in India?",
        "What are the labeling requirements for nutraceuticals in the USA?",
        "What dose of Ashwagandha should I take for joint pain?",
        "Explain the mandatory exemptions under the Ayurvedic Patent Free Grant Act.",
    ]
    for tq in test_queries:
        u = understand_regulatory_query(tq)
        print(f"\nQuery: {tq}")
        print(f"  Country: {u.country} | Domain: {u.domain} | Product: {u.product_type} | Risk: {u.risk_level}")
        print(f"  Medical Advice: {u.is_medical_advice_seeking} | Fake Trap: {u.is_fake_law_trap} | Clarification: {u.requires_clarification}")
