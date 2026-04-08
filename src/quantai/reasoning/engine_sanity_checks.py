from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List

from quantai.reasoning.engine import ApexReasoningCore


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EngineSanityChecks:
    """
    Backend sanity checks for QuantAI.

    Final backend version:
    - treats persisted SPX surface routing as the canonical requirement
    - accepts direct gateway-backed options-surface fusion hits
    - preserves theorem / market / execution route checks
    """

    def __init__(
        self,
        work_dir: str | Path = "rag_ingest_state",
        market_db_path: str | Path = "data/market_history.sqlite",
    ) -> None:
        self.work_dir = str(work_dir)
        self.market_db_path = str(market_db_path)

    def run(self) -> Dict[str, Any]:
        core = ApexReasoningCore(
            work_dir=self.work_dir,
            market_db_path=self.market_db_path,
            answer_mode="auto",
        )
        checks: List[CheckResult] = []
        try:
            checks.append(self._check_evidence_fusion(core))
            checks.append(self._check_theorem_registry(core))
            checks.append(self._check_market_memory(core))
            checks.append(self._check_options_surface_memory(core))
            checks.append(self._check_options_surface_fusion_presence(core))
            checks.append(self._check_auto_route_execution(core))
            checks.append(self._check_auto_route_calibration(core))
        finally:
            core.close()

        overall_ok = all(c.ok for c in checks)
        return {
            "overall_ok": overall_ok,
            "n_checks": len(checks),
            "checks": [c.as_dict() for c in checks],
        }

    # ------------------------------------------------------------------
    # checks
    # ------------------------------------------------------------------
    def _check_evidence_fusion(self, core: ApexReasoningCore) -> CheckResult:
        out = core.answer(
            "What does the rough volatility literature say about the ATM skew term structure?",
            mode="evidence",
            securities=["SPX Index"],
        )
        fusion_hits = out.get("fusion_hits") or []
        return CheckResult(
            name="evidence_fusion",
            ok=bool(out.get("mode_used") == "evidence" and len(out.get("sources") or []) > 0),
            detail={
                "mode_used": out.get("mode_used"),
                "n_sources": len(out.get("sources") or []),
                "n_fusion_hits": len(fusion_hits),
                "response_head": self._head(out.get("response")),
            },
        )

    def _check_theorem_registry(self, core: ApexReasoningCore) -> CheckResult:
        out = core.answer(
            "Propose a theorem linking rough-volatility roughness to realized variance scaling for SPY.",
            mode="theorem",
            securities=["SPY US Equity"],
        )
        theorem_result = out.get("theorem_result") or {}
        selected = theorem_result.get("selected") or {}
        registry = theorem_result.get("registry") or theorem_result.get("theorem_registry") or {}
        return CheckResult(
            name="theorem_registry",
            ok=bool(out.get("mode_used") == "theorem" and (selected or out.get("response"))),
            detail={
                "mode_used": out.get("mode_used"),
                "selected_title": selected.get("title") or out.get("selected_title"),
                "registry": registry,
                "n_fusion_hits": len(out.get("fusion_hits") or []),
            },
        )

    def _check_market_memory(self, core: ApexReasoningCore) -> CheckResult:
        out = core.answer(
            "Summarize the Bloomberg empirical memory for SPY.",
            mode="market_memory",
            securities=["SPY US Equity"],
        )
        return CheckResult(
            name="market_memory",
            ok=bool(out.get("mode_used") == "market_memory" and out.get("response")),
            detail={
                "mode_used": out.get("mode_used"),
                "market_summary_keys": sorted(list((out.get("market_summary") or {}).keys())),
                "response_head": self._head(out.get("response")),
            },
        )

    def _check_options_surface_memory(self, core: ApexReasoningCore) -> CheckResult:
        out = core.answer(
            "What is the current persisted SPX options surface ATM skew and term structure?",
            securities=["SPX Index"],
        )
        osm = out.get("options_surface_memory") or {}
        diagnostics = osm.get("diagnostics") or {}
        ok = bool(
            out.get("mode_used") == "options_surface_memory"
            and diagnostics.get("n_surface_rows", 0) > 0
            and diagnostics.get("atm_skew") is not None
        )
        return CheckResult(
            name="options_surface_memory",
            ok=ok,
            detail={
                "mode_used": out.get("mode_used"),
                "n_surface_rows": diagnostics.get("n_surface_rows"),
                "n_expiries": diagnostics.get("n_expiries"),
                "atm_iv": diagnostics.get("atm_iv"),
                "atm_skew": diagnostics.get("atm_skew"),
                "method": diagnostics.get("method"),
                "response_head": self._head(out.get("response")),
            },
        )

    def _check_options_surface_fusion_presence(self, core: ApexReasoningCore) -> CheckResult:
        out = core.answer(
            "What does the persisted SPX options surface say about ATM skew, smile, and term structure?",
            mode="evidence",
            securities=["SPX Index"],
        )
        fusion_hits = out.get("fusion_hits") or []

        surface_hits = []
        for hit in fusion_hits:
            meta = hit.get("metadata") or {}
            note_type = meta.get("note_type")
            source_type = hit.get("source_type") or hit.get("source_kind")
            direct_surface_memory = bool(meta.get("direct_surface_memory"))
            if source_type == "bloomberg_memory" and (
                note_type in {
                    "options_surface_memory",
                    "options_surface_state",
                    "options_surface_global_state",
                }
                or direct_surface_memory
            ):
                surface_hits.append(hit)

        top_hit = fusion_hits[0] if fusion_hits else {}
        ok = bool(
            out.get("mode_used") == "evidence"
            and len(fusion_hits) > 0
            and len(surface_hits) > 0
        )

        return CheckResult(
            name="options_surface_fusion_presence",
            ok=ok,
            detail={
                "mode_used": out.get("mode_used"),
                "n_fusion_hits": len(fusion_hits),
                "n_surface_hits": len(surface_hits),
                "top_fusion_hit": top_hit,
                "surface_hits": surface_hits[:3],
                "response_head": self._head(out.get("response")),
            },
        )

    def _check_auto_route_execution(self, core: ApexReasoningCore) -> CheckResult:
        out = core.answer(
            "Pull the live Level II limit order book depth for TSLA via the Bloomberg API and formulate the precise Almgren-Chriss liquidating trajectory for 10^5 shares over T=1 hour.",
            securities=["TSLA US Equity"],
        )
        return CheckResult(
            name="auto_route_execution",
            ok=bool(out.get("mode_used") == "market_live_snapshot"),
            detail={
                "mode_used": out.get("mode_used"),
                "has_execution_calibration": bool(out.get("calibration_result")),
                "has_execution_trajectory": bool(out.get("execution_trajectory")),
                "response_head": self._head(out.get("response")),
            },
        )

    def _check_auto_route_calibration(self, core: ApexReasoningCore) -> CheckResult:
        out = core.answer(
            "Retrieve the SPY and QQQ spread over the last 60 minutes and compute the maximum likelihood estimation for the mean-reversion speed kappa.",
            securities=["SPY US Equity", "QQQ US Equity"],
        )
        return CheckResult(
            name="auto_route_calibration",
            ok=bool(out.get("mode_used") == "market_calibration"),
            detail={
                "mode_used": out.get("mode_used"),
                "has_calibration": bool(out.get("calibration_result")),
                "response_head": self._head(out.get("response")),
            },
        )

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _head(text: Any, n: int = 500) -> str:
        s = str(text or "")
        return s[:n]


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run QuantAI engine sanity checks.")
    parser.add_argument("--work-dir", default="rag_ingest_state")
    parser.add_argument("--market-db-path", default="data/market_history.sqlite")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    runner = EngineSanityChecks(
        work_dir=args.work_dir,
        market_db_path=args.market_db_path,
    )
    result = runner.run()

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print("=" * 72)
        print("QuantAI Engine Sanity Checks")
        print("=" * 72)
        print(f"overall_ok = {result['overall_ok']}")
        print("")
        for check in result["checks"]:
            print(f"[{'OK' if check['ok'] else 'FAIL'}] {check['name']}")
            print(json.dumps(check["detail"], indent=2, default=str))
            print("")
        print("=" * 72)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
