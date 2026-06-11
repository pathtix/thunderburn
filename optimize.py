"""Optimisation coach.

Two modes:
  - Live (Claude key present): ask Claude to rewrite the prompt more concisely
    while preserving intent.
  - Offline heuristic: apply cheap text cleanups (collapse whitespace, strip
    filler phrases, trim politeness padding) so the demo still produces a
    "before vs after" without any API.

Also surfaces simple structural tips (few-shot bloat, most efficient language).
"""

import os
import re
from functools import lru_cache

# Filler phrases that rarely change model behaviour but cost tokens.
_FILLERS = [
    r"\bplease\b",
    r"\bkindly\b",
    r"\bI would like you to\b",
    r"\bI want you to\b",
    r"\bcould you please\b",
    r"\bcan you please\b",
    r"\bif you don't mind\b",
    r"\bas an AI language model\b",
    r"\bin order to\b",
    r"\bbasically\b",
    r"\bjust\b",
    r"\bvery\b",
    r"\breally\b",
    r"\bactually\b",
]


def has_live_optimizer() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


@lru_cache(maxsize=1)
def _client():
    try:
        import anthropic

        return anthropic.Anthropic()
    except Exception:
        return None


def heuristic_rewrite(text: str) -> str:
    """Cheap, deterministic shortening — no API."""
    out = text
    for pat in _FILLERS:
        out = re.sub(pat, "", out, flags=re.IGNORECASE)
    # "in order to" -> "to" handled above by removal; tidy leftovers.
    out = re.sub(r"\s+", " ", out)              # collapse whitespace
    out = re.sub(r"\s+([,.!?;:])", r"\1", out)  # no space before punctuation
    out = re.sub(r"([,.!?;:]){2,}", r"\1", out)  # de-dup punctuation
    return out.strip().capitalize()


def llm_rewrite(text: str) -> str | None:
    """Ask Claude to rewrite concisely. Returns None if unavailable/failed."""
    client = _client()
    if client is None:
        return None
    try:
        resp = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            system=(
                "Rewrite the user's prompt to be as concise as possible while "
                "fully preserving its intent and any constraints. Output ONLY the "
                "rewritten prompt, nothing else."
            ),
            messages=[{"role": "user", "content": text}],
        )
        out = "".join(b.text for b in resp.content if b.type == "text").strip()
        return out or None
    except Exception:
        return None


def rewrite(text: str) -> tuple[str, str]:
    """Return (rewritten_text, method) where method is 'claude' or 'heuristic'."""
    live = llm_rewrite(text)
    if live is not None:
        return live, "claude"
    return heuristic_rewrite(text), "heuristic"


def structural_tips(text: str, lang_counts: dict[str, int]) -> list[str]:
    """Static analysis tips that don't need an API."""
    tips: list[str] = []

    # Few-shot bloat: lots of "Example:" / numbered examples.
    examples = len(re.findall(r"\b(example|e\.g\.|for instance)\b", text, re.I))
    if examples >= 3:
        tips.append(
            f"You include ~{examples} inline examples. Few-shot examples often "
            "dominate token count — try trimming to 1–2 of the strongest ones."
        )

    # Most token-efficient language for this prompt.
    if lang_counts:
        best = min(lang_counts, key=lang_counts.get)
        worst = max(lang_counts, key=lang_counts.get)
        if best != worst and lang_counts[worst] > 0:
            saved = 100 * (1 - lang_counts[best] / lang_counts[worst])
            tips.append(
                f"**{best}** is the most token-efficient phrasing here "
                f"({lang_counts[best]} tokens) — about {saved:.0f}% fewer tokens "
                f"than **{worst}** ({lang_counts[worst]})."
            )

    if len(text) > 600:
        tips.append(
            "This prompt is long. Move stable context (instructions, examples) "
            "into a cached system prompt so you don't pay for it on every call."
        )

    if not tips:
        tips.append("This prompt is already fairly lean. 👍")
    return tips
