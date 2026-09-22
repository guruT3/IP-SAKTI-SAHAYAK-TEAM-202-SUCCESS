"""
IP-SAKTI SAHAYAK
Authoritative Regulatory Source Registry
==========================================
Defines the authoritative multi-jurisdictional regulatory source architecture
across India (Primary Tier 1), International Organizations, US, EU, UK, China,
Japan, Australia, Singapore, and other priority countries.

Every source contains explicit provenance, domain mappings, authority classification,
and source hierarchy priority (1 to 5) so that statutory legislation and binding
regulations always supersede secondary or advisory sources.
"""

from typing import List, Dict, Any, Optional

REGULATORY_SOURCES: List[Dict[str, Any]] = [
    # =========================================================================
    # 1. INDIA — PRIMARY STATUTORY & REGULATORY AUTHORITIES (TIER 1)
    # =========================================================================
    # Food & Food Safety
    {
        "source_id": "fssai_india",
        "name": "Food Safety and Standards Authority of India",
        "organization": "FSSAI",
        "country": "India",
        "jurisdiction": "India",
        "domains": ["Food", "Food Safety", "Nutraceutical", "Cosmetic", "Packaging/Labelling", "Advertising/Claims", "Consumer Protection"],
        "authority_level": "statutory_regulator",
        "source_priority": 1,
        "official": True,
        "base_url": "https://www.fssai.gov.in",
        "document_types": ["Act", "Regulation", "Official Notification", "Standard", "Advisory", "Operational Manual"],
        "description": "Apex statutory body established under Food Safety and Standards Act, 2006 governing food, nutraceuticals, dietary supplements, packaging, and health claims in India.",
        "active": True,
    },
    # Health, Medicine & Pharmaceuticals
    {
        "source_id": "cdsco_india",
        "name": "Central Drugs Standard Control Organization",
        "organization": "CDSCO",
        "country": "India",
        "jurisdiction": "India",
        "domains": ["Medicine", "Drug", "Medical Device", "Cosmetic", "Clinical/Medical Research", "Healthcare", "Import/Export"],
        "authority_level": "statutory_regulator",
        "source_priority": 1,
        "official": True,
        "base_url": "https://cdsco.gov.in",
        "document_types": ["Act", "Rule", "Gazette Notification", "Guideline", "Medical Device Rules", "Clinical Trial Protocols"],
        "description": "National regulatory authority for pharmaceuticals, medical devices, cosmetics, and clinical trials under Drugs and Cosmetics Act, 1940 and Medical Devices Rules, 2017.",
        "active": True,
    },
    {
        "source_id": "mohfw_india",
        "name": "Ministry of Health and Family Welfare",
        "organization": "MoHFW",
        "country": "India",
        "jurisdiction": "India",
        "domains": ["Healthcare", "Medicine", "Drug", "Public Health", "Consumer Protection"],
        "authority_level": "ministry",
        "source_priority": 1,
        "official": True,
        "base_url": "https://main.mohfw.gov.in",
        "document_types": ["Statute", "Policy", "Gazette Notification", "Advisory"],
        "description": "Union ministry responsible for national health policy, drug legislation, public health guidelines, and statutory healthcare regulations.",
        "active": True,
    },
    # Ayurveda & Traditional Systems of Medicine
    {
        "source_id": "ayush_india",
        "name": "Ministry of AYUSH",
        "organization": "Ministry of AYUSH",
        "country": "India",
        "jurisdiction": "India",
        "domains": ["Ayurveda", "Traditional Medicine", "Medicine", "Nutraceutical", "Healthcare", "Traditional Knowledge"],
        "authority_level": "ministry",
        "source_priority": 1,
        "official": True,
        "base_url": "https://ayush.gov.in",
        "document_types": ["Rule 158B Guidelines", "Schedule T GMP", "Pharmacopoeial Standards", "Gazette Notifications", "DMR Act Guidelines"],
        "description": "Regulates education, research, formulation standards, and licensing for Ayurveda, Yoga & Naturopathy, Unani, Siddha, and Homoeopathy.",
        "active": True,
    },
    {
        "source_id": "pcimh_india",
        "name": "Pharmacopoeia Commission for Indian Medicine & Homoeopathy",
        "organization": "PCIM&H",
        "country": "India",
        "jurisdiction": "India",
        "domains": ["Ayurveda", "Traditional Medicine", "Drug", "Standard"],
        "authority_level": "statutory_regulator",
        "source_priority": 1,
        "official": True,
        "base_url": "https://pcimh.gov.in",
        "document_types": ["Ayurvedic Pharmacopoeia of India (API)", "Ayurvedic Formulary of India (AFI)", "Monographs", "Standards"],
        "description": "Official body under Ministry of AYUSH publishing official drug monographs, pharmacopoeial purity standards, and classical testing parameters for ASU drugs.",
        "active": True,
    },
    # Biodiversity & Access and Benefit Sharing (ABS)
    {
        "source_id": "nba_india",
        "name": "National Biodiversity Authority",
        "organization": "NBA",
        "country": "India",
        "jurisdiction": "India",
        "domains": ["Biodiversity", "ABS", "Traditional Knowledge", "Biotechnology", "Agriculture"],
        "authority_level": "statutory_regulator",
        "source_priority": 1,
        "official": True,
        "base_url": "https://nbaindia.gov.in",
        "document_types": ["Biological Diversity Act", "ABS Regulations", "Form I-IV Procedures", "Gazette Orders", "SBB Notifications"],
        "description": "Autonomous statutory body implementing the Biological Diversity Act, 2002 & 2023 Amendment; administers mandatory approvals for biological resource access and IPR commercialization.",
        "active": True,
    },
    {
        "source_id": "moefcc_india",
        "name": "Ministry of Environment, Forest and Climate Change",
        "organization": "MoEFCC",
        "country": "India",
        "jurisdiction": "India",
        "domains": ["Biodiversity", "Environmental Regulation", "Biotechnology", "ABS"],
        "authority_level": "ministry",
        "source_priority": 1,
        "official": True,
        "base_url": "https://moef.gov.in",
        "document_types": ["Statute", "Rules", "Notifications", "Environmental Impact Guidelines"],
        "description": "Union ministry administering wildlife, biodiversity, environment protection laws, and genetic engineering appraisal regulations.",
        "active": True,
    },
    # Traditional Knowledge & Prior Art Repositories
    {
        "source_id": "tkdl_india",
        "name": "Traditional Knowledge Digital Library",
        "organization": "CSIR / TKDL",
        "country": "India",
        "jurisdiction": "India",
        "domains": ["Traditional Knowledge", "Ayurveda", "Traditional Medicine", "Patent", "Prior Art"],
        "authority_level": "institutional",
        "source_priority": 2,
        "official": True,
        "base_url": "https://www.tkdl.res.in",
        "document_types": ["TKRC Classifications", "Formulation Prior Art Records", "Examiner Access Compacts"],
        "description": "Pioneering digital repository created by CSIR & Ministry of AYUSH translating over 4.5 lakh classical formulations into international languages for global patent examiners.",
        "active": True,
    },
    # Intellectual Property & Statutory Codes
    {
        "source_id": "ip_india",
        "name": "Office of the Controller General of Patents, Designs & Trade Marks",
        "organization": "CGPDTM / IP India",
        "country": "India",
        "jurisdiction": "India",
        "domains": ["IP", "Patent", "Trademark", "GI", "Design", "Traditional Knowledge"],
        "authority_level": "statutory_regulator",
        "source_priority": 1,
        "official": True,
        "base_url": "https://ipindia.gov.in",
        "document_types": ["Patents Act & Rules", "Trade Marks Act & Rules", "GI Act", "Manual of Patent Office Practice & Procedure", "Guidelines for Examination of TK Innovations"],
        "description": "Administers patent grants, trademark registrations, design protections, and geographical indications in India under DPIIT, Ministry of Commerce & Industry.",
        "active": True,
    },
    {
        "source_id": "india_code",
        "name": "India Code — Digital Repository of All Central and State Acts",
        "organization": "Legislative Department, Ministry of Law and Justice",
        "country": "India",
        "jurisdiction": "India",
        "domains": ["General Regulation", "IP", "Food", "Medicine", "Biodiversity", "Consumer Protection"],
        "authority_level": "statutory_repository",
        "source_priority": 1,
        "official": True,
        "base_url": "https://www.indiacode.nic.in",
        "document_types": ["Central Acts", "State Acts", "Subordinate Legislation", "Statutory Amendments"],
        "description": "Official government database containing all authentic up-to-date Central and State statutes as enacted and amended by the Parliament of India.",
        "active": True,
    },
    {
        "source_id": "egazette_india",
        "name": "The Gazette of India / e-Gazette",
        "organization": "Department of Publication, Govt. of India",
        "country": "India",
        "jurisdiction": "India",
        "domains": ["General Regulation", "Official Notification", "Amendment"],
        "authority_level": "official_gazette",
        "source_priority": 1,
        "official": True,
        "base_url": "https://egazette.gov.in",
        "document_types": ["Extraordinary Gazettes", "Statutory Notifications", "Commencement Dates", "Amending Acts"],
        "description": "Official public journal and primary legal publication authority of the Government of India for bringing statutory rules and amendments into legal force.",
        "active": True,
    },
    # Plant Varieties & Agricultural Standards
    {
        "source_id": "ppvfra_india",
        "name": "Protection of Plant Varieties and Farmers' Rights Authority",
        "organization": "PPV&FRA",
        "country": "India",
        "jurisdiction": "India",
        "domains": ["Plant Variety", "Agriculture", "Biodiversity", "Traditional Knowledge"],
        "authority_level": "statutory_regulator",
        "source_priority": 1,
        "official": True,
        "base_url": "https://plantauthority.gov.in",
        "document_types": ["PPV&FR Act", "Crop DUS Guidelines", "Registrations", "Farmers' Rights Compendiums"],
        "description": "Statutory body established under the PPV&FR Act, 2001 protecting plant breeders' rights, extant varieties, and farmers' traditional conservation rights in India.",
        "active": True,
    },
    # Metrology, Consumer Protection & Packaging
    {
        "source_id": "legal_metrology_india",
        "name": "Department of Consumer Affairs — Legal Metrology Division",
        "organization": "Legal Metrology",
        "country": "India",
        "jurisdiction": "India",
        "domains": ["Packaging/Labelling", "Consumer Protection", "Food", "Medicine", "General Regulation"],
        "authority_level": "statutory_regulator",
        "source_priority": 1,
        "official": True,
        "base_url": "https://consumeraffairs.nic.in",
        "document_types": ["Legal Metrology Act, 2009", "Packaged Commodities Rules, 2011", "Mandatory Label Declarations"],
        "description": "Enforces mandatory declarations on pre-packaged goods including MRP, net quantity, manufacturer/packer details, consumer care contacts, and country of origin.",
        "active": True,
    },
    # Biotechnology & Medical Research Ethics
    {
        "source_id": "dbt_icmr_india",
        "name": "Department of Biotechnology & ICMR",
        "organization": "DBT / ICMR",
        "country": "India",
        "jurisdiction": "India",
        "domains": ["Biotechnology", "Clinical/Medical Research", "Research Ethics", "Healthcare"],
        "authority_level": "statutory_regulator",
        "source_priority": 2,
        "official": True,
        "base_url": "https://dbtindia.gov.in",
        "document_types": ["Recombinant DNA Guidelines", "Bio-safety Rules", "ICMR Ethical Guidelines for Biomedical Research"],
        "description": "Regulatory oversight for genetic engineering, bio-safety, clinical research protocols, and ethical clearances for biomedical and AYUSH clinical studies.",
        "active": True,
    },

    # =========================================================================
    # 2. INTERNATIONAL & GLOBAL REGULATORY BODIES
    # =========================================================================
    {
        "source_id": "who_global",
        "name": "World Health Organization",
        "organization": "WHO",
        "country": "Global",
        "jurisdiction": "International",
        "domains": ["Healthcare", "Medicine", "Traditional Medicine", "Ayurveda", "Research Ethics", "Food Safety"],
        "authority_level": "international_body",
        "source_priority": 3,
        "official": True,
        "base_url": "https://www.who.int",
        "document_types": ["WHO Traditional Medicine Strategy", "Guidelines on Good Agricultural and Collection Practices (GACP)", "Pharmacopoeia Standards", "Technical Reports"],
        "description": "United Nations specialized agency for international public health; issues normative guidelines for traditional medicine safety, herbal quality control, and clinical research methodologies.",
        "active": True,
    },
    {
        "source_id": "wipo_lex_global",
        "name": "World Intellectual Property Organization & WIPO Lex",
        "organization": "WIPO",
        "country": "Global",
        "jurisdiction": "International",
        "domains": ["IP", "Patent", "Trademark", "Copyright", "Design", "Traditional Knowledge", "ABS", "Plant Variety"],
        "authority_level": "international_body",
        "source_priority": 1,
        "official": True,
        "base_url": "https://www.wipo.int/wipolex",
        "document_types": ["International Treaties (PCT, Madrid, Paris, Berne, 2024 GR/TK Treaty)", "National IP Laws Repository", "Treaty Status Databases"],
        "description": "Global forum for IP services, policy, and information; maintains WIPO Lex repository of national laws and administers international IP filing treaties.",
        "active": True,
    },
    {
        "source_id": "wto_trips_global",
        "name": "World Trade Organization (TRIPS Agreement)",
        "organization": "WTO",
        "country": "Global",
        "jurisdiction": "International",
        "domains": ["IP", "Patent", "International IP", "Import/Export", "General Regulation"],
        "authority_level": "international_body",
        "source_priority": 1,
        "official": True,
        "base_url": "https://www.wto.org",
        "document_types": ["TRIPS Agreement Articles", "Dispute Settlement Reports", "Doha Declaration on TRIPS & Public Health"],
        "description": "Multilateral agreement setting minimum standards for national IP regulation and subject matter patentability exclusions.",
        "active": True,
    },
    {
        "source_id": "cbd_nagoya_global",
        "name": "Convention on Biological Diversity & Nagoya Protocol Secretariat",
        "organization": "CBD / UNEP",
        "country": "Global",
        "jurisdiction": "International",
        "domains": ["Biodiversity", "ABS", "Traditional Knowledge", "Environmental Regulation"],
        "authority_level": "international_body",
        "source_priority": 1,
        "official": True,
        "base_url": "https://www.cbd.int",
        "document_types": ["Nagoya Protocol Articles", "Access and Benefit-Sharing Clearing-House (ABSCH)", "COP Decisions"],
        "description": "International treaty governance on conservation, sustainable use, and fair & equitable sharing of benefits arising out of genetic resource utilization (PIC & MAT).",
        "active": True,
    },
    {
        "source_id": "codex_alimentarius_global",
        "name": "Codex Alimentarius Commission (FAO / WHO)",
        "organization": "Codex Alimentarius",
        "country": "Global",
        "jurisdiction": "International",
        "domains": ["Food", "Food Safety", "Packaging/Labelling", "Import/Export"],
        "authority_level": "international_body",
        "source_priority": 2,
        "official": True,
        "base_url": "https://www.fao.org/fao-who-codexalimentarius",
        "document_types": ["International Food Standards", "Codes of Practice", "Pesticide MRLs", "Contaminant Thresholds"],
        "description": "International food standards body established by FAO and WHO to protect consumer health and ensure fair trade practices in global food commerce.",
        "active": True,
    },
    {
        "source_id": "upov_global",
        "name": "International Union for the Protection of New Varieties of Plants",
        "organization": "UPOV",
        "country": "Global",
        "jurisdiction": "International",
        "domains": ["Plant Variety", "Agriculture", "IP"],
        "authority_level": "international_body",
        "source_priority": 1,
        "official": True,
        "base_url": "https://www.upov.int",
        "document_types": ["UPOV Conventions (1978/1991)", "DUS Test Guidelines", "Plant Breeders' Rights Compendia"],
        "description": "Intergovernmental organization providing and promoting an effective system of plant variety protection across member states.",
        "active": True,
    },

    # =========================================================================
    # 3. UNITED STATES OF AMERICA
    # =========================================================================
    {
        "source_id": "fda_us",
        "name": "United States Food and Drug Administration",
        "organization": "US FDA",
        "country": "USA",
        "jurisdiction": "USA",
        "domains": ["Medicine", "Drug", "Food", "Food Safety", "Nutraceutical", "Cosmetic", "Medical Device", "Packaging/Labelling", "Advertising/Claims"],
        "authority_level": "statutory_regulator",
        "source_priority": 1,
        "official": True,
        "base_url": "https://www.fda.gov",
        "document_types": ["21 CFR (Code of Federal Regulations)", "FDA Guidance for Industry: Botanical Drug Development", "DSHEA (Dietary Supplements)", "IND/NDA Pathways", "Food Safety Modernization Act (FSMA)"],
        "description": "Federal agency of the US Department of Health and Human Services regulating pharmaceuticals, biological products, medical devices, food safety, dietary supplements, and cosmetics.",
        "active": True,
    },
    {
        "source_id": "usda_us",
        "name": "United States Department of Agriculture",
        "organization": "USDA",
        "country": "USA",
        "jurisdiction": "USA",
        "domains": ["Food", "Agriculture", "Plant Variety", "Biotechnology", "Import/Export"],
        "authority_level": "ministry",
        "source_priority": 1,
        "official": True,
        "base_url": "https://www.usda.gov",
        "document_types": ["National Organic Program (NOP)", "APHIS Biotechnology Regulations", "Food Safety and Inspection Service (FSIS) Rules"],
        "description": "US federal executive department responsible for developing and executing federal laws related to farming, forestry, rural economic development, and food standards.",
        "active": True,
    },
    {
        "source_id": "uspto_us",
        "name": "United States Patent and Trademark Office",
        "organization": "USPTO",
        "country": "USA",
        "jurisdiction": "USA",
        "domains": ["IP", "Patent", "Trademark", "Traditional Knowledge"],
        "authority_level": "patent_office",
        "source_priority": 1,
        "official": True,
        "base_url": "https://www.uspto.gov",
        "document_types": ["35 U.S.C. (Patent Act)", "37 CFR", "MPEP (Manual of Patent Examining Procedure)", "Subject Matter Eligibility (Alice/Mayo Guidelines)", "TKDL Access Compendium"],
        "description": "US federal agency granting US patents and registering trademarks under Title 35 of the United States Code.",
        "active": True,
    },

    # =========================================================================
    # 4. EUROPEAN UNION
    # =========================================================================
    {
        "source_id": "ema_eu",
        "name": "European Medicines Agency",
        "organization": "EMA",
        "country": "European Union",
        "jurisdiction": "European Union",
        "domains": ["Medicine", "Drug", "Traditional Medicine", "Ayurveda", "Clinical/Medical Research", "Healthcare"],
        "authority_level": "statutory_regulator",
        "source_priority": 1,
        "official": True,
        "base_url": "https://www.ema.europa.eu",
        "document_types": ["Traditional Herbal Medicinal Products Directive (THMPD 2004/24/EC)", "HMPC Herbal Monographs", "Centralised Marketing Authorisation Rules", "Good Clinical Practice (GCP) Guidelines"],
        "description": "European Union agency responsible for the scientific evaluation, supervision and safety monitoring of medicines developed by pharmaceutical companies for use in the EU.",
        "active": True,
    },
    {
        "source_id": "efsa_eu",
        "name": "European Food Safety Authority",
        "organization": "EFSA",
        "country": "European Union",
        "jurisdiction": "European Union",
        "domains": ["Food", "Food Safety", "Nutraceutical", "Packaging/Labelling", "Advertising/Claims"],
        "authority_level": "statutory_regulator",
        "source_priority": 1,
        "official": True,
        "base_url": "https://www.efsa.europa.eu",
        "document_types": ["EU General Food Law (Regulation EC 178/2002)", "Novel Food Regulation (EU 2015/2283)", "Health Claims Register (Regulation EC 1924/2006)", "Food Supplements Directive"],
        "description": "European agency that delivers independent scientific advice and communicates on existing and emerging risks associated with the food chain across the European Union.",
        "active": True,
    },
    {
        "source_id": "eurlex_eu",
        "name": "EUR-Lex — European Union Law",
        "organization": "European Commission",
        "country": "European Union",
        "jurisdiction": "European Union",
        "domains": ["General Regulation", "Food", "Medicine", "ABS", "IP", "Consumer Protection"],
        "authority_level": "statutory_repository",
        "source_priority": 1,
        "official": True,
        "base_url": "https://eur-lex.europa.eu",
        "document_types": ["EU Regulations", "EU Directives", "EU Decisions", "EU Nagoya Compliance Regulation 511/2014"],
        "description": "Official access point to European Union law, including all binding Regulations, Directives, Decisions, and consolidated legislative texts.",
        "active": True,
    },
    {
        "source_id": "epo_eu",
        "name": "European Patent Office",
        "organization": "EPO",
        "country": "European Union",
        "jurisdiction": "European Union",
        "domains": ["IP", "Patent", "Traditional Knowledge"],
        "authority_level": "patent_office",
        "source_priority": 1,
        "official": True,
        "base_url": "https://www.epo.org",
        "document_types": ["European Patent Convention (EPC Articles 52-57)", "Guidelines for Examination", "Boards of Appeal Case Law (Neem Case Precedent)"],
        "description": "Examines and grants European patents across 39 member states under the European Patent Convention.",
        "active": True,
    },
    {
        "source_id": "euipo_eu",
        "name": "European Union Intellectual Property Office",
        "organization": "EUIPO",
        "country": "European Union",
        "jurisdiction": "European Union",
        "domains": ["IP", "Trademark", "Design", "GI"],
        "authority_level": "patent_office",
        "source_priority": 1,
        "official": True,
        "base_url": "https://euipo.europa.eu",
        "document_types": ["European Union Trade Mark (EUTM) Regulations", "Registered Community Design (RCD) Regulations"],
        "description": "Administers EU Trade Marks and Registered Community Designs valid across all 27 EU member states.",
        "active": True,
    },

    # =========================================================================
    # 5. UNITED KINGDOM
    # =========================================================================
    {
        "source_id": "mhra_uk",
        "name": "Medicines and Healthcare products Regulatory Agency",
        "organization": "MHRA",
        "country": "UK",
        "jurisdiction": "UK",
        "domains": ["Medicine", "Drug", "Medical Device", "Traditional Medicine", "Healthcare"],
        "authority_level": "statutory_regulator",
        "source_priority": 1,
        "official": True,
        "base_url": "https://www.gov.uk/government/organisations/medicines-and-healthcare-products-regulatory-agency",
        "document_types": ["Human Medicines Regulations 2012", "Traditional Herbal Registration (THR) Scheme", "Medical Devices Regulations"],
        "description": "UK executive agency regulating medicines, medical devices and herbal traditional remedies in the United Kingdom.",
        "active": True,
    },
    {
        "source_id": "fsa_uk",
        "name": "Food Standards Agency",
        "organization": "FSA",
        "country": "UK",
        "jurisdiction": "UK",
        "domains": ["Food", "Food Safety", "Nutraceutical", "Packaging/Labelling"],
        "authority_level": "statutory_regulator",
        "source_priority": 1,
        "official": True,
        "base_url": "https://www.food.gov.uk",
        "document_types": ["Food Safety Act 1990", "Novel Foods Guidance", "Food Supplement Guidelines", "Allergen Labelling Standards"],
        "description": "Non-ministerial government department responsible for public health and safety in relation to food in England, Wales, and Northern Ireland.",
        "active": True,
    },
    {
        "source_id": "ukipo_uk",
        "name": "Intellectual Property Office (UKIPO)",
        "organization": "UKIPO",
        "country": "UK",
        "jurisdiction": "UK",
        "domains": ["IP", "Patent", "Trademark", "Design", "Copyright"],
        "authority_level": "patent_office",
        "source_priority": 1,
        "official": True,
        "base_url": "https://www.gov.uk/government/organisations/intellectual-property-office",
        "document_types": ["Patents Act 1977", "Trade Marks Act 1994", "Manual of Patent Practice (MOPP)"],
        "description": "Official UK government body responsible for intellectual property rights including Patents, Designs, Trade Marks and Copyright.",
        "active": True,
    },

    # =========================================================================
    # 6. CHINA
    # =========================================================================
    {
        "source_id": "nmpa_china",
        "name": "National Medical Products Administration",
        "organization": "NMPA",
        "country": "China",
        "jurisdiction": "China",
        "domains": ["Medicine", "Drug", "Traditional Medicine", "Medical Device", "Cosmetic", "Healthcare"],
        "authority_level": "statutory_regulator",
        "source_priority": 1,
        "official": True,
        "base_url": "https://www.nmpa.gov.cn",
        "document_types": ["Drug Administration Law of the PRC", "Regulations on Traditional Chinese Medicine (TCM)", "Cosmetic Supervision and Administration Regulations"],
        "description": "Chinese national agency directly under the State Administration for Market Regulation responsible for drug, TCM, medical device, and cosmetic regulation.",
        "active": True,
    },
    {
        "source_id": "samr_china",
        "name": "State Administration for Market Regulation",
        "organization": "SAMR",
        "country": "China",
        "jurisdiction": "China",
        "domains": ["Food", "Food Safety", "Nutraceutical", "Consumer Protection", "Packaging/Labelling", "Advertising/Claims"],
        "authority_level": "statutory_regulator",
        "source_priority": 1,
        "official": True,
        "base_url": "https://www.samr.gov.cn",
        "document_types": ["Food Safety Law of the PRC", "Health Food Registration and Filing Measures", "National Food Safety Standards (GB Standards)"],
        "description": "Ministerial-level executive agency responsible for market supervision, food safety, health food ('Blue Hat' registration), anti-monopoly, and pricing regulation.",
        "active": True,
    },
    {
        "source_id": "cnipa_china",
        "name": "China National Intellectual Property Administration",
        "organization": "CNIPA",
        "country": "China",
        "jurisdiction": "China",
        "domains": ["IP", "Patent", "Trademark", "GI", "Traditional Knowledge"],
        "authority_level": "patent_office",
        "source_priority": 1,
        "official": True,
        "base_url": "https://www.cnipa.gov.cn",
        "document_types": ["Patent Law of the PRC", "Guidelines for Patent Examination", "TCM Patent Examination Guidelines", "Genetic Resource Origin Disclosure Rules (Article 26.5)"],
        "description": "National patent and trademark office of the People's Republic of China.",
        "active": True,
    },

    # =========================================================================
    # 7. JAPAN
    # =========================================================================
    {
        "source_id": "pmda_mhlw_japan",
        "name": "Pharmaceuticals and Medical Devices Agency & MHLW",
        "organization": "PMDA / MHLW",
        "country": "Japan",
        "jurisdiction": "Japan",
        "domains": ["Medicine", "Drug", "Traditional Medicine", "Medical Device", "Cosmetic", "Healthcare"],
        "authority_level": "statutory_regulator",
        "source_priority": 1,
        "official": True,
        "base_url": "https://www.pmda.go.jp",
        "document_types": ["PMD Act (Pharmaceuticals and Medical Devices Act)", "Japanese Pharmacopoeia (JP)", "Kampo (Traditional Medicine) Approval Standards"],
        "description": "Japanese regulatory agency responsible for ensuring the safety, efficacy, and quality of pharmaceuticals, Kampo traditional preparations, and medical devices.",
        "active": True,
    },
    {
        "source_id": "caa_maff_japan",
        "name": "Consumer Affairs Agency & MAFF Japan",
        "organization": "CAA / MAFF",
        "country": "Japan",
        "jurisdiction": "Japan",
        "domains": ["Food", "Food Safety", "Nutraceutical", "Agriculture", "Packaging/Labelling"],
        "authority_level": "statutory_regulator",
        "source_priority": 1,
        "official": True,
        "base_url": "https://www.caa.go.jp",
        "document_types": ["Food Sanitation Act", "FOSHU (Foods for Specified Health Uses) Standards", "Foods with Function Claims (FFC) Guidelines"],
        "description": "Administers Japan's world-renowned functional food regulatory frameworks including FOSHU and FFC systems.",
        "active": True,
    },
    {
        "source_id": "jpo_japan",
        "name": "Japan Patent Office",
        "organization": "JPO",
        "country": "Japan",
        "jurisdiction": "Japan",
        "domains": ["IP", "Patent", "Trademark", "Design", "Traditional Knowledge"],
        "authority_level": "patent_office",
        "source_priority": 1,
        "official": True,
        "base_url": "https://www.jpo.go.jp",
        "document_types": ["Patent Act of Japan", "Examination Guidelines for Patent and Utility Model", "TKDL Search Agreements"],
        "description": "Japanese government agency administering patent grants, design registrations, and trademark rights under METI.",
        "active": True,
    },

    # =========================================================================
    # 8. OTHER PRIORITY REGULATORY AUTHORITIES
    # =========================================================================
    {
        "source_id": "tga_australia",
        "name": "Therapeutic Goods Administration (Australia)",
        "organization": "TGA",
        "country": "Australia",
        "jurisdiction": "Australia",
        "domains": ["Medicine", "Drug", "Traditional Medicine", "Ayurveda", "Nutraceutical", "Medical Device"],
        "authority_level": "statutory_regulator",
        "source_priority": 1,
        "official": True,
        "base_url": "https://www.tga.gov.au",
        "document_types": ["Therapeutic Goods Act 1989", "Complementary Medicines Guidelines (Listed vs Registered)", "Australian Register of Therapeutic Goods (ARTG)"],
        "description": "Australian regulatory body for therapeutic goods including prescription medicines, vaccines, medical devices, and complementary/herbal/Ayurvedic medicines.",
        "active": True,
    },
    {
        "source_id": "hsa_singapore",
        "name": "Health Sciences Authority (Singapore)",
        "organization": "HSA",
        "country": "Singapore",
        "jurisdiction": "Singapore",
        "domains": ["Medicine", "Drug", "Traditional Medicine", "Health Supplements", "Cosmetic", "Medical Device"],
        "authority_level": "statutory_regulator",
        "source_priority": 1,
        "official": True,
        "base_url": "https://www.hsa.gov.sg",
        "document_types": ["Health Products Act", "Medicines Act", "Chinese Proprietary Medicines (CPM) & Health Supplements Guidelines"],
        "description": "Singapore statutory board regulating health products, health supplements, traditional medicines, and medical devices.",
        "active": True,
    },
    {
        "source_id": "anvisa_brazil",
        "name": "Agência Nacional de Vigilância Sanitária (ANVISA Brazil)",
        "organization": "ANVISA",
        "country": "Brazil",
        "jurisdiction": "Brazil",
        "domains": ["Medicine", "Drug", "Food", "Traditional Medicine", "Cosmetic", "Medical Device", "Biodiversity"],
        "authority_level": "statutory_regulator",
        "source_priority": 1,
        "official": True,
        "base_url": "https://www.gov.br/anvisa",
        "document_types": ["RDC Resolutions", "Phytotherapeutic Medicines Regulations", "Food Supplement Normatives"],
        "description": "Brazilian regulatory agency exercising sanitary control over all products including medicines, health foods, cosmetics, and medical devices.",
        "active": True,
    },
    {
        "source_id": "sahpra_south_africa",
        "name": "South African Health Products Regulatory Authority",
        "organization": "SAHPRA",
        "country": "South Africa",
        "jurisdiction": "South Africa",
        "domains": ["Medicine", "Drug", "Traditional Medicine", "Complementary Medicine", "Medical Device"],
        "authority_level": "statutory_regulator",
        "source_priority": 1,
        "official": True,
        "base_url": "https://www.sahpra.org.za",
        "document_types": ["Medicines and Related Substances Act", "Complementary Medicines Guidelines (Category D)"],
        "description": "South African regulatory authority for medicines, complementary medicines, medical devices, and clinical trials.",
        "active": True,
    },
]


