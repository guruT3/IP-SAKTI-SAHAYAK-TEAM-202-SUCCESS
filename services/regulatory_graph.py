"""
IP-SAKTI SAHAYAK
Regulatory Knowledge Graph Extensions
=======================================
Extends the Knowledge Graph with comprehensive regulatory ontology nodes & relationships:
- Product Categories (Ayurvedic Medicine, Nutraceutical, Food, Medical Device, Botanical Drug)
- Regulatory Authorities (FSSAI, CDSCO, Ministry of AYUSH, US FDA, EMA, EFSA, WHO, NBA)
- Regulatory Statutes (FSSAI 2022 Regs, Rule 158B, Schedule T GMP, DSHEA 1994, THMPD 2004/24/EC)
- Quality Standards & Limits (Heavy Metals, Microbial Limits, RDA Caps, NDI, GRAS)
- Legal Relationships (GOVERNS, APPLIES_TO, REQUIRES_LICENSE, CONTAINS_STANDARD, ENFORCED_BY)
"""

from typing import Dict, Any, List

REGULATORY_GRAPH_NODES: List[Dict[str, str]] = [
    # Regulatory Authorities
    {"id": "fssai", "label": "Food Safety & Standards Authority (FSSAI)", "type": "authority", "group": "Authorities"},
    {"id": "cdsco", "label": "Central Drugs Standard Control Org (CDSCO)", "type": "authority", "group": "Authorities"},
    {"id": "fda", "label": "US Food & Drug Administration (FDA)", "type": "authority", "group": "Authorities"},
    {"id": "ema", "label": "European Medicines Agency (EMA)", "type": "authority", "group": "Authorities"},
    {"id": "efsa", "label": "European Food Safety Authority (EFSA)", "type": "authority", "group": "Authorities"},
    {"id": "who", "label": "World Health Organization (WHO)", "type": "authority", "group": "Authorities"},

    # Regulatory Instruments & Statutes
    {"id": "fssai_nutra_reg_2022", "label": "FSSAI Nutraceutical Regs 2022", "type": "regulation", "group": "Statutes"},
    {"id": "fssai_ayurveda_ahara", "label": "FSSAI Ayurveda Aahara Regs 2022", "type": "regulation", "group": "Statutes"},
    {"id": "schedule_t_gmp", "label": "Schedule T GMP & Quality Limits", "type": "regulation", "group": "Statutes"},
    {"id": "fda_dshea_1994", "label": "US DSHEA (Dietary Supplements 1994)", "type": "statute", "group": "Statutes"},
    {"id": "fda_botanical_guidance", "label": "US FDA Botanical Drug Guidance", "type": "guideline", "group": "Statutes"},
    {"id": "ema_thmpd", "label": "EU THMPD (Directive 2004/24/EC)", "type": "regulation", "group": "Statutes"},
    {"id": "dmr_act_1954", "label": "Drugs & Magic Remedies Act 1954", "type": "statute", "group": "Statutes"},
    {"id": "legal_metrology_rules", "label": "Legal Metrology Packaged Rules 2011", "type": "regulation", "group": "Statutes"},

    # Product Categories & Standards
    {"id": "cat_nutraceutical", "label": "Nutraceutical / Health Supplement", "type": "category", "group": "Product Categories"},
    {"id": "cat_ayurvedic_drug", "label": "Ayurvedic Proprietary Medicine", "type": "category", "group": "Product Categories"},
    {"id": "cat_botanical_drug", "label": "Botanical Drug Product (USA)", "type": "category", "group": "Product Categories"},
    {"id": "cat_traditional_herbal_eu", "label": "Traditional Herbal Product (EU)", "type": "category", "group": "Product Categories"},
    {"id": "std_heavy_metals", "label": "AYUSH Heavy Metal Limits (Pb, As, Cd, Hg)", "type": "standard", "group": "Standards"},
    {"id": "std_rda_caps", "label": "100% ICMR-NIN RDA Vitamin/Mineral Cap", "type": "standard", "group": "Standards"},
    {"id": "std_dshea_disclaimer", "label": "Mandatory DSHEA Disclaimer Statement", "type": "standard", "group": "Standards"},
]

REGULATORY_GRAPH_EDGES: List[Dict[str, str]] = [
    {"source": "cat_nutraceutical", "target": "fssai_nutra_reg_2022", "relation": "governed_by"},
    {"source": "fssai_nutra_reg_2022", "target": "fssai", "relation": "enforced_by"},
    {"source": "fssai_nutra_reg_2022", "target": "std_rda_caps", "relation": "mandates"},

    {"source": "cat_ayurvedic_drug", "target": "rule_158b", "relation": "licensed_under"},
    {"source": "cat_ayurvedic_drug", "target": "schedule_t_gmp", "relation": "must_comply_with"},
    {"source": "schedule_t_gmp", "target": "std_heavy_metals", "relation": "enforces_limits"},
    {"source": "schedule_t_gmp", "target": "ayush", "relation": "administered_by"},

    {"source": "cat_botanical_drug", "target": "fda_botanical_guidance", "relation": "governed_by"},
    {"source": "fda_botanical_guidance", "target": "fda", "relation": "evaluated_by"},

    {"source": "cat_traditional_herbal_eu", "target": "ema_thmpd", "relation": "registered_under"},
    {"source": "ema_thmpd", "target": "ema", "relation": "supervised_by"},

    {"source": "cat_nutraceutical", "target": "fda_dshea_1994", "relation": "regulated_in_us_as"},
    {"source": "fda_dshea_1994", "target": "std_dshea_disclaimer", "relation": "mandates"},

    {"source": "curcuma_longa", "target": "cat_nutraceutical", "relation": "permitted_ingredient_in"},
    {"source": "withania_somnifera", "target": "cat_ayurvedic_drug", "relation": "classical_constituent_of"},

    {"source": "cat_ayurvedic_drug", "target": "dmr_act_1954", "relation": "advertising_restricted_by"},
    {"source": "cat_nutraceutical", "target": "legal_metrology_rules", "relation": "packaging_regulated_by"},
]


def get_extended_knowledge_graph() -> Dict[str, Any]:
    """Returns combined IP + Regulatory Knowledge Graph."""
    from services.knowledge_graph import BASE_NODES, BASE_EDGES

    all_nodes = list(BASE_NODES) + [n for n in REGULATORY_GRAPH_NODES if n["id"] not in {x["id"] for x in BASE_NODES}]
    all_edges = list(BASE_EDGES) + REGULATORY_GRAPH_EDGES

    return {"nodes": all_nodes, "edges": all_edges}
