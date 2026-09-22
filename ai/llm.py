"""
IP-SAKTI SAHAYAK
LLM Client
==========
Thin, singleton wrapper around the Groq API (OpenAI-compatible). Never
raises raw SDK exceptions up to routes — always returns a structured
result so the Flask layer can show a friendly error instead of a stack
trace (spec Section 46).
"""

import logging
from dataclasses import dataclass
from typing import List, Dict, Optional

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class LLMResult:
    success: bool
    text: str = ""
    error: Optional[str] = None
    model: Optional[str] = None


class GroqClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._client = None
        return cls._instance

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not settings.GROQ_API_KEY:
            logger.warning("GROQ_API_KEY not set — LLM generation is disabled.")
            return None
        try:
            from groq import Groq
            self._client = Groq(api_key=settings.GROQ_API_KEY, max_retries=0, timeout=12.0)
        except Exception as e:
            logger.error("Failed to initialize Groq client: %s", e)
            self._client = None
        return self._client

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.2,
              max_tokens: int = 800) -> LLMResult:
        client = self._get_client()
        if client is None:
            return LLMResult(success=False, error="LLM backend unavailable (missing API key or client init failed).")

        try:
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            text = response.choices[0].message.content
            return LLMResult(success=True, text=text, model=settings.GROQ_MODEL)
        except Exception as e:
            logger.error("Groq API call failed: %s", e)
            return LLMResult(success=False, error="The language model request failed. Please try again shortly.")


llm_client = GroqClient()


def translate(protected_text: str, target_language: str) -> str:
    """Callable injected into ai/multilingual.py's translate_response()."""
    from ai.multilingual import LANGUAGE_NAMES
    from ai.prompts import build_translation_prompt

    lang_name = LANGUAGE_NAMES.get(target_language, target_language)
    messages = build_translation_prompt(protected_text, lang_name)
    result = llm_client.chat(messages, temperature=0.0, max_tokens=800)
    if not result.success:
        raise RuntimeError(result.error)
    return result.text


# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    res = llm_client.chat([{"role": "user", "content": "Say 'ok' and nothing else."}])
    print("llm self-test:", res.success, res.text or res.error)
