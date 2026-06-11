"""Model catalog: pricing, tokenizer family, and a relative energy factor.

Prices are USD per 1,000,000 tokens (input / output). These are editable in the
UI — treat the defaults as "good enough for a demo" snapshots, not billing truth.

`tokenizer` picks how we count tokens offline:
  - "o200k"  -> tiktoken o200k_base   (GPT-4o family, good proxy for modern models)
  - "cl100k" -> tiktoken cl100k_base  (older GPT-3.5/4 family)
  - "claude" -> exact via Anthropic API if a key is present, else o200k proxy
The `energy` field is a relative multiplier on the carbon baseline (bigger model
=> more energy per token). See carbon.py for how it is used.
"""

from dataclasses import dataclass


@dataclass
class Model:
    name: str
    provider: str
    price_in: float       # USD per 1M input tokens
    price_out: float      # USD per 1M output tokens
    tokenizer: str        # "o200k" | "cl100k" | "claude"
    api_id: str = ""      # real model id, used for live Claude token counting
    energy: float = 1.0   # relative energy factor (1.0 == baseline)


# Ordered roughly small -> large within a provider.
MODELS: list[Model] = [
    # --- Anthropic (pricing from the Claude API reference, per 1M tokens) ---
    Model("Claude Haiku 4.5",  "Anthropic", 1.00,  5.00,  "claude", "claude-haiku-4-5",  energy=0.6),
    Model("Claude Sonnet 4.6", "Anthropic", 3.00,  15.00, "claude", "claude-sonnet-4-6", energy=1.0),
    Model("Claude Opus 4.8",   "Anthropic", 5.00,  25.00, "claude", "claude-opus-4-8",   energy=1.8),
    Model("Claude Fable 5",    "Anthropic", 10.00, 50.00, "claude", "claude-fable-5",    energy=2.4),

    # --- OpenAI (approximate public pricing — edit in the UI) ---
    Model("GPT-4o mini", "OpenAI", 0.15, 0.60,  "o200k", energy=0.5),
    Model("GPT-4o",      "OpenAI", 2.50, 10.00, "o200k", energy=1.5),

    # --- Google (approximate public pricing — edit in the UI) ---
    Model("Gemini 1.5 Flash", "Google", 0.075, 0.30, "o200k", energy=0.5),
    Model("Gemini 1.5 Pro",   "Google", 1.25,  5.00, "o200k", energy=1.4),
]

MODELS_BY_NAME = {m.name: m for m in MODELS}
