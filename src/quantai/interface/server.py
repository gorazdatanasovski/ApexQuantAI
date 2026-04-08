from __future__ import annotations

import importlib
import os
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"

DEFAULT_WORK_DIR = os.getenv("QUANTAI_WORK_DIR", "rag_ingest_state")
DEFAULT_DB_PATH = os.getenv("QUANTAI_DB_PATH", "data/market_history.sqlite")
DEFAULT_SECURITIES = ["SPX Index"]
BACKEND_TIMEOUT_SECONDS = int(os.getenv("QUANTAI_BACKEND_TIMEOUT_SECONDS", "75"))


class QueryRequest(BaseModel):
    query: str
    mode: str = "auto"
    securities: List[str] = DEFAULT_SECURITIES


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


def _load_engine_class() -> Any:
    module = importlib.import_module("quantai.reasoning.engine")
    return getattr(module, "ApexReasoningCore")


@lru_cache(maxsize=1)
def get_core() -> Any:
    ApexReasoningCore = _load_engine_class()
    return ApexReasoningCore(
        work_dir=DEFAULT_WORK_DIR,
        market_db_path=DEFAULT_DB_PATH,
        answer_mode="auto",
    )


def run_backend_query(query: str, mode: str, securities: List[str]) -> Dict[str, Any]:
    core = get_core()
    if mode == "auto":
        return core.answer(query, securities=securities)
    return core.answer(query, mode=mode, securities=securities)


app = FastAPI(title="QuantAI UI")

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def root() -> Response:
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)

    return Response(
        content=(
            "<!doctype html><html><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>QuantAI</title></head>"
            "<body style='background:#212121;color:#ececec;font-family:system-ui;"
            "display:grid;place-items:center;min-height:100vh'>"
            "<div><h1>QuantAI</h1><p>Frontend files not found.</p></div>"
            "</body></html>"
        ),
        media_type="text/html",
    )


@app.get("/favicon.ico")
def favicon() -> Response:
    return Response(status_code=204)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "static_dir_exists": STATIC_DIR.exists(),
        "work_dir": DEFAULT_WORK_DIR,
        "db_path": DEFAULT_DB_PATH,
    }


@app.get("/healthz")
def healthz() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/query")
def api_query(payload: QueryRequest) -> Dict[str, Any]:
    query = payload.query.strip()
    if not query:
        return {
            "response": "Query is empty.",
            "mode_used": "error",
            "sources": [],
            "fusion_hits": [],
            "options_surface_memory": None,
            "market_summary": None,
            "llm_stats": None,
        }

    mode = infer_mode(query, payload.mode)
    securities = [x.strip() for x in payload.securities if x.strip()] or DEFAULT_SECURITIES

    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            fut = pool.submit(run_backend_query, query, mode, securities)
            result = fut.result(timeout=BACKEND_TIMEOUT_SECONDS)
    except FutureTimeout:
        return {
            "response": f"QuantAI backend timed out after {BACKEND_TIMEOUT_SECONDS} seconds.",
            "mode_used": "timeout",
            "sources": [],
            "fusion_hits": [],
            "options_surface_memory": None,
            "market_summary": None,
            "llm_stats": None,
        }
    except Exception as exc:
        return {
            "response": f"QuantAI backend unavailable in this deploy: {exc}",
            "mode_used": "backend_unavailable",
            "sources": [],
            "fusion_hits": [],
            "options_surface_memory": None,
            "market_summary": None,
            "llm_stats": None,
        }

    return {
        "response": str(result.get("response") or "No response produced."),
        "mode_used": result.get("mode_used", mode),
        "sources": result.get("sources") or [],
        "fusion_hits": result.get("fusion_hits") or [],
        "options_surface_memory": result.get("options_surface_memory"),
        "market_summary": result.get("market_summary"),
        "llm_stats": result.get("llm_stats"),
    }