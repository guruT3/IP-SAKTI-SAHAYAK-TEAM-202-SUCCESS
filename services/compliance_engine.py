"""
IP-SAKTI SAHAYAK
Compliance Engine
===================
Rule-based "preliminary compliance guidance" (spec Section 31). Maps a
described activity to the regulatory/IP areas it likely touches, using
transparent keyword rules — explicitly NOT presented as definitive
legal advice.
"""

from typing import Dict, Any, List

RULES: List[Dict[str, Any]] = [
    {
        "keywords": ["commercializ", "sell", "market", "launch"],
        "area": "General commercialization compliance",
        "notes": "Commercial use typically triggers business registration, labeling, and consumer-protection requirements in addition to any IP considerations.",
    },
    {
        "keywords": ["ayurved", "herbal", "traditional medicine", "unani", "siddha"],
        "area": "AYUSH regulatory approval",
        "notes": "Products marketed with therapeutic claims under Ayurveda/Unani/Siddha typically require approval/licensing under AYUSH-administered rules.",
        "authority": "Ministry of AYUSH",
    },
    {
        "keywords": ["traditional knowledge", "indigenous", "folklore", "community knowledge"],
        "area": "Traditional Knowledge protection",
        "notes": "Use of documented traditional knowledge may be checked against TKDL to avoid conflicting patent claims.",
        "authority": "TKDL / CSIR",
    },
    {
        "keywords": ["biological resource", "genetic resource", "plant extract", "biodiversity"],
        "area": "Biodiversity / Access & Benefit Sharing (ABS)",
        "notes": "Accessing biological resources for commercial use in India generally requires approval under the Biological Diversity Act and ABS regulations.",
        "authority": "National Biodiversity Authority",
    },
    {
        "keywords": ["patent", "invention", "novel formulation", "novel process"],
        "area": "Patent protection",
        "notes": "A novel, non-obvious, industrially applicable invention may be eligible for patent protection, subject to exclusions like Section 3(d).",
        "authority": "IP India (CGPDTM)",
    },
    {
        "keywords": ["brand", "trademark", "logo", "product name"],
        "area": "Trademark protection",
        "notes": "A distinctive brand name or logo used in trade can typically be registered as a trademark.",
        "authority": "IP India (Trade Marks Registry)",
    },
    {
        "keywords": ["region", "origin", "geographical", "gi tag"],
        "area": "Geographical Indication (GI)",
        "notes": "Products whose qualities are tied to a specific geographic origin may be eligible for GI registration.",
        "authority": "GI Registry",
    },
]


def check_compliance(description: str) -> Dict[str, Any]:
    text = description.lower()
    matched = []
    for rule in RULES:
        if any(kw in text for kw in rule["keywords"]):
            matched.append({
                "area": rule["area"],
                "notes": rule["notes"],
                "relevant_authority": rule.get("authority"),
            })

    return {
        "input_summary": description[:300],
        "potentially_relevant_areas": matched,
        "label": "Preliminary compliance guidance",
        "disclaimer": (
            "This is preliminary, rule-based guidance highlighting areas that may be relevant. "
            "It is not definitive legal advice — confirm requirements with the named authority or "
            "a qualified legal professional before proceeding."
        ),
    }


# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":
    result = check_compliance("I want to commercialize a traditional Ayurvedic herbal formulation.")
    assert result["potentially_relevant_areas"]
    print("compliance_engine self-test passed:", [a["area"] for a in result["potentially_relevant_areas"]])
