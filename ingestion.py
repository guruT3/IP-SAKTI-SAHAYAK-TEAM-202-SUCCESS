"""
IP-SAKTI SAHAYAK
Ingestion & Knowledge Base Bootstrap
=====================================
Builds the comprehensive local knowledge cache:
Loads statutory texts across:
1. Indian Patents Act, 1970 (Sections 3(d), 3(p), 3(e), 3(h), 3(k), 25, 64)
2. Biological Diversity Act, 2002 & Biological Diversity (Amendment) Act, 2023
3. Drugs and Cosmetics Act, 1940 & AYUSH Rules (Rule 158B, Schedule T GMP)
4. Traditional Knowledge Digital Library (TKDL) & Classical Ayurvedic Text References
5. International IP Treaties (WIPO PCT, TRIPS, Nagoya Protocol, WIPO IGC Treaty)
6. Landmark Traditional Knowledge Case Precedents (Turmeric, Neem, Basmati, Novartis)

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
# COMPREHENSIVE AUTHORITATIVE LEGAL & TRADITIONAL KNOWLEDGE CORPUS
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
    # 2. BIOLOGICAL DIVERSITY ACT, 2002 & 2023 AMENDMENT (NBA & ABS)
    # ---------------------------------------------------------------------
    {
        "title": "Biological Diversity Act, 2002 — Section 3 & Section 4: Access to Biological Resources",
        "authority": "National Biodiversity Authority (NBA)",
        "jurisdiction": "India",
        "domain": "Biodiversity",
        "url": "https://nbaindia.gov.in",
        "text": (
            "Section 3 of the Biological Diversity Act, 2002 prohibits non-Indian citizens, non-resident Indians (NRIs), and entities "
            "having foreign participation in share capital or management from obtaining any biological resource occurring in India or "
            "knowledge associated thereto for research, commercial utilization, bio-survey, or bio-utilization without prior approval "
            "of the National Biodiversity Authority (NBA).\n"
            "Section 4 prohibits any person from transferring the results of any research relating to biological resources occurring in "
            "or obtained from India to non-citizens or foreign-controlled entities without prior approval of the NBA."
        ),
    },
    {
        "title": "Biological Diversity Act, 2002 — Section 6: Mandatory Prior Approval for IPR Filing",
        "authority": "National Biodiversity Authority (NBA)",
        "jurisdiction": "India",
        "domain": "ABS",
        "url": "https://nbaindia.gov.in",
        "text": (
            "Section 6(1) of the Biological Diversity Act, 2002 provides that no person shall apply for any intellectual property right, "
            "by whatever name called, in or outside India for any invention based on any research or information on a biological resource "
            "obtained from India without obtaining the prior approval of the National Biodiversity Authority before grant of such IPR.\n"
            "In case of patent applications, permission of the NBA may be obtained after filing the application for patent but must be "
            "secured before the grant of the patent by the patent office. The NBA while granting approval may impose benefit sharing fees "
            "or royalty conditions (Access and Benefit Sharing - ABS)."
        ),
    },
    {
        "title": "Biological Diversity (Amendment) Act, 2023 — AYUSH Exemptions & Decriminalization",
        "authority": "National Biodiversity Authority (NBA)",
        "jurisdiction": "India",
        "domain": "ABS",
        "url": "https://nbaindia.gov.in",
        "text": (
            "The Biological Diversity (Amendment) Act, 2023 introduced significant reforms:\n"
            "1. AYUSH Practitioners Exemption: Codified traditional knowledge holders and registered AYUSH practitioners (Vaidyas, Hakims) "
            "are exempted from prior intimation to State Biodiversity Boards (SBBs) for accessing biological resources for treating patients.\n"
            "2. Fast-Track IPR Approval: Clear timelines are established for NBA approval regarding patent grants.\n"
            "3. Decriminalization: Criminal penalties (imprisonment) under the 2002 Act have been replaced with civil financial penalties "
            "ranging from Rs. 1 lakh to Rs. 50 lakhs, with ongoing contravention penalties up to Rs. 1 crore.\n"
            "4. Cultivated Medicinal Plants: Simplification of compliance for cultivated bio-resources with registration mechanisms."
        ),
    },
    {
        "title": "NBA Guidelines on Access and Benefit Sharing (ABS) Regulations",
        "authority": "National Biodiversity Authority (NBA)",
        "jurisdiction": "India",
        "domain": "ABS",
        "url": "https://nbaindia.gov.in",
        "text": (
            "Access and Benefit Sharing (ABS) regulations prescribe the monetary and non-monetary obligations when utilizing Indian "
            "biological resources. For commercial utilization:\n"
            "- Option A: Payment of 0.1% to 0.5% of the annual ex-factory gross sales of the product depending on sales slabs (0.1% for "
            "turnover up to Rs. 1 crore, 0.2% between 1 to 3 crores, and 0.5% for above 3 crores).\n"
            "- Option B: Fixed percentage of purchase price of the biological resource (ranging from 1.0% to 3.0% for high-economic-value resources).\n"
            "- For IPR Commercialization: In case of transfer of IPR or commercial licensing to third parties, 3.0% to 5.0% of the royalty or "
            "license fee received must be shared with the NBA."
        ),
    },

    # ---------------------------------------------------------------------
    # 3. AYUSH & DRUGS AND COSMETICS ACT (AYURVEDIC FORMULATION REGULATION)
    # ---------------------------------------------------------------------
    {
        "title": "Drugs and Cosmetics Act, 1940 — Rule 158B: Licensing of ASU Drugs",
        "authority": "Ministry of AYUSH",
        "jurisdiction": "India",
        "domain": "Ayurveda",
        "url": "https://ayush.gov.in",
        "text": (
            "Rule 158-B of the Drugs and Cosmetics Rules, 1945 categorizes Ayurvedic, Siddha, and Unani (ASU) medicines for manufacturing licenses:\n"
            "1. Classical Formulations (Shastriya Aushadhi): Formulations manufactured strictly in accordance with recipes in authoritative "
            "books specified in the First Schedule of the Act (e.g. Charaka Samhita, Sushruta Samhita, Sharangadhara Samhita, API). "
            "These require proof of textual reference and adherence to classical ingredients and preparation methods; safety/efficacy clinical "
            "trials are generally not required for classical indications.\n"
            "2. Patent or Proprietary Medicines (Anubhuta / Saundarya / Modern Innovations): Formulations containing ingredients specified in "
            "classical texts but formulated in new dosage forms, new proportions, or new therapeutic indications. These require published "
            "pharmacological and safety study evidence, acute toxicity studies (OECD guidelines), and clinical trial proof of effectiveness."
        ),
    },
    {
        "title": "Schedule T — Good Manufacturing Practices (GMP) for Ayurvedic Medicines",
        "authority": "Ministry of AYUSH",
        "jurisdiction": "India",
        "domain": "Regulatory",
        "url": "https://ayush.gov.in",
        "text": (
            "Schedule T of the Drugs and Cosmetics Rules, 1945 prescribes Good Manufacturing Practices (GMP) for manufacturing Ayurvedic, "
            "Siddha, and Unani medicines. Requirements include:\n"
            "- Factory premises hygiene, adequate water supply, and dedicated manufacturing sections for Churna, Vati, Asava/Arishta, "
            "Taila/Ghrita, Rasashastra (Bhasma/Kupipakwa), and modern solid dosage forms.\n"
            "- Quality Control Laboratory testing for raw herbs, identity, purity, heavy metals (Lead, Cadmium, Mercury, Arsenic within AYUSH limits), "
            "microbial contamination (E. coli, Salmonella), pesticide residues, and aflatoxins.\n"
            "- Batch manufacturing records and standard shelf-life/stability testing."
        ),
    },
    {
        "title": "Drugs and Magic Remedies (Objectionable Advertisements) Act, 1954 — AYUSH Warnings",
        "authority": "Ministry of AYUSH",
        "jurisdiction": "India",
        "domain": "Regulatory",
        "url": "https://ayush.gov.in",
        "text": (
            "Manufacturers and marketers of Ayurvedic formulations are strictly prohibited under the Drugs and Magic Remedies "
            "(Objectionable Advertisements) Act, 1954 and Rule 170 of Drugs and Cosmetics Rules from making misleading or absolute cure "
            "claims for specified chronic conditions including diabetes, cancer, blindness, paralysis, hypertension, and sexual performance.\n"
            "Any health claim for an Ayurvedic innovation must be supported by clinical evidence and prior advertising clearance from the "
            "State Licensing Authority."
        ),
    },

    # ---------------------------------------------------------------------
    # 4. TRADITIONAL KNOWLEDGE DIGITAL LIBRARY (TKDL) & CLASSICAL FORMULATIONS
    # ---------------------------------------------------------------------
    {
        "title": "TKDL Architecture, Purpose and Patent Office Access Agreements",
        "authority": "CSIR / TKDL",
        "jurisdiction": "India",
        "domain": "Traditional Knowledge",
        "url": "https://www.tkdl.res.in",
        "text": (
            "The Traditional Knowledge Digital Library (TKDL) is a pioneering Indian database created by CSIR and the Ministry of AYUSH. "
            "It translates classical Indian medical formulations from Sanskrit, Urdu, Arabic, Persian, and Tamil texts into five international "
            "languages (English, French, German, Japanese, Spanish) using the Traditional Knowledge Resource Classification (TKRC).\n"
            "TKDL has institutional access agreements with the European Patent Office (EPO), USPTO, JPO, UK IPO, IP Australia, and CIPO. "
            "Patent examiners worldwide search TKDL as non-patent prior art before granting patents, which has successfully prevented hundreds "
            "of wrongful patent monopolies over Indian traditional medicinal knowledge."
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
            "3. Kwatha / Kashaya (boiled water decoction, typically reduced to 1/4th or 1/8th)\n"
            "4. Hima (cold aqueous infusion)\n"
            "5. Phanta (hot aqueous infusion)\n"
            "Secondary classical dosage forms include Asava/Arishta (self-generated alcoholic bio-fermentation for enhanced bioavailability), "
            "Sneha Kalpana (Ghrita/Taila lipid-soluble extract for cell membrane transport), Vati/Gutika (compressed pills), and Avaleha (herbal jams).\n"
            "Patent claims describing aqueous or hydro-alcoholic extraction of known Ayurvedic herbs for classical indications are directly anticipated by TKDL."
        ),
    },
    {
        "title": "Classical Polyherbal Synergies: Trikatu and Triphala Prior Art",
        "authority": "CSIR / TKDL",
        "jurisdiction": "India",
        "domain": "Traditional Knowledge",
        "url": "https://www.tkdl.res.in",
        "text": (
            "Trikatu (consisting of Piper nigrum [Maricha/Black Pepper], Piper longum [Pippali/Long Pepper], and Zingiber officinale [Shunthi/Ginger]) "
            "is documented in Charaka Samhita as a Yogavahi (bioenhancer) that enhances the absorption, bioavailability, and digestive fire (Agni) "
            "of co-administered botanical actives (due to piperine content).\n"
            "Triphala (Emblica officinalis [Amalaki], Terminalia chebula [Haritaki], and Terminalia bellirica [Bibhitaki]) is extensively documented "
            "for Rasayana (rejuvenation), ocular health, and metabolic disorders.\n"
            "Combinations using Piperine or Trikatu as bioenhancers for curcumin, withanolides, or boswellic acids have extensive classical prior art "
            "and require proof of non-obvious synergistic ratios to satisfy patent novelty requirements."
        ),
    },

    # ---------------------------------------------------------------------
    # 5. INTERNATIONAL IP & TREATIES (WIPO, TRIPS, NAGOYA)
    # ---------------------------------------------------------------------
    {
        "title": "Patent Cooperation Treaty (PCT) — International Filing & Search Guidelines",
        "authority": "WIPO",
        "jurisdiction": "International",
        "domain": "International IP",
        "url": "https://www.wipo.int/pct",
        "text": (
            "The Patent Cooperation Treaty (PCT) administered by WIPO allows an applicant to file a single international application "
            "valid across more than 155 Contracting States. Key steps:\n"
            "1. Filing an International Application with a receiving Office (e.g. Indian Patent Office or WIPO International Bureau).\n"
            "2. International Search Report (ISR) and Written Opinion by an International Searching Authority (ISA) establishing novelty and inventive step.\n"
            "3. International Publication after 18 months.\n"
            "4. National Phase Entry at 30/31 months in designated countries (e.g. US, Europe, Japan, China, Australia).\n"
            "Important note for Indian applicants: Section 39 of the Indian Patents Act requires mandatory prior foreign filing permission "
            "or filing first in India at least 6 weeks prior to foreign/PCT filing if the inventor is resident in India."
        ),
    },
    {
        "title": "WTO TRIPS Agreement — Article 27: Patentable Subject Matter & Exceptions",
        "authority": "WTO (TRIPS)",
        "jurisdiction": "International",
        "domain": "International IP",
        "url": "https://www.wto.org/english/tratop_e/trips_e/trips_e.htm",
        "text": (
            "Article 27.1 of the WTO TRIPS Agreement mandates that patents shall be available for any inventions, whether products or processes, "
            "in all fields of technology, provided they are new, involve an inventive step (non-obvious), and are capable of industrial application.\n"
            "Article 27.2 permits Members to exclude from patentability inventions contrary to ordre public or morality, including to protect human, "
            "animal, or plant life or health, or to avoid serious prejudice to the environment.\n"
            "Article 27.3(a) allows exclusion of 'diagnostic, therapeutic and surgical methods for the treatment of humans or animals'.\n"
            "Article 27.3(b) permits exclusion of plants and animals other than micro-organisms, provided plant varieties are protected either by patents "
            "or by an effective sui generis system (such as UPOV or India's PPV&FR Act)."
        ),
    },
    {
        "title": "Nagoya Protocol on Access and Benefit-Sharing (ABS)",
        "authority": "Convention on Biological Diversity (CBD)",
        "jurisdiction": "International",
        "domain": "ABS",
        "url": "https://www.cbd.int/abs",
        "text": (
            "The Nagoya Protocol on Access to Genetic Resources and the Fair and Equitable Sharing of Benefits Arising from their Utilization "
            "is a supplementary agreement to the Convention on Biological Diversity (CBD). Core obligations:\n"
            "1. Prior Informed Consent (PIC): Access to genetic resources requires consent from the country of origin providing the resources.\n"
            "2. Mutually Agreed Terms (MAT): Users and providers must negotiate fair terms regarding monetary benefits (milestone payments, royalties) "
            "and non-monetary benefits (technology transfer, joint research, capacity building).\n"
            "3. Compliance and Monitoring: User countries must take measures to monitor utilization of genetic resources, including through designated "
            "checkpoints (such as Patent Offices requiring proof of ABS compliance at the time of patent application)."
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
            "The treaty establishes a new mandatory international patent disclosure requirement: where a claimed invention in a patent application is based "
            "on genetic resources, each contracting party shall require patent applicants to disclose the country of origin or the source of the genetic resources; "
            "and where the invention is based on traditional knowledge associated with genetic resources, applicants must disclose the Indigenous Peoples or "
            "local community who provided the knowledge.\n"
            "This treaty represents international harmonization of the disclosure principle pioneered in Indian patent and biodiversity law."
        ),
    },

    # ---------------------------------------------------------------------
    # 6. LANDMARK TRADITIONAL KNOWLEDGE & PATENT CASE PRECEDENTS
    # ---------------------------------------------------------------------
    {
        "title": "Landmark Precedent: The Turmeric (Curcuma longa) Patent Revocation",
        "authority": "CSIR / USPTO Case History",
        "jurisdiction": "India",
        "domain": "Traditional Knowledge",
        "url": "https://www.tkdl.res.in",
        "text": (
            "In 1995, US Patent 5,401,504 was granted to the University of Mississippi Medical Center on the 'Use of Turmeric in Wound Healing'. "
            "The Council of Scientific and Industrial Research (CSIR), India, filed a formal re-examination petition challenging novelty.\n"
            "CSIR produced 32 documentary references, including Sanskrit texts (Ayurvedic Samhitas) and Urdu publications documenting that the topical "
            "use of turmeric powder for wound healing and sprains has been an ancient, well-known practice in India for centuries.\n"
            "The USPTO upheld the challenge and revoked all claims of the patent in 1997, establishing worldwide precedent that published traditional "
            "medicinal knowledge constitutes anticipation and invalidates patent claims."
        ),
    },
    {
        "title": "Landmark Precedent: The Neem (Azadirachta indica) Fungicidal Patent Revocation",
        "authority": "EPO / CSIR Case History",
        "jurisdiction": "International",
        "domain": "Traditional Knowledge",
        "url": "https://www.tkdl.res.in",
        "text": (
            "In 1992, European Patent 0436257 was granted to W.R. Grace & Co. and the USDA for a method of controlling fungi on plants using a novel "
            "hydrophobic extracted neem oil formulation.\n"
            "A legal opposition was filed by Indian scientists and civil society demonstrating that rural farmers in India and Ayurvedic texts had used "
            "hydrophobic and aqueous extracts of neem seeds as natural pesticides and anti-fungal agents for generations.\n"
            "In 2000 (upheld by the EPO Technical Board of Appeal in 2005), the European Patent Office completely revoked the patent on the grounds of "
            "lack of novelty and lack of inventive step over traditional Indian prior art."
        ),
    },
    {
        "title": "Landmark Precedent: The Basmati Rice GI and Patent Dispute (RiceTec)",
        "authority": "IP India / USPTO Case History",
        "jurisdiction": "India",
        "domain": "GI",
        "url": "https://ipindia.gov.in",
        "text": (
            "In 1997, RiceTec Inc. was granted US Patent 5,663,484 on 'Basmati rice lines and grains'. The patent claimed novel rice lines having "
            "characteristics similar to traditional Indian Basmati rice.\n"
            "India challenged 20 claims of the patent through the Agricultural and Processed Food Products Export Development Authority (APEDA), "
            "demonstrating that the claimed grain length, aroma (2-acetyl-1-pyrroline), and cooking qualities were inherent to traditional Basmati "
            "varieties cultivated in the Indo-Gangetic plains for centuries.\n"
            "RiceTec was forced to withdraw 15 of its 20 broad claims. The dispute accelerated India's enactment of the Geographical Indications of Goods Act, 1999."
        ),
    },
    {
        "title": "Landmark Precedent: Novartis AG v. Union of India (2013 Supreme Court)",
        "authority": "Supreme Court of India",
        "jurisdiction": "India",
        "domain": "Patent",
        "url": "https://main.sci.gov.in",
        "text": (
            "In Novartis AG v. Union of India (2013) 6 SCC 1, the Supreme Court of India rendered a definitive interpretation of Section 3(d) of the Patents Act, 1970.\n"
            "Novartis sought a patent for the beta-crystalline form of Imatinib Mesylate (used in cancer drug Glivec), arguing that the beta-crystalline form possessed "
            "superior thermodynamic stability, lower hygroscopicity, and 30% increased bioavailability compared to the free base.\n"
            "The Supreme Court held that in the case of pharmaceutical substances, 'efficacy' under Section 3(d) means therapeutic efficacy specifically—the ability to "
            "cure or alleviate disease in human patients. Increased bioavailability or physical stability alone does not constitute enhanced therapeutic efficacy unless "
            "it directly results in a significant increase in clinical therapeutic action. The patent was denied."
        ),
    },
    {
        "title": "Geographical Indications of Goods Act, 1999 — Protection of Regional Traditional Heritage",
        "authority": "IP India (GI Registry)",
        "jurisdiction": "India",
        "domain": "GI",
        "url": "https://ipindia.gov.in",
        "text": (
            "The Geographical Indications of Goods (Registration and Protection) Act, 1999 provides legal protection to goods whose quality, reputation, "
            "or characteristics are essentially attributable to their geographic origin. GI tags in the Ayurvedic, herbal, and agricultural sectors include:\n"
            "- Ayurvedic and Herbal GIs: Navara Rice (medicinal rice used in Panchakarma), Nilambur Teak, Erode Turmeric, Kandhamal Haldi, Sirsi Supari, "
            "Malabar Pepper, Alleppey Green Cardamom, Darjeeling Tea, Kashmir Saffron.\n"
            "- Rights & Enforcement: GI protection prevents unauthorized commercial exploitation and deceptive imitation by third parties outside the "
            "demarcated geographical territory, protecting community farmers and traditional producers."
        ),
    },
]


def run_ingestion() -> None:
    """Ingests all seed statutory and TK passages into SQLite, FAISS, and BM25."""
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
            logger.warning(
                "FAISS unavailable during ingestion (%s) — semantic search will fall back to BM25.", e
            )

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
    """Called once at app startup: seeds DB and indexes if empty."""
    init_db()
    with get_session() as db:
        has_documents = db.query(Document).first() is not None
        chunk_count = db.query(DocumentChunk).count()
    if not has_documents or chunk_count < 10:
        logger.info("Running initial comprehensive ingestion...")
        run_ingestion()
    else:
        vector_store.load_or_create()
        rebuild_bm25_from_db()


if __name__ == "__main__":
    run_ingestion()
