"""Trailblazer — Prompt → Tokens → Cost → Carbon → Optimisation.

A Streamlit dashboard with four pillars:n
  1. 🌍 Multi-language token comparison
  2. 💰 Cost estimator across models
  3. 🌱 Environmental impact (CO2 / green score)
  4. 🔧 Optimisation coach (concise rewrite + savings)

Run:  streamlit run app.py
Works fully offline; set ANTHROPIC_API_KEY for live translation + LLM rewrites.
"""

import os

from dotenv import load_dotenv

load_dotenv()  # pick up ANTHROPIC_API_KEY from a .env file if present

LOGO = "Mr burns logo.png"

import altair as alt
import pandas as pd
import streamlit as st

import auth
import carbon
import chat
import cost
import optimize
import translate
from models import MODELS, MODELS_BY_NAME
from samples import LANGUAGES, SAMPLES
from tokenizer import count_tokens

st.set_page_config(page_title="Thunderburn", page_icon=LOGO, layout="wide")

# Dummy login gate — blocks here until the user signs in.
auth.require_login()


# --------------------------------------------------------------------------- #
# Sidebar — inputs & assumptions
# --------------------------------------------------------------------------- #
st.sidebar.image(LOGO, width=120)
st.sidebar.title("Thunderburn")
st.sidebar.caption("Prompt → Tokens → Cost → Carbon → Optimisation")

auth.logout_button()

live = bool(os.environ.get("ANTHROPIC_API_KEY"))
if live:
    st.sidebar.success("Claude API key detected — live translation + rewrites on.")
# else:
#     st.sidebar.info(
#         "No API key — running offline. Use a sample prompt for the language "
#         "comparison, and the heuristic optimiser for rewrites. Set "
#         "`ANTHROPIC_API_KEY` to unlock live mode."
#     )

st.sidebar.subheader("Models to compare")
selected_names = st.sidebar.multiselect(
    "Models",
    [m.name for m in MODELS],
    default=["Claude Haiku 4.5", "Claude Sonnet 4.6", "GPT-4o", "Gemini 1.5 Flash"],
)
selected_models = [MODELS_BY_NAME[n] for n in selected_names] or MODELS[:4]

st.sidebar.subheader("Assumptions")
output_tokens = st.sidebar.slider(
    "Assumed output tokens per call", 0, 2000, 300, step=50,
    help="Cost = prompt (input) + this assumed completion (output).",
)
calls_per_month = st.sidebar.number_input(
    "Calls per month", min_value=1, value=100_000, step=10_000,
)

with st.sidebar.expander("Carbon model"):
    wh_per_1k = st.slider(
        "Wh per 1k tokens (baseline)", 0.05, 2.0, carbon.BASELINE_WH_PER_1K, 0.05
    )
    grid = st.slider(
        "Grid intensity (g CO₂/kWh)", 50, 900, int(carbon.GRID_INTENSITY), 10
    )


# --------------------------------------------------------------------------- #
# Sidebar — standalone optimisation chatbot (separate from Pillar 4)
# --------------------------------------------------------------------------- #
st.sidebar.divider()
st.sidebar.subheader("🤖 Optimisation chat")
st.sidebar.caption(
    "Paste a prompt or ask how to make one cheaper. "
    + ("Powered by Claude." if chat.has_live_chat() else "Offline helper.")
)

if "opt_chat" not in st.session_state:
    st.session_state.opt_chat = []

with st.sidebar:
    chat_box = st.container(height=300)
    with chat_box:
        if not st.session_state.opt_chat:
            st.caption("👋 Paste a prompt and I'll trim the bloat.")
        for msg in st.session_state.opt_chat:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    if st.session_state.opt_chat and st.button("Clear chat", use_container_width=True):
        st.session_state.opt_chat = []
        st.rerun()

    user_msg = st.chat_input("Ask the optimiser…")
    if user_msg:
        st.session_state.opt_chat.append({"role": "user", "content": user_msg})
        with st.spinner("Thinking…"):
            answer = chat.reply(st.session_state.opt_chat)
        st.session_state.opt_chat.append({"role": "assistant", "content": answer})
        st.rerun()


# --------------------------------------------------------------------------- #
# Input layer — prompt + language source
# --------------------------------------------------------------------------- #
st.title("Prompt cost, carbon & optimisation explorer")

mode = st.radio(
    "Prompt source",
    ["Use a sample prompt", "Write my own prompt"],
    horizontal=True,
)

