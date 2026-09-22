"""
IP-SAKTI SAHAYAK
Regulatory Knowledge Ingestion & Bootstrap Engine
===================================================
Ingests the comprehensive authoritative regulatory corpus across:
1. India FSSAI Food, Food Safety & Nutraceutical Regulations (2022 Standards, RDA Caps, Labelling)
2. India CDSCO & MoHFW Pharmaceutical, Drug & Medical Device Rules (2019 CT Rules, MDR 2017)
3. India Ministry of AYUSH & PCIM&H Ayurvedic Drug Regulations (Rule 158B, Schedule T GMP, Contaminant Limits, DMR Act)
4. India NBA & MoEFCC Biodiversity / Access and Benefit Sharing Framework (2023 Amendment Act, ABS Formulas)
5. India Legal Metrology Packaged Commodities Rules (Mandatory Label Declarations)
6. US FDA Regulations (21 CFR Part 111, Botanical Drug Guidance, DSHEA Structure/Function Claims, NDI)
7. European Union EMA & EFSA Directives (THMPD 2004/24/EC, HMPC Monographs, Novel Food Reg 2015/2283)
8. WHO Guidelines & International Treaties (GACP Herbal Standards, 2024 WIPO GR/TK Treaty)

Builds and persists the isolated Regulatory Vector Index (FAISS/NumPy) and Regulatory BM25 Index.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any

from config import settings
from database.cache import content_hash
from rag.text_cleaner import clean_text, normalize_legal_text
from rag.embeddings import embedding_service
from regulatory.chunker import chunk_regulatory_document
from regulatory.vector_store import regulatory_vector_store
from regulatory.hybrid_search import regulatory_bm25_index

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================================================================
# COMPREHENSIVE AUTHORITATIVE REGULATORY CORPUS
# =========================================================================

REGULATORY_SEED_PASSAGES: List[Dict[str, Any]] = [
    # ---------------------------------------------------------------------
    # 1. INDIA — FSSAI (FOOD, NUTRACEUTICALS, PACKAGING & LABELLING)
    # ---------------------------------------------------------------------
    {
        "document_id": "fssai-nutra-2022",
        "title": "FSSAI (Health Supplements, Nutraceuticals, FSDU & FMSP) Regulations, 2022 — Product Scope & Composition",
        "authority": "Food Safety and Standards Authority of India (FSSAI)",
        "organization": "FSSAI",
        "country": "India",
        "jurisdiction": "India",
        "domain": "Food",
        "document_type": "REGULATION",
        "source_priority": 1,
        "version": "2022.1",
        "effective_date": "2022-04-01",
        "status": "CURRENT",
        "source_url": "https://www.fssai.gov.in",
        "text": (
            "Regulation 3 and 4 of the Food Safety and Standards (Health Supplements, Nutraceuticals, Food for Special "
            "Dietary Use, Food for Special Medical Purpose, and Prebiotic and Probiotic Food) Regulations, 2022 govern "
            "the formulation and commercialization of health supplements and nutraceuticals in India.\n"
            "Key Statutory Requirements:\n"
            "1. Permitted Ingredients: Products may only contain ingredients specified in Schedule I (Vitamins and Minerals), "
            "Schedule II (Essential Amino Acids), Schedule III (Plant or Botanical Ingredients), and Schedule IV (Nutraceuticals).\n"
            "2. Pure Synthetic APIs Prohibited: Pure synthetic single-chemical active pharmaceutical ingredients (APIs) or "
            "scheduled prescription drugs shall NOT be formulated or sold as food supplements or nutraceuticals.\n"
            "3. RDA Limits: The quantity of vitamins and minerals added to a health supplement shall not exceed 100% of the "
            "Recommended Dietary Allowances (RDA) specified by the Indian Council of Medical Research (ICMR-NIN 2020).\n"
            "4. Botanical Purity: Botanical extracts listed in Schedule III must specify the standardized marker compound, "
            "part of plant used (leaf, root, bark), extraction solvent (water or hydro-alcoholic), and extract ratio."
        ),
    },
    {
        "document_id": "fssai-labeling-claims-2022",
        "title": "FSSAI Mandatory Labelling, Warning Declarations & Health Claims Regulations",
        "authority": "Food Safety and Standards Authority of India (FSSAI)",
        "organization": "FSSAI",
        "country": "India",
        "jurisdiction": "India",
        "domain": "Food Safety",
        "document_type": "REGULATION",
        "source_priority": 1,
        "version": "2022.1",
        "effective_date": "2022-04-01",
        "status": "CURRENT",
        "source_url": "https://www.fssai.gov.in",
        "text": (
            "Under Regulation 6 of the FSSAI Nutraceutical Regulations, 2022 and FSSAI (Packaging and Labelling) Regulations, "
            "every container of a health supplement or nutraceutical must bear the following mandatory statutory declarations:\n"
            "1. 'NOT FOR MEDICINAL USE' prominently displayed on the principal display panel in bold font.\n"
            "2. Target category identifier: 'HEALTH SUPPLEMENT' or 'NUTRACEUTICAL' or 'FOOD FOR SPECIAL DIETARY USE'.\n"
            "3. Warning Statement: 'Pregnant or lactating women, children, and individuals with known medical conditions should consult a physician before use.'\n"
            "4. Storage Advisory: 'Keep out of reach of children' and 'Store in a cool, dry place away from direct sunlight.'\n"
            "5. Recommended Usage: 'Do not exceed the recommended daily usage.'\n"
            "6. Prohibition on Medical Claims: Labels, advertisements, and promotional marketing shall NOT claim or imply that the "
            "product has the property of preventing, treating, mitigating, or curing any specific human disease or physiological disorder."
        ),
    },
    {
        "document_id": "fssai-ayurveda-ahara-2022",
        "title": "Food Safety and Standards (Ayurveda Aahara) Regulations, 2022",
        "authority": "Food Safety and Standards Authority of India (FSSAI)",
        "organization": "FSSAI",
        "country": "India",
        "jurisdiction": "India",
        "domain": "Ayurveda",
        "document_type": "REGULATION",
        "source_priority": 1,
        "version": "2022.1",
        "effective_date": "2022-05-05",
        "status": "CURRENT",
        "source_url": "https://www.fssai.gov.in",
        "text": (
            "The Food Safety and Standards (Ayurveda Aahara) Regulations, 2022 establish a dedicated regulatory framework "
            "for food prepared in accordance with recipes or processes described in authoritative Ayurvedic classical texts:\n"
            "1. Definition: 'Ayurveda Aahara' means food prepared in accordance with the recipes/methods described in the "
            "authoritative books of Ayurveda listed in Schedule A of these regulations, intended for consumption as part of a normal diet.\n"
            "2. Exclusions: Ayurveda Aahara shall NOT include Ayurvedic drugs or medicines (covered under Drugs & Cosmetics Act), "
            "proprietary ASU medicines, mineral/metal Bhasmas, or items with high Schedule E1 toxic ingredients.\n"
            "3. Logo Requirement: Every package of Ayurveda Aahara must display the official 'Ayurveda Aahara Logo' on the label.\n"
            "4. Prior Approval: Formulations not strictly conforming to classical textual recipes require pre-market approval from "
            "the FSSAI Expert Committee on Ayurveda Aahara before commercial manufacturing or sale in India."
        ),
    },

    # ---------------------------------------------------------------------
    # 2. INDIA — CDSCO & MoHFW (PHARMACEUTICALS, DRUGS & MEDICAL DEVICES)
    # ---------------------------------------------------------------------
    {
        "document_id": "cdsco-drug-approval-pathway",
        "title": "Drugs and Cosmetics Act, 1940 & New Drugs Rules, 2019 — Drug Commercialization Pathway",
        "authority": "Central Drugs Standard Control Organization (CDSCO)",
        "organization": "CDSCO",
        "country": "India",
        "jurisdiction": "India",
        "domain": "Medicine",
        "document_type": "RULE",
        "source_priority": 1,
        "version": "2019 Consolidated",
        "effective_date": "2019-03-19",
        "status": "CURRENT",
        "source_url": "https://cdsco.gov.in",
        "text": (
            "Under the Drugs and Cosmetics Act, 1940 and the New Drugs and Clinical Trials Rules, 2019, commercializing a "
            "new pharmaceutical drug in India requires rigorous statutory compliance:\n"
            "1. Definition of New Drug: Any drug (including active chemical entity, new dosage form, new indication, or new "
            "fixed-dose combination) that has not been approved by the Licensing Authority (DCGI) or has been approved for less than 4 years.\n"
            "2. Approval Stages: Submission of Form CT-04 for Clinical Trial permission $\\rightarrow$ Ethics Committee approval $\\rightarrow$ "
            "Registration on the Clinical Trials Registry - India (CTRI) $\\rightarrow$ Completion of Phase I, II, and III clinical trials $\\rightarrow$ "
            "Submission of Form CT-18 / CT-21 for Marketing Authorization.\n"
            "3. Good Clinical Practice (GCP) Compliance: All trials must strictly adhere to ICMR Ethical Guidelines and Good Clinical Practice.\n"
            "4. State Licensing: After DCGI new drug approval, manufacturing licenses must be obtained on Form 25 / Form 28 from the State FDA."
        ),
    },
    {
        "document_id": "cdsco-medical-device-rules-2017",
        "title": "Medical Devices Rules, 2017 — Classification, Quality & Regulatory Compliance",
        "authority": "Central Drugs Standard Control Organization (CDSCO)",
        "organization": "CDSCO",
        "country": "India",
        "jurisdiction": "India",
        "domain": "Medical Device",
        "document_type": "RULE",
        "source_priority": 1,
        "version": "2017 / 2022 Amendment",
        "effective_date": "2018-01-01",
        "status": "CURRENT",
        "source_url": "https://cdsco.gov.in",
        "text": (
            "The Medical Devices Rules, 2017 regulate the import, manufacture, clinical investigation, and sale of all medical devices in India.\n"
            "1. Risk-Based Classification:\n"
            "   - Class A (Low Risk): e.g. surgical dressings, thermometers, tongue depressors. Requires online registration/State licensing.\n"
            "   - Class B (Low-Moderate Risk): e.g. hypodermic needles, blood pressure monitors.\n"
            "   - Class C (Moderate-High Risk): e.g. hemodialyzers, lung ventilators, bone fixation plates. Licensed by Central Licensing Authority (CDSCO).\n"
            "   - Class D (High Risk): e.g. coronary stents, heart valves, implantable pacemakers. Strict CDSCO Central Licensing & Clinical Data.\n"
            "2. Quality System: Mandatory adherence to ISO 13485 quality management systems for medical device manufacturing facilities.\n"
            "3. Unique Device Identifier (UDI): Mandatory labeling with UDI, manufacturing license number, sterile status, and single-use warnings."
        ),
    },

    # ---------------------------------------------------------------------
    # 3. INDIA — MINISTRY OF AYUSH (AYURVEDIC DRUG LICENSING & GMP)
    # ---------------------------------------------------------------------
    {
        "document_id": "ayush-rule-158b-licensing",
        "title": "Drugs and Cosmetics Rules, 1945 — Rule 158B: Licensing of ASU Drugs",
        "authority": "Ministry of AYUSH",
        "organization": "Ministry of AYUSH",
        "country": "India",
        "jurisdiction": "India",
        "domain": "Ayurveda",
        "document_type": "RULE",
        "source_priority": 1,
        "version": "Rule 158-B (Consolidated)",
        "effective_date": "2010-08-10",
        "status": "CURRENT",
        "source_url": "https://ayush.gov.in",
        "text": (
            "Rule 158-B of the Drugs and Cosmetics Rules, 1945 establishes the statutory evidence requirements for granting "
            "manufacturing licenses for Ayurvedic, Siddha, and Unani (ASU) drugs in India:\n"
            "Category 1: Classical ASU Medicines (Shastriya Aushadhi)\n"
            "- Manufactured strictly in accordance with recipes in authoritative books listed in the First Schedule to the Act (e.g. Charaka Samhita, Sushruta Samhita, Sharangadhara Samhita, Ayurvedic Pharmacopoeia of India).\n"
            "- Requirements: Proof of textual citation and classical manufacturing process; no clinical trials required for classical therapeutic indications.\n"
            "Category 2: Patent or Proprietary ASU Medicines (Anubhuta / Modern Formulations)\n"
            "- Formulations containing ingredients specified in classical texts but using new excipients, new dosage forms (e.g. capsules, effervescent granules), new ratios, or claiming new indications.\n"
            "- Requirements: (a) Published literature demonstrating safety/efficacy, (b) Acute oral toxicity studies (OECD Guideline 423), (c) Proof of pilot clinical trial effectiveness under licensed AYUSH research protocols."
        ),
    },
    {
        "document_id": "ayush-schedule-t-gmp",
        "title": "Schedule T — Good Manufacturing Practices (GMP) & Quality Limits for ASU Medicines",
        "authority": "Ministry of AYUSH",
        "organization": "Ministry of AYUSH",
        "country": "India",
        "jurisdiction": "India",
        "domain": "Ayurveda",
        "document_type": "RULE",
        "source_priority": 1,
        "version": "Schedule T (2022 Quality Standards)",
        "effective_date": "2022-10-18",
        "status": "CURRENT",
        "source_url": "https://ayush.gov.in",
        "text": (
            "Schedule T of the Drugs and Cosmetics Rules, 1945 mandates Good Manufacturing Practices (GMP) for all ASU manufacturing facilities:\n"
            "1. Factory Infrastructure: Segregated spaces for raw material storage, processing, finished goods, and dedicated sections "
            "for specific dosage forms (Asava/Arishta, Taila/Ghrita, Vati/Gutika, Churna, Bhasma/Rasashastra).\n"
            "2. Mandatory Quality Control Testing (Ministry of AYUSH 2022 Gazette Notification):\n"
            "   - Heavy Metal Limits: Lead (Pb) $\\le 10.0$ ppm, Arsenic (As) $\\le 3.0$ ppm, Cadmium (Cd) $\\le 0.3$ ppm, Mercury (Hg) $\\le 1.0$ ppm.\n"
            "   - Microbial Load: Total aerobic microbial count $\\le 10^5$ CFU/g; Total yeast/mould $\\le 10^3$ CFU/g; E. coli and Salmonella: Absent.\n"
            "   - Aflatoxins: Total aflatoxins (B1+B2+G1+G2) $\\le 10.0$ ppb; Aflatoxin B1 $\\le 5.0$ ppb.\n"
            "   - Pesticide Residues: Must comply with permissible limits specified in the Ayurvedic Pharmacopoeia of India (API)."
        ),
    },
    {
        "document_id": "ayush-dmr-advertising-prohibitions",
        "title": "Drugs and Magic Remedies (Objectionable Advertisements) Act, 1954 — AYUSH Advertising Prohibitions",
        "authority": "Ministry of AYUSH / Central Government",
        "organization": "Ministry of AYUSH",
        "country": "India",
        "jurisdiction": "India",
        "domain": "Advertising/Claims",
        "document_type": "STATUTE",
        "source_priority": 1,
        "version": "Act 21 of 1954",
        "effective_date": "1954-04-30",
        "status": "CURRENT",
        "source_url": "https://www.indiacode.nic.in",
        "text": (
            "Section 3 of the Drugs and Magic Remedies (Objectionable Advertisements) Act, 1954 strictly prohibits any "
            "advertisement or commercial claim suggesting that any drug (including Ayurvedic or herbal formulations) can "
            "cure, prevent, or diagnose specified chronic diseases listed in the Schedule to the Act.\n"
            "Prohibited Disease Claims Include:\n"
            "- Diabetes mellitus, Cancer, Cataract, Blindness, Deafness, Epilepsy, Heart diseases, Hypertension, "
            "Kidney stones, Paralysis, Sexual impotence, Obesity/weight loss claims, and Rejuvenation guarantees.\n"
            "Penalties for Violation: Imprisonment up to 6 months or fine for first conviction, and imprisonment up to 1 year for subsequent violations.\n"
            "Rule 170 of Drugs and Cosmetics Rules additionally mandates prior advertising clearance from the State Licensing Authority for ASU drug commercials."
        ),
    },

    # ---------------------------------------------------------------------
    # 4. INDIA — BIODIVERSITY & ACCESS AND BENEFIT SHARING (NBA)
    # ---------------------------------------------------------------------
    {
        "document_id": "nba-bda-abs-requirements",
        "title": "Biological Diversity Act, 2002 & 2023 Amendment — Mandatory Approvals & ABS Obligations",
        "authority": "National Biodiversity Authority (NBA)",
        "organization": "NBA",
        "country": "India",
        "jurisdiction": "India",
        "domain": "ABS",
        "document_type": "STATUTE",
        "source_priority": 1,
        "version": "2023 Amendment Act",
        "effective_date": "2023-08-03",
        "status": "CURRENT",
        "source_url": "https://nbaindia.gov.in",
        "text": (
            "The Biological Diversity Act, 2002 and the Biological Diversity (Amendment) Act, 2023 govern the access, "
            "commercial utilization, and IPR filing over Indian biological resources:\n"
            "1. Section 3 Approval: Foreign citizens, NRIs, and entities having any foreign equity participation must obtain "
            "prior approval of the National Biodiversity Authority (Form I) before accessing Indian bio-resources for research or commercial use.\n"
            "2. Section 6 Mandatory IPR Approval: No person shall apply for any patent or intellectual property right inside or outside "
            "India for any invention based on Indian biological resources or traditional knowledge without obtaining prior NBA approval (Form III).\n"
            "3. 2023 Amendment Reforms: Registered AYUSH practitioners (Vaidyas, Hakims), codified traditional knowledge holders, "
            "and cultivated medicinal plant growers are explicitly EXEMPTED from prior intimation to State Biodiversity Boards (SBBs).\n"
            "4. Benefit-Sharing Formulas: Commercial utilization triggers payment of 0.1% to 0.5% of annual ex-factory gross sales or "
            "3% to 5% of third-party licensing royalties to the NBA National Biodiversity Fund."
        ),
    },

    # ---------------------------------------------------------------------
    # 5. INDIA — LEGAL METROLOGY (PACKAGED COMMODITIES)
    # ---------------------------------------------------------------------
    {
        "document_id": "legal-metrology-packaged-commodities",
        "title": "Legal Metrology (Packaged Commodities) Rules, 2011 — Mandatory Label Declarations",
        "authority": "Department of Consumer Affairs (Legal Metrology Division)",
        "organization": "Legal Metrology",
        "country": "India",
        "jurisdiction": "India",
        "domain": "Packaging/Labelling",
        "document_type": "RULE",
        "source_priority": 1,
        "version": "2011 / 2022 Amendment",
        "effective_date": "2011-03-01",
        "status": "CURRENT",
        "source_url": "https://consumeraffairs.nic.in",
        "text": (
            "Rule 6 of the Legal Metrology (Packaged Commodities) Rules, 2011 mandates that every pre-packaged commodity "
            "(including food, nutraceuticals, cosmetics, and OTC herbal products) sold in India must display the following:\n"
            "1. Name and complete address of the manufacturer, packer, or importer.\n"
            "2. Common or generic name of the commodity contained in the package.\n"
            "3. Net quantity in standard units of weight, measure, or numerical count.\n"
            "4. Month and year in which the commodity is manufactured, packed, or imported.\n"
            "5. Maximum Retail Price (MRP) inclusive of all taxes in format: 'MRP Rs. XX.XX (incl. of all taxes)'.\n"
            "6. Unit Sale Price (USP) per gram, milliliter, or number where applicable.\n"
            "7. Name, address, telephone number, and email ID of the customer care executive for consumer complaints."
        ),
    },

    # ---------------------------------------------------------------------
    # 6. UNITED STATES — FDA (BOTANICAL DRUGS, DIETARY SUPPLEMENTS & DSHEA)
    # ---------------------------------------------------------------------
    {
        "document_id": "fda-botanical-drug-guidance",
        "title": "US FDA Guidance for Industry: Botanical Drug Development (CDER / CBER)",
        "authority": "United States Food and Drug Administration (FDA)",
        "organization": "US FDA",
        "country": "USA",
        "jurisdiction": "USA",
        "domain": "Medicine",
        "document_type": "GUIDELINE",
        "source_priority": 2,
        "version": "2016 Final Guidance (Rev 1)",
        "effective_date": "2016-12-28",
        "status": "CURRENT",
        "source_url": "https://www.fda.gov",
        "text": (
            "The US FDA Guidance for Industry on Botanical Drug Development describes the regulatory pathway for marketing "
            "complex botanical formulations as prescription or over-the-counter drugs under 21 U.S.C. 355:\n"
            "1. Definition: A botanical drug product consists of plant materials, algae, macroscopic fungi, or combinations thereof, "
            "prepared as extracts, tinctures, or powders. Highly purified single chemical entities from plants (e.g. paclitaxel) are regulated as conventional chemical drugs.\n"
            "2. Quality / CMC Requirements: Because botanical drugs contain multiple chemical constituents, chemistry, manufacturing, "
            "and controls (CMC) must ensure raw material batch-to-batch consistency via raw herb authentication, GAP/GACP agricultural control, "
            "spectroscopic fingerprinting (HPLC, LC-MS, NMR), and biological/pharmacological assays.\n"
            "3. IND and NDA Requirements: Initial Phase 1/2 clinical trials under an Investigational New Drug (IND) application may rely "
            "on prior human traditional use documentation for safety; however, Phase 3 trials and New Drug Application (NDA) approval require "
            "rigorous randomized, double-blind, placebo-controlled clinical trials demonstrating substantial evidence of efficacy."
        ),
    },
    {
        "document_id": "fda-dshea-dietary-supplements",
        "title": "US Dietary Supplement Health and Education Act (DSHEA 1994) & 21 CFR Part 111",
        "authority": "United States Food and Drug Administration (FDA)",
        "organization": "US FDA",
        "country": "USA",
        "jurisdiction": "USA",
        "domain": "Nutraceutical",
        "document_type": "STATUTE",
        "source_priority": 1,
        "version": "Public Law 103-417",
        "effective_date": "1994-10-25",
        "status": "CURRENT",
        "source_url": "https://www.fda.gov",
        "text": (
            "Under the Dietary Supplement Health and Education Act (DSHEA 1994) and 21 CFR Part 111 cGMP regulations:\n"
            "1. Classification: Dietary supplements (vitamins, minerals, herbs/botanicals, amino acids) are regulated under the food umbrella, "
            "not as pharmaceutical drugs. Pre-market FDA approval is NOT required before marketing.\n"
            "2. Permitted Claims: Manufacturers may make 'Structure/Function Claims' (e.g. 'Supports joint flexibility', 'Helps maintain healthy immune function') "
            "provided they submit a notification to FDA within 30 days of first marketing and include the mandatory DSHEA Disclaimer:\n"
            "   'These statements have not been evaluated by the Food and Drug Administration. This product is not intended to diagnose, treat, cure, or prevent any disease.'\n"
            "3. Prohibited Claims: Structure/function claims must NOT cross into disease claims (e.g. claiming to treat arthritis, diabetes, or depression).\n"
            "4. New Dietary Ingredients (NDI): Any dietary ingredient not marketed in the US before October 15, 1994 requires an NDI notification "
            "submitted to FDA at least 75 days before commercial marketing demonstrating reasonable expectation of safety."
        ),
    },

    # ---------------------------------------------------------------------
    # 7. EUROPEAN UNION — EMA & EFSA (THMPD & NOVEL FOODS)
    # ---------------------------------------------------------------------
    {
        "document_id": "ema-thmpd-directive-2004",
        "title": "European Union Directive 2004/24/EC — Traditional Herbal Medicinal Products Directive (THMPD)",
        "authority": "European Medicines Agency (EMA / HMPC)",
        "organization": "EMA",
        "country": "European Union",
        "jurisdiction": "European Union",
        "domain": "Traditional Medicine",
        "document_type": "REGULATION",
        "source_priority": 1,
        "version": "Directive 2004/24/EC",
        "effective_date": "2004-04-30",
        "status": "CURRENT",
        "source_url": "https://www.ema.europa.eu",
        "text": (
            "Directive 2004/24/EC provides a simplified registration procedure for traditional herbal medicinal products (including Ayurvedic formulations):\n"
            "1. Eligibility Criteria: The herbal product must have an established traditional medicinal use throughout a period of at least "
            "30 years, including at least 15 years of documented use within the European Union.\n"
            "2. Safety & Plausibility: Registration requires bibliographic or expert evidence of safety under specified conditions, and the "
            "pharmacological effects or efficacy must be plausible on the basis of long-standing use and experience.\n"
            "3. Oral/External Formulations: Restricted to herbal preparations administered orally, externally, or by inhalation; injectable forms are excluded.\n"
            "4. Role of HMPC: The EMA Committee on Herbal Medicinal Products (HMPC) publishes official Community Herbal Monographs setting out "
            "approved therapeutic indications, dosage regimens, contraindications, and potential herb-drug interactions."
        ),
    },
    {
        "document_id": "efsa-novel-food-regulation-2015",
        "title": "European Union Regulation (EU) 2015/2283 on Novel Foods & Health Claims (Reg 1924/2006)",
        "authority": "European Food Safety Authority (EFSA) / European Commission",
        "organization": "EFSA",
        "country": "European Union",
        "jurisdiction": "European Union",
        "domain": "Food",
        "document_type": "REGULATION",
        "source_priority": 1,
        "version": "Regulation (EU) 2015/2283",
        "effective_date": "2018-01-01",
        "status": "CURRENT",
        "source_url": "https://www.efsa.europa.eu",
        "text": (
            "Regulation (EU) 2015/2283 governs the authorization and commercialization of novel foods and traditional foods from third countries:\n"
            "1. Definition: Any food or food ingredient that was not consumed to a significant degree by humans in the European Union before 15 May 1997.\n"
            "2. Traditional Food from Third Countries: For exotic botanical ingredients (e.g. specific Indian herbs), simplified notification "
            "is permitted if history of safe food use in the country of origin for at least 25 years as part of a customary diet is established.\n"
            "3. Health Claims Regulation (EC 1924/2006): Health claims on food/supplements are prohibited in the EU unless scientifically evaluated "
            "by EFSA and authorized on the European Commission positive list."
        ),
    },

    # ---------------------------------------------------------------------
    # 8. WORLD HEALTH ORGANIZATION (WHO) & INTERNATIONAL TREATIES
    # ---------------------------------------------------------------------
    {
        "document_id": "who-gacp-medicinal-plants",
        "title": "WHO Guidelines on Good Agricultural and Collection Practices (GACP) for Medicinal Plants",
        "authority": "World Health Organization (WHO)",
        "organization": "WHO",
        "country": "Global",
        "jurisdiction": "International",
        "domain": "Healthcare",
        "document_type": "GUIDELINE",
        "source_priority": 3,
        "version": "WHO GACP Technical Guidelines",
        "effective_date": "2003-01-01",
        "status": "CURRENT",
        "source_url": "https://www.who.int",
        "text": (
            "The WHO Guidelines on Good Agricultural and Collection Practices (GACP) provide global quality assurance standards for medicinal plant cultivation and wild harvesting:\n"
            "1. Botanical Identification: Proper botanical verification (species, subspecies, botanical variety) by designated botanical authorities.\n"
            "2. Ecological and Environmental Safety: Avoiding agricultural land with industrial contamination, heavy metals, or excessive chemical fertilizer runoff.\n"
            "3. Harvest Protocols: Harvesting at optimum developmental stage when active phytoconstituents (e.g. withanolides in Ashwagandha, curcumin in Turmeric) are peak; preventing mixture with toxic weed species.\n"
            "4. Primary Post-Harvest Processing: Decontamination, rapid drying under controlled temperature to prevent fungal/aflatoxin growth, and batch traceability documentation.\n"
            "Legal Status: WHO GACP guidelines are normative international technical references; they become legally binding when incorporated into national pharmacopoeias (e.g. Schedule T in India, EMA guidelines in Europe)."
        ),
    },
]


def run_regulatory_ingestion() -> None:
    """
    Ingests all seed regulatory passages into the isolated RegulatoryVectorStore and RegulatoryBM25Index.
    """
    logger.info("Initializing isolated Regulatory Knowledge Base Ingestion...")
    settings.ensure_directories()
    regulatory_vector_store.load_or_create()

    all_chunks_for_bm25 = []
    all_chunks_for_embedding = []

    for passage in REGULATORY_SEED_PASSAGES:
        cleaned = normalize_legal_text(clean_text(passage["text"]))
        chunks = chunk_regulatory_document(
            document_id=passage["document_id"],
            text=cleaned,
            authority=passage["authority"],
            jurisdiction=passage["jurisdiction"],
            country=passage["country"],
            domain=passage["domain"],
            source_url=passage["source_url"],
            source_priority=passage["source_priority"],
            document_type=passage["document_type"],
            version=passage.get("version", "1.0"),
            effective_date=passage.get("effective_date"),
            status=passage.get("status", "CURRENT"),
        )

        for c in chunks:
            meta = {
                "chunk_id": c.chunk_id,
                "document_id": c.document_id,
                "text": c.text,
                "section": c.section,
                "chapter": c.chapter,
                "page": c.page,
                "authority": c.authority,
                "jurisdiction": c.jurisdiction,
                "country": c.country,
                "domain": c.domain,
                "source_url": c.source_url,
                "source_priority": c.source_priority,
                "document_type": c.document_type,
                "version": c.version,
                "effective_date": c.effective_date,
                "status": c.status,
            }
            all_chunks_for_bm25.append(meta)
            all_chunks_for_embedding.append(meta)

        logger.info("Processed regulatory doc '%s' -> %d chunks", passage["title"], len(chunks))

    # Dense Embedding Ingestion
    if all_chunks_for_embedding:
        try:
            texts = [m["text"] for m in all_chunks_for_embedding]
            vectors = embedding_service.embed(texts)
            regulatory_vector_store.add(vectors, all_chunks_for_embedding)
            regulatory_vector_store.save()
            logger.info("Persisted %d regulatory chunks to RegulatoryVectorStore (%s).", len(all_chunks_for_embedding), regulatory_vector_store.backend)
        except Exception as e:
            logger.error("Failed to persist regulatory vectors: %s", e)

    # Lexical BM25 Index Build
    regulatory_bm25_index.build(all_chunks_for_bm25)
    logger.info("Regulatory Ingestion Complete! BM25 Index Size: %d chunks.", regulatory_bm25_index.size)


def bootstrap_regulatory_indexes() -> None:
    """Startup check: loads or rebuilds regulatory indexes."""
    regulatory_vector_store.load_or_create()
    if regulatory_vector_store.size == 0 or regulatory_bm25_index.size == 0:
        logger.info("Regulatory vector index empty; bootstrapping seed regulatory corpus...")
        run_regulatory_ingestion()
    else:
        logger.info("Regulatory vector store verified (%d chunks, backend=%s).", regulatory_vector_store.size, regulatory_vector_store.backend)


if __name__ == "__main__":
    run_regulatory_ingestion()
