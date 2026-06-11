"""Translation.

Offline-first: with no API key we can only work with the bundled sample prompts
(see samples.py). When a Claude API key is present we translate an *arbitrary*
user prompt into the target languages live.
"""

import os
from functools import lru_cache

from samples import LANGUAGES


def has_live_translation() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


@lru_cache(maxsize=1)
def _client():
    try:
        import anthropic

        return anthropic.Anthropic()
    except Exception:
        return None


def translate(text: str, languages: list[str] = LANGUAGES) -> dict[str, str]:
    """Translate `text` (assumed English) into each target language via Claude.

    Returns a dict {language: translated_text}. English is passed through. On any
    failure for a language, that language is simply omitted.
    """
    client = _client()
    out: dict[str, str] = {}
    targets = [l for l in languages if l != "English"]
    out["English"] = text
    if client is None:
        return out

    for lang in targets:
        try:
            resp = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=1024,
                system=(
                    "You are a translation engine. Translate the user's text into "
                    f"{lang}. Output ONLY the translation, no quotes, no notes."
                ),
                messages=[{"role": "user", "content": text}],
            )
            translated = "".join(
                b.text for b in resp.content if b.type == "text"
            ).strip()
            if translated:
                out[lang] = translated
        except Exception:
            continue
    return out
