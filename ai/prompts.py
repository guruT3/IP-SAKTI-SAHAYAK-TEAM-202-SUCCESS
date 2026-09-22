"""
IP-SAKTI SAHAYAK
Prompt Templates
=================
Builds the grounded RAG prompt sent to Groq. Encodes the non-negotiable
rules from spec Section 22 directly into the system prompt: answer only
from evidence, never fabricate citations/sections/URLs, abstain when
insufficient, never give definitive legal advice.
"""

from typing import List, Dict, Any

SYSTEM_PROMPT = """You are IP-SAKTI SAHAYAK, an AI research assistant specialized in Indian and \
international Intellectual Property law, Traditional Knowledge, Ayurveda, and related regulatory \
frameworks (SIH 2026, PS26045).

STRICT RULES — follow every one of these without exception:
1. Answer ONLY using the evidence provided below. Do not use outside knowledge for legal facts.
2. Never invent legal provisions, section numbers, case names, or treaty articles.
3. Never fabricate citations or source URLs. If a URL is not in the evidence, do not include one.
4. Clearly distinguish stated fact (from evidence) from your own interpretation.
5. Respect the jurisdiction given; do not blend Indian and international law unless asked.
6. If the evidence is insufficient, conflicting, or off-topic, say so plainly and abstain from a
   confident answer rather than guessing.
7. Mention uncertainty explicitly when it exists.
8. You are not a lawyer. Never claim to be one, and never present your answer as definitive legal advice.
9. Cite supporting evidence using the exact bracket format [Source 1], [Source 2], etc., matching
   the numbering of the evidence list below.

Structure every answer using these exact section headers:
DIRECT ANSWER
KEY POINTS
APPLICABLE JURISDICTION
IMPORTANT CONDITIONS
SOURCES
DISCLAIMER
"""

DISCLAIMER_TEXT = (
    "This information is provided for informational and research purposes only and does not "
    "constitute legal advice. Verify important matters with the relevant authority or a qualified "
    "legal professional."
)


def format_evidence(chunks: List[Dict[str, Any]]) -> str:
    if not chunks:
        return "NO EVIDENCE RETRIEVED."
    lines = []
    for i, c in enumerate(chunks, start=1):
        lines.append(
            f"[Source {i}] Authority: {c.get('authority') or 'Unknown'} | "
            f"Jurisdiction: {c.get('jurisdiction') or 'Unspecified'} | "
            f"Section: {c.get('section') or 'N/A'} | "
            f"URL: {c.get('source_url') or 'Source URL unavailable'}\n"
            f"{c.get('text', '').strip()}"
        )
    return "\n\n".join(lines)


def build_rag_prompt(
    query: str,
    evidence_chunks: List[Dict[str, Any]],
    domain: str,
    jurisdiction: str,
    language: str = "en",
) -> List[Dict[str, str]]:
    evidence_block = format_evidence(evidence_chunks)
    user_prompt = f"""DOMAIN: {domain}
JURISDICTION: {jurisdiction}
RESPONSE LANGUAGE: {language}

USER QUESTION:
{query}

EVIDENCE:
{evidence_block}

Using ONLY the evidence above, answer the user's question following the required structure and rules. \
If the evidence does not adequately support an answer, say so in DIRECT ANSWER and explain what \
additional information would be needed, rather than guessing."""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def build_translation_prompt(text: str, target_language_name: str) -> List[Dict[str, str]]:
    return [
        {"role": "system", "content": (
            f"Translate the following text into {target_language_name}. Preserve any tokens that "
            f"look like __PROTECTED_N__ exactly as-is, unchanged. Output only the translation."
        )},
        {"role": "user", "content": text},
    ]


def build_abstention_message(reason: str) -> str:
    return (
        "I could not find sufficient authoritative evidence in the available sources to answer this "
        f"reliably. Reason: {reason}\n\n{DISCLAIMER_TEXT}"
    )


# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":
    sample_chunks = [{"authority": "IP India", "jurisdiction": "India", "section": "Section 3(d)",
                       "source_url": "https://ipindia.gov.in", "text": "Mere discovery is excluded."}]
    messages = build_rag_prompt("What is Section 3(d)?", sample_chunks, "Patent", "India")
    assert messages[0]["role"] == "system"
    assert "Section 3(d)" in messages[1]["content"]
    print("prompts self-test passed.")
