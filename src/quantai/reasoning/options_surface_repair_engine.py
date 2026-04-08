from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import pandas as pd

from quantai.reasoning.options_surface_builder import OptionsSurfaceBuilder


@dataclass(frozen=True)
class SurfaceRepairAttempt:
    attempt_name: str
    underlying: str
    option_type: Optional[str]
    max_contracts: int
    ok: bool
    n_chain_rows: int
    n_snapshot_rows: int
    n_surface_rows: int
    n_expiries: int
    option_types_found: List[str]
    diagnostics: Dict[str, Any]
    calibration: Optional[Dict[str, Any]]
    error_type: Optional[str] = None
    error: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OptionsSurfaceRepairEngine:
    """
    Repair and harden Bloomberg options-surface extraction.

    Why this exists:
    - theorem / pair-linkage layers are now strong
    - the remaining weak Bloomberg frontier is the SPX surface path
    - prior diagnostics showed chain/snapshot success but zero usable surface rows

    Strategy:
    - run multiple surface extraction strategies
    - score them by usable surface depth
    - persist the best successful surface + diagnostics
    - return a single concise verdict instead of huge raw logs
    """

    DEFAULT_OPTION_TYPES: Sequence[Optional[str]] = ("P", "C", None)
    DEFAULT_MAX_CONTRACTS: Sequence[int] = (300, 800, 1500)

    def __init__(
        self,
        output_dir: str | Path = "artifacts/options_surface_repairs",
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def repair_underlying(
        self,
        underlying: str = "SPX Index",
        *,
        option_types: Optional[Sequence[Optional[str]]] = None,
        max_contracts_grid: Optional[Sequence[int]] = None,
    ) -> Dict[str, Any]:
        builder = OptionsSurfaceBuilder()
        option_types = list(option_types or self.DEFAULT_OPTION_TYPES)
        max_contracts_grid = list(max_contracts_grid or self.DEFAULT_MAX_CONTRACTS)

        attempts: List[SurfaceRepairAttempt] = []
        best_surface: Optional[pd.DataFrame] = None
        best_attempt: Optional[SurfaceRepairAttempt] = None

        for option_type in option_types:
            for max_contracts in max_contracts_grid:
                attempt_name = f"{underlying}|type={option_type or 'ALL'}|max={max_contracts}"
                try:
                    surface_result = builder.build_surface(
                        underlying=underlying,
                        option_type=option_type,
                        max_contracts=max_contracts,
                    )

                    surface_df = self._extract_surface_df(surface_result)
                    diagnostics = self._extract_diagnostics(surface_result)
                    calibration = self._maybe_calibrate(builder, surface_df, underlying)

                    attempt = SurfaceRepairAttempt(
                        attempt_name=attempt_name,
                        underlying=underlying,
                        option_type=option_type,
                        max_contracts=max_contracts,
                        ok=bool(len(surface_df) > 0),
                        n_chain_rows=int(diagnostics.get("rows_chain", 0) or diagnostics.get("n_chain_rows", 0) or 0),
                        n_snapshot_rows=int(diagnostics.get("rows_raw", 0) or diagnostics.get("n_snapshot_rows", 0) or 0),
                        n_surface_rows=int(len(surface_df)),
                        n_expiries=int(surface_df["expiry"].nunique()) if "expiry" in surface_df.columns and len(surface_df) > 0 else 0,
                        option_types_found=sorted(surface_df["option_type"].dropna().astype(str).unique().tolist()) if "option_type" in surface_df.columns and len(surface_df) > 0 else [],
                        diagnostics=diagnostics,
                        calibration=calibration,
                    )
                except Exception as exc:
                    attempt = SurfaceRepairAttempt(
                        attempt_name=attempt_name,
                        underlying=underlying,
                        option_type=option_type,
                        max_contracts=max_contracts,
                        ok=False,
                        n_chain_rows=0,
                        n_snapshot_rows=0,
                        n_surface_rows=0,
                        n_expiries=0,
                        option_types_found=[],
                        diagnostics={},
                        calibration=None,
                        error_type=type(exc).__name__,
                        error=str(exc),
                    )
                    surface_df = pd.DataFrame()

                attempts.append(attempt)

                if self._is_better_attempt(attempt, best_attempt):
                    best_attempt = attempt
                    best_surface = surface_df.copy()

        summary = {
            "created_at": self._utc_now(),
            "underlying": underlying,
            "n_attempts": len(attempts),
            "best_attempt": best_attempt.as_dict() if best_attempt else None,
            "attempts": [a.as_dict() for a in attempts],
        }
        files = self._persist_result(
            underlying=underlying,
            summary=summary,
            best_surface=best_surface,
        )
        return {
            "summary": summary,
            "files": files,
        }

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------
    def _extract_surface_df(self, surface_result: Any) -> pd.DataFrame:
        if hasattr(surface_result, "surface"):
            df = surface_result.surface
            if isinstance(df, pd.DataFrame):
                return df.copy()
        if isinstance(surface_result, dict):
            df = surface_result.get("surface")
            if isinstance(df, pd.DataFrame):
                return df.copy()
            preview = surface_result.get("surface_preview")
            if isinstance(preview, list):
                return pd.DataFrame(preview)
        return pd.DataFrame()

    def _extract_diagnostics(self, surface_result: Any) -> Dict[str, Any]:
        if hasattr(surface_result, "diagnostics"):
            diagnostics = getattr(surface_result, "diagnostics")
            if isinstance(diagnostics, dict):
                return dict(diagnostics)
        if hasattr(surface_result, "as_dict"):
            payload = surface_result.as_dict()
            if isinstance(payload, dict):
                return dict(payload.get("diagnostics") or {})
        if isinstance(surface_result, dict):
            return dict(surface_result.get("diagnostics") or {})
        return {}

    def _maybe_calibrate(
        self,
        builder: OptionsSurfaceBuilder,
        surface_df: pd.DataFrame,
        underlying: str,
    ) -> Optional[Dict[str, Any]]:
        if surface_df is None or surface_df.empty:
            return None

        required = {"expiry", "strike", "implied_vol", "spot"}
        if not required.issubset(set(surface_df.columns)):
            return None

        calib_input = surface_df.rename(columns={"underlying": "security"}).copy()
        try:
            calibration = builder.calibration_engine.calibrate_atm_skew_scaling(
                calib_input,
                security=underlying,
            )
            if hasattr(calibration, "as_dict"):
                return calibration.as_dict()
            if isinstance(calibration, dict):
                return calibration
            return {"repr": str(calibration)}
        except Exception as exc:
            return {
                "error_type": type(exc).__name__,
                "error": str(exc),
            }

    @staticmethod
    def _is_better_attempt(candidate: SurfaceRepairAttempt, incumbent: Optional[SurfaceRepairAttempt]) -> bool:
        if incumbent is None:
            return True
        cand_key = (
            int(candidate.ok),
            candidate.n_surface_rows,
            candidate.n_expiries,
            candidate.n_snapshot_rows,
            candidate.n_chain_rows,
            -candidate.max_contracts,
        )
        inc_key = (
            int(incumbent.ok),
            incumbent.n_surface_rows,
            incumbent.n_expiries,
            incumbent.n_snapshot_rows,
            incumbent.n_chain_rows,
            -incumbent.max_contracts,
        )
        return cand_key > inc_key

    def _persist_result(
        self,
        *,
        underlying: str,
        summary: Dict[str, Any],
        best_surface: Optional[pd.DataFrame],
    ) -> Dict[str, Any]:
        stem = self._slugify(f"{underlying}_surface_repair")
        json_path = self.output_dir / f"{stem}.json"
        md_path = self.output_dir / f"{stem}.md"
        csv_path = self.output_dir / f"{stem}.csv"

        json_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
        md_path.write_text(self._summary_markdown(summary), encoding="utf-8")

        wrote_csv = False
        if isinstance(best_surface, pd.DataFrame) and not best_surface.empty:
            best_surface.to_csv(csv_path, index=False)
            wrote_csv = True

        return {
            "json_path": str(json_path),
            "markdown_path": str(md_path),
            "csv_path": str(csv_path) if wrote_csv else None,
            "bytes_json": json_path.stat().st_size,
            "bytes_markdown": md_path.stat().st_size,
            "bytes_csv": csv_path.stat().st_size if wrote_csv else 0,
        }

    def _summary_markdown(self, summary: Dict[str, Any]) -> str:
        best = summary.get("best_attempt") or {}
        lines = [
            f"# Options Surface Repair: {summary.get('underlying')}",
            "",
            f"- Created at: {summary.get('created_at')}",
            f"- Attempts: {summary.get('n_attempts')}",
            "",
            "## Best attempt",
            "```json",
            json.dumps(best, indent=2, default=str),
            "```",
            "",
            "## Attempts",
        ]
        for attempt in summary.get("attempts", []):
            lines.append(f"### {attempt['attempt_name']}")
            lines.append(f"- OK: {attempt['ok']}")
            lines.append(f"- Surface rows: {attempt['n_surface_rows']}")
            lines.append(f"- Expiries: {attempt['n_expiries']}")
            lines.append(f"- Option types found: {attempt['option_types_found']}")
            if attempt.get("error"):
                lines.append(f"- Error: {attempt['error_type']}: {attempt['error']}")
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _slugify(text: str) -> str:
        import re
        return re.sub(r"[^A-Za-z0-9]+", "_", str(text)).strip("_").lower() or "surface_repair"

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Repair Bloomberg options-surface extraction.")
    parser.add_argument("--underlying", default="SPX Index")
    parser.add_argument("--output-dir", default="artifacts/options_surface_repairs")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    engine = OptionsSurfaceRepairEngine(output_dir=args.output_dir)
    result = engine.repair_underlying(underlying=args.underlying)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print("=" * 72)
        print("Options Surface Repair Engine")
        print("=" * 72)
        print(json.dumps({
            "best_attempt": result["summary"].get("best_attempt"),
            "files": result.get("files"),
        }, indent=2, default=str))
        print("=" * 72)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