if mode == "Use a sample prompt":
    sample_name = st.selectbox("Sample", list(SAMPLES.keys()))
    translations = SAMPLES[sample_name]
    prompt = translations["English"]
    st.text_area("English prompt", prompt, height=80, disabled=True)
else:
    prompt = st.text_area(
        "Your prompt (English)",
        "Write a polite reply to a customer who is unhappy about a late "
        "delivery and wants a refund.",
        height=120,
    )
    if live:
        with st.spinner("Translating with Claude…"):
            translations = translate.translate(prompt)
    else:
        translations = {"English": prompt}
        st.warning(
            "Custom prompts need a Claude API key to translate. Showing English "
            "only — switch to a sample prompt to see the full language spread."
        )

if not prompt.strip():
    st.stop()

# Show the prompt in every available language (sample translations, or live
# Claude translations for a custom prompt).
available_langs = [l for l in LANGUAGES if translations.get(l)]
with st.expander(f"📜 Prompt in all languages ({len(available_langs)})", expanded=True):
    if len(available_langs) <= 1:
        st.caption(
            "Only English is available. Pick a sample prompt (or set a Claude "
            "API key to translate your own) to see every language."
        )
    cols = st.columns(2)
    for i, lang in enumerate(available_langs):
        with cols[i % 2]:
            st.markdown(f"**{lang}**")
            st.markdown(
                f"<div dir='auto' style='font-size:0.95rem'>{translations[lang]}</div>",
                unsafe_allow_html=True,
            )


# --------------------------------------------------------------------------- #
# Token analysis (per language) — uses the FIRST selected model's tokenizer
# --------------------------------------------------------------------------- #
ref_model = selected_models[0]

lang_rows = []
lang_counts: dict[str, int] = {}
any_approx = False
for lang in LANGUAGES:
    text = translations.get(lang)
    if not text:
        continue
    tokens, exact = count_tokens(text, ref_model)
    any_approx = any_approx or not exact
    lang_counts[lang] = tokens
    lang_rows.append(
        {"Language": lang, "Tokens": tokens, "Characters": len(text)}
    )

lang_df = pd.DataFrame(lang_rows).sort_values("Tokens")


# --------------------------------------------------------------------------- #
# Pillar 1 — Multi-language token comparison
# --------------------------------------------------------------------------- #
st.header("🌍 1 · Multi-language token comparison")
st.caption(
    f"Token counts for the same meaning, tokenised with **{ref_model.name}** "
    f"({ref_model.tokenizer})."
    + ("  ⚠️ Claude counts are approximated (no API key)." if any_approx else "")
)

c1, c2 = st.columns([2, 3])
with c1:
    st.dataframe(
        lang_df.style.format({"Tokens": "{:,}", "Characters": "{:,}"}),
        hide_index=True,
        use_container_width=True,
    )
with c2:
    chart = (
        alt.Chart(lang_df)
        .mark_bar()
        .encode(
            x=alt.X("Tokens:Q"),
            y=alt.Y("Language:N", sort="-x"),
            color=alt.Color("Tokens:Q", scale=alt.Scale(scheme="redyellowgreen", reverse=True), legend=None),
            tooltip=["Language", "Tokens", "Characters"],
        )
        .properties(height=260)
    )
    st.altair_chart(chart, use_container_width=True)

# Tokens we carry forward for cost/carbon: the English prompt on each model.
english_text = translations["English"]


# --------------------------------------------------------------------------- #
# Pillar 2 — Cost estimator across models
# --------------------------------------------------------------------------- #
st.header("💰 2 · Cost estimator")
st.caption(
    f"Per-call cost = English prompt (input) + {output_tokens} assumed output "
    "tokens. Projected to your monthly volume."
)

cost_rows = []
model_tokens: dict[str, int] = {}
for m in selected_models:
    in_tokens, exact = count_tokens(english_text, m)
    model_tokens[m.name] = in_tokens
    per_call = cost.cost_per_call(in_tokens, output_tokens, m)
    cost_rows.append(
        {
            "Model": m.name,
            "Provider": m.provider,
            "Input tokens": in_tokens,
            "Per call ($)": per_call,
            "Per 1k calls ($)": per_call * 1_000,
            f"Per month ($, {calls_per_month:,} calls)": per_call * calls_per_month,
        }
    )

