from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _ok(name: str, detail: Any = None) -> Dict[str, Any]:
    return {"name": name, "ok": True, "detail": detail}


def _fail(name: str, exc: Exception) -> Dict[str, Any]:
    return {
        "name": name,
        "ok": False,
        "error_type": type(exc).__name__,
        "error": str(exc),
        "traceback": traceback.format_exc(limit=5),
    }


def check_imports() -> Dict[str, Any]:
    try:
        import quantai.reasoning.feature_store
        import quantai.reasoning.conjecture_engine
        import quantai.reasoning.verification_engine
        import quantai.reasoning.theorem_lab
        import quantai.reasoning.research_router
        import quantai.reasoning.calibration_engine
        import quantai.reasoning.options_surface_builder
        import quantai.reasoning.intraday_estimation_engine
        import quantai.reasoning.execution_trajectory_engine
        import quantai.reasoning.execution_parameter_calibrator
        import quantai.reasoning.theorem_registry
        import quantai.reasoning.engine
        return _ok("imports", "all critical reasoning modules imported")
    except Exception as exc:
        return _fail("imports", exc)


def check_sqlite_layout(db_path: Path) -> Dict[str, Any]:
    try:
        if not db_path.exists():
            raise FileNotFoundError(f"database not found: {db_path}")
        conn = sqlite3.connect(str(db_path))
        try:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
        finally:
            conn.close()
        tables = [r[0] for r in rows]
        return _ok("sqlite_layout", {"db_path": str(db_path), "tables": tables})
    except Exception as exc:
        return _fail("sqlite_layout", exc)


def check_book_memory(work_dir: Path) -> Dict[str, Any]:
    try:
        from quantai.memory.book_memory import BookMemory
        mem = BookMemory(work_dir)
        try:
            hits = mem.retrieve("rough volatility", top_k=3)
            preview = [h.as_dict() for h in hits[:3]]
        finally:
            mem.close()
        return _ok("book_memory", {"n_hits": len(hits), "preview": preview})
    except Exception as exc:
        return _fail("book_memory", exc)


def check_bloomberg_memory_table(db_path: Path) -> Dict[str, Any]:
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT security, note_type, title, as_of_date FROM bloomberg_research_memory ORDER BY security LIMIT 10"
            ).fetchall()
        finally:
            conn.close()
        payload = [dict(r) for r in rows]
        return _ok("bloomberg_memory", {"rows": payload, "count": len(payload)})
    except Exception as exc:
        return _fail("bloomberg_memory", exc)


def check_theorem_registry(db_path: Path) -> Dict[str, Any]:
    try:
        from quantai.reasoning.theorem_registry import TheoremRegistry
        reg = TheoremRegistry(db_path=db_path)
        entries = reg.list_entries(limit=10)
        payload = [e.as_dict() for e in entries[:5]]
        return _ok("theorem_registry", {"count": len(entries), "preview": payload})
    except Exception as exc:
        return _fail("theorem_registry", exc)


def check_router() -> Dict[str, Any]:
    try:
        from quantai.reasoning.research_router import ResearchRouter
        router = ResearchRouter()
        tests = {
            "market_memory": router.route(
                "What is the current Bloomberg empirical memory for SPY?",
                securities=["SPY US Equity"],
            ).as_dict(),
            "theorem": router.route(
                "Propose a theorem linking rough-volatility roughness to realized variance scaling for SPY.",
                securities=["SPY US Equity"],
            ).as_dict(),
            "live_execution": router.route(
                "Pull the live Level II limit order book depth for TSLA via the Bloomberg API and formulate the precise Almgren-Chriss liquidating trajectory for 10^5 shares over T=1 hour.",
                securities=["TSLA US Equity"],
            ).as_dict(),
            "live_calibration": router.route(
                "Retrieve the SPY and QQQ spread over the last 60 minutes and compute the maximum likelihood estimation for the OU mean-reversion speed kappa.",
                securities=["SPY US Equity", "QQQ US Equity"],
            ).as_dict(),
        }
        return _ok("router", tests)
    except Exception as exc:
        return _fail("router", exc)


def check_engine_local(work_dir: Path, db_path: Path) -> Dict[str, Any]:
    try:
        from quantai.reasoning.engine import ApexReasoningCore

        core = ApexReasoningCore(
            work_dir=work_dir,
            market_db_path=db_path,
            answer_mode="auto",
        )
        try:
            cases = {}

            out1 = core.answer(
                "What is the current Bloomberg empirical memory for SPY?",
                securities=["SPY US Equity"],
            )
            cases["market_memory"] = {
                "mode_used": out1.get("mode_used"),
                "has_response": bool(out1.get("response")),
            }

            out2 = core.answer(
                "Propose a theorem linking rough-volatility roughness to realized variance scaling for SPY.",
                securities=["SPY US Equity"],
            )
            cases["theorem"] = {
                "mode_used": out2.get("mode_used"),
                "selected_title": out2.get("selected_title"),
                "registry": out2.get("theorem_registry"),
            }

            out3 = core.answer(
                "State the exact covariance structure of fractional Brownian motion.",
                securities=[],
            )
            cases["evidence"] = {
                "mode_used": out3.get("mode_used"),
                "n_sources": len(out3.get("sources", [])),
            }
        finally:
            core.close()
        return _ok("engine_local", cases)
    except Exception as exc:
        return _fail("engine_local", exc)


def check_live_bloomberg() -> Dict[str, Any]:
    try:
        from quantai.reasoning.market_data import PhysicalMarketGateway
        with PhysicalMarketGateway() as bbg:
            ping = bbg.ping()
        return _ok("live_bloomberg", ping)
    except Exception as exc:
        return _fail("live_bloomberg", exc)


def main() -> int:
    parser = argparse.ArgumentParser(description="QuantAI end-to-end doctor.")
    parser.add_argument("--work-dir", default="rag_ingest_state")
    parser.add_argument("--market-db-path", default="data/market_history.sqlite")
    parser.add_argument("--include-live", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    work_dir = Path(args.work_dir)
    db_path = Path(args.market_db_path)

    checks: List[Dict[str, Any]] = []
    checks.append(check_imports())
    checks.append(check_sqlite_layout(db_path))
    checks.append(check_book_memory(work_dir))
    checks.append(check_bloomberg_memory_table(db_path))
    checks.append(check_theorem_registry(db_path))
    checks.append(check_router())
    checks.append(check_engine_local(work_dir, db_path))

    if args.include_live:
        checks.append(check_live_bloomberg())

    ok = all(c.get("ok") for c in checks)
    result = {
        "overall_ok": ok,
        "n_checks": len(checks),
        "checks": checks,
    }

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print("=" * 72)
        print("QuantAI Doctor")
        print("=" * 72)
        print(f"overall_ok = {ok}")
        for c in checks:
            status = "OK" if c.get("ok") else "FAIL"
            print(f"\n[{status}] {c['name']}")
            if c.get("ok"):
                detail = c.get("detail")
                if detail is not None:
                    print(json.dumps(detail, indent=2, default=str)[:5000])
            else:
                print(c.get("error_type"))
                print(c.get("error"))
        print("=" * 72)

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
