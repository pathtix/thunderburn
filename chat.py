"""Sidebar optimisation chatbot.

A small, self-contained conversational assistant focused on prompt
optimisation. Completely separate from the Pillar 4 "Optimisation coach" — this
is a free-form chat where the user can paste prompts, ask "how do I make this
cheaper?", etc.

Live mode (Claude key present): a short multi-turn conversation with Haiku.
Offline mode: a deterministic helper that rewrites whatever the user pasted and
offers a couple of standing tips.
"""

import os
from functools import lru_cache

import optimize

SYSTEM = (
    "You are a prompt-optimisation assistant inside a token/cost/carbon tool. "
    "Help the user write shorter, cheaper, more token-efficient prompts without "
    "losing intent. When the user pastes a prompt, reply with: (1) a concise "
    "rewritten version, then (2) one short line naming what you cut and roughly "
    "how many tokens it saves. If they ask a general question, answer briefly. "
    "Keep every reply tight — a few sentences at most."
)


def has_live_chat() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


@lru_cache(maxsize=1)
def _client():
    try:
        import anthropic

        return anthropic.Anthropic()
    except Exception:
        return None


def _offline_reply(user_msg: str) -> str:
    """Deterministic, no-API helper."""
    rewritten = optimize.heuristic_rewrite(user_msg)
    if rewritten and rewritten.lower() != user_msg.strip().lower() and len(user_msg.split()) > 4:
        return (
            "Here's a leaner version (offline heuristic — set a Claude key for a "
            "smarter rewrite):\n\n"
            f"> {rewritten}\n\n"
            "I dropped filler words like *please, kindly, just, really, in order "
            "to*. For bigger wins: cut redundant examples, move fixed "
            "instructions into a cached system prompt, and prefer a "
            "token-efficient language."
        )
    return (
        "Tips for cheaper prompts: remove politeness padding and hedging, keep "
        "one strong example instead of several, state the format directly "
        "(\"3 bullets\" beats a paragraph describing it), and put stable context "
        "in a cached system prompt. Paste a prompt and I'll trim it. "
        "(Set a Claude API key for a smarter rewrite.)"
    )


def reply(history: list[dict]) -> str:
    """Return the assistant's reply given the full chat history.

    `history` is a list of {"role": "user"|"assistant", "content": str}; the last
    entry must be the new user message.
    """
    user_msg = history[-1]["content"] if history else ""

    client = _client()
    if client is None:
        return _offline_reply(user_msg)

    try:
        resp = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=600,
            system=SYSTEM,
            messages=[{"role": m["role"], "content": m["content"]} for m in history],
        )
        out = "".join(b.text for b in resp.content if b.type == "text").strip()
        return out or _offline_reply(user_msg)
    except Exception:
        return _offline_reply(user_msg)