cost_df = pd.DataFrame(cost_rows)
month_col = f"Per month ($, {calls_per_month:,} calls)"

c1, c2 = st.columns([3, 2])
with c1:
    st.dataframe(
        cost_df.style.format(
            {
                "Input tokens": "{:,}",
                "Per call ($)": "${:,.6f}",
                "Per 1k calls ($)": "${:,.4f}",
                month_col: "${:,.2f}",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )
with c2:
    cost_chart = (
        alt.Chart(cost_df)
        .mark_bar()
        .encode(
            x=alt.X(f"{month_col}:Q", title="Monthly cost ($)"),
            y=alt.Y("Model:N", sort="-x"),
            color=alt.Color("Provider:N", legend=None),
            tooltip=["Model", month_col],
        )
        .properties(height=260)
    )
    st.altair_chart(cost_chart, use_container_width=True)


# --------------------------------------------------------------------------- #
# Pillar 3 — Environmental impact
# --------------------------------------------------------------------------- #
st.header("🌱 3 · Environmental impact")
st.caption(
    "Rough CO₂ estimate per call and per month. Tune the model in the sidebar."
)

carbon_rows = []
for m in selected_models:
    toks = model_tokens[m.name] + output_tokens
    grams = carbon.grams_co2(toks, m, wh_per_1k=wh_per_1k, grid_intensity=grid)
    grade, emoji = carbon.green_score(grams)
    carbon_rows.append(
        {
            "Model": m.name,
            "g CO₂ / call": grams,
            "kg CO₂ / month": grams * calls_per_month / 1000,
            "Green score": f"{emoji} {grade}",
        }
    )

carbon_df = pd.DataFrame(carbon_rows)

# Headline meter for the reference (first) model.
head = carbon_df.iloc[0]
m1, m2, m3 = st.columns(3)
m1.metric(f"{head['Model']} — per call", f"{head['g CO₂ / call']:.3f} g CO₂")
m1.caption(carbon.equivalent(head["g CO₂ / call"]))
m2.metric("Per month", f"{head['kg CO₂ / month']:.1f} kg CO₂")
m3.metric("Green score", head["Green score"])

st.dataframe(
    carbon_df.style.format({"g CO₂ / call": "{:.3f}", "kg CO₂ / month": "{:,.1f}"}),
    hide_index=True,
    use_container_width=True,
)


# --------------------------------------------------------------------------- #
# Pillar 4 — Optimisation coach
# --------------------------------------------------------------------------- #
st.header("🔧 4 · Optimisation coach")

if st.button("Optimise this prompt", type="primary"):
    with st.spinner("Rewriting…"):
        rewritten, method = optimize.rewrite(english_text)

    before_tokens, _ = count_tokens(english_text, ref_model)
    after_tokens, _ = count_tokens(rewritten, ref_model)
    saved = before_tokens - after_tokens
    pct = (saved / before_tokens * 100) if before_tokens else 0.0

    badge = "Claude rewrite" if method == "claude" else "heuristic rewrite (offline)"
    st.caption(f"Method: **{badge}**")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Before**")
        st.code(english_text, language="text")
        st.metric("Tokens", f"{before_tokens:,}")
    with c2:
        st.markdown("**After**")
        st.code(rewritten, language="text")
        st.metric("Tokens", f"{after_tokens:,}", delta=f"{-saved:,}")

    if saved > 0:
        # Project the saving across cost + carbon on the reference model.
        saved_cost = cost.cost_per_call(saved, 0, ref_model) * calls_per_month
        saved_co2 = (
            carbon.grams_co2(saved, ref_model, wh_per_1k=wh_per_1k, grid_intensity=grid)
            * calls_per_month
            / 1000
        )
        s1, s2, s3 = st.columns(3)
        s1.metric("Tokens saved", f"{saved:,}", delta=f"-{pct:.0f}%")
        s2.metric("Monthly $ saved", f"${saved_cost:,.2f}")
        s3.metric("Monthly CO₂ saved", f"{saved_co2:.1f} kg")
    else:
        st.info("No token savings found — this prompt is already concise.")

st.subheader("Tips")
for tip in optimize.structural_tips(english_text, lang_counts):
    st.markdown(f"- {tip}")

st.divider()
st.caption(
    "Cost figures use editable per-model pricing (see models.py). Carbon is a "
    "simplified, transparent estimate — tune it in the sidebar. Not billing or "
    "lab-grade data."
)
