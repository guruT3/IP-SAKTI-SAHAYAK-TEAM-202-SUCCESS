"""
IP-SAKTI SAHAYAK
Dynamic Knowledge Graph Engine
===============================
Generates dynamic and comprehensive entity-relationship graphs for IP, Ayurveda,
and Traditional Knowledge domains:
- Botanicals & Plants
- Classical Ayurvedic Texts & Samhitas
- Active Phyto-chemical Compounds
- Traditional Formulations & Dosage Forms
- Statutory Provisions (Section 3(d), 3(p), 3(e), Section 6 BDA, Rule 158B)
- Regulatory Authorities (IP India, AYUSH, NBA, CSIR TKDL, WIPO, EPO, USPTO)
- Landmark Case Precedents (Turmeric, Neem, Basmati, Novartis)
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Complete authoritative domain ontology
BASE_NODES: List[Dict[str, str]] = [
    # Botanicals
    {"id": "curcuma_longa", "label": "Curcuma longa (Turmeric)", "type": "botanical", "group": "Botanicals"},
    {"id": "withania_somnifera", "label": "Withania somnifera (Ashwagandha)", "type": "botanical", "group": "Botanicals"},
    {"id": "azadirachta_indica", "label": "Azadirachta indica (Neem)", "type": "botanical", "group": "Botanicals"},
    {"id": "piper_nigrum", "label": "Piper nigrum (Black Pepper)", "type": "botanical", "group": "Botanicals"},
    {"id": "commiphora_mukul", "label": "Commiphora mukul (Guggulu)", "type": "botanical", "group": "Botanicals"},
    {"id": "boswellia_serrata", "label": "Boswellia serrata (Shallaki)", "type": "botanical", "group": "Botanicals"},

    # Phytochemical Actives
    {"id": "curcumin", "label": "Curcuminoids", "type": "active", "group": "Actives"},
    {"id": "withanolides", "label": "Withanolides", "type": "active", "group": "Actives"},
    {"id": "piperine", "label": "Piperine (Bioenhancer)", "type": "active", "group": "Actives"},
    {"id": "azadirachtin", "label": "Azadirachtin", "type": "active", "group": "Actives"},

    # Classical Texts & Databases
    {"id": "charaka_samhita", "label": "Charaka Samhita", "type": "classical_text", "group": "Classical Texts"},
    {"id": "sushruta_samhita", "label": "Sushruta Samhita", "type": "classical_text", "group": "Classical Texts"},
    {"id": "tkdl", "label": "TKDL Database (CSIR)", "type": "institution", "group": "Institutions"},
    {"id": "trikatu", "label": "Trikatu Formulation", "type": "formulation", "group": "Formulations"},
    {"id": "triphala", "label": "Triphala Formulation", "type": "formulation", "group": "Formulations"},

    # Statutory Provisions
    {"id": "sec_3d", "label": "Section 3(d) (Efficacy Bar)", "type": "law_section", "group": "Statutes"},
    {"id": "sec_3p", "label": "Section 3(p) (TK Exclusion)", "type": "law_section", "group": "Statutes"},
    {"id": "sec_3e", "label": "Section 3(e) (Admixture Bar)", "type": "law_section", "group": "Statutes"},
    {"id": "sec_6_bda", "label": "Section 6 BDA (NBA Approval)", "type": "law_section", "group": "Statutes"},
    {"id": "rule_158b", "label": "Rule 158B (AYUSH Licensing)", "type": "regulation", "group": "Statutes"},
    {"id": "wipo_treaty_2024", "label": "WIPO GR & TK Treaty (2024)", "type": "treaty", "group": "Treaties"},

    # Authorities
    {"id": "ip_india", "label": "IP India (CGPDTM)", "type": "authority", "group": "Authorities"},
    {"id": "nba", "label": "National Biodiversity Authority", "type": "authority", "group": "Authorities"},
    {"id": "ayush", "label": "Ministry of AYUSH", "type": "authority", "group": "Authorities"},
    {"id": "uspto", "label": "USPTO (United States)", "type": "authority", "group": "Authorities"},
    {"id": "epo", "label": "EPO (Europe)", "type": "authority", "group": "Authorities"},

    # Landmark Cases
    {"id": "case_turmeric", "label": "Turmeric Patent Revocation", "type": "case_law", "group": "Landmark Cases"},
    {"id": "case_neem", "label": "Neem Fungicide Revocation", "type": "case_law", "group": "Landmark Cases"},
    {"id": "case_novartis", "label": "Novartis v. UOI (Sec 3d)", "type": "case_law", "group": "Landmark Cases"},
]

BASE_EDGES: List[Dict[str, str]] = [
    {"source": "curcuma_longa", "target": "curcumin", "relation": "contains_active"},
    {"source": "withania_somnifera", "target": "withanolides", "relation": "contains_active"},
    {"source": "piper_nigrum", "target": "piperine", "relation": "contains_active"},
    {"source": "azadirachta_indica", "target": "azadirachtin", "relation": "contains_active"},

    {"source": "curcuma_longa", "target": "charaka_samhita", "relation": "documented_in"},
    {"source": "withania_somnifera", "target": "charaka_samhita", "relation": "documented_in"},
    {"source": "azadirachta_indica", "target": "sushruta_samhita", "relation": "documented_in"},
    {"source": "piper_nigrum", "target": "trikatu", "relation": "constituent_of"},

    {"source": "charaka_samhita", "target": "tkdl", "relation": "codified_in"},
    {"source": "sushruta_samhita", "target": "tkdl", "relation": "codified_in"},

    {"source": "tkdl", "target": "sec_3p", "relation": "triggers_rejection_under"},
    {"source": "curcumin", "target": "sec_3d", "relation": "requires_therapeutic_efficacy_under"},
    {"source": "trikatu", "target": "sec_3e", "relation": "scrutinized_as_admixture_under"},

    {"source": "curcuma_longa", "target": "sec_6_bda", "relation": "requires_nba_approval_under"},
    {"source": "withania_somnifera", "target": "sec_6_bda", "relation": "requires_nba_approval_under"},
    {"source": "sec_6_bda", "target": "nba", "relation": "administered_by"},

    {"source": "sec_3p", "target": "ip_india", "relation": "enforced_by"},
    {"source": "sec_3d", "target": "ip_india", "relation": "enforced_by"},
    {"source": "rule_158b", "target": "ayush", "relation": "governed_by"},

    {"source": "tkdl", "target": "uspto", "relation": "searched_by"},
    {"source": "tkdl", "target": "epo", "relation": "searched_by"},

    {"source": "case_turmeric", "target": "curcuma_longa", "relation": "established_prior_art_for"},
    {"source": "case_turmeric", "target": "uspto", "relation": "revoked_by"},
    {"source": "case_neem", "target": "azadirachta_indica", "relation": "established_prior_art_for"},
    {"source": "case_neem", "target": "epo", "relation": "revoked_by"},
    {"source": "case_novartis", "target": "sec_3d", "relation": "definitive_interpretation_of"},

    {"source": "wipo_treaty_2024", "target": "curcuma_longa", "relation": "protects_global_origin_of"},
]


def get_knowledge_graph() -> Dict[str, Any]:
    """Returns the combined IP & Regulatory authoritative ontology graph."""
    try:
        from services.regulatory_graph import REGULATORY_GRAPH_NODES, REGULATORY_GRAPH_EDGES
        all_nodes = list(BASE_NODES) + [n for n in REGULATORY_GRAPH_NODES if n["id"] not in {x["id"] for x in BASE_NODES}]
        all_edges = list(BASE_EDGES) + REGULATORY_GRAPH_EDGES
        return {"nodes": all_nodes, "edges": all_edges}
    except Exception:
        return {"nodes": BASE_NODES, "edges": BASE_EDGES}


def get_dynamic_subgraph(query: str) -> Dict[str, Any]:
    """
    Returns an entity-filtered subgraph matching terms in user query/innovation.
    """
    full_graph = get_knowledge_graph()
    nodes = full_graph["nodes"]
    edges = full_graph["edges"]

    q_lower = query.lower()
    matched_node_ids = set()

    # Search for matching nodes
    for node in nodes:
        label_lower = node["label"].lower()
        if any(term in label_lower or term in node["id"] for term in q_lower.split()):
            matched_node_ids.add(node["id"])

    # If no specific matches, return core connected nodes
    if not matched_node_ids:
        matched_node_ids = {
            "curcuma_longa", "curcumin", "charaka_samhita", "tkdl", "sec_3d",
            "sec_3p", "sec_6_bda", "ip_india", "nba", "case_turmeric", "fssai", "ayush"
        }

    # Include 1-hop neighbor nodes
    extended_ids = set(matched_node_ids)
    for edge in edges:
        if edge["source"] in matched_node_ids or edge["target"] in matched_node_ids:
            extended_ids.add(edge["source"])
            extended_ids.add(edge["target"])

    filtered_nodes = [n for n in nodes if n["id"] in extended_ids]
    filtered_edges = [e for e in edges if e["source"] in extended_ids and e["target"] in extended_ids]

    return {"nodes": filtered_nodes, "edges": filtered_edges}


# =====================================================
# TEST
# =====================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    g = get_knowledge_graph()
    assert len(g["nodes"]) >= 20
    sub = get_dynamic_subgraph("Ashwagandha arthritis formulation")
    print(f"Dynamic Knowledge Graph self-test passed: {len(g['nodes'])} total nodes, {len(sub['nodes'])} subgraph nodes.")
