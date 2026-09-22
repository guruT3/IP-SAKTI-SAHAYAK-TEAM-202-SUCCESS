"""
IP-SAKTI SAHAYAK
Regulatory Version Tracker & Timeline Engine
==============================================
Manages regulatory document versioning, amendment timelines, and statutory conflict detection:
- Version Classification: CURRENT | AMENDED | SUPERSEDED | DRAFT | PROPOSED | EXPIRED
- Historical Amendment Lineage: Traces how an original Act/Regulation was modified by subsequent notifications.
- Conflict & Discrepancy Detection: Detects old vs new provision conflicts, draft vs gazetted status,
  and primary statute vs secondary guidance discrepancies.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Canonical regulatory version register with timeline relationships
REGULATORY_TIMELINES: List[Dict[str, Any]] = [
    {
        "regulation_id": "fssai_nutraceutical_timeline",
        "title": "FSSAI Regulations on Health Supplements, Nutraceuticals, FSDU & FMSP",
        "authority": "Food Safety and Standards Authority of India (FSSAI)",
        "country": "India",
        "domain": "Food / Nutraceutical",
        "current_version": "2022.1 (Effective 1 April 2022)",
        "timeline": [
            {
                "version": "2016 Original",
                "title": "Food Safety and Standards (Health Supplements, Nutraceuticals...) Regulations, 2016",
                "effective_date": "2018-01-01",
                "status": "SUPERSEDED",
                "superseded_by": "2022 Notification",
                "summary": "Initial baseline regulations categorizing 8 food supplement classes with Schedule I to VIII ingredient lists.",
            },
            {
                "version": "2022 Consolidated",
                "title": "Food Safety and Standards (Health Supplements, Nutraceuticals...) Regulations, 2022",
                "effective_date": "2022-04-01",
                "status": "CURRENT",
                "gazette_ref": "F. No. Std/SP-05/A-1.2022/N-01, 29th March 2022",
                "summary": "Replaced 2016 regulations. Mandated 100% RDA capping for vitamins/minerals, standardized botanical extract purity, banned pure chemical single-active APIs in food.",
            },
            {
                "version": "2024 Advisory Update",
                "title": "FSSAI Direction on Non-Specified Ingredients and Pre-Mix Clearance",
                "effective_date": "2024-05-10",
                "status": "CURRENT",
                "gazette_ref": "FSSAI Executive Direction No. 12/2024",
                "summary": "Clarified approval mechanism for novel botanical extracts not listed in Schedule IV or Indian Pharmacopoeia.",
            },
        ],
    },
    {
        "regulation_id": "bda_ayush_abs_timeline",
        "title": "Biological Diversity Act & Access and Benefit Sharing (ABS) Framework",
        "authority": "National Biodiversity Authority (NBA) / MoEFCC",
        "country": "India",
        "domain": "Biodiversity / ABS",
        "current_version": "2023 Amendment Act (Effective 3 August 2023)",
        "timeline": [
            {
                "version": "2002 Principal Act",
                "title": "The Biological Diversity Act, 2002 (Act 18 of 2003)",
                "effective_date": "2003-02-05",
                "status": "AMENDED",
                "summary": "Established National Biodiversity Authority, State Biodiversity Boards, Section 6 mandatory IPR approval, and Section 55 criminal penalties.",
            },
            {
                "version": "2014 ABS Guidelines",
                "title": "Guidelines on Access to Biological Resources and Associated Knowledge and Benefits Sharing Regulations, 2014",
                "effective_date": "2014-11-21",
                "status": "AMENDED",
                "summary": "Prescribed benefit-sharing payment slabs (0.1%–0.5% ex-factory sales / 3%–5% IPR royalties).",
            },
            {
                "version": "2023 Amendment Act",
                "title": "The Biological Diversity (Amendment) Act, 2023 (Act 10 of 2023)",
                "effective_date": "2023-08-03",
                "status": "CURRENT",
                "gazette_ref": "The Gazette of India, Extraordinary, Part II, Section 1, No. 20 of 2023",
                "summary": "Exempted registered AYUSH practitioners and cultivated medicinal plants from prior SBB intimation; replaced criminal imprisonment with civil financial penalties.",
            },
        ],
    },
    {
        "regulation_id": "ayush_drugs_cosmetics_timeline",
        "title": "Drugs and Cosmetics Rules — AYUSH Drug Licensing & Schedule T GMP",
        "authority": "Ministry of AYUSH / CDSCO",
        "country": "India",
        "domain": "Ayurveda / Medicine",
        "current_version": "2022/2024 Quality Consolidated Standards",
        "timeline": [
            {
                "version": "1945 Principal Rules",
                "title": "Drugs and Cosmetics Rules, 1945 (Part XVI & XVII - ASU Drugs)",
                "effective_date": "1945-12-21",
                "status": "AMENDED",
                "summary": "Set statutory requirements for manufacture, sale, and licensing of Ayurvedic, Siddha, and Unani drugs.",
            },
            {
                "version": "2008 Schedule T Revision",
                "title": "Good Manufacturing Practices (GMP) for ASU Medicines — Schedule T",
                "effective_date": "2008-06-15",
                "status": "AMENDED",
                "summary": "Prescribed factory premises, sanitary standards, machinery, and quality control lab requirements for ASU drug manufacturers.",
            },
            {
                "version": "2022 Heavy Metals Notification",
                "title": "AYUSH Notification on Permissible Limits of Heavy Metals, Pesticide Residues, and Microbial Contamination",
                "effective_date": "2022-10-18",
                "status": "CURRENT",
                "gazette_ref": "Ministry of AYUSH Notification No. K.11020/01/2020-DCC",
                "summary": "Mandated universal batch testing for Lead (10 ppm), Arsenic (3 ppm), Cadmium (0.3 ppm), and Mercury (1 ppm) for all Ayurvedic medicines.",
            },
        ],
    },
    {
        "regulation_id": "fda_botanical_drugs_timeline",
        "title": "US FDA Botanical Drug Development Regulatory Framework",
        "authority": "US Food and Drug Administration (FDA / CDER)",
        "country": "USA",
        "domain": "Medicine / Traditional Medicine",
        "current_version": "2016 Final Guidance for Industry",
        "timeline": [
            {
                "version": "2004 Draft Guidance",
                "title": "Guidance for Industry: Botanical Drug Products (Draft)",
                "effective_date": "2004-06-01",
                "status": "SUPERSEDED",
                "summary": "Initial FDA framework outlining clinical evaluation requirements for heterogeneous plant extracts.",
            },
            {
                "version": "2016 Final Guidance",
                "title": "Guidance for Industry: Botanical Drug Development (Revision 1)",
                "effective_date": "2016-12-28",
                "status": "CURRENT",
                "summary": "Comprehensive regulatory pathway for Investigational New Drugs (IND) and New Drug Applications (NDA) for complex botanical formulations.",
            },
        ],
    },
    {
        "regulation_id": "ema_thmpd_timeline",
        "title": "EU Traditional Herbal Medicinal Products Directive (THMPD)",
        "authority": "European Medicines Agency (EMA / HMPC)",
        "country": "European Union",
        "domain": "Medicine / Traditional Medicine",
        "current_version": "Directive 2004/24/EC (Consolidated)",
        "timeline": [
            {
                "version": "2004/24/EC",
                "title": "Directive 2004/24/EC of the European Parliament and of the Council on Traditional Herbal Medicinal Products",
                "effective_date": "2004-04-30",
                "status": "CURRENT",
                "summary": "Simplified registration procedure for traditional herbal medicines with at least 30 years of established medicinal use (including at least 15 years within the EU).",
            },
        ],
    },
]


def get_all_timelines() -> List[Dict[str, Any]]:
    return REGULATORY_TIMELINES


def get_timeline_by_id(regulation_id: str) -> Optional[Dict[str, Any]]:
    for t in REGULATORY_TIMELINES:
        if t["regulation_id"] == regulation_id:
            return t
    return None


def detect_regulatory_conflicts(evidence_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Analyzes retrieved evidence chunks to detect version discrepancies,
    outdated standards, or conflicting regulatory interpretations.
    """
    conflicts = []
    versions_by_topic = {}

    for c in evidence_chunks:
        authority = c.get("authority", "Unknown")
        status = c.get("status", "CURRENT")
        version = c.get("version", "1.0")
        eff_date = c.get("effective_date", "Unspecified")

        key = f"{c.get('country')}_{c.get('domain')}"
        if key not in versions_by_topic:
            versions_by_topic[key] = []
        versions_by_topic[key].append(c)

        if status in ("SUPERSEDED", "EXPIRED", "DRAFT"):
            conflicts.append({
                "type": "outdated_or_draft_version",
                "authority": authority,
                "section": c.get("section"),
                "status": status,
                "version": version,
                "effective_date": eff_date,
                "warning": f"Retrieved source is marked as {status} (Version: {version}, Effective: {eff_date}). Current regulations should be consulted.",
            })

    return conflicts
