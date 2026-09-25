"""
IP-SAKTI SAHAYAK
Ingestion & Knowledge Base Bootstrap
=====================================
Builds the comprehensive local knowledge cache:
Loads statutory, medical, Ayurvedic pharmacopoeial, and TK texts across:
1. Indian Patents Act, 1970 (Sections 3(d), 3(p), 3(e), 3(h), 3(j), 10, 25, 64)
2. Biological Diversity Act, 2002 & Biological Diversity (Amendment) Act, 2023 (NBA & ABS)
3. PCIM&H (Pharmacopoeia Commission for Indian Medicine & Homoeopathy) — API/AFI Monographs & Raw Drug Standards
4. Ministry of AYUSH & Drugs and Cosmetics Act (Rule 158B, Schedule T GMP)
5. Traditional Knowledge Digital Library (TKDL) & Classical Text Prior Art (Charaka, Sushruta, Trikatu, Triphala)
6. PubMed & Biomedical Literature — Phytochemistry, Pharmacology & Clinical Trial Evidence
7. International IP Treaties (WIPO PCT, TRIPS, Nagoya Protocol, WIPO 2024 Genetic Resources Treaty)
8. FSSAI Ayurveda-Aahara Regulations 2022 & CDSCO Phytopharmaceutical Guidelines
9. Landmark TK Patent Precedents (Turmeric, Neem, Basmati, Novartis)

Cleans, chunks with legal section awareness, embeds with BAAI/bge-m3,
and populates FAISS + BM25 + SQLite Document/DocumentChunk tables.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any

from config import settings
from database.db import init_db, get_session
from database.models import Document, DocumentChunk, Source
from database.cache import content_hash, new_expiry
from rag.text_cleaner import clean_text, normalize_legal_text
from rag.chunker import chunk_document
from rag.embeddings import embedding_service
from rag.vector_store import vector_store, VectorStoreUnavailableError
from rag.hybrid_search import bm25_index

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================================================================
# COMPREHENSIVE AUTHORITATIVE LEGAL, MEDICAL & AYURVEDA CORPUS
# =========================================================================

SEED_PASSAGES: List[Dict[str, Any]] = [
    # ---------------------------------------------------------------------
    # 1. INDIAN PATENTS ACT, 1970
    # ---------------------------------------------------------------------
    {
        "title": "Patents Act, 1970 — Section 3(d): Incremental Inventions & Efficacy",
        "authority": "IP India (CGPDTM)",
        "jurisdiction": "India",
        "domain": "Patent",
        "url": "https://ipindia.gov.in",
        "text": (
            "Section 3(d) of the Patents Act, 1970 provides that the following are not inventions within "
            "the meaning of the Act: 'the mere discovery of a new form of a known substance which does not "
            "result in the enhancement of the known efficacy of that substance or the mere discovery of any "
            "new property or new use for a known substance or of the mere use of a known process, machine or "
            "apparatus unless such known process results in a new product or employs at least one new reactant.'\n"
            "Explanation to Section 3(d): For the purposes of this clause, salts, esters, ethers, polymorphs, "
            "metabolites, pure form, particle size, isomers, mixtures of isomers, complexes, combinations and "
            "other derivatives of known substance shall be considered to be the same substance, unless they differ "
            "significantly in properties with regard to therapeutic efficacy."
        ),
    },
    {
        "title": "Patents Act, 1970 — Section 3(p): Traditional Knowledge Exclusion",
        "authority": "IP India (CGPDTM)",
        "jurisdiction": "India",
        "domain": "Traditional Knowledge",
        "url": "https://ipindia.gov.in",
        "text": (
            "Section 3(p) of the Patents Act, 1970 explicitly excludes from patentability: 'an invention which in "
            "effect, is traditional knowledge or which is an aggregation or duplication of known properties of "
            "traditionally known component or components.'\n"
            "This statutory bar ensures that traditional medicinal knowledge—such as Ayurvedic, Siddha, Unani, or "
            "tribal remedies documented in classical texts or oral tradition—cannot be monopolized as patent rights "
            "in India. To overcome Section 3(p), an applicant must demonstrate substantial technical novelty, unexpected "
            "synergism, or non-obvious inventive modifications beyond classical preparations."
        ),
    },
    {
        "title": "Patents Act, 1970 — Section 3(e): Mere Admixture Bar",
        "authority": "IP India (CGPDTM)",
        "jurisdiction": "India",
        "domain": "Patent",
        "url": "https://ipindia.gov.in",
        "text": (
            "Section 3(e) of the Patents Act, 1970 excludes from patentability: 'a substance obtained by a mere "
            "admixture resulting only in the aggregation of the properties of the components thereof or a process "
            "for producing such substance.'\n"
            "In Ayurvedic polyherbal formulations, combining known herbs (e.g. Ashwagandha + Turmeric) is treated "
            "as a mere admixture under Section 3(e) unless experimental data or clinical trials prove synergistic "
            "bio-enhancement or therapeutic activity exceeding the sum of individual components."
        ),
    },
    {
        "title": "Patents Act, 1970 — Section 3(h) and 3(j): Agriculture & Biological Processes",
        "authority": "IP India (CGPDTM)",
        "jurisdiction": "India",
        "domain": "Patent",
        "url": "https://ipindia.gov.in",
        "text": (
            "Section 3(h) of the Patents Act, 1970 excludes 'a method of agriculture or horticulture.'\n"
            "Section 3(j) excludes 'plants and animals in whole or any part thereof other than micro-organisms; but "
            "including seeds, varieties and species and essentially biological processes for production or propagation "
            "of plants and animals.'\n"
            "Medicinal plant varieties, herbal cultivation methods, and natural harvesting techniques cannot be patented; "
            "plant varieties may instead be protected under the Protection of Plant Varieties and Farmers' Rights (PPV&FR) Act, 2001."
        ),
    },
    {
        "title": "Patents Act, 1970 — Section 25 & Section 64: Oppositions and Revocation on TK Grounds",
        "authority": "IP India (CGPDTM)",
        "jurisdiction": "India",
        "domain": "Patent",
        "url": "https://ipindia.gov.in",
        "text": (
            "Under Section 25(1)(k) [Pre-Grant Opposition] and Section 25(2)(k) [Post-Grant Opposition] of the Patents Act, 1970, "
            "a patent application or granted patent may be opposed on the ground 'that the invention so far as claimed in any claim "
            "of the complete specification was not an invention within the meaning of this Act, or was not patentable under this Act, "
            "including that the invention was anticipated having regard to the knowledge, oral or otherwise, available within any "
            "local or indigenous community in India or elsewhere.'\n"
            "Section 64(1)(p) and 64(1)(q) provide statutory grounds for revocation of a patent by the High Court if the complete "
            "specification does not disclose or wrongly mentions the source or geographical origin of biological material used for "
            "the invention, or if the invention was anticipated having regard to traditional knowledge."
        ),
    },
    {
        "title": "Patents Act, 1970 — Section 10(4)(d): Mandatory Disclosure of Biological Resources",
        "authority": "IP India (CGPDTM)",
        "jurisdiction": "India",
        "domain": "Patent",
        "url": "https://ipindia.gov.in",
        "text": (
            "Section 10(4)(d)(ii) of the Indian Patents Act, 1970 mandates that if an invention described in a patent specification "
            "uses biological material from India, the applicant must explicitly disclose the source and geographical origin of the "
            "biological material in the specification.\n"
            "Furthermore, Form 1 of the Patent Rules requires the applicant to submit a formal declaration affirming that necessary "
            "approval from the National Biodiversity Authority (NBA) has been obtained or will be obtained prior to the grant of the patent."
        ),
    },

    # ---------------------------------------------------------------------
    # 2. PCIM&H — AYURVEDIC PHARMACOPOEIA & RAW DRUG STANDARDS
    # ---------------------------------------------------------------------
    {
        "title": "PCIM&H — Ayurvedic Pharmacopoeia of India (API) Monograph Standards",
        "authority": "PCIM&H",
        "jurisdiction": "India",
        "domain": "Ayurveda",
        "url": "https://pcimh.gov.in",
        "text": (
            "The Pharmacopoeia Commission for Indian Medicine & Homoeopathy (PCIM&H) publishes the official Ayurvedic Pharmacopoeia "
            "of India (API) and Ayurvedic Formulary of India (AFI) under the First Schedule of the Drugs and Cosmetics Act, 1940.\n"
            "API Monograph Requirements:\n"
            "1. Botanical Identity & Macroscopic/Microscopic Standards: Official Latin binomial name (e.g. Curcuma longa L., Withania somnifera (L.) Dunal, Azadirachta indica A. Juss.) and macroscopic/microscopic section characteristics.\n"
            "2. Physicochemical Quality Parameters: Foreign matter limit (not more than 2%), Total Ash value, Acid-insoluble ash, Alcohol-soluble extractive, and Water-soluble extractive.\n"
            "3. Safety Limits: Heavy metals limits (Lead <= 10 ppm, Arsenic <= 3 ppm, Cadmium <= 0.3 ppm, Mercury <= 1 ppm), Aflatoxins (B1 <= 0.5 ppb, Total <= 5 ppb), and Pesticide Residues (according to API limits).\n"
            "4. Classical Pharmacopoeial Reference: Every API monograph serves as statutory identity proof for classical Ayurvedic raw drugs and preparations."
        ),
    },
    {
        "title": "PCIM&H — Botanical Identity & Pharmacopoeial References for Key Ayurvedic Raw Drugs",
        "authority": "PCIM&H",
        "jurisdiction": "India",
        "domain": "Ayurveda",
        "url": "https://pcimh.gov.in",
        "text": (
            "Official PCIM&H Botanical Identity and Pharmacopoeial References:\n"
            "- Haridra (Turmeric): Curcuma longa L. (Family Zingiberaceae). Dried rhizome. Minimum curcuminoid content 3.0% w/w.\n"
            "- Ashwagandha: Withania somnifera (L.) Dunal (Family Solanaceae). Dried root. Minimum withanolide content 0.5% w/w.\n"
            "- Nimba (Neem): Azadirachta indica A. Juss. (Family Meliaceae). Dried leaf, seed oil, and stem bark.\n"
            "- Shunthi (Ginger): Zingiber officinale Roscoe (Family Zingiberaceae). Dried rhizome.\n"
            "- Pippali (Long Pepper): Piper longum L. (Family Piperaceae). Dried fruit.\n"
            "- Maricha (Black Pepper): Piper nigrum L. (Family Piperaceae). Dried fruit.\n"
            "These pharmacopoeial standards establish standard identity and baseline prior art for classical raw drug extracts."
        ),
    },

    # ---------------------------------------------------------------------
    # 3. PUBMED & SCIENTIFIC / MEDICAL LITERATURE INTEGRATION
    # ---------------------------------------------------------------------
    {
        "title": "PubMed / NLM — Scientific Literature vs Legal Patentability Distinction",
        "authority": "PubMed / NLM",
        "jurisdiction": "International",
        "domain": "Medical",
        "url": "https://pubmed.ncbi.nlm.nih.gov",
        "text": (
            "Biomedical literature indexed in PubMed documents pharmacological activity, in vitro assays, animal models, and clinical trial results for medicinal plants.\n"
            "Critical IP Distinction — Legal Authority vs Scientific Evidence:\n"
            "- Scientific literature in PubMed demonstrates biological activity (e.g., anti-inflammatory activity of Curcumin or adaptogenic effect of Withanolides).\n"
            "- However, demonstrating biological activity in PubMed does NOT automatically establish patentability or legal validity under patent law.\n"
            "- For an Ayurvedic formulation, patentability requires overcoming statutory bars (Section 3(p) traditional knowledge bar, Section 3(e) admixture bar, Section 3(d) efficacy bar).\n"
            "- Published PubMed literature acts as non-patent prior art (35 U.S.C. 102 / EPC Art 54 / Indian Patents Act Sec 13) that can anticipate or render obvious claimed inventions."
        ),
    },
    {
        "title": "PubMed Literature — Curcumin & Piperine Bio-Enhancement Prior Art",
        "authority": "PubMed / NLM",
        "jurisdiction": "International",
        "domain": "Medical",
        "url": "https://pubmed.ncbi.nlm.nih.gov",
        "text": (
            "Extensive biomedical literature (e.g. Shoba et al., Planta Med 1998) documents that co-administration of Piperine (from Piper nigrum / Piper longum) "
            "with Curcumin (from Curcuma longa) increases the bioavailability of curcumin by 2000% in humans by inhibiting glucuronidation.\n"
            "Patent Implications: Because the bio-enhancing effect of Piperine and Trikatu on Curcumin is widely published in peer-reviewed scientific literature "
            "and documented in classical Ayurvedic Charaka Samhita texts (Yogavahi effect), simple combinations of Curcumin and Piperine lack inventive step "
            "and are statutorily barred under Section 3(e) and Section 3(p) unless specific non-obvious ratios or novel drug delivery systems are proved."
        ),
    },

    # ---------------------------------------------------------------------
    # 4. BIOLOGICAL DIVERSITY ACT, 2002 & 2023 AMENDMENT (NBA & ABS)
    # ---------------------------------------------------------------------
    {
        "title": "Biological Diversity Act, 2002 — Section 3 & Section 4: Access to Biological Resources",
        "authority": "National Biodiversity Authority (NBA)",
        "jurisdiction": "India",
        "domain": "Biodiversity",
        "url": "https://nbaindia.gov.in",
        "text": (
            "Section 3 of the Biological Diversity Act, 2002 prohibits non-Indian citizens, NRIs, and entities having foreign participation in share capital or management "
            "from obtaining any biological resource occurring in India or associated knowledge for research, commercial utilization, bio-survey, or bio-utilization "
            "without prior approval of the National Biodiversity Authority (NBA).\n"
            "Section 4 prohibits any person from transferring the results of research relating to Indian biological resources to foreign entities without NBA approval."
        ),
    },
    {
        "title": "Biological Diversity Act, 2002 — Section 6: Mandatory Prior Approval for IPR Filing",
        "authority": "National Biodiversity Authority (NBA)",
        "jurisdiction": "India",
        "domain": "ABS",
        "url": "https://nbaindia.gov.in",
        "text": (
            "Section 6(1) of the Biological Diversity Act, 2002 mandates that no person shall apply for any intellectual property right, in or outside India, "
            "for any invention based on any research or information on a biological resource obtained from India without obtaining prior approval of the NBA.\n"
            "For patent applications, NBA approval may be secured after patent application filing but MUST be obtained prior to the grant of the patent by the patent office. "
            "Failure to obtain NBA clearance constitutes statutory ground for pre-grant/post-grant opposition and patent revocation under Section 64(1)(p)."
        ),
    },
    {
        "title": "Biological Diversity (Amendment) Act, 2023 — AYUSH Exemptions & ABS Slabs",
        "authority": "National Biodiversity Authority (NBA)",
        "jurisdiction": "India",
        "domain": "ABS",
        "url": "https://nbaindia.gov.in",
        "text": (
            "The Biological Diversity (Amendment) Act, 2023 introduced key statutory updates:\n"
            "1. Registered AYUSH Practitioners Exemption: Codified traditional knowledge holders and registered AYUSH practitioners are exempted from intimation to State Biodiversity Boards (SBBs) when accessing resources for patient treatment.\n"
            "2. Access & Benefit Sharing (ABS) Slabs: Commercial utilization of biological resources attracts benefit sharing fees (0.1% to 0.5% of gross sales turnover, or 3.0% to 5.0% of licensing royalties).\n"
            "3. Decriminalization: Replaced criminal imprisonment with civil financial penalties ranging from Rs. 1 lakh to Rs. 50 lakhs (up to Rs. 1 crore for continuing contravention)."
        ),
    },

    # ---------------------------------------------------------------------
    # 5. AYUSH & DRUGS AND COSMETICS ACT (RULE 158B, SCHEDULE T)
    # ---------------------------------------------------------------------
    {
        "title": "Drugs and Cosmetics Act, 1940 — Rule 158B: Licensing of ASU Drugs",
        "authority": "Ministry of AYUSH",
        "jurisdiction": "India",
        "domain": "Ayurveda",
        "url": "https://ayush.gov.in",
        "text": (
            "Rule 158-B of the Drugs and Cosmetics Rules, 1945 prescribes licensing criteria for Ayurvedic, Siddha, and Unani (ASU) drugs:\n"
            "1. Classical Formulations (Shastriya Aushadhi): Formulations manufactured strictly according to recipes in authoritative books listed in the First Schedule. "
            "Requires classical textual references; safety/efficacy clinical trials are generally exempt.\n"
            "2. Patent or Proprietary Medicines (Anubhuta ASU Innovations): Formulations containing classical ingredients in new proportions, new dosage forms, or new indications. "
            "Requires published safety and acute toxicity study data (OECD guidelines) and proof of effectiveness."
        ),
    },
    {
        "title": "Schedule T — Good Manufacturing Practices (GMP) for Ayurvedic Medicines",
        "authority": "Ministry of AYUSH",
        "jurisdiction": "India",
        "domain": "Regulatory",
        "url": "https://ayush.gov.in",
        "text": (
            "Schedule T of the Drugs and Cosmetics Rules, 1945 prescribes mandatory Good Manufacturing Practices (GMP) for ASU drugs:\n"
            "- Hygiene, dedicated manufacturing sections for Churna, Vati, Asava/Arishta, Taila/Ghrita, and Bhasma.\n"
            "- Quality Control Laboratory testing for identity, purity, heavy metal limits (Lead, Cadmium, Mercury, Arsenic), microbial contamination, and pesticide residues."
        ),
    },
    {
        "title": "FSSAI (Ayurveda Aahara) Regulations, 2022",
        "authority": "FSSAI",
        "jurisdiction": "India",
        "domain": "Regulatory",
        "url": "https://www.fssai.gov.in",
        "text": (
            "The Food Safety and Standards (Ayurveda Aahara) Regulations, 2022 regulate food products prepared in accordance with Ayurvedic recipes:\n"
            "- Requires FSSAI license with special 'AYURVEDA AAHARA' logo.\n"
            "- Strictly prohibits claiming treatment, cure, or prevention of any disease on food labels.\n"
            "- Formulations must adhere to approved recipes and safety parameters."
        ),
    },
    {
        "title": "CDSCO Phytopharmaceutical Drug Guidelines (Rule 122E)",
        "authority": "CDSCO",
        "jurisdiction": "India",
        "domain": "Medical",
        "url": "https://cdsco.gov.in",
        "text": (
            "Phytopharmaceutical drugs are defined under CDSCO regulations as purified, standardized fractionated extracts of medicinal plants intended for internal or external use in humans.\n"
            "- Requires submission of chromatographic fingerprinting (HPLC/HPTLC), batch-to-batch consistency data, Phase I-III clinical trial protocols, and safety data.\n"
            "- Represents a distinct drug regulatory category separate from traditional ASU proprietary medicines."
        ),
    },

    # ---------------------------------------------------------------------
    # 6. TRADITIONAL KNOWLEDGE DIGITAL LIBRARY (TKDL) & CLASSICAL TEXTS
    # ---------------------------------------------------------------------
    {
        "title": "TKDL Architecture, Purpose and Patent Office Access Agreements",
        "authority": "CSIR / TKDL",
        "jurisdiction": "India",
        "domain": "Traditional Knowledge",
        "url": "https://www.tkdl.res.in",
        "text": (
            "The Traditional Knowledge Digital Library (TKDL) is a joint initiative of CSIR and Ministry of AYUSH translating classical Indian medical texts "
            "(Sanskrit, Urdu, Arabic, Persian, Tamil) into 5 international languages using Traditional Knowledge Resource Classification (TKRC).\n"
            "TKDL has non-patent prior art search agreements with EPO, USPTO, JPO, UK IPO, IP Australia, and CIPO.\n"
            "Important Transparency Notice: The complete full TKDL database is restricted to authorized patent offices under confidentiality agreements to protect national sovereign rights. "
            "IP-SAKTI SAHAYAK queries public TKDL guidelines, published revocation case precedents, and indexed classical pharmacopoeia texts, and does not claim unrestricted access to private TKDL files."
        ),
    },
    {
        "title": "Classical Ayurvedic Extraction Methods & Formulations (Charaka & Sushruta)",
        "authority": "CSIR / TKDL",
        "jurisdiction": "India",
        "domain": "Traditional Knowledge",
        "url": "https://www.tkdl.res.in",
        "text": (
            "Classical Ayurvedic pharmaceutical science (Bhaishajya Kalpana) recognizes five basic extraction preparations (Pancha Vidha Kashaya Kalpana):\n"
            "1. Swarasa (fresh juice extraction)\n"
            "2. Kalka (fine paste/crush)\n"
            "3. Kwatha / Kashaya (boiled water decoction, reduced to 1/4th or 1/8th)\n"
            "4. Hima (cold aqueous infusion)\n"
            "5. Phanta (hot aqueous infusion)\n"
            "Secondary classical dosage forms include Asava/Arishta (bio-fermentation), Ghrita/Taila (lipid-soluble extract), Vati/Gutika (tablets), and Avaleha (herbal jams).\n"
            "Patent claims describing standard aqueous or alcoholic extractions of classical herbs for traditional indications are anticipated by TKDL prior art."
        ),
    },

    # ---------------------------------------------------------------------
    # 7. INTERNATIONAL IP & TREATIES (WIPO, TRIPS, NAGOYA)
    # ---------------------------------------------------------------------
    {
        "title": "Patent Cooperation Treaty (PCT) — International Filing & Search Guidelines",
        "authority": "WIPO",
        "jurisdiction": "International",
        "domain": "International IP",
        "url": "https://www.wipo.int/pct",
        "text": (
            "The Patent Cooperation Treaty (PCT) administered by WIPO allows filing a single international application valid across 155+ Contracting States.\n"
            "Key Phases: International Search Report (ISR), Written Opinion by International Searching Authority (ISA), Publication at 18 months, National Phase Entry at 30/31 months.\n"
            "Mandatory Requirement for Indian Residents: Section 39 of the Indian Patents Act requires mandatory written permission from Controller General or filing first in India 6 weeks prior to foreign/PCT filing."
        ),
    },
    {
        "title": "WTO TRIPS Agreement — Article 27: Patentable Subject Matter & Exceptions",
        "authority": "WTO (TRIPS)",
        "jurisdiction": "International",
        "domain": "International IP",
        "url": "https://www.wto.org/english/tratop_e/trips_e/trips_e.htm",
        "text": (
            "Article 27.1 TRIPS mandates patents for inventions in all fields of technology provided they are new, involve an inventive step, and are capable of industrial application.\n"
            "Article 27.2 permits excluding inventions contrary to ordre public or morality, or to protect human/animal/plant life or health.\n"
            "Article 27.3(b) permits excluding plants and animals other than micro-organisms, requiring plant variety protection either by patents or sui generis systems (e.g. PPV&FR Act)."
        ),
    },
    {
        "title": "WIPO Treaty on Intellectual Property, Genetic Resources and Associated Traditional Knowledge (2024)",
        "authority": "WIPO",
        "jurisdiction": "International",
        "domain": "International IP",
        "url": "https://www.wipo.int",
        "text": (
            "In May 2024, WIPO member states adopted the landmark Treaty on Intellectual Property, Genetic Resources and Associated Traditional Knowledge.\n"
            "Establishes a mandatory international patent disclosure requirement: patent applicants must disclose the country of origin/source of genetic resources "
            "and the Indigenous Peoples or local community providing associated traditional knowledge in their patent applications."
        ),
    },

    # ---------------------------------------------------------------------
    # 8. LANDMARK TRADITIONAL KNOWLEDGE & PATENT CASE PRECEDENTS
    # ---------------------------------------------------------------------
    {
        "title": "Landmark Precedent: The Turmeric (Curcuma longa) Patent Revocation",
        "authority": "CSIR / USPTO Case History",
        "jurisdiction": "India",
        "domain": "Traditional Knowledge",
        "url": "https://www.tkdl.res.in",
        "text": (
            "In 1995, US Patent 5,401,504 granted to Univ. of Mississippi on 'Use of Turmeric in Wound Healing' was challenged by CSIR India.\n"
            "CSIR produced 32 documentary references including Sanskrit Ayurvedic Samhitas and Urdu texts proving topical turmeric use for wound healing was known for centuries.\n"
            "USPTO revoked all claims in 1997, establishing worldwide precedent that documented traditional knowledge invalidates patent claims."
        ),
    },
    {
        "title": "Landmark Precedent: The Neem (Azadirachta indica) Fungicidal Patent Revocation",
        "authority": "EPO / CSIR Case History",
        "jurisdiction": "International",
        "domain": "Traditional Knowledge",
        "url": "https://www.tkdl.res.in",
        "text": (
            "European Patent 0436257 granted to W.R. Grace & Co. for hydrophobic neem oil antifungal formulation was opposed by Indian scientists.\n"
            "EPO revoked the patent completely in 2000 (upheld 2005) for lack of novelty and inventive step over traditional Indian prior art."
        ),
    },
    {
        "title": "Landmark Precedent: Novartis AG v. Union of India (2013 Supreme Court)",
        "authority": "Supreme Court of India",
        "jurisdiction": "India",
        "domain": "Patent",
        "url": "https://main.sci.gov.in",
        "text": (
            "In Novartis AG v. Union of India (2013) 6 SCC 1, the Supreme Court of India held that 'efficacy' under Section 3(d) means therapeutic efficacy specifically—the ability to cure or alleviate disease in human patients. "
            "Increased bioavailability or physical stability alone does not constitute enhanced therapeutic efficacy unless it directly increases clinical therapeutic action. The patent for beta-crystalline Imatinib Mesylate was denied."
        ),
    },
]


def run_ingestion() -> None:
    """Ingests all seed statutory, medical, PCIM&H, and TK passages into SQLite, FAISS, and BM25."""
    init_db()
    vector_store.load_or_create()

    all_chunks_for_bm25 = []
    all_meta = []

    with get_session() as db:
        for passage in SEED_PASSAGES:
            cleaned = normalize_legal_text(clean_text(passage["text"]))
            h = content_hash(cleaned)

            existing = db.query(Document).filter(Document.content_hash == h).first()
            if existing:
                logger.info("Skipping already-ingested document: %s", passage["title"])
                continue

            authority_name = passage["authority"].split("/")[0].strip()
            source_row = db.query(Source).filter(Source.source_name.ilike(f"%{authority_name}%")).first()

            document = Document(
                source_id=source_row.id if source_row else None,
                title=passage["title"],
                url=passage["url"],
                doc_type=passage.get("domain", "statutory-corpus"),
                jurisdiction=passage["jurisdiction"],
                authority=passage["authority"],
                content_hash=h,
                expires_at=new_expiry(),
            )
            db.add(document)
            db.flush()

            chunks = chunk_document(
                document_id=document.id,
                text=cleaned,
                authority=passage["authority"],
                jurisdiction=passage["jurisdiction"],
                source_url=passage["url"],
            )

            for c in chunks:
                db_chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_text=c.text,
                    section=c.section,
                    page=c.page,
                    jurisdiction=c.jurisdiction,
                    authority=c.authority,
                    source_url=c.source_url,
                )
                db.add(db_chunk)
                db.flush()

                meta = {
                    "chunk_id": db_chunk.id,
                    "document_id": document.id,
                    "text": c.text,
                    "section": c.section or passage["title"],
                    "page": c.page,
                    "authority": c.authority,
                    "jurisdiction": c.jurisdiction,
                    "domain": passage.get("domain", "General IP"),
                    "source_url": c.source_url,
                    "priority": source_row.priority if source_row else 2,
                }
                all_chunks_for_bm25.append(meta)
                all_meta.append(meta)

            logger.info("Ingested '%s' -> %d chunks", passage["title"], len(chunks))

    if all_meta:
        try:
            vectors = embedding_service.embed([m["text"] for m in all_meta])
            vector_store.add(vectors, all_meta)
            vector_store.save()
            logger.info("Added %d chunks to the FAISS index (backend=%s).", len(all_meta), embedding_service.backend)
        except VectorStoreUnavailableError as e:
            logger.warning("FAISS unavailable during ingestion (%s) — semantic search will fall back to BM25.", e)

    rebuild_bm25_from_db()
    logger.info("Ingestion complete. Total BM25 index size: %d chunks.", bm25_index.size)


def rebuild_bm25_from_db() -> None:
    """Rebuild the in-memory BM25 index from existing DocumentChunk rows."""
    with get_session() as db:
        chunks = db.query(DocumentChunk).all()
        meta = []
        for c in chunks:
            doc = c.document
            meta.append(
                {
                    "chunk_id": c.id,
                    "document_id": c.document_id,
                    "text": c.chunk_text,
                    "section": c.section or (doc.title if doc else "Statutory Provision"),
                    "page": c.page,
                    "authority": c.authority,
                    "jurisdiction": c.jurisdiction,
                    "domain": doc.doc_type if doc else "General IP",
                    "source_url": c.source_url,
                    "priority": 2,
                }
            )
    bm25_index.build(meta)
    logger.info("Rebuilt BM25 index from %d existing chunks in database.", len(meta))


def bootstrap_indexes() -> None:
    """Called once at app startup: seeds DB and indexes if empty or outdated."""
    init_db()
    with get_session() as db:
        chunk_count = db.query(DocumentChunk).count()
    if chunk_count < 15:
        logger.info("Running comprehensive legal, medical & Ayurvedic corpus ingestion...")
        run_ingestion()
    else:
        vector_store.load_or_create()
        rebuild_bm25_from_db()


if __name__ == "__main__":
    run_ingestion()
