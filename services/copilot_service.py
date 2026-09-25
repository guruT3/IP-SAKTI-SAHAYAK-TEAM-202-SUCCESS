"""
IP-SAKTI SAHAYAK
AI Website Copilot Engine (Multi-Mode Conversational Orchestrator)
=====================================================================
Combines General AI Conversation (ChatGPT-style), Website Assistance
(Microsoft Copilot-style), and IP-SAKTI Domain Intelligence (Dual-RAG,
Knowledge Graph, Prior Art, Compliance Engine, Multilingual & Voice).
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from config import settings
from ai.llm import llm_client
from ai.multilingual import detect_language, normalize_language_code, translate_response, protect_terms, restore_terms
from ai.confidence import compute_confidence
from ai.abstention import check_abstention

logger = logging.getLogger(__name__)

# =====================================================================
# 1. WEBSITE KNOWLEDGE BASE & ROUTE MAP
# =====================================================================

WEBSITE_PAGES_REGISTRY = {
    "/": {
        "title": "Home / Platform Overview",
        "description": "Main landing overview of IP-SAKTI SAHAYAK highlighting dual-RAG, Knowledge Graph, prior art, and regulatory tools.",
        "features": ["Quick Overview", "Platform Architecture", "Feature Directory", "Live Metrics"],
        "suggested_prompts": [
            "What is IP-SAKTI Sahayak?",
            "How does the dual-RAG pipeline work?",
            "Show me available features",
            "Open Prior Art Search"
        ]
    },
    "/chat": {
        "title": "IP Intelligence Chat (RAG)",
        "description": "Interactive dual-mode (Quick & Deep) RAG assistant for Indian & Global Patent Laws, Section 3(d)/3(p)/3(e), and TKDL.",
        "features": ["IP Querying", "Quick vs Deep Mode", "Jurisdiction Filter", "Source Citations", "Claim Traceability"],
        "suggested_prompts": [
            "What is Section 3(d) of Indian Patents Act?",
            "Explain Section 3(p) for traditional knowledge",
            "How does TKDL prevent biopiracy?",
            "Compare Indian vs USPTO patentability criteria"
        ]
    },
    "/regulatory-rag": {
        "title": "Regulatory Intelligence RAG",
        "description": "Dedicated regulatory query engine covering FSSAI, AYUSH, FDA, EMA, Schedule T, and global nutraceutical regulations.",
        "features": ["Regulatory RAG Query", "Evidence Hierarchy", "Version & Effective Date Audit", "Authority Filter"],
        "suggested_prompts": [
            "What are FSSAI Ayurveda Aahara regulations?",
            "Explain AYUSH Rule 158B licensing requirements",
            "Show effective date for novel food regulations",
            "What regulations apply to botanical extracts?"
        ]
    },
    "/analyze-innovation": {
        "title": "Innovation & Patentability Analyzer",
        "description": "Flagship 5-stage assessment tool analyzing novelty, Section 3 bars, TKDL conflicts, BDA approval, and drafting recommendations.",
        "features": ["Multi-stage Patent Assessment", "Botanical & Formulation Parsing", "BDA Section 6 Compliance", "Patentability Score"],
        "suggested_prompts": [
            "How do I analyze my herbal formulation?",
            "What inputs are needed for innovation analysis?",
            "Explain the patentability scoring breakdown",
            "Check Section 3(e) admixture bar for my product"
        ]
    },
    "/comparative": {
        "title": "Comparative IP Law Matrix",
        "description": "Cross-jurisdictional legal engine comparing IP provisions across India (IP India), USA (USPTO), Europe (EPO), and WIPO.",
        "features": ["India vs Global Matrix", "Efficacy Standard Comparisons", "Disclosure Requirements", "Biopiracy Precedents"],
        "suggested_prompts": [
            "Compare Section 3(d) with US Utility standards",
            "How does EPO handle traditional medicine patents?",
            "What are WIPO 2024 Treaty disclosure rules?",
            "Explain Turmeric and Neem precedent cases"
        ]
    },
    "/prior-art": {
        "title": "Prior Art & TKDL Search Engine",
        "description": "Search engine for prior art patents, TKDL classical texts (Charaka/Sushruta), and published botanical literature.",
        "features": ["Prior Art Query", "TKDL Match Verification", "Patentability Obstacle Detection", "Relevance Scoring"],
        "suggested_prompts": [
            "Search prior art for Curcumin bio-enhancement",
            "Are there TKDL references for Ashwagandha joint pain?",
            "Why is my formulation considered prior art?",
            "Explain top prior art search results"
        ]
    },
    "/compliance": {
        "title": "Regulatory Compliance & Checklist Engine",
        "description": "Evidence-backed compliance generator for Herbal, Nutraceutical, Cosmeceutical, and Botanical products across global markets.",
        "features": ["Compliance Checklist Generation", "Mandatory Testing Rules", "Labeling & Claims Verification", "Gap Analysis"],
        "suggested_prompts": [
            "Generate compliance checklist for Herbal Dietary Supplement",
            "What are mandatory labeling rules for Ayurveda Aahara?",
            "Explain missing compliance items",
            "Check EU Novel Food compliance"
        ]
    },
    "/regulations": {
        "title": "Regulatory Sources & Timeline Feed",
        "description": "Authoritative registry of official gazettes, acts, rules, and live regulatory amendment timelines.",
        "features": ["Source Registry Explorer", "Amendment Timelines", "Authority Filter", "Official Document Download"],
        "suggested_prompts": [
            "Show authoritative regulatory sources",
            "What are recent AYUSH regulatory amendments?",
            "Find National Biodiversity Authority guidelines",
            "Filter sources by country"
        ]
    },
    "/knowledge-graph": {
        "title": "Ayurveda & IP Knowledge Graph",
        "description": "Interactive 2D/3D ontology graph mapping Botanicals, Phytochemical Actives, Classical Texts, Patents, and Statutory Sections.",
        "features": ["Entity Graph Visualization", "Relationship Filtering", "Dynamic Subgraph Search", "Entity Details Inspector"],
        "suggested_prompts": [
            "Explain Curcuma longa entity connections",
            "Show statutory links for Ashwagandha",
            "What entities are linked to Section 3(p)?",
            "Find connected classical texts"
        ]
    },
    "/documents": {
        "title": "Document Library & Ingestion Manager",
        "description": "Manage uploaded legal documents, acts, patent PDF files, and indexed text chunks.",
        "features": ["Document Upload", "Ingestion Status", "Chunk Viewer", "Metadata Tagging"],
        "suggested_prompts": [
            "How do I upload a legal document?",
            "What file formats are supported?",
            "View indexed document list",
            "Check ingestion status"
        ]
    },
    "/sources": {
        "title": "Authoritative IP & Web Sources",
        "description": "Registry of live verified databases including IP India, WIPO Patentscope, TKDL, FSSAI Portal, and PubMed.",
        "features": ["Web Source Status", "Live Crawler Feeds", "Source Priority Ranking", "Verification Badges"],
        "suggested_prompts": [
            "List active web sources",
            "How is source priority calculated?",
            "Is WIPO Patentscope live?",
            "Show verified legal databases"
        ]
    },
    "/dashboard": {
        "title": "Executive Dashboard & Risk Radar",
        "description": "Comprehensive analytics overview with regulatory risk radar, recent activity, and system metrics.",
        "features": ["Risk Radar Assessment", "Recent System Queries", "Filing Trends", "Activity Summary"],
        "suggested_prompts": [
            "Explain the Risk Radar scores",
            "What are key regulatory risks shown?",
            "Summarize platform activity",
            "Go to Innovation Analyzer"
        ]
    },
    "/ip-analytics": {
        "title": "Indian Patent Analytics (CGPDTM)",
        "description": "Filing statistics, grant rates, state-wise distribution, and e-filing metrics from CGPDTM.",
        "features": ["Filing Statistics", "Grant Rate Charts", "State Distribution Map", "Controller General Data Feed"],
        "suggested_prompts": [
            "Which state leads in patent filings?",
            "What is the total patent grant count?",
            "Explain CGPDTM online share metric",
            "Show state-wise patent stats"
        ]
    },
    "/benchmark": {
        "title": "System Benchmark & Quality Metrics",
        "description": "Evaluation dashboard measuring RAG precision, claim recall, citation accuracy, and response latency.",
        "features": ["RAG Evaluation Benchmark", "Retrieval Latency Charts", "Citation Precision Score", "Abstention Rate"],
        "suggested_prompts": [
            "What is the system citation accuracy score?",
            "How fast is quick mode vs deep mode?",
            "Explain RAG evaluation methodology",
            "Show benchmark results"
        ]
    },
    "/admin": {
        "title": "System Administration & Diagnostics",
        "description": "Backend index health, vector DB sizes, LLM connection status, and configuration management.",
        "features": ["Vector Store Size", "BM25 Index Size", "LLM Health Check", "Database Diagnostics"],
        "suggested_prompts": [
            "Check system health status",
            "How many vector chunks are indexed?",
            "Is the Groq LLM backend active?",
            "Show database status"
        ]
    }
}

CAPABILITIES_REGISTRY = {
    "general_chat": True,
    "general_knowledge": True,
    "coding_assistance": True,
    "writing_assistance": True,
    "ip_rag": True,
    "regulatory_rag": True,
    "knowledge_graph": True,
    "prior_art_search": True,
    "innovation_analysis": True,
    "comparative_ip": True,
    "compliance_engine": True,
    "report_generation": True,
    "multilingual": True,
    "voice_input": True,
    "voice_output": True,
    "navigation_assistance": True,
    "website_error_assistant": True,
    "diagnostic_mode": True,
}


# =====================================================================
# 2. CONTROLLED TOOL IMPLEMENTATION
# =====================================================================

def execute_tool(tool_name: str, params: Dict[str, Any], page_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes controlled tools with validated inputs and outputs.
    """
    try:
        if tool_name == "website_navigation_tool":
            target = (params.get("target") or "/").lower()
            matched_route = "/"
            for route, info in WEBSITE_PAGES_REGISTRY.items():
                route_slug = route.strip("/").replace("-", " ")
                if route != "/" and (route.lower() in target or route_slug in target or route_slug in target.replace("-", " ")):
                    matched_route = route
                    break
                if any(k in target for k in ["knowledge graph", "graph", "entity"]) and "knowledge-graph" in route:
                    matched_route = route
                    break
                if any(k in target for k in ["prior art", "tkdl"]) and "prior-art" in route:
                    matched_route = route
                    break
                if any(k in target for k in ["regulatory", "regulations"]) and ("regulatory-rag" in route or "regulations" in route):
                    matched_route = route
                    break
                if any(k in target for k in ["compliance"]) and "compliance" in route:
                    matched_route = route
                    break
                if any(k in target for k in ["innovation", "analyzer"]) and "analyze-innovation" in route:
                    matched_route = route
                    break

            info = WEBSITE_PAGES_REGISTRY.get(matched_route, WEBSITE_PAGES_REGISTRY["/"])
            return {
                "success": True,
                "action": "NAVIGATE",
                "target_route": matched_route,
                "title": info["title"],
                "description": info["description"],
                "message": f"I can take you to {info['title']} (`{matched_route}`)."
            }

        elif tool_name == "website_help_tool":
            query = params.get("query", "")
            current_route = page_context.get("current_route", "/")
            info = WEBSITE_PAGES_REGISTRY.get(current_route, WEBSITE_PAGES_REGISTRY["/"])
            return {
                "success": True,
                "current_page": info["title"],
                "description": info["description"],
                "features": info["features"],
                "all_pages": [{"route": r, "title": m["title"]} for r, m in WEBSITE_PAGES_REGISTRY.items()]
            }

        elif tool_name == "prior_art_tool":
            from services.prior_art_search import search_prior_art
            desc = params.get("description") or params.get("query") or ""
            jurisdiction = params.get("jurisdiction") or "India"
            if not desc:
                return {"success": False, "error": "Description required for prior art search."}
            res = search_prior_art(desc, jurisdiction=jurisdiction)
            return {
                "success": True,
                "query": desc,
                "patent_obstacles": res.get("patentability_obstacles", []),
                "tkdl_matches": res.get("tkdl_matches", []),
                "prior_art_documents": res.get("prior_art_documents", [])[:4],
                "summary": res.get("search_summary", "")
            }

        elif tool_name == "compliance_tool":
            from services.regulatory_compliance import generate_compliance_checklist
            desc = params.get("description") or params.get("query") or ""
            country = params.get("country") or "India"
            domain = params.get("domain") or "Nutraceutical"
            if not desc:
                return {"success": False, "error": "Product description required for compliance check."}
            res = generate_compliance_checklist(product_description=desc, country=country, domain=domain)
            return {
                "success": True,
                "product": desc,
                "country": country,
                "domain": domain,
                "overall_status": res.get("overall_status", "PENDING_VERIFICATION"),
                "checklist_summary": res.get("checklist_summary", ""),
                "mandatory_requirements": res.get("mandatory_requirements", [])[:5],
                "missing_compliance_items": res.get("missing_compliance_items", [])
            }

        elif tool_name == "knowledge_graph_tool":
            from services.knowledge_graph import get_dynamic_subgraph
            query = params.get("query", "")
            sub = get_dynamic_subgraph(query)
            return {
                "success": True,
                "query": query,
                "matched_nodes_count": len(sub.get("nodes", [])),
                "matched_edges_count": len(sub.get("edges", [])),
                "nodes_sample": [{"id": n["id"], "label": n["label"], "group": n["group"]} for n in sub.get("nodes", [])[:6]],
                "edges_sample": [{"source": e["source"], "target": e["target"], "relation": e["relation"]} for e in sub.get("edges", [])[:6]]
            }

        elif tool_name == "system_status_tool":
            from rag.vector_store import vector_store
            from regulatory.vector_store import regulatory_vector_store
            from regulatory.hybrid_search import regulatory_bm25_index
            from regulatory.registry import get_all_regulatory_sources
            return {
                "success": True,
                "vector_store_chunks": vector_store.size,
                "regulatory_vector_store_chunks": regulatory_vector_store.size,
                "regulatory_bm25_terms": regulatory_bm25_index.size,
                "regulatory_sources_count": len(get_all_regulatory_sources()),
                "llm_backend": bool(llm_client._get_client()),
                "groq_model": settings.GROQ_MODEL
            }

        else:
            return {"success": False, "error": f"Unknown tool '{tool_name}'"}

    except Exception as e:
        logger.exception("Error executing tool %s", tool_name)
        return {"success": False, "error": f"Tool execution error: {str(e)}"}


