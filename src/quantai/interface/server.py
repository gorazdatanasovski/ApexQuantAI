from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel

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

DEFAULT_WORK_DIR = "rag_ingest_state"
DEFAULT_DB_PATH = "data/market_history.sqlite"
DEFAULT_SECURITIES = ["SPX Index"]
BACKEND_TIMEOUT_SECONDS = 75


class QueryRequest(BaseModel):
    query: str
    mode: str = "auto"
    securities: List[str] = DEFAULT_SECURITIES


@lru_cache(maxsize=1)
def get_core() -> Any:
    if ApexReasoningCore is None:
        raise RuntimeError(f"ApexReasoningCore unavailable: {IMPORT_ERROR}")
    return ApexReasoningCore(
        work_dir=DEFAULT_WORK_DIR,
        market_db_path=DEFAULT_DB_PATH,
        answer_mode="auto",
    )


def infer_mode(query: str, selected_mode: str) -> str:
    if selected_mode != "auto":
        return selected_mode

    q = query.lower()

    if any(x in q for x in ("surface", "smile", "atm skew", "term structure", "implied vol")):
        return "options_surface_memory"
    if any(x in q for x in ("theorem", "conjecture", "prove", "lemma", "proposition")):
        return "theorem"
    if any(x in q for x in ("market memory", "empirical memory", "bloomberg memory")):
        return "market_memory"
    if any(x in q for x in ("level ii", "order book", "live snapshot", "bid ask")):
        return "market_live_snapshot"
    if any(x in q for x in ("calibrate", "mle", "kappa", "mean reversion")):
        return "market_calibration"
    if any(x in q for x in ("literature", "what does the book say", "evidence")):
        return "evidence"

    return "auto"


def run_backend_query(query: str, mode: str, securities: List[str]) -> Dict[str, Any]:
    core = get_core()
    if mode == "auto":
        return core.answer(query, securities=securities)
    return core.answer(query, mode=mode, securities=securities)


app = FastAPI(title="QuantAI UI")


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    return HTML


@app.get("/favicon.ico")
def favicon() -> Response:
    return Response(status_code=204)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "engine_imported": ApexReasoningCore is not None,
        "import_error": IMPORT_ERROR,
    }


