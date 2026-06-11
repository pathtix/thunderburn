"""Token counting.

Offline by default using tiktoken. For Claude models we use the Anthropic API's
exact `count_tokens` endpoint *if* a key is available, otherwise we fall back to
the o200k tiktoken encoding as a close proxy (and label it as approximate).
"""

from functools import lru_cache

import tiktoken

from models import Model


@lru_cache(maxsize=4)
def _encoding(name: str):
    return tiktoken.get_encoding(name)


def _tiktoken_count(text: str, encoding_name: str) -> int:
    return len(_encoding(encoding_name).encode(text))


@lru_cache(maxsize=1)
def _anthropic_client():
    """Lazily build an Anthropic client; returns None if unavailable."""
    import os

    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic

        return anthropic.Anthropic()
    except Exception:
        return None


def count_tokens(text: str, model: Model) -> tuple[int, bool]:
    """Return (token_count, exact).

    `exact` is False when we used an approximation (e.g. tiktoken proxy for a
    Claude model with no API key available).
    """
    if not text.strip():
        return 0, True

    if model.tokenizer == "cl100k":
        return _tiktoken_count(text, "cl100k_base"), True

    if model.tokenizer == "o200k":
        return _tiktoken_count(text, "o200k_base"), True

    # Claude: try the exact API count, else proxy with o200k.
    client = _anthropic_client()
    if client is not None and model.api_id:
        try:
            resp = client.messages.count_tokens(
                model=model.api_id,
                messages=[{"role": "user", "content": text}],
            )
            return resp.input_tokens, True
        except Exception:
            pass  # fall through to the proxy

    return _tiktoken_count(text, "o200k_base"), False