# =====================================================================
# 3. ENHANCED INTENT CLASSIFICATION & ROUTING
# =====================================================================

def classify_intent(query: str, page_context: Dict[str, Any]) -> str:
    """
    Classifies user prompt into multi-mode intents covering General AI,
    Website Operations, and IP/Regulatory Domain intelligence.
    """
    q = query.lower().strip()
    current_route = page_context.get("current_route", "/")

    # 1. Greetings (supports hi, hii, hiii, hello, hey, namaste, etc.)
    greeting_pattern = r'^(hi+|hello+|hey+|namaste+|greetings+|good\s*(morning|afternoon|evening)|hola|haei+|namaskar+)\b'
    if re.search(greeting_pattern, q) or q in ["hi", "hii", "hiii", "hello", "hey", "namaste", "हाए", "नमस्ते", "ନମସ୍କାର", "hi there", "hey there", "hello there"]:
        return "GREETING"

    # 2. Thank you
    if any(k in q for k in ["thanks", "thank you", "dhanyawad", "धन्यवाद", "ଧନ୍ୟବାଦ", "thx", "shukriya"]):
        return "THANK_YOU"

    # 3. Farewell
    if any(k in q for k in ["bye", "goodbye", "see you", "good night", "alvida", "अलबिदा"]):
        return "FAREWELL"

    # 4. Capability / Identity Query
    if any(k in q for k in ["what can you do", "who are you", "what are your capabilities", "help me", "what is your name", "who built you", "what do you do"]):
        return "CAPABILITY_QUERY"

    # 5. Casual Chat & Jokes
    if any(k in q for k in ["how are you", "tell me a joke", "tell a joke", "make me laugh", "how's it going", "how is it going", "tell me a story", "what's up", "what up", "how do you do"]):
        return "CASUAL_CHAT"

    # 6. Navigation triggers
    if any(k in q for k in ["go to", "open", "take me to", "navigate to", "show page", "where can i find", "open prior art", "open knowledge graph", "open compliance"]):
        return "NAVIGATION"

    # 7. Short Follow-Up / Pronoun Resolution
    if q in ["why", "how", "what", "which one", "explain it simply", "give me an example", "give an example", "explain simply", "more", "tell me more", "in hindi", "in odia", "show source", "explain that", "explain this", "this", "that", "these", "those", "continue", "what next", "simple", "short", "in detail"]:
        return "FOLLOW_UP"

    # 8. Specific feature domain triggers
    if "prior art" in q or "tkdl" in q or (current_route == "/prior-art" and ("search" in q or "patent" in q)):
        return "PRIOR_ART_QUERY"

    if "compliance" in q or "labeling" in q or "license" in q or "rule 158b" in q or current_route == "/compliance":
        return "COMPLIANCE_QUERY"

    if "knowledge graph" in q or "entity" in q or "curcumin" in q or "botanical" in q or current_route == "/knowledge-graph":
        return "KNOWLEDGE_GRAPH_QUERY"

    if "regulatory" in q or "fssai" in q or "ayush" in q or "fda" in q or "amendment" in q or current_route == "/regulatory-rag":
        return "REGULATORY_QUERY"

    # 9. Coding assistance
    if any(k in q for k in ["write a python", "code for", "program to", "def ", "function in", "sort an array", "binary search", "python script", "code example"]):
        return "CODING_ASSISTANCE"

    # 10. Writing & Brainstorming assistance
    if any(k in q for k in ["write an email", "ideas for my presentation", "brainstorm", "write an essay", "summarize this text", "rephrase", "write a short introduction", "write a description", "draft a letter"]):
        return "WRITING_ASSISTANCE"

    # 11. Website help triggers
    if any(k in q for k in ["how do i use", "what is this page", "what can i do here", "how does this work", "explain this page", "what is ip-sakti", "how do i search prior art", "how do i generate a report"]):
        return "WEBSITE_HELP"

    # 12. System health diagnostics
    if any(k in q for k in ["health", "status", "diagnostic", "vector index"]) or current_route == "/admin":
        return "SYSTEM_STATUS"

    # 13. Action triggers
    if any(k in q for k in ["run a search", "analyze my formulation", "generate report"]):
        return "ACTION_REQUEST"

    # 14. Check explicit IP & Statutory keywords
    ip_keywords = [
        "patent", "patents", "section 3", "section 6", "prior art", "fssai", "ayush", "rule 158b",
        "schedule t", "tkdl", "traditional knowledge", "biopiracy", "bda", "biological diversity",
        "claims", "infringement", "novelty", "inventive step", "statutory", "act", "patents act",
        "pct", "trips", "wipo", "ep-", "us-", "in-", "specification", "nutraceutical", "phytochemical",
        "botanical drug", "fda guidance", "compliance checklist", "ayurveda aahara", "monograph", "jurisdiction"
    ]
    if any(kw in q for kw in ip_keywords):
        return "IP_QUERY"

    # Default general queries without IP keywords to GENERAL_KNOWLEDGE
    return "GENERAL_KNOWLEDGE"


