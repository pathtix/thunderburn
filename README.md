# 🌍 Thunderburn

**Prompt → Token Count → Cost Estimate → Environmental Impact → Optimisation Tips**

A Streamlit dashboard that shows how the *same* prompt costs wildly different
amounts — in tokens, dollars, and CO₂ — depending on the **language** you write
it in and the **model** you send it to, then coaches you to make it leaner.

## Four pillars

1. **🌍 Multi-language token comparison** — the same meaning in English, Spanish,
   French, Hindi, Arabic, Chinese, Japanese; watch the token counts diverge.
2. **💰 Cost estimator** — live-ish per-model pricing → cost per call / per 1k /
   per month across GPT-4o, Claude, Gemini.
3. **🌱 Environmental impact** — a transparent CO₂-per-request meter with a green
   score, tunable to whichever energy study you trust.
4. **🔧 Optimisation coach** — rewrites the prompt concisely (Claude when a key
   is set, heuristic otherwise) and shows the % tokens / $ / CO₂ saved.

## Quick start

```bash
cd /Users/denizgencoatilla/trailblazer
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Then open the URL Streamlit prints (usually http://localhost:8501).

### Offline vs live

The app runs **fully offline** out of the box:
- Token counts use `tiktoken` (exact for GPT/Gemini-family encodings; an o200k
  proxy for Claude when no key is present).
- The multi-language comparison uses **bundled translations** of the sample
  prompts.
- The optimiser uses a deterministic heuristic rewrite.

Set a Claude API key to unlock **live mode** — translate *any* custom prompt,
exact Claude token counts, and an LLM-powered concise rewrite:

```bash
cp .env.example .env   # then edit ANTHROPIC_API_KEY
# or: export ANTHROPIC_API_KEY=sk-ant-...
```

## Project layout

| File | Role |
|------|------|
| `app.py` | Streamlit dashboard (the four pillars) |
| `models.py` | Model catalog: pricing, tokenizer family, energy factor |
| `tokenizer.py` | Token counting (tiktoken + optional exact Claude API) |
| `cost.py` | Cost math |
| `carbon.py` | CO₂ estimate + green score |
| `translate.py` | Live Claude translation (custom prompts) |
| `optimize.py` | Concise rewrite (Claude or heuristic) + structural tips |
| `samples.py` | Bundled multi-language sample prompts |

## Notes & honesty

- **Pricing** is editable snapshots in `models.py` — Claude prices come from the
  Claude API reference; OpenAI/Google figures are approximate public numbers.
- **Carbon** is a deliberately simple `tokens × energy × grid-intensity` model,
  exposed in the sidebar so you can defend the numbers. It's for intuition, not
  for a sustainability audit.
