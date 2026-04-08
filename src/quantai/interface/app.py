from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence

import streamlit as st

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

try:
    from quantai.reasoning.engine import ApexReasoningCore
except Exception as exc:
    ApexReasoningCore = None  # type: ignore
    IMPORT_ERROR = str(exc)
else:
    IMPORT_ERROR = ""


APP_TITLE = "QuantAI"
DEFAULT_WORK_DIR = "rag_ingest_state"
DEFAULT_DB_PATH = "data/market_history.sqlite"

MODE_OPTIONS = {
    "Auto":        "auto",
    "Evidence":    "evidence",
    "Theorem":     "theorem",
    "Surface":     "options_surface_memory",
    "Memory":      "market_memory",
    "Live":        "market_live_snapshot",
    "Calibration": "market_calibration",
}


def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600&display=swap');

        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        html, body, .stApp {
            background: #0d0d0d !important;
            color: #e8e8e8;
            font-family: 'Sora', sans-serif;
        }

        /* hide all streamlit chrome */
        header[data-testid="stHeader"],
        footer,
        #MainMenu,
        section[data-testid="stSidebar"],
        .stDeployButton,
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"] {
            display: none !important;
        }

        .block-container {
            max-width: 740px !important;
            padding: 0 1.5rem 4rem !important;
            margin: 0 auto !important;
        }

        /* ── top bar ── */
        .qai-topbar {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 100;
            padding: 1.1rem 2rem;
            background: rgba(13,13,13,0.92);
            backdrop-filter: blur(12px);
        }
        .qai-brand {
            font-size: 0.95rem;
            font-weight: 600;
            letter-spacing: 0.08em;
            color: #e8e8e8;
            text-transform: uppercase;
        }

        /* ── center hero ── */
        .qai-hero {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 68vh;
            padding-top: 5rem;
        }
        .qai-headline {
            font-size: 1.65rem;
            font-weight: 500;
            color: #e8e8e8;
            letter-spacing: -0.02em;
            margin-bottom: 2rem;
            text-align: center;
        }

        /* ── pill input shell ── */
        .qai-pill-shell {
            width: 100%;
            max-width: 680px;
            background: #1a1a1a;
            border: 1px solid #2e2e2e;
            border-radius: 999px;
            padding: 0.55rem 0.65rem 0.55rem 1.4rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            box-shadow: 0 4px 32px rgba(0,0,0,0.45);
            transition: border-color 0.2s;
        }
        .qai-pill-shell:focus-within {
            border-color: #444;
        }

        /* hide streamlit form border */
        div[data-testid="stForm"] {
            border: none !important;
            background: transparent !important;
            padding: 0 !important;
        }

        /* text input inside pill */
        div[data-testid="stTextInput"] {
            flex: 1;
        }
        div[data-testid="stTextInput"] label { display: none !important; }
        div[data-testid="stTextInput"] > div { background: transparent !important; }
        div[data-testid="stTextInput"] input {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: #e8e8e8 !important;
            font-family: 'Sora', sans-serif !important;
            font-size: 0.97rem !important;
            padding: 0.45rem 0 !important;
            caret-color: #e8e8e8;
        }
        div[data-testid="stTextInput"] input::placeholder {
            color: #555 !important;
        }
        div[data-testid="stTextInput"] input:focus {
            outline: none !important;
        }

        /* selectbox inside pill */
        div[data-testid="stSelectbox"] label { display: none !important; }
        div[data-testid="stSelectbox"] > div { background: transparent !important; }
        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
            background: #252525 !important;
            border: 1px solid #333 !important;
            border-radius: 999px !important;
            min-height: 36px !important;
            padding: 0 0.75rem !important;
            font-size: 0.82rem !important;
            color: #aaa !important;
            cursor: pointer;
        }
        div[data-testid="stSelectbox"] div[data-baseweb="select"] svg {
            fill: #666 !important;
        }

        /* submit button */
        button[kind="primary"] {
            background: #e8e8e8 !important;
            color: #0d0d0d !important;
            border: none !important;
            border-radius: 999px !important;
            width: 38px !important;
            height: 38px !important;
            min-width: 38px !important;
            padding: 0 !important;
            font-size: 1.1rem !important;
            font-weight: 700 !important;
            cursor: pointer;
            flex-shrink: 0;
            transition: background 0.15s;
        }
        button[kind="primary"]:hover {
            background: #fff !important;
        }

        /* ── chat messages ── */
        .qai-messages {
            max-width: 680px;
            margin: 2rem auto 6rem auto;
        }

        div[data-testid="stChatMessage"] {
            background: transparent !important;
            border: none !important;
            padding: 0.5rem 0 !important;
        }

        div[data-testid="stChatMessage"] p {
            font-size: 0.95rem;
            line-height: 1.65;
            color: #d4d4d4;
        }

        /* user bubble */
        div[data-testid="stChatMessage"][data-testid*="user"] p {
            color: #e8e8e8;
        }

        /* details expander */
        div[data-testid="stExpander"] {
            background: #161616 !important;
            border: 1px solid #222 !important;
            border-radius: 14px !important;
            margin-top: 0.5rem;
        }
        div[data-testid="stExpander"] summary {
            color: #666 !important;
            font-size: 0.8rem !important;
        }

        .qai-source {
            border-left: 2px solid #2a2a2a;
            padding: 0.5rem 0.8rem;
            margin-bottom: 0.6rem;
        }
        .qai-source-title {
            font-size: 0.8rem;
            font-weight: 600;
            color: #888;
            margin-bottom: 0.2rem;
        }
        .qai-source-meta {
            font-size: 0.75rem;
            color: #555;
            margin-bottom: 0.2rem;
        }
        .qai-source-text {
            font-size: 0.82rem;
            color: #999;
            line-height: 1.5;
        }

        /* bottom fixed bar when messages exist */
        .qai-bottom-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            z-index: 100;
            background: rgba(13,13,13,0.95);
            backdrop-filter: blur(14px);
            padding: 0.9rem 1.5rem 1.2rem;
            display: flex;
            justify-content: center;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource(show_spinner=False)
