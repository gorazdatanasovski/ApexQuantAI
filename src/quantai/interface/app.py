
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
    "Auto": "auto",
    "Evidence": "evidence",
    "Theorem": "theorem",
    "Surface": "options_surface_memory",
    "Memory": "market_memory",
    "Live": "market_live_snapshot",
    "Calibration": "market_calibration",
}


def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        :root{
            --bg: #212121;
            --bg-soft: #181818;
            --panel: rgba(39,39,39,0.94);
            --panel-2: rgba(49,49,49,0.88);
            --text: #ececec;
            --muted: #9f9f9f;
            --border: rgba(255,255,255,0.08);
            --border-2: rgba(255,255,255,0.12);
            --shadow: 0 18px 50px rgba(0,0,0,0.34);
            --rail-collapsed: 64px;
            --rail-expanded: 238px;
            --content-width: 780px;
            --composer-width: min(860px, calc(100vw - 96px));
            --topbar-h: 56px;
        }

        * { box-sizing: border-box; }

        html, body, .stApp {
            background:
                radial-gradient(circle at top left, rgba(255,255,255,0.03), transparent 18%),
                radial-gradient(circle at top right, rgba(255,255,255,0.02), transparent 16%),
                linear-gradient(180deg, #212121 0%, #1d1d1d 100%) !important;
            color: var(--text) !important;
            font-family: "Inter", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
        }

        body {
            overflow-x: hidden;
        }

        /* Hide Streamlit chrome */
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
            max-width: 100% !important;
            padding: 0 22px 120px 22px !important;
            margin: 0 auto !important;
        }

        /* ---------- Shell chrome ---------- */

        .qai-rail {
            position: fixed;
            top: 0;
            left: 0;
            bottom: 0;
            width: var(--rail-collapsed);
            background: rgba(23,23,23,0.92);
            border-right: 1px solid rgba(255,255,255,0.06);
            backdrop-filter: blur(14px);
            transition: width 0.22s ease;
            z-index: 120;
            overflow: hidden;
        }

        .qai-rail:hover {
            width: var(--rail-expanded);
        }

        .qai-rail-inner {
            height: 100%;
            display: flex;
            flex-direction: column;
            padding: 12px 10px;
            gap: 8px;
        }

        .qai-rail-top {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-top: 6px;
        }

        .qai-rail-item {
            width: 100%;
            height: 44px;
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 0 12px;
            border-radius: 14px;
            color: #e8e8e8;
            text-decoration: none;
            background: transparent;
            border: 1px solid transparent;
            transition: background 0.18s ease, border-color 0.18s ease;
            white-space: nowrap;
            overflow: hidden;
        }

        .qai-rail-item:hover {
            background: rgba(255,255,255,0.05);
            border-color: rgba(255,255,255,0.05);
        }

        .qai-rail-icon {
            width: 18px;
            min-width: 18px;
            text-align: center;
            font-size: 0.95rem;
            opacity: 0.95;
        }

        .qai-rail-label {
            opacity: 0;
            transform: translateX(-8px);
            transition: opacity 0.16s ease, transform 0.16s ease;
            color: #d7d7d7;
            font-size: 0.93rem;
            font-weight: 500;
        }

        .qai-rail:hover .qai-rail-label {
            opacity: 1;
            transform: translateX(0);
        }

        .qai-topbar {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: var(--topbar-h);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 22px 0 88px;
            background: rgba(33,33,33,0.72);
            backdrop-filter: blur(16px);
            z-index: 110;
        }

        .qai-brand {
            color: var(--text);
            font-size: 1.06rem;
            font-weight: 600;
            letter-spacing: -0.02em;
            user-select: none;
        }

        .qai-top-actions {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .qai-top-btn {
            width: 34px;
            height: 34px;
            border-radius: 999px;
            border: 1px solid rgba(255,255,255,0.08);
            background: rgba(255,255,255,0.03);
            color: #d8d8d8;
            display: grid;
            place-items: center;
            font-size: 0.95rem;
            line-height: 1;
            user-select: none;
        }

        /* ---------- Main layout ---------- */

        .qai-shell {
            width: 100%;
            max-width: var(--content-width);
            margin: 0 auto;
            padding-top: calc(var(--topbar-h) + 8px);
        }

        .qai-hero {
            min-height: calc(100vh - 120px);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            transform: translateY(-3.5vh);
        }

        .qai-headline {
            margin: 0 0 22px 0;
            font-size: clamp(2rem, 4vw, 2.62rem);
            font-weight: 500;
            letter-spacing: -0.04em;
            color: var(--text);
            text-align: center;
        }

        .qai-shell.chat-started .qai-hero {
            min-height: auto;
            justify-content: flex-start;
            transform: none;
            padding-top: 8px;
        }

        .qai-shell.chat-started .qai-headline {
            display: none;
        }

        .qai-messages {
            width: 100%;
            max-width: 760px;
            margin: 0 auto 134px auto;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .qai-top-composer-wrap,
        .qai-bottom-composer-wrap {
            width: 100%;
            display: flex;
            justify-content: center;
        }

        .qai-shell.chat-started .qai-top-composer-wrap {
            display: none;
        }

        .qai-bottom-composer-wrap {
            display: none;
        }

        .qai-shell.chat-started .qai-bottom-composer-wrap {
            display: flex;
            position: fixed;
            left: 50%;
            bottom: 18px;
            transform: translateX(-50%);
            width: var(--composer-width);
            z-index: 115;
        }

        /* ---------- Composer ---------- */

        div[data-testid="stForm"] {
            width: var(--composer-width) !important;
            background: transparent !important;
            border: none !important;
            padding: 0 !important;
        }

        .qai-pill-shell {
            width: 100%;
            display: flex;
            align-items: flex-end;
            gap: 10px;
            padding: 10px 12px;
            border-radius: 28px;
            border: 1px solid var(--border-2);
            background: var(--panel);
            box-shadow: var(--shadow);
        }

        .qai-pill-shell:focus-within {
            border-color: rgba(255,255,255,0.16);
        }

        div[data-testid="stTextInput"] label,
        div[data-testid="stSelectbox"] label {
            display: none !important;
        }

        div[data-testid="stTextInput"] {
            flex: 1 1 auto;
        }

        div[data-testid="stTextInput"] > div {
            background: transparent !important;
        }

        div[data-testid="stTextInput"] input {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: var(--text) !important;
            font-size: 0.98rem !important;
            padding: 0.58rem 0 !important;
            caret-color: var(--text);
        }

        div[data-testid="stTextInput"] input::placeholder {
            color: #8b8b8b !important;
        }

        div[data-testid="stTextInput"] input:focus {
            outline: none !important;
        }

        div[data-testid="stSelectbox"] > div {
            background: transparent !important;
        }

        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
            min-height: 42px !important;
            border-radius: 999px !important;
            border: 1px solid rgba(255,255,255,0.08) !important;
            background: rgba(255,255,255,0.04) !important;
            color: #d8d8d8 !important;
            padding: 0 0.8rem !important;
            font-size: 0.85rem !important;
        }

        div[data-testid="stSelectbox"] div[data-baseweb="select"] svg {
            fill: #8b8b8b !important;
        }

        button[kind="primary"] {
            width: 42px !important;
            min-width: 42px !important;
            height: 42px !important;
            border-radius: 999px !important;
            border: none !important;
            background: #f0f0f0 !important;
            color: #171717 !important;
            font-size: 1.08rem !important;
            font-weight: 700 !important;
            padding: 0 !important;
            box-shadow: none !important;
        }

        button[kind="primary"]:hover {
            background: #ffffff !important;
        }

        button[kind="primary"]:disabled {
            opacity: 0.45 !important;
            cursor: not-allowed !important;
        }

        /* ---------- Chat messages ---------- */

        div[data-testid="stChatMessage"] {
            background: transparent !important;
            border: none !important;
            padding: 7px 0 !important;
        }

        div[data-testid="stChatMessage"] > div {
            gap: 10px !important;
        }

        div[data-testid="stChatMessage"] p {
            font-size: 0.98rem;
            line-height: 1.72;
            color: #d7d7d7;
        }

        .qai-user-bubble {
            display: inline-block;
            margin-left: auto;
            padding: 13px 17px;
            border-radius: 22px;
            background: var(--panel-2);
            border: 1px solid rgba(255,255,255,0.06);
            box-shadow: 0 10px 26px rgba(0,0,0,0.18);
        }

        .qai-assistant-block {
            padding-top: 2px;
        }

        div[data-testid="stExpander"] {
            background: rgba(31,31,31,0.92) !important;
            border: 1px solid rgba(255,255,255,0.05) !important;
            border-radius: 16px !important;
            margin-top: 10px !important;
        }

        div[data-testid="stExpander"] summary {
            color: #8e8e8e !important;
            font-size: 0.8rem !important;
        }

        .qai-source {
            border-left: 2px solid rgba(255,255,255,0.10);
            padding: 0.55rem 0.85rem;
            margin-bottom: 0.65rem;
        }

        .qai-source-title {
            font-size: 0.82rem;
            font-weight: 600;
            color: #a8a8a8;
            margin-bottom: 0.22rem;
        }

        .qai-source-meta {
            font-size: 0.74rem;
            color: #6f6f6f;
            margin-bottom: 0.28rem;
        }

        .qai-source-text {
            font-size: 0.82rem;
            color: #b1b1b1;
            line-height: 1.55;
        }

        /* ---------- Mobile ---------- */

        @media (max-width: 900px) {
            .qai-topbar {
                padding-left: 78px;
                padding-right: 14px;
            }
            .qai-brand {
                font-size: 1rem;
            }
            .qai-shell {
                max-width: 100%;
            }
            .qai-headline {
                font-size: clamp(1.8rem, 5vw, 2.2rem);
            }
            :root {
                --composer-width: min(100vw - 26px, 860px);
            }
        }

        @media (max-width: 640px) {
            .qai-rail {
                width: 58px;
            }
            .qai-rail:hover {
                width: 216px;
            }
            .qai-topbar {
                padding-left: 72px;
            }
            .qai-top-actions {
                gap: 8px;
            }
            .qai-top-btn {
                width: 32px;
                height: 32px;
            }
            .qai-pill-shell {
                padding: 8px 9px;
                gap: 8px;
            }
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
    return [x.strip() for x in raw.replace("\\n", ",").split(",") if x.strip()]


def run_query(core: Any, query: str, mode: str, securities: Sequence[str]) -> Dict[str, Any]:
    t0 = time.perf_counter()
    out = core.answer(query, mode=mode, securities=list(securities))
    out["_elapsed_seconds"] = time.perf_counter() - t0
    return out


def render_shell_chrome() -> None:
    st.markdown(
        """
        <div class="qai-rail">
          <div class="qai-rail-inner">
            <div class="qai-rail-top">
              <a class="qai-rail-item" href="/">
                <span class="qai-rail-icon">＋</span>
                <span class="qai-rail-label">New chat</span>
              </a>
              <div class="qai-rail-item">
                <span class="qai-rail-icon">⌕</span>
                <span class="qai-rail-label">Search chats</span>
              </div>
            </div>
          </div>
        </div>

        <div class="qai-topbar">
          <div class="qai-brand">QuantAI</div>
          <div class="qai-top-actions">
            <div class="qai-top-btn">⇪</div>
            <div class="qai-top-btn">⋯</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
            text = " ".join(
                str(hit.get("excerpt") or hit.get("context_text") or hit.get("text") or "").split()
            )[:420]

            st.markdown(
                f"""
                <div class="qai-source">
                    <div class="qai-source-title">{title}</div>
                    <div class="qai-source-meta">{meta}</div>
                    <div class="qai-source-text">{text}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def prompt_bar(form_key: str) -> tuple[str, str, bool]:
    mode_labels = list(MODE_OPTIONS.keys())
    default_label = next(
        (k for k, v in MODE_OPTIONS.items() if v == st.session_state.get("mode_value", "auto")),
        "Auto",
    )

    with st.form(key=form_key, clear_on_submit=True):
        st.markdown('<div class="qai-pill-shell">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([7.2, 1.9, 0.7], gap="small")

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
    render_shell_chrome()

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "mode_value" not in st.session_state:
        st.session_state.mode_value = "auto"
    if "securities_raw" not in st.session_state:
        st.session_state.securities_raw = "SPX Index"

    has_messages = bool(st.session_state.messages)

    st.markdown(
        f'<div class="qai-shell {"chat-started" if has_messages else ""}">',
        unsafe_allow_html=True,
    )

    if not has_messages:
        st.markdown('<div class="qai-hero">', unsafe_allow_html=True)
        st.markdown('<h1 class="qai-headline">What are you working on?</h1>', unsafe_allow_html=True)
        st.markdown('<div class="qai-top-composer-wrap">', unsafe_allow_html=True)
        query, mode_val, submitted = prompt_bar("qai_form_top")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown('<div class="qai-messages">', unsafe_allow_html=True)

        for msg in st.session_state.messages:
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(
                        f'<div class="qai-user-bubble">{msg["content"]}</div>',
                        unsafe_allow_html=True,
                    )
            else:
                with st.chat_message("assistant"):
                    st.markdown(
                        f'<div class="qai-assistant-block">{msg["content"]}</div>',
                        unsafe_allow_html=True,
                    )
                    if msg.get("result"):
                        render_sources(msg["result"])

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="qai-bottom-composer-wrap">', unsafe_allow_html=True)
        query, mode_val, submitted = prompt_bar("qai_form_bottom")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.session_state.mode_value = mode_val

    if not submitted or not query.strip():
        return

    securities = parse_securities(st.session_state.securities_raw)

    st.session_state.messages.append(
        {
            "role": "user",
            "content": query,
        }
    )

    if ApexReasoningCore is None:
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": f"Backend unavailable: {IMPORT_ERROR}",
                "result": None,
            }
        )
        st.rerun()

    try:
        core = get_core(work_dir=DEFAULT_WORK_DIR, market_db_path=DEFAULT_DB_PATH)
    except Exception as exc:
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": f"Backend initialization failed: {exc}",
                "result": None,
            }
        )
        st.rerun()

    with st.spinner(""):
        try:
            result = run_query(core, query, mode_val, securities)
        except Exception as exc:
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"Query failed: {exc}",
                    "result": None,
                }
            )
            st.rerun()

    response = str(result.get("response") or "No response produced.")
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response,
            "result": result,
        }
    )

    st.rerun()


if __name__ == "__main__":
    main()

