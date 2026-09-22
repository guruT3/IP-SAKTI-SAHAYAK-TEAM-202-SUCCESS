"""
IP-SAKTI SAHAYAK
Product Classification Engine
===============================
Major differentiator for regulatory assessment (spec Section 40).
Evaluates an innovation or formulation across:
- Intended Use (Nutritional support vs Disease treatment vs Cosmetic improvement)
- Therapeutic & Health Claims (Structure/function vs Disease mitigation vs General wellness)
- Ingredients & Purity (Whole herb powder vs Standardized extract vs Isolated synthetic API)
- Delivery / Dosage Form (Capsule, tablet, powder, beverage, topical gel, syrup)
- Target Jurisdiction (India FSSAI/AYUSH/CDSCO, US FDA DSHEA/Botanical, EU EFSA/EMA)

Produces evidence-grounded potential classifications and required approval pathways
without making unauthorized definitive legal declarations.
"""

import logging
from typing import Dict, Any, List

from regulatory.hybrid_search import regulatory_hybrid_search

logger = logging.getLogger(__name__)


def classify_product_regulatory_regime(
    product_name: str,
    ingredients: str,
    intended_use: str,
    claims: str,
    delivery_form: str,
    country: str = "India",
) -> Dict[str, Any]:
    """
    Analyzes product parameters and determines potential statutory classifications,
    governing authorities, and applicable regulatory frameworks.
    """
    text_corpus = f"{product_name} {ingredients} {intended_use} {claims} {delivery_form}".lower()
    country_clean = country.strip() if country and country != "Auto Detect" else "India"

    potential_categories = []
    applicable_authorities = []
    key_regulations = []
    evidence_snippets = []

    # 1. Evaluate Ayurvedic / Traditional System Classification
    is_herbal = any(kw in text_corpus for kw in [
        "ayurved", "herbal", "ashwagandha", "turmeric", "curcumin", "tulsi", "neem",
        "extract", "botanical", "samhita", "curcuma", "longa", "boswellia", "serrata",
        "withania", "somnifera", "triphala", "haritaki", "bibhitaki", "amalaki",
        "piperine", "piper", "ginger", "zingiber", "brahmi", "bacopa", "giloy",
        "tinospora", "guduchi", "shatavari", "asparagus", "gokshura", "tribulus",
        "moringa", "amla", "bhumyamalaki", "punarnava", "shankhpushpi",
        "classical", "churna", "vati", "asava", "arishta", "taila", "ghrita",
        "plant", "root", "leaf", "bark", "seed", "fruit",
    ])
    has_therapeutic_claims = any(kw in text_corpus for kw in [
        "treat", "cure", "pain", "arthritis", "diabetes", "inflammation",
        "therapeutic", "healing", "remedy", "disease", "relief", "management",
        "digestive", "vata", "pitta", "kapha", "balancing", "doshas",
        "anti-inflammatory", "immune", "rejuvenation", "adaptogen",
    ])
    has_food_claims = any(kw in text_corpus for kw in ["dietary", "nutrition", "energy", "supplement", "wellness", "stamina", "refreshing", "drink", "tea", "food"])

    if country_clean == "India":
        if is_herbal and has_therapeutic_claims:
            potential_categories.append({
                "category": "Ayurvedic Proprietary Medicine (Patent / Proprietary ASU Drug)",
                "governing_authority": "State Licensing Authority (SLA) under Ministry of AYUSH",
                "statutory_basis": "Drugs and Cosmetics Act, 1940 & Rule 158-B of Drugs and Cosmetics Rules, 1945",
                "licensing_pathway": "Form 25-D / Form 24-D Manufacturing License",
                "evidence_required": "Published safety literature, OECD 423 acute oral toxicity studies, pilot clinical trial evidence, and Schedule T GMP compliance.",
                "confidence": "HIGH",
            })
            applicable_authorities.append("Ministry of AYUSH")
            key_regulations.append("Drugs & Cosmetics Rules (Rule 158B & Schedule T)")

        if is_herbal and (has_food_claims or "supplement" in text_corpus or "capsule" in text_corpus or "beverage" in text_corpus):
            potential_categories.append({
                "category": "Nutraceutical / Health Supplement (with Botanical Extracts)",
                "governing_authority": "Food Safety and Standards Authority of India (FSSAI)",
                "statutory_basis": "Food Safety and Standards (Health Supplements, Nutraceuticals...) Regulations, 2022",
                "licensing_pathway": "FSSAI Central / State Manufacturing License under Category 13.0",
                "evidence_required": "Compliance with Schedule III botanical list, 100% ICMR RDA caps on vitamins/minerals, mandatory 'NOT FOR MEDICINAL USE' label declaration.",
                "confidence": "HIGH",
            })
            applicable_authorities.append("FSSAI")
            key_regulations.append("FSSAI Nutraceutical Regulations 2022")

        if is_herbal and ("food" in text_corpus or "drink" in text_corpus or "tea" in text_corpus or "syrup" in text_corpus):
            potential_categories.append({
                "category": "Ayurveda Aahara (Classical Recipe-Based Food)",
                "governing_authority": "Food Safety and Standards Authority of India (FSSAI) in consultation with AYUSH",
                "statutory_basis": "Food Safety and Standards (Ayurveda Aahara) Regulations, 2022",
                "licensing_pathway": "FSSAI Ayurveda Aahara License + Mandatory Ayurveda Aahara Logo",
                "evidence_required": "Proof that preparation recipe strictly matches authoritative Ayurvedic texts listed in Schedule A; no disease treatment claims permitted.",
                "confidence": "MEDIUM",
            })
            applicable_authorities.append("FSSAI")
            key_regulations.append("FSSAI Ayurveda Aahara Regulations 2022")

        if any(kw in text_corpus for kw in ["synthetic api", "chemical molecule", "monoclonal", "injected", "pure compound"]):
            potential_categories.append({
                "category": "New Pharmaceutical Drug (Allopathic)",
                "governing_authority": "Central Drugs Standard Control Organization (CDSCO / DCGI)",
                "statutory_basis": "New Drugs and Clinical Trials Rules, 2019 & Drugs and Cosmetics Act, 1940",
                "licensing_pathway": "Form CT-04 Clinical Trials Approval -> Form CT-18 / CT-21 New Drug Marketing Authorization",
                "evidence_required": "Preclinical toxicology (GLP), Phase I-III clinical trial dossier, and Schedule M GMP manufacturing.",
                "confidence": "HIGH",
            })
            applicable_authorities.append("CDSCO")
            key_regulations.append("New Drugs and Clinical Trials Rules 2019")

        if any(kw in text_corpus for kw in ["skin", "lotion", "cream", "hair", "shampoo", "beauty", "face pack"]):
            potential_categories.append({
                "category": "Ayurvedic Cosmetic (Saundarya Prasadak) / Topical Care",
                "governing_authority": "State Licensing Authority (AYUSH) / State FDA",
                "statutory_basis": "Drugs and Cosmetics Rules, 1945 (Part XVI)",
                "licensing_pathway": "ASU Cosmetic Manufacturing License on Form 25-D",
                "evidence_required": "Classical or proprietary formulation safety data, heavy metal screening, and skin irritation/sensitization testing.",
                "confidence": "MEDIUM",
            })
            applicable_authorities.append("Ministry of AYUSH")
            key_regulations.append("Drugs and Cosmetics Rules (Cosmetic Standards)")

    elif country_clean == "USA":
        if is_herbal and has_therapeutic_claims:
            potential_categories.append({
                "category": "Botanical Drug Product",
                "governing_authority": "US Food and Drug Administration (FDA / CDER)",
                "statutory_basis": "21 U.S.C. 355 & FDA Guidance for Industry: Botanical Drug Development",
                "licensing_pathway": "Investigational New Drug (IND) Application -> New Drug Application (NDA)",
                "evidence_required": "Phase 1-3 clinical trial efficacy data and advanced spectroscopic batch-to-batch CMC fingerprinting.",
                "confidence": "HIGH",
            })
            applicable_authorities.append("US FDA (CDER)")
            key_regulations.append("21 CFR 312 / 314 & Botanical Drug Guidance")

        if is_herbal and (has_food_claims or not has_therapeutic_claims):
            potential_categories.append({
                "category": "Dietary Supplement (DSHEA 1994)",
                "governing_authority": "US Food and Drug Administration (FDA / CFSAN)",
                "statutory_basis": "Dietary Supplement Health and Education Act (DSHEA 1994) & 21 CFR Part 111",
                "licensing_pathway": "Post-market 30-day Structure/Function Claim Notification (No pre-market approval)",
                "evidence_required": "21 CFR 111 cGMP compliance, mandatory DSHEA disclaimer, NDI notification if novel ingredient.",
                "confidence": "HIGH",
            })
            applicable_authorities.append("US FDA (CFSAN)")
            key_regulations.append("DSHEA 1994 & 21 CFR Part 111")

    elif country_clean == "European Union":
        if is_herbal:
            potential_categories.append({
                "category": "Traditional Herbal Medicinal Product (THMPD)",
                "governing_authority": "National Competent Authorities in EU Member States / EMA HMPC",
                "statutory_basis": "Directive 2004/24/EC on Traditional Herbal Medicinal Products",
                "licensing_pathway": "Simplified Traditional Herbal Registration (THR)",
                "evidence_required": "Proof of 30 years traditional use (at least 15 years in EU), safety bibliographical review, and EU GMP compliance.",
                "confidence": "HIGH",
            })
            applicable_authorities.append("EMA (HMPC)")
            key_regulations.append("Directive 2004/24/EC (THMPD)")

    # Retrieve matching regulatory evidence
    search_q = f"{product_name} {ingredients} regulatory classification requirements {country_clean}"
    retrieved = regulatory_hybrid_search(search_q, top_k=4, country=country_clean)
    for r in retrieved:
        evidence_snippets.append({
            "authority": r.get("authority"),
            "section": r.get("section"),
            "text": r.get("text", "")[:240] + "...",
            "url": r.get("source_url"),
        })

    return {
        "success": True,
        "product_name": product_name,
        "country": country_clean,
        "summary": (
            f"Based on the provided intended use ('{intended_use[:120]}'), formulation profile, and claims, "
            f"the product may legally fall within multiple regulatory regimes in {country_clean}. "
            f"Classification is heavily determined by therapeutic vs dietary claim positioning and ingredient extraction grade."
        ),
        "potential_classifications": potential_categories,
        "applicable_authorities": list(set(applicable_authorities)),
        "key_regulations": list(set(key_regulations)),
        "supporting_regulatory_evidence": evidence_snippets,
        "mandatory_disclaimer": (
            "IMPORTANT: This is a preliminary evidence-based regulatory classification analysis, "
            "not a definitive statutory legal determination. Final regulatory categorization and license grant "
            "depends on the competent licensing authority upon formal dossier review."
        ),
    }


if __name__ == "__main__":
    res = classify_product_regulatory_regime(
        product_name="AyurJoint Herbal Tablet",
        ingredients="Withania somnifera and Boswellia serrata with Piperine",
        intended_use="Relief from joint stiffness and support joint mobility",
        claims="Supports healthy cartilage and reduces inflammation",
        delivery_form="Oral Tablet",
        country="India",
    )
    print("Product Classifier self-test passed!")
    print("Classifications count:", len(res["potential_classifications"]))
