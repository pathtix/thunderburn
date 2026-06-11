"""Dummy login gate.

A purely cosmetic auth screen for demos — no real backend. Any non-empty
username works; the demo password is `demo`. Call `require_login()` once, right
after `st.set_page_config`, before rendering the rest of the app.
"""

import streamlit as st

DEMO_USER = "admin"
DEMO_PASSWORD = "demo"
DEMO_GOOGLE_EMAIL = "demo.user@gmail.com"

# Inline Google "G" logo (SVG) for the dummy sign-in button.
_GOOGLE_G_SVG = """
<svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg" style="vertical-align:middle;margin-right:8px">
  <path fill="#4285F4" d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.72v2.26h2.92c1.7-1.57 2.68-3.88 2.68-6.62z"/>
  <path fill="#34A853" d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.92-2.26c-.8.54-1.84.86-3.04.86-2.34 0-4.32-1.58-5.03-3.7H.96v2.33A9 9 0 0 0 9 18z"/>
  <path fill="#FBBC05" d="M3.97 10.72a5.4 5.4 0 0 1 0-3.44V4.95H.96a9 9 0 0 0 0 8.1l3.01-2.33z"/>
  <path fill="#EA4335" d="M9 3.58c1.32 0 2.5.45 3.44 1.35l2.58-2.58A9 9 0 0 0 .96 4.95l3.01 2.33C4.68 5.16 6.66 3.58 9 3.58z"/>
</svg>
"""


def _check(username: str, password: str) -> bool:
    """Accept the demo account, or any non-empty username with the demo password."""
    if not username.strip():
        return False
    return password == DEMO_PASSWORD


def require_login() -> str:
    """Block until logged in. Returns the username once authenticated."""
    if st.session_state.get("authenticated"):
        return st.session_state.get("username", "user")

    # Clicking the (fake) Google button navigates here with ?glogin=1.
    if st.query_params.get("glogin") == "1":
        st.session_state.authenticated = True
        st.session_state.username = DEMO_GOOGLE_EMAIL
        st.session_state.auth_provider = "Google"
        st.query_params.clear()
        st.rerun()

    # Centered login card.
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        lc1, lc2, lc3 = st.columns([1, 1, 1])
        with lc2:
            try:
                st.image("Mr burns logo.png", use_container_width=True)
            except Exception:
                st.markdown("# 🌍")
        st.markdown("<h1 style='text-align:center;margin-top:0'>Thunderburn</h1>", unsafe_allow_html=True)
        st.markdown(
            "<p style='text-align:center;color:#9aa0a6'>"
            "Prompt → Tokens → Cost → Carbon → Optimisation</p>",
            unsafe_allow_html=True,
        )
        st.markdown("#### Sign in")

        # --- Dummy "Continue with Google" (the whole button is clickable) ---
        st.markdown(
            f"""
            <a href="?glogin=1" target="_self" style="text-decoration:none">
              <div style="display:flex;align-items:center;justify-content:center;
                          border:1px solid #dadce0;border-radius:6px;padding:11px;
                          margin-bottom:6px;font-family:'Roboto',sans-serif;
                          font-size:14px;font-weight:500;color:#3c4043;
                          background:#fff;cursor:pointer;transition:background .15s"
                   onmouseover="this.style.background='#f7f8f8'"
                   onmouseout="this.style.background='#fff'">
                {_GOOGLE_G_SVG}<span>Continue with Google</span>
              </div>
            </a>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            "<div style='text-align:center;color:#9aa0a6;margin:8px 0'>— or —</div>",
            unsafe_allow_html=True,
        )

        # --- Username / password ---
        with st.form("login", clear_on_submit=False):
            username = st.text_input("Username", placeholder="admin")
            password = st.text_input(
                "Password", type="password", placeholder="demo"
            )
            submitted = st.form_submit_button("Log in", use_container_width=True, type="primary")

        st.caption("🔓 Demo login — use **admin** / **demo**, or the Google button above.")

        if submitted:
            if _check(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username.strip() or "admin"
                st.session_state.auth_provider = "password"
                st.rerun()
            else:
                st.error("Invalid credentials. Try username **admin**, password **demo**.")

    st.stop()


def logout_button() -> None:
    """Render a sidebar logout control. Call inside the app after login."""
    user = st.session_state.get("username", "user")
    provider = st.session_state.get("auth_provider", "")
    badge = " 🔵 Google" if provider == "Google" else ""
    st.sidebar.caption(f"Signed in as **{user}**{badge}")
    if st.sidebar.button("Log out", use_container_width=True):
        for key in ("authenticated", "username", "auth_provider"):
            st.session_state.pop(key, None)
        st.rerun()