def get_all_regulatory_sources() -> List[Dict[str, Any]]:
    """Returns the full list of authoritative regulatory sources."""
    return REGULATORY_SOURCES


def get_source_by_id(source_id: str) -> Optional[Dict[str, Any]]:
    """Lookup source metadata by source_id."""
    for s in REGULATORY_SOURCES:
        if s["source_id"] == source_id:
            return s
    return None


def get_sources_by_country(country: str) -> List[Dict[str, Any]]:
    """Filter sources by country/jurisdiction (case-insensitive)."""
    c_lower = country.lower()
    return [
        s for s in REGULATORY_SOURCES
        if s["country"].lower() == c_lower or s["jurisdiction"].lower() == c_lower
    ]


def get_sources_by_domain(domain: str) -> List[Dict[str, Any]]:
    """Filter sources containing a specific regulatory domain."""
    d_lower = domain.lower()
    return [
        s for s in REGULATORY_SOURCES
        if any(d.lower() == d_lower or d_lower in d.lower() for d in s["domains"])
    ]


def filter_sources(
    country: Optional[str] = None,
    domain: Optional[str] = None,
    max_priority: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Multi-attribute filtering over the regulatory registry."""
    results = REGULATORY_SOURCES
    if country and country not in ("All", "Auto Detect", "Global", "Unspecified"):
        c_lower = country.lower()
        results = [
            s for s in results
            if s["country"].lower() == c_lower or s["jurisdiction"].lower() == c_lower or s["country"] == "Global"
        ]
    if domain and domain not in ("All", "Auto Detect", "General Regulation"):
        d_lower = domain.lower()
        results = [
            s for s in results
            if any(d.lower() == d_lower or d_lower in d.lower() for d in s["domains"])
        ]
    if max_priority is not None:
        results = [s for s in results if s.get("source_priority", 5) <= max_priority]
    return results


if __name__ == "__main__":
    print(f"Regulatory Source Registry loaded: {len(REGULATORY_SOURCES)} total authoritative authorities.")
    india_sources = get_sources_by_country("India")
    print(f"  India: {len(india_sources)} sources (FSSAI, CDSCO, AYUSH, NBA, etc.)")
    food_sources = get_sources_by_domain("Food")
    print(f"  Food: {len(food_sources)} sources (FSSAI, FDA, EFSA, Codex, etc.)")
    ayurveda_sources = get_sources_by_domain("Ayurveda")
    print(f"  Ayurveda: {len(ayurveda_sources)} sources (AYUSH, PCIM&H, TKDL, WHO, etc.)")
