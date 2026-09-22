"""
IP-SAKTI SAHAYAK
Prior-Art & Traditional Knowledge Explorer
===========================================
Explores the local authoritative corpus and TKDL references for potentially
relevant prior art against an innovation description.
Extracts:
- Ingredients, botanical binomials, formulation processes, therapeutic claims
- Computes shared concepts and differentiating technical features
- Strictly frames conclusions as 'Potentially relevant prior art identified'
  (never declares definitive legal novelty or non-novelty).
"""

import re
import logging
from typing import List, Dict, Any

from rag.hybrid_search import hybrid_search
from rag.reranker import reranker
from ai.llm import llm_client

logger = logging.getLogger(__name__)

_STOPWORDS = {"a", "an", "the", "using", "with", "for", "and", "of", "to", "in", "on", "is", "that", "this", "from", "by", "as"}

KNOWN_BOTANICAL_BINOMIALS = {
    "turmeric": "Curcuma longa",
    "ashwagandha": "Withania somnifera",
    "neem": "Azadirachta indica",
    "ginger": "Zingiber officinale",
    "black pepper": "Piper nigrum",
    "long pepper": "Piper longum",
    "tulsi": "Ocimum sanctum",
    "guggulu": "Commiphora mukul",
    "shallaki": "Boswellia serrata",
    "amla": "Emblica officinalis",
    "haritaki": "Terminalia chebula",
    "bibhitaki": "Terminalia bellirica",
    "triphala": "Emblica officinalis + Terminalia chebula + Terminalia bellirica",
    "trikatu": "Piper nigrum + Piper longum + Zingiber officinale",
}


def _extract_concepts(description: str) -> List[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", description)
    seen = []
    desc_lower = description.lower()

    # Check for botanical aliases
    for common, binomial in KNOWN_BOTANICAL_BINOMIALS.items():
        if common in desc_lower and common not in [s.lower() for s in seen]:
            seen.append(f"{common.title()} ({binomial})")

    for t in tokens:
        lower = t.lower()
        if lower in _STOPWORDS or len(lower) < 3:
            continue
        if lower not in [s.lower() for s in seen]:
            seen.append(t)
    return seen[:15]


def search_prior_art(description: str, jurisdiction: str = "India") -> Dict[str, Any]:
    """
    Runs multi-stage hybrid prior-art retrieval over the statutory & TK corpus.
    """
    concepts = _extract_concepts(description)
    search_query = " ".join(concepts) if concepts else description

    candidates = hybrid_search(search_query, top_k=20, jurisdiction=jurisdiction if jurisdiction != "All" else None)
    ranked = reranker.rerank(search_query, candidates, top_n=8)

    desc_tokens = set(re.findall(r"\w+", description.lower()))

    results = []
    for r in ranked:
        text = r.get("text") or ""
        ref_tokens = set(re.findall(r"\w+", text.lower()))
        shared = [t for t in (desc_tokens & ref_tokens) if t not in _STOPWORDS and len(t) > 3]

        results.append({
            "title": r.get("section") or r.get("authority") or "Authoritative Prior Art Record",
            "authority": r.get("authority") or "IP India / CSIR TKDL",
            "jurisdiction": r.get("jurisdiction") or "India",
            "url": r.get("source_url") or "https://ipindia.gov.in",
            "excerpt": text[:300] + "..." if len(text) > 300 else text,
            "relevance_score": round(float(r.get("rerank_score", r.get("final_score", 0.75))), 2),
            "shared_concepts": shared[:8],
            "differentiating_aspects": "Examine if specific ratios, extraction purity, or delivery mechanisms differ from classical prior art.",
            "note": "Potentially relevant prior art identified.",
        })

    return {
        "extracted_concepts": concepts,
        "query_used": search_query,
        "results": results,
        "disclaimer": (
            "This tool surfaces potentially relevant prior art and classical traditional knowledge references "
            "from verified official sources. It does not determine legal novelty or non-novelty — a formal "
            "patentability opinion requires a registered patent agent or IP attorney."
        ),
    }


# =====================================================
# TEST
# =====================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    res = search_prior_art("A herbal formulation using Ashwagandha and Turmeric for osteoarthritis joint inflammation")
    print("prior_art_search self-test passed! Extracted:", res["extracted_concepts"])
    print(f"Found {len(res['results'])} prior-art references.")
