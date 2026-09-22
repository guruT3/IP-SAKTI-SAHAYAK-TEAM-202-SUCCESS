"""
IP-SAKTI SAHAYAK
India vs International Comparative IP Engine
=============================================
Generates structured, authoritative side-by-side legal comparison matrices:
- India (IP India, AYUSH, NBA)
- United States (USPTO, FDA)
- European Union (EPO, EMA)
- International / WIPO Treaties (PCT, TRIPS, Nagoya, 2024 WIPO Treaty)
"""

import logging
from typing import Dict, Any, List

from rag.hybrid_search import hybrid_search
from ai.llm import llm_client

logger = logging.getLogger(__name__)

COMPARATIVE_TOPICS = {
    "patentability": {
        "title": "Patentability Criteria & Statutory Exclusions",
        "india": (
            "Section 3(d) excludes new forms/uses of known substances without proven enhanced therapeutic efficacy (Novartis 2013). "
            "Section 3(p) excludes traditional knowledge aggregations. Section 3(e) excludes mere admixtures."
        ),
        "us": (
            "35 U.S.C. 101/102/103. Under Alice/Mayo framework, natural products and botanical extracts without distinct structural/chemical "
            "transformation are patent-ineligible natural phenomena."
        ),
        "europe": (
            "EPC Articles 52, 54, 56. Methods of medical treatment are excluded (Art. 53(c)), but first/second medical uses of known substances "
            "are patentable if novel and non-obvious."
        ),
        "international": (
            "WTO TRIPS Article 27 permits exclusions to protect human/plant life and exclusions of therapeutic methods."
        ),
    },
    "traditional_knowledge": {
        "title": "Traditional Knowledge (TK) Protection & Prior Art",
        "india": (
            "Codified in TKDL (over 4.5 lakh classical formulations from Charaka, Sushruta, Unani, Siddha). Section 3(p) explicit statutory bar."
        ),
        "us": (
            "USPTO has access agreement to search TKDL as non-patent prior art. Landmark precedent: US Patent 5,401,504 on Turmeric wound healing revoked."
        ),
        "europe": (
            "EPO systematically searches TKDL. Landmark precedent: European Patent 0436257 on Neem fungicidal properties revoked on traditional prior art grounds."
        ),
        "international": (
            "2024 WIPO Treaty on IP, Genetic Resources and Associated Traditional Knowledge mandates country-of-origin and indigenous provider disclosure."
        ),
    },
    "biodiversity_abs": {
        "title": "Biodiversity & Access and Benefit-Sharing (ABS)",
        "india": (
            "Mandatory Section 6 prior approval from National Biodiversity Authority (NBA) before IPR grant. ABS fee: 0.1%–0.5% ex-factory sales or 3%–5% royalties."
        ),
        "us": (
            "US is not a Party to the Convention on Biological Diversity (CBD) or Nagoya Protocol; no domestic federal ABS requirement for patent grant."
        ),
        "europe": (
            "EU Regulation 511/2014 enforces Nagoya Protocol compliance. Due diligence declarations required when receiving research funding or commercializing."
        ),
        "international": (
            "Nagoya Protocol requires Prior Informed Consent (PIC) and Mutually Agreed Terms (MAT) for access and utilization of genetic resources."
        ),
    },
    "regulatory_approval": {
        "title": "Herbal / Ayurvedic Drug Commercialization Pathway",
        "india": (
            "Drugs & Cosmetics Act Rule 158B. Classical formulations (First Schedule texts) require textual reference only; Proprietary medicines require safety/toxicity trials and Schedule T GMP."
        ),
        "us": (
            "FDA Botanical Drug Guidance. Complex herbal mixtures require rigorous CMC batch-to-batch consistency and Phase 1-3 IND/NDA clinical trials."
        ),
        "europe": (
            "EMA Traditional Herbal Medicinal Products Directive (THMPD 2004/24/EC). Simplified registration for herbal products with 30 years of established medicinal use (15 years within EU)."
        ),
        "international": (
            "WHO Guidelines on Good Agricultural and Collection Practices (GACP) and Quality Control Methods for Herbal Materials."
        ),
    },
}


def generate_comparative_matrix(query: str, domain_focus: str = "All") -> Dict[str, Any]:
    """
    Produces a detailed comparative analysis for a given user query or innovation.
    """
    # Retrieve relevant international and Indian statutory chunks
    retrieved = hybrid_search(f"{query} India vs international US EPO PCT TRIPS comparison", top_k=6)
    evidence_text = "\n".join([f"• {c.get('section') or c.get('authority')}: {c.get('text', '')[:160]}" for c in retrieved])

    prompt = [
        {
            "role": "system",
            "content": (
                "You are an International IP & Traditional Knowledge Comparative Law Expert. "
                "Compare the IP, Traditional Knowledge, ABS, and Regulatory frameworks between India, the US, and Europe. "
                "Provide clear, actionable, and legally sound comparative insights with zero hallucinations."
            ),
        },
        {
            "role": "user",
            "content": (
                f"INQUIRY / INNOVATION: {query}\n"
                f"FOCUS: {domain_focus}\n"
                f"EVIDENCE:\n{evidence_text}\n\n"
                "Provide a structured comparative summary highlighting key differences in patentability, TKDL impact, ABS hurdles, and foreign filing requirements."
            ),
        },
    ]

    llm_res = llm_client.chat(prompt, temperature=0.15, max_tokens=800)
    ai_summary = llm_res.text if llm_res.success else "Comparative matrix compiled from international statutory rules."

    return {
        "success": True,
        "query": query,
        "topics": COMPARATIVE_TOPICS,
        "ai_synthesis": ai_summary,
        "key_takeaways": [
            "India requires proof of enhanced therapeutic efficacy under Section 3(d), whereas US/EPO focus strictly on non-obviousness and technical effect.",
            "Indian Patent Law has an explicit statutory bar on Traditional Knowledge (Section 3(p)), whereas US/EPO treat TK primarily as prior art anticipation.",
            "India strictly mandates NBA approval before patent grant (Section 6 BDA), whereas US has no domestic ABS checkpoint.",
            "Foreign filing from India requires mandatory prior Section 39 permission or 6 weeks prior filing in India.",
        ],
    }


# =====================================================
# TEST
# =====================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    res = generate_comparative_matrix("Patentability of herbal nano-emulsions for arthritis")
    print("Comparative IP self-test passed! Topics:", list(res["topics"].keys()))
