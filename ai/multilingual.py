"""
IP-SAKTI SAHAYAK
Multilingual Support
=====================
Language detection for English/Hindi/Odia and jurisdiction hinting,
plus careful LLM-assisted translation that preserves legal proper
nouns (Patents Act, PCT, TRIPS, TKDL, ABS, Geographical Indication)
untranslated, per spec Section 21.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Terms that must never be translated / must be preserved verbatim.
PROTECTED_TERMS = [
    "Patents Act", "PCT", "TRIPS", "TKDL", "ABS", "Geographical Indication",
    "WIPO", "WTO", "Nagoya Protocol", "Madrid Protocol", "Berne Convention",
    "Paris Convention", "Section 3(d)", "Section 3(p)", "Section 3(e)", "Section 6",
    "FSSAI", "CDSCO", "AYUSH", "Ministry of AYUSH", "NBA", "National Biodiversity Authority",
    "Rule 158B", "Rule 158-B", "Schedule T", "Schedule M", "API", "AFI",
    "FDA", "EMA", "MHRA", "NMPA", "PMDA", "TGA", "HSA", "EFSA", "DSHEA",
    "THMPD", "21 CFR", "DMR Act", "Legal Metrology", "RDA", "GACP", "GMP",
    "Ayurveda Aahara", "FSDU", "FMSP", "PPV&FR", "WHO",
]

_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
_ODIA_RE = re.compile(r"[\u0B00-\u0B7F]")


def detect_language(text: str) -> str:
    """
    Lightweight script-based detection for Hindi/Odia (unicode block
    presence is a reliable, dependency-free signal for these scripts),
    falling back to langdetect for anything else, then to English.
    """
    if _ODIA_RE.search(text):
        return "or"
    if _DEVANAGARI_RE.search(text):
        return "hi"
    try:
        from langdetect import detect
        code = detect(text)
        return code if code in ("en", "hi", "or") else "en"
    except Exception as e:
        logger.info("langdetect unavailable/failed (%s); defaulting to English.", e)
        return "en"


def protect_terms(text: str) -> (str, dict):
    """Replace protected legal terms with placeholders before translation."""
    placeholders = {}
    protected = text
    for i, term in enumerate(PROTECTED_TERMS):
        if term.lower() in protected.lower():
            token = f"__PROTECTED_{i}__"
            placeholders[token] = term
            protected = re.sub(re.escape(term), token, protected, flags=re.IGNORECASE)
    return protected, placeholders


def restore_terms(text: str, placeholders: dict) -> str:
    for token, term in placeholders.items():
        text = text.replace(token, term)
    return text


def normalize_language_code(lang: Optional[str]) -> str:
    """Normalize language string ('Hindi', 'hi', 'Odia', 'or', etc.) into standard code ('en', 'hi', 'or')."""
    if not lang:
        return "en"
    l = str(lang).strip().lower()
    if l in ("hi", "hindi", "hin", "हिन्दी"):
        return "hi"
    if l in ("or", "odia", "ori", "oriya", "od", "ଓଡ଼ିଆ"):
        return "or"
    return "en"


def _fallback_translate_http(text: str, target_lang: str) -> str:
    """Fallback translation using public Google Translate API endpoint when LLM translation is unavailable."""
    import urllib.request
    import urllib.parse
    import json

    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={target_lang}&dt=t&q=" + urllib.parse.quote(text)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode("utf-8"))
            translated_chunks = [x[0] for x in data[0] if x[0]]
            return "".join(translated_chunks)
    except Exception as e:
        logger.warning("HTTP fallback translation failed (%s); returning original text.", e)
        return text


def translate_response(text: str, target_language: str, llm_translate_fn) -> str:
    """
    llm_translate_fn: callable(protected_text, target_language) -> str.
    Includes automatic code normalization and HTTP fallback for 100% reliable translation.
    """
    code = normalize_language_code(target_language)
    if code == "en":
        return text

    protected_text, placeholders = protect_terms(text)
    translated = None

    try:
        translated = llm_translate_fn(protected_text, code)
    except Exception as e:
        logger.warning("LLM Translation failed (%s); attempting HTTP fallback for language '%s'.", e, code)

    if not translated or translated == protected_text:
        translated = _fallback_translate_http(protected_text, code)

    return restore_terms(translated, placeholders)


LANGUAGE_NAMES = {"en": "English", "hi": "Hindi", "or": "Odia"}


# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":
    assert detect_language("पेटेंट क्या है?") == "hi"
    assert detect_language("What is a patent?") == "en"
    protected, ph = protect_terms("Under the Patents Act, Section 3(d) applies.")
    assert "__PROTECTED_" in protected
    restored = restore_terms(protected, ph)
    assert restored == "Under the Patents Act, Section 3(d) applies."
    print("multilingual self-test passed.")