# =====================================================================
# 4. MAIN COPILOT ORCHESTRATION PIPELINE
# =====================================================================

def process_copilot_request(
    query: str,
    page_context: Optional[Dict[str, Any]] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    requested_language: Optional[str] = None,
    requested_voice_output: bool = False
) -> Dict[str, Any]:
    """
    Main entry point for AI Copilot processing. Handles general AI,
    website navigation, feature help, and IP domain intelligence seamlessly.
    """
    page_context = page_context or {}
    conversation_history = conversation_history or []
    current_route = page_context.get("current_route", "/")

    # 1. Language detection & normalization
    detected_lang = detect_language(query)
    user_lang = normalize_language_code(requested_language or detected_lang)

    # 2. Intent Classification
    intent = classify_intent(query, page_context)
    page_info = WEBSITE_PAGES_REGISTRY.get(current_route, WEBSITE_PAGES_REGISTRY["/"])

    logger.info("Copilot query: '%s' | Intent: %s | Route: %s | Lang: %s", query, intent, current_route, user_lang)

    # Defaults
    response_text = ""
    citations = []
    sources = []
    actions = []
    navigation_target = None
    confidence = 0.95
    confidence_level = "HIGH"

    # 3. Intent Routing

    # A. GREETINGS
    if intent == "GREETING":
        if user_lang == "hi":
            response_text = "नमस्ते! 🙏 मैं आपका IP-SAKTI Copilot हूँ। मैं सामान्य बातचीत कर सकता हूँ, वेबसाइट नेविगेट करने में सहायता कर सकता हूँ, या IP और पेटेंट सवालों के उत्तर दे सकता हूँ। आज मैं आपकी क्या मदद करूँ?"
        elif user_lang == "or":
            response_text = "ନମସ୍କାର! 🙏 ମୁଁ ଆପଣଙ୍କର IP-SAKTI Copilot | ମୁଁ ସାଧାରଣ ଆଲୋଚନା କରିପାରିବି, ୱେବସାଇଟ୍ ନେଭିଗେଟ୍ କରିବାରେ ସାହାଯ୍ୟ କରିପାରିବି, କିମ୍ବା IP ଏବଂ ପେଟେଣ୍ଟ ପ୍ରଶ୍ନର ଉତ୍ତର ଦେଇପାରିବି |"
        else:
            response_text = "Hi! 👋 I'm your IP-SAKTI Copilot. I can chat with you naturally, guide you through the platform, explain features, or answer IP and regulatory questions. What would you like to explore today?"

    # B. THANK YOU
    elif intent == "THANK_YOU":
        response_text = "You're very welcome! 😊 Feel free to ask anytime if you need further help with IP-SAKTI or general topics."

    # C. FAREWELL
    elif intent == "FAREWELL":
        response_text = "Goodbye! 👋 Have a wonderful day ahead, and feel free to return whenever you need assistance."

    # D. CASUAL CHAT & JOKES
    elif intent == "CASUAL_CHAT":
        if "joke" in query.lower():
            response_text = "Why did the patent attorney cross the road? To claim exclusive rights to the other side! 😄"
        else:
            response_text = "I'm doing great, thank you for asking! How can I assist you with your work or research today?"

    # E. CAPABILITY QUERY
    elif intent == "CAPABILITY_QUERY":
        response_text = (
            "I'm your **IP-SAKTI Copilot**, an AI assistant built into IP-SAKTI SAHAYAK.\n\n"
            "I can help you with:\n"
            "- 💬 **General AI Conversation & Questions** (Explain concepts, code, write emails, brainstorm)\n"
            "- 🔎 **IP & Patent Intelligence** (Section 3(d), 3(p), 3(e), TKDL, PCT treaties, patentability criteria)\n"
            "- 📚 **Regulatory Intelligence** (FSSAI, AYUSH, Rule 158B, FDA, EMA, Schedule T)\n"
            "- 🌿 **Prior Art & TKDL Search** (Classical Ayurveda texts & patent databases)\n"
            "- 🕸 **Knowledge Graph Exploration** (Entities, botanicals, statutory connections)\n"
            "- ✅ **Regulatory Compliance Engine** (Product checklists & gap analysis)\n"
            "- 🧭 **Website Navigation & Guidance** (Direct deep links to platform tools)\n"
            "- 🌐 **Multilingual Support** (English, Hindi, and Odia)\n"
            "- 🎙 **Voice AI** (Speech input & text-to-speech output)\n\n"
            "You can also simply talk to me like ChatGPT!"
        )

    # F. GENERAL KNOWLEDGE / CODING / WRITING (No legal RAG required)
    elif intent in ["GENERAL_KNOWLEDGE", "CODING_ASSISTANCE", "WRITING_ASSISTANCE"]:
        system_prompt = (
            "You are a helpful, intelligent, friendly AI assistant built into IP-SAKTI SAHAYAK. "
            "Answer the user's general knowledge, programming, or writing query accurately, clearly, and naturally. "
            "Do NOT pretend the answer comes from legal sources or state that it is unrelated to IP-SAKTI."
        )
        llm_res = llm_client.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ], temperature=0.3, max_tokens=700)
        
        response_text = llm_res.text if llm_res.success else f"Here is an explanation for **{query}**:\n\nIt is a core concept that can be applied effectively across modern technologies and research workflows."

    # G. NAVIGATION
    elif intent == "NAVIGATION":
        tool_res = execute_tool("website_navigation_tool", {"target": query}, page_context)
        navigation_target = tool_res.get("target_route")
        response_text = f"You can find **{tool_res.get('title')}** at `{navigation_target}`. Click the action button below to go directly there!"
        actions.append({
            "type": "NAVIGATE",
            "label": f"Open {tool_res.get('title')}",
            "route": navigation_target
        })

    # H. WEBSITE HELP
    elif intent == "WEBSITE_HELP":
        tool_res = execute_tool("website_help_tool", {"query": query}, page_context)
        current_page_title = tool_res.get("current_page")
        desc = tool_res.get("description")
        features_list = ", ".join(tool_res.get("features", []))
        response_text = (
            f"You are currently on **{current_page_title}**.\n\n"
            f"**Purpose:** {desc}\n\n"
            f"**Key Features on this page:** {features_list}.\n\n"
            f"You can ask me questions about any module, search legal regulations, check prior art, or navigate across IP-SAKTI SAHAYAK."
        )
        actions.append({"type": "NAVIGATE", "label": "Explore Knowledge Graph", "route": "/knowledge-graph"})
        actions.append({"type": "NAVIGATE", "label": "Open Prior Art Search", "route": "/prior-art"})

    # I. PRIOR ART QUERY
    elif intent == "PRIOR_ART_QUERY":
        tool_res = execute_tool("prior_art_tool", {"query": query, "jurisdiction": page_context.get("jurisdiction", "India")}, page_context)
        if tool_res.get("success"):
            summary = tool_res.get("summary", "")
            obstacles = tool_res.get("patent_obstacles", [])
            docs = tool_res.get("prior_art_documents", [])

            response_text = f"### Prior Art Analysis Results\n\n{summary}\n\n"
            if obstacles:
                response_text += "**Identified Patentability Obstacles:**\n" + "\n".join([f"- {o}" for o in obstacles]) + "\n\n"
            if docs:
                response_text += "**Top Prior Art References Found:**\n"
                for d in docs:
                    response_text += f"- **{d.get('title')}** ({d.get('source')}): {d.get('relevance_reason', '')}\n"

            actions.append({"type": "NAVIGATE", "label": "Go to Prior Art Search Tool", "route": "/prior-art"})
        else:
            response_text = f"I couldn't complete the prior art query: {tool_res.get('error')}"

    # J. COMPLIANCE QUERY
    elif intent == "COMPLIANCE_QUERY":
        tool_res = execute_tool("compliance_tool", {"query": query, "country": page_context.get("country", "India")}, page_context)
        if tool_res.get("success"):
            response_text = (
                f"### Regulatory Compliance Overview ({tool_res.get('country')})\n\n"
                f"**Overall Status:** `{tool_res.get('overall_status')}`\n\n"
                f"{tool_res.get('checklist_summary')}\n\n"
            )
            reqs = tool_res.get("mandatory_requirements", [])
            if reqs:
                response_text += "**Key Mandatory Requirements:**\n"
                for r in reqs:
                    response_text += f"- **{r.get('category')}**: {r.get('requirement')} *(Authority: {r.get('authority')})*\n"

            actions.append({"type": "NAVIGATE", "label": "Open Full Compliance Checker", "route": "/compliance"})
        else:
            response_text = f"Compliance check error: {tool_res.get('error')}"

    # K. KNOWLEDGE GRAPH QUERY
    elif intent == "KNOWLEDGE_GRAPH_QUERY":
        tool_res = execute_tool("knowledge_graph_tool", {"query": query}, page_context)
        if tool_res.get("success"):
            sample_nodes = tool_res.get("nodes_sample", [])
            response_text = (
                f"### Knowledge Graph Entity Inspection\n\n"
                f"Found **{tool_res.get('matched_nodes_count')} connected entities** and **{tool_res.get('matched_edges_count')} relationships** matching your query.\n\n"
                f"**Key Entities:**\n"
            )
            for n in sample_nodes:
                response_text += f"- **{n['label']}** ({n['group']})\n"

            actions.append({"type": "NAVIGATE", "label": "View Interactive 3D Knowledge Graph", "route": "/knowledge-graph"})
        else:
            response_text = f"Knowledge Graph lookup error: {tool_res.get('error')}"

    # L. SYSTEM STATUS
    elif intent == "SYSTEM_STATUS":
        tool_res = execute_tool("system_status_tool", {}, page_context)
        response_text = (
            f"### IP-SAKTI SAHAYAK System Health Diagnostics\n\n"
            f"- **Vector Index Chunks (IP):** `{tool_res.get('vector_store_chunks')}`\n"
            f"- **Regulatory Vector Chunks:** `{tool_res.get('regulatory_vector_store_chunks')}`\n"
            f"- **Regulatory BM25 Index Size:** `{tool_res.get('regulatory_bm25_terms')}`\n"
            f"- **Registered Regulatory Sources:** `{tool_res.get('regulatory_sources_count')}`\n"
            f"- **LLM Engine:** Groq `{tool_res.get('groq_model')}` (Active: `{tool_res.get('llm_backend')}`)\n"
        )

    # M. FOLLOW-UP QUESTIONS (Context Resolution)
    elif intent == "FOLLOW_UP":
        last_user_msg = conversation_history[-2]["content"] if len(conversation_history) >= 2 else "previous query"
        last_asst_msg = conversation_history[-1]["content"] if len(conversation_history) >= 1 else ""
        
        system_prompt = (
            f"You are the IP-SAKTI Copilot. Resolve the user's short follow-up '{query}' in the context of "
            f"the previous discussion about '{last_user_msg}' and current page '{page_info['title']}'. "
            f"Provide a direct, natural, and helpful response."
        )
        llm_res = llm_client.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Previous conversation snippet:\n{last_asst_msg[:400]}\n\nUser follow-up: {query}"}
        ], temperature=0.2, max_tokens=600)
        
        response_text = llm_res.text if llm_res.success else f"Regarding your follow-up on {last_user_msg}: {page_info['description']}"

    # N. GROUNDED DOMAIN IP / REGULATORY RAG QUERY
    else:
        from rag.rag_pipeline import answer_query
        rag_res = answer_query(query, requested_jurisdiction=page_context.get("jurisdiction"), requested_language="en", mode="quick")
        
        response_text = rag_res.answer
        citations = rag_res.citations
        sources = rag_res.sources
        confidence = rag_res.confidence
        confidence_level = rag_res.confidence_level

    # 4. Multilingual Translation if needed (preserving protected terms)
    if user_lang != "en" and response_text and intent not in ["GREETING", "THANK_YOU", "FAREWELL"]:
        try:
            response_text = translate_response(response_text, user_lang, lambda t, l: llm_client.chat([
                {"role": "system", "content": f"You are a professional legal & technical translator. Translate the text accurately to {l}. Preserve all protected tokens like __PROTECTED_0__ exactly without modification."},
                {"role": "user", "content": t}
            ]).text)
        except Exception as e:
            logger.warning("Multilingual translation in Copilot failed (%s), returning English.", e)

    # 5. Build context-aware suggested prompts for next turn
    next_suggestions = page_info.get("suggested_prompts", [
        "What is Section 3(d)?",
        "Search prior art",
        "Open Knowledge Graph",
        "Check regulatory compliance"
    ])

    return {
        "success": True,
        "query": query,
        "intent": intent,
        "language": user_lang,
        "current_page": page_info["title"],
        "current_route": current_route,
        "message": response_text,
        "confidence": confidence,
        "confidence_level": confidence_level,
        "citations": citations,
        "sources": sources,
        "actions": actions,
        "navigation_target": navigation_target,
        "suggested_prompts": next_suggestions,
        "capabilities": CAPABILITIES_REGISTRY,
        "voice_supported": True
    }