def get_core(work_dir: str, market_db_path: str) -> Any:
    if ApexReasoningCore is None:
        raise RuntimeError(f"ApexReasoningCore unavailable: {IMPORT_ERROR}")
    return ApexReasoningCore(
        work_dir=work_dir,
        market_db_path=market_db_path,
        answer_mode="auto",
    )


def parse_securities(raw: str) -> List[str]:
    return [x.strip() for x in raw.replace("\n", ",").split(",") if x.strip()]


def run_query(core: Any, query: str, mode: str, securities: Sequence[str]) -> Dict[str, Any]:
    t0 = time.perf_counter()
    out = core.answer(query, mode=mode, securities=list(securities))
    out["_elapsed_seconds"] = time.perf_counter() - t0
    return out


def render_sources(result: Dict[str, Any]) -> None:
    fusion = result.get("fusion_hits") or []
    sources = result.get("sources") or []
    if not fusion and not sources:
        return
    with st.expander("Sources", expanded=False):
        for hit in (fusion[:4] + sources[:4]):
            title = hit.get("title") or hit.get("file_name") or "Source"
            score = hit.get("score", 0)
            page = hit.get("page_no")
            meta = f"score={score:.3f}"
            if page:
                meta += f" | p.{page}"
            text = " ".join(str(
                hit.get("excerpt") or hit.get("context_text") or hit.get("text") or ""
            ).split())[:400]
            st.markdown(
                f"""<div class="qai-source">
                    <div class="qai-source-title">{title}</div>
                    <div class="qai-source-meta">{meta}</div>
                    <div class="qai-source-text">{text}</div>
                </div>""",
                unsafe_allow_html=True,
            )


def prompt_bar(bottom: bool = False) -> tuple[str, str, bool]:
    """Renders the pill input bar. Returns (query, mode_value, submitted)."""
    mode_labels = list(MODE_OPTIONS.keys())
    default_label = next(
        (k for k, v in MODE_OPTIONS.items() if v == st.session_state.get("mode_value", "auto")),
        "Auto",
    )

    with st.form(key="qai_form_bottom" if bottom else "qai_form_top", clear_on_submit=True):
        st.markdown('<div class="qai-pill-shell">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([7.5, 1.8, 0.7], gap="small")
        with c1:
            query = st.text_input(
                "q",
                value="",
                placeholder="Ask anything",
                label_visibility="collapsed",
            )
        with c2:
            mode_label = st.selectbox(
                "mode",
                options=mode_labels,
                index=mode_labels.index(default_label),
                label_visibility="collapsed",
            )
        with c3:
            submitted = st.form_submit_button("↑", type="primary", use_container_width=False)
        st.markdown("</div>", unsafe_allow_html=True)

    return query, MODE_OPTIONS[mode_label], submitted


def main() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="∑",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    inject_css()

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "mode_value" not in st.session_state:
        st.session_state.mode_value = "auto"
    if "securities_raw" not in st.session_state:
        st.session_state.securities_raw = "SPX Index"

    # ── top bar ──
    st.markdown(
        f'<div class="qai-topbar"><div class="qai-brand">{APP_TITLE}</div></div>',
        unsafe_allow_html=True,
    )

    has_messages = bool(st.session_state.messages)

    # ── hero (only when empty) ──
    if not has_messages:
        st.markdown('<div class="qai-hero">', unsafe_allow_html=True)
        st.markdown('<div class="qai-headline">What are you working on?</div>', unsafe_allow_html=True)
        query, mode_val, submitted = prompt_bar(bottom=False)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        # render conversation
        st.markdown('<div class="qai-messages">', unsafe_allow_html=True)
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg["role"] == "assistant" and msg.get("result"):
                    render_sources(msg["result"])
        st.markdown("</div>", unsafe_allow_html=True)

        # bottom fixed bar
        st.markdown('<div class="qai-bottom-bar">', unsafe_allow_html=True)
        query, mode_val, submitted = prompt_bar(bottom=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.session_state.mode_value = mode_val

    if not submitted or not query.strip():
        return

    securities = parse_securities(st.session_state.securities_raw)

    with st.chat_message("user"):
        st.markdown(query)
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("assistant"):
        if ApexReasoningCore is None:
            st.error(f"Backend unavailable: {IMPORT_ERROR}")
            return

        try:
            core = get_core(work_dir=DEFAULT_WORK_DIR, market_db_path=DEFAULT_DB_PATH)
        except Exception as exc:
            st.error(f"Backend initialization failed: {exc}")
            return

        with st.spinner(""):
            try:
                result = run_query(core, query, mode_val, securities)
            except Exception as exc:
                st.error(f"Query failed: {exc}")
                return

        response = str(result.get("response") or "No response produced.")
        st.markdown(response)
        render_sources(result)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "result": result,
    })

    st.rerun()


if __name__ == "__main__":
    main()