@app.post("/api/query")
def api_query(payload: QueryRequest) -> Dict[str, Any]:
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query is empty.")

    mode = infer_mode(query, payload.mode)
    securities = [x.strip() for x in payload.securities if x.strip()] or DEFAULT_SECURITIES

    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            fut = pool.submit(run_backend_query, query, mode, securities)
            result = fut.result(timeout=BACKEND_TIMEOUT_SECONDS)
    except FutureTimeout:
        raise HTTPException(
            status_code=504,
            detail=f"QuantAI backend timed out after {BACKEND_TIMEOUT_SECONDS} seconds.",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Query failed: {exc}") from exc

    return {
        "response": str(result.get("response") or "No response produced."),
        "mode_used": result.get("mode_used", mode),
        "sources": result.get("sources") or [],
        "fusion_hits": result.get("fusion_hits") or [],
        "options_surface_memory": result.get("options_surface_memory"),
        "market_summary": result.get("market_summary"),
        "llm_stats": result.get("llm_stats"),
    }


HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>QuantAI</title>
<style>
:root{
  --bg:#212121;
  --bg2:#1f1f1f;
  --text:#ececec;
  --muted:#a7a7a7;
  --border:rgba(255,255,255,.08);
  --shadow:0 18px 48px rgba(0,0,0,.22);
  --composer-width:min(820px, calc(100vw - 28px));
  --topbar-height:56px;
}
*{box-sizing:border-box}
html,body{
  margin:0;
  min-height:100%;
  background:
    radial-gradient(circle at top left, rgba(255,255,255,.035), transparent 18%),
    linear-gradient(180deg,#212121 0%,#1f1f1f 100%);
  color:var(--text);
  font-family:ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Arial, sans-serif;
}
body{overflow-x:hidden}
body.chat-started{padding-bottom:118px}
.topbar{
  position:fixed;
  inset:0 0 auto 0;
  height:var(--topbar-height);
  display:flex;
  align-items:center;
  padding:0 20px;
  background:rgba(33,33,33,.72);
  backdrop-filter:blur(14px);
  z-index:30;
}
.brand{
  color:var(--text);
  text-decoration:none;
  font-weight:600;
  font-size:1rem;
  letter-spacing:-.02em;
}
.page{
  width:min(920px, calc(100vw - 28px));
  margin:0 auto;
  padding-top:var(--topbar-height);
}
.hero{
  min-height:calc(100vh - var(--topbar-height));
  display:grid;
  place-items:center;
}
body.chat-started .hero{
  min-height:auto;
  display:block;
}
.hero-stack{
  width:100%;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  gap:22px;
}
body.chat-started .hero-stack{gap:0}
.headline{
  margin:0;
  font-size:clamp(2rem, 4vw, 2.55rem);
  font-weight:500;
  letter-spacing:-.04em;
  text-align:center;
}
body.chat-started .headline{display:none}
.composer-wrap{
  width:100%;
  display:flex;
  justify-content:center;
}
body.chat-started .composer-wrap{
  position:fixed;
  left:50%;
  bottom:18px;
  transform:translateX(-50%);
  width:var(--composer-width);
  z-index:25;
}
.composer{
  position:relative;
  width:var(--composer-width);
  display:flex;
  align-items:flex-end;
  gap:10px;
  padding:10px 12px;
  border-radius:28px;
  border:1px solid rgba(255,255,255,.10);
  background:rgba(48,48,48,.96);
  box-shadow:var(--shadow);
}
.mode-cluster{
  position:relative;
  flex:0 0 auto;
}
.mode-button{
  height:44px;
  display:inline-flex;
  align-items:center;
  gap:8px;
  padding:0 14px;
  border:none;
  border-radius:999px;
  background:rgba(255,255,255,.05);
  color:var(--text);
  font:inherit;
  cursor:pointer;
}
.mode-button:hover{background:rgba(255,255,255,.08)}
.mode-chevron{opacity:.72}
.mode-menu{
  position:absolute;
  left:0;
  bottom:58px;
  width:194px;
  display:flex;
  flex-direction:column;
  gap:4px;
  padding:8px;
  border-radius:18px;
  border:1px solid var(--border);
  background:rgba(42,42,42,.98);
  box-shadow:var(--shadow);
}
.mode-menu.hidden{display:none}
.mode-menu button{
  text-align:left;
  padding:10px 12px;
  border:none;
  border-radius:12px;
  background:transparent;
  color:var(--text);
  font:inherit;
  cursor:pointer;
}
.mode-menu button:hover{background:rgba(255,255,255,.06)}
.prompt-input{
  flex:1 1 auto;
  min-height:44px;
  max-height:220px;
  resize:none;
  padding:10px 2px;
  border:none;
  outline:none;
  background:transparent;
  color:var(--text);
  font:inherit;
  line-height:1.5;
}
.prompt-input::placeholder{color:var(--muted)}
.send-button{
  flex:0 0 auto;
  width:44px;
  height:44px;
  border:none;
  border-radius:999px;
  background:#ececec;
  color:#1d1d1d;
  font-size:1.08rem;
  font-weight:700;
  cursor:pointer;
}
.send-button:hover{background:#ffffff}
.send-button:disabled{opacity:.45;cursor:not-allowed}
.conversation{
  width:min(760px, 100%);
  margin:0 auto;
  display:flex;
  flex-direction:column;
  gap:28px;
}
.message{
  display:flex;
  flex-direction:column;
}
.message-user{align-items:flex-end}
.message-assistant{align-items:stretch}
.message-inner{
  max-width:760px;
  white-space:pre-wrap;
  word-break:break-word;
  line-height:1.72;
  font-size:1rem;
}
.message-inner-user{
  padding:14px 18px;
  border-radius:24px;
  border:1px solid var(--border);
  background:rgba(52,52,52,.9);
  box-shadow:var(--shadow);
}
.message-inner-assistant{
  padding:0;
  border:none;
  background:transparent;
  box-shadow:none;
}
.details{
  margin-top:12px;
  padding:10px 14px;
  border-radius:18px;
  border:1px solid var(--border);
  background:rgba(47,47,47,.92);
}
.details.hidden{display:none}
.details summary{
  color:var(--muted);
  cursor:pointer;
  user-select:none;
}
.details-body{
  margin-top:10px;
  display:flex;
  flex-direction:column;
  gap:10px;
}
.card{
  padding:12px 14px;
  border-radius:14px;
  border:1px solid var(--border);
  background:rgba(59,59,59,.84);
}
.card .title{
  font-weight:600;
  margin-bottom:4px;
}
.card .meta{
  margin-bottom:6px;
  color:var(--muted);
  font-size:.82rem;
}
.card .text{
  color:#d9d9d9;
  font-size:.92rem;
  line-height:1.55;
  white-space:pre-wrap;
}
@media (max-width: 640px){
  .topbar{padding:0 16px}
  .page{width:calc(100vw - 18px)}
  .conversation{width:100%}
  .composer,
  body.chat-started .composer-wrap{
    width:calc(100vw - 18px);
  }
  .composer{gap:8px;padding:8px}
  .mode-button{padding:0 12px;height:42px}
  .send-button{width:42px;height:42px}
}
</style>
</head>
<body>
<header class="topbar">
  <a class="brand" href="/" title="Refresh">QuantAI</a>
</header>

<main class="page">
  <section class="hero" id="hero">
    <div class="hero-stack">
      <h1 class="headline">What are you working on?</h1>

      <div class="composer-wrap" id="composerWrap">
        <form class="composer" id="composer" autocomplete="off">
          <div class="mode-cluster">
            <button class="mode-button" id="modeButton" type="button" aria-label="Choose mode">
              <span id="modeLabel">Auto</span>
              <span class="mode-chevron">▾</span>
            </button>

            <div class="mode-menu hidden" id="modeMenu">
              <button type="button" data-mode="auto">Auto</button>
              <button type="button" data-mode="evidence">Evidence</button>
              <button type="button" data-mode="theorem">Theorem</button>
              <button type="button" data-mode="options_surface_memory">Surface</button>
              <button type="button" data-mode="market_memory">Memory</button>
              <button type="button" data-mode="market_live_snapshot">Live</button>
              <button type="button" data-mode="market_calibration">Calibration</button>
            </div>
          </div>

          <textarea
            id="promptInput"
            class="prompt-input"
            rows="1"
            placeholder="Ask anything"
            aria-label="Ask anything"
          ></textarea>

          <button class="send-button" id="sendButton" type="submit" aria-label="Send">↑</button>
        </form>
      </div>
    </div>
  </section>

  <section class="conversation" id="conversation"></section>
</main>

<template id="userMessageTemplate">
  <article class="message message-user">
    <div class="message-inner message-inner-user"></div>
  </article>
</template>

<template id="assistantMessageTemplate">
  <article class="message message-assistant">
    <div class="message-inner message-inner-assistant"></div>
    <details class="details hidden">
      <summary>Details</summary>
      <div class="details-body"></div>
    </details>
  </article>
</template>

<script>
window.addEventListener("DOMContentLoaded", () => {
  const body = document.body;
  const conversation = document.getElementById("conversation");
  const composer = document.getElementById("composer");
  const modeButton = document.getElementById("modeButton");
  const modeMenu = document.getElementById("modeMenu");
  const modeLabel = document.getElementById("modeLabel");
  const promptInput = document.getElementById("promptInput");
  const sendButton = document.getElementById("sendButton");

  const userTemplate = document.getElementById("userMessageTemplate");
  const assistantTemplate = document.getElementById("assistantMessageTemplate");

  let currentMode = "auto";
  const securities = ["SPX Index"];
  let requestInFlight = false;

  function autosize() {
    promptInput.style.height = "0px";
    promptInput.style.height = Math.min(promptInput.scrollHeight, 220) + "px";
  }

  function closeMenu() {
    modeMenu.classList.add("hidden");
  }

  function activateChatLayout() {
    if (!body.classList.contains("chat-started")) {
      body.classList.add("chat-started");
    }
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function cardHTML(title, meta, text) {
    return `
      <div class="card">
        <div class="title">${escapeHtml(title)}</div>
        <div class="meta">${escapeHtml(meta)}</div>
        <div class="text">${escapeHtml(text)}</div>
      </div>
    `;
  }

  function buildMessage(role, text) {
    const tpl = role === "user" ? userTemplate : assistantTemplate;
    const node = tpl.content.firstElementChild.cloneNode(true);
    node.querySelector(".message-inner").textContent = text;
    return node;
  }

  function renderDetails(node, result) {
    const details = node.querySelector(".details");
    const detailsBody = node.querySelector(".details-body");
    const fusion = result.fusion_hits || [];
    const sources = result.sources || [];
    let html = "";

    fusion.slice(0, 6).forEach((hit) => {
      const meta = hit.metadata || {};
      let metaLine = `${hit.source_type || hit.source_kind || "unknown"} | score=${Number(hit.score || 0).toFixed(4)}`;
      if (meta.security) metaLine += ` | ${meta.security}`;
      if (meta.note_type) metaLine += ` | ${meta.note_type}`;
      const text = ((hit.excerpt || hit.context_text || "") + "").replace(/\s+/g, " ").slice(0, 500);
      html += cardHTML(hit.title || "Fusion hit", metaLine, text);
    });

    sources.slice(0, 8).forEach((hit) => {
      const metaLine = `page ${hit.page_no ?? "?"} | chunk ${hit.chunk_no ?? "?"} | score=${Number(hit.score || 0).toFixed(4)}`;
      const text = ((hit.text || "") + "").replace(/\s+/g, " ").slice(0, 500);
      html += cardHTML(hit.file_name || "Source", metaLine, text);
    });

    if (!html) return;
    details.classList.remove("hidden");
    detailsBody.innerHTML = html;
  }

  async function submitQuery(query) {
    const userNode = buildMessage("user", query);
    conversation.appendChild(userNode);

    const assistantNode = buildMessage("assistant", "Thinking…");
    conversation.appendChild(assistantNode);

    activateChatLayout();
    window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
    sendButton.disabled = true;
    requestInFlight = true;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 80000);

    try {
      const response = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          mode: currentMode,
          securities
        }),
        signal: controller.signal
      });

      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "Request failed.");

      assistantNode.querySelector(".message-inner").textContent =
        payload.response || "No response produced.";
      renderDetails(assistantNode, payload);
    } catch (err) {
      const message = err && err.name === "AbortError"
        ? "Frontend request timed out."
        : (err && err.message ? err.message : String(err));
      assistantNode.querySelector(".message-inner").textContent = `Error: ${message}`;
      console.error(err);
    } finally {
      clearTimeout(timeoutId);
      sendButton.disabled = false;
      requestInFlight = false;
      window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
    }
  }

  async function handleSubmit() {
    if (requestInFlight) return;
    const query = promptInput.value.trim();
    if (!query) return;
    promptInput.value = "";
    autosize();
    await submitQuery(query);
  }

  modeButton.addEventListener("click", (e) => {
    e.preventDefault();
    const hidden = modeMenu.classList.contains("hidden");
    closeMenu();
    if (hidden) modeMenu.classList.remove("hidden");
  });

  modeMenu.querySelectorAll("button").forEach((btn) => {
    btn.addEventListener("click", () => {
      currentMode = btn.dataset.mode;
      modeLabel.textContent = btn.textContent.trim();
      closeMenu();
    });
  });

  document.addEventListener("click", (e) => {
    if (!modeMenu.contains(e.target) && !modeButton.contains(e.target)) {
      closeMenu();
    }
  });

  composer.addEventListener("submit", async (e) => {
    e.preventDefault();
    await handleSubmit();
  });

  sendButton.addEventListener("click", async (e) => {
    e.preventDefault();
    await handleSubmit();
  });

  promptInput.addEventListener("input", autosize);

  promptInput.addEventListener("keydown", async (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      await handleSubmit();
    }
  });

  autosize();
});
</script>
</body>
</html>
'''
