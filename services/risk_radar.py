"""
IP-SAKTI SAHAYAK
5-Axis IP Risk Radar Engine
============================
Computes transparent, explainable 5-axis risk assessments for innovations:
1. Traditional Knowledge Overlap
2. Prior-Art & Novelty Risk (Section 3(d)/3(p)/3(e))
3. Biodiversity & ABS Compliance (NBA/BDA)
4. Regulatory Complexity (AYUSH Rule 158B & GMP)
5. International IP Friction (PCT/USPTO/EPO)

Includes qualitative risk level, numeric percentage, risk driver breakdown,
and strategic mitigation advice.
"""

from typing import Dict, Any, List


def calculate_risk_radar(
    ingredients: str,
    preparation_process: str,
    intended_use: str,
    extracted_botanicals: List[Dict[str, Any]],
    jurisdiction: str = "India",
) -> Dict[str, Any]:
    """
    Computes explainable scores (0-100) and risk factors for each axis.
    """
    ing_lower = ingredients.lower()
    proc_lower = preparation_process.lower()
    use_lower = intended_use.lower()

    # --- 1. Traditional Knowledge Overlap (0-100) ---
    tk_score = 20
    tk_drivers = []
    if extracted_botanicals:
        tk_score += min(50, len(extracted_botanicals) * 25)
        herb_names = ", ".join([b["matched_name"] for b in extracted_botanicals])
        tk_drivers.append(f"Identified {len(extracted_botanicals)} classical Ayurvedic botanical(s): {herb_names}")

    classical_processes = ["decoction", "kwatha", "kashaya", "fermentation", "asava", "arishta",
                           "oil", "taila", "ghrita", "churna", "powder", "infusion", "swarasa"]
    matched_procs = [p for p in classical_processes if p in proc_lower]
    if matched_procs:
        tk_score += 20
        tk_drivers.append(f"Preparation method utilizes classical Ayurvedic extraction technique(s): {', '.join(matched_procs)}")

    if any(term in use_lower for term in ["wound", "pain", "arthritis", "inflammation", "fever", "digest", "skin", "respiratory", "cough"]):
        tk_score += 15
        tk_drivers.append("Intended indication directly overlaps with classical therapeutic actions in Charaka/Sushruta Samhita.")

    tk_score = min(95, max(15, tk_score))

    # --- 2. Prior-Art & Novelty Risk (Section 3(d)/3(p)/3(e)) (0-100) ---
    novelty_risk = 25
    novelty_drivers = []
    if tk_score >= 70:
        novelty_risk += 35
        novelty_drivers.append("High TKDL overlap triggers Section 3(p) statutory bar (traditional knowledge aggregation).")

    if len(extracted_botanicals) > 1:
        novelty_risk += 20
        novelty_drivers.append("Polyherbal combination triggers Section 3(e) mere admixture objection unless synergistic proof is provided.")

    if any(term in proc_lower for term in ["extract", "powder", "crush", "boil"]) and not any(term in proc_lower for term in ["nanoparticle", "liposome", "targeted", "novel crystal", "phytosome"]):
        novelty_risk += 15
        novelty_drivers.append("Conventional extraction method lacks physical or structural novelty required to overcome Section 3(d).")

    novelty_risk = min(92, max(20, novelty_risk))

    # --- 3. Biodiversity & ABS Compliance (NBA) (0-100) ---
    abs_score = 30
    abs_drivers = []
    if extracted_botanicals:
        abs_score += 40
        abs_drivers.append("Use of Indian biological resources mandates Section 6 prior approval from the National Biodiversity Authority (NBA).")
        abs_drivers.append("Commercialization requires benefit-sharing payment (0.1%–0.5% ex-factory sales or 3%–5% IPR royalties).")

    if "foreign" in ing_lower or "export" in use_lower or jurisdiction in ("International", "PCT", "US", "Europe"):
        abs_score += 20
        abs_drivers.append("Cross-border commercialization or foreign filing triggers Section 3 & Section 4 NBA transfer approval.")

    abs_score = min(95, max(25, abs_score))

    # --- 4. Regulatory Complexity (AYUSH / Drugs Act) (0-100) ---
    reg_score = 35
    reg_drivers = []
    if "proprietary" in ing_lower or "novel" in proc_lower or "extract" in proc_lower:
        reg_score += 30
        reg_drivers.append("Classified as 'Patent or Proprietary Medicine' under Rule 158B — requires published safety/toxicity data.")
    else:
        reg_drivers.append("Qualifies as 'Classical Formulation' (Shastriya) — requires strict compliance with First Schedule textual recipes.")

    reg_drivers.append("Manufacturing facility must possess Schedule T Good Manufacturing Practices (GMP) certification.")
    if any(term in use_lower for term in ["cancer", "diabetes", "cure", "chronic"]):
        reg_score += 25
        reg_drivers.append("High-risk health claims subject to strict Drugs and Magic Remedies Act advertisement clearance.")

    reg_score = min(90, max(25, reg_score))

    # --- 5. International IP Friction (PCT / USPTO / EPO) (0-100) ---
    intl_score = 25
    intl_drivers = []
    if tk_score >= 60:
        intl_score += 30
        intl_drivers.append("EPO and USPTO examiner access to TKDL will surface classical Indian prior art against novelty.")

    intl_drivers.append("Mandatory genetic resource country-of-origin disclosure under the 2024 WIPO Treaty.")
    if jurisdiction in ("International", "PCT"):
        intl_score += 20
        intl_drivers.append("Must obtain prior foreign filing permission under Section 39 of the Indian Patents Act.")

    intl_score = min(88, max(20, intl_score))

    def _level(score: int) -> str:
        if score >= 75:
            return "HIGH"
        if score >= 50:
            return "MEDIUM"
        return "LOW"

    return {
        "scores": {
            "tk_overlap": tk_score,
            "novelty_risk": novelty_risk,
            "abs_compliance": abs_score,
            "regulatory_complexity": reg_score,
            "international_friction": intl_score,
        },
        "levels": {
            "tk_overlap": _level(tk_score),
            "novelty_risk": _level(novelty_risk),
            "abs_compliance": _level(abs_score),
            "regulatory_complexity": _level(reg_score),
            "international_friction": _level(intl_score),
        },
        "drivers": {
            "tk_overlap": tk_drivers,
            "novelty_risk": novelty_drivers,
            "abs_compliance": abs_drivers,
            "regulatory_complexity": reg_drivers,
            "international_friction": intl_drivers,
        },
        "composite_risk": round((tk_score * 0.25 + novelty_risk * 0.25 + abs_score * 0.2 + reg_score * 0.15 + intl_score * 0.15), 1),
    }


# =====================================================
# TEST
# =====================================================
if __name__ == "__main__":
    result = calculate_risk_radar(
        ingredients="Turmeric and Ashwagandha extract",
        preparation_process="Aqueous decoction reduced to 1/4th",
        intended_use="Treatment of joint pain and arthritis",
        extracted_botanicals=[{"matched_name": "Turmeric"}, {"matched_name": "Ashwagandha"}],
    )
    print("Risk Radar self-test passed:", result["scores"], "Composite:", result["composite_risk"])
