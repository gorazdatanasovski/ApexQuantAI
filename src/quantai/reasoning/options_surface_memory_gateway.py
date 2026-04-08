from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class OptionsSurfaceMemorySnapshot:
    underlying: str
    valuation_date: str
    memory_note: Dict[str, Any]
    calibration_rows: List[Dict[str, Any]]
    surface_preview: List[Dict[str, Any]]
    diagnostics: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OptionsSurfaceMemoryGateway:
    """
    Read-only gateway over persisted options-surface memory.

    Purpose:
    - expose SPX/SPY options-surface state without rebuilding the surface
    - let the engine answer surface/skew questions from local persisted memory
    - keep routing fast and deterministic

    Tables expected:
    - bloomberg_options_surface_memory
    - bloomberg_options_surface_calibration
    - bloomberg_options_surface_history
    """

    def __init__(self, market_db_path: str | Path = "data/market_history.sqlite") -> None:
        self.market_db_path = Path(market_db_path)

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def available(self) -> bool:
        if not self.market_db_path.exists():
            return False
        try:
            conn = sqlite3.connect(str(self.market_db_path))
            existing = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            conn.close()
            required = {
                "bloomberg_options_surface_memory",
                "bloomberg_options_surface_calibration",
                "bloomberg_options_surface_history",
            }
            return required.issubset(existing)
        except Exception:
            return False

    def latest_snapshot(
        self,
        underlying: str = "SPX Index",
        *,
        preview_rows: int = 20,
    ) -> Optional[OptionsSurfaceMemorySnapshot]:
        if not self.available():
            return None

        conn = sqlite3.connect(str(self.market_db_path))
        conn.row_factory = sqlite3.Row
        try:
            memory_row = conn.execute(
                """
                SELECT underlying, valuation_date, n_surface_rows, n_expiries,
                       atm_iv, atm_skew, method, summary_text, note_json
                FROM bloomberg_options_surface_memory
                WHERE underlying = ?
                ORDER BY valuation_date DESC, id DESC
                LIMIT 1
                """,
                [underlying],
            ).fetchone()

            if memory_row is None:
                return None

            valuation_date = str(memory_row["valuation_date"])
            calibration_rows = [
                dict(row)
                for row in conn.execute(
                    """
                    SELECT expiry, tau_years, n_points, atm_iv, skew, intercept, r_squared, method, raw_json
                    FROM bloomberg_options_surface_calibration
                    WHERE underlying = ? AND valuation_date = ?
                    ORDER BY expiry
                    """,
                    [underlying, valuation_date],
                ).fetchall()
            ]

            surface_preview = [
                dict(row)
                for row in conn.execute(
                    """
                    SELECT option_ticker, expiry, tau_years, option_type, strike, spot,
                           implied_vol, mid_price, volume, open_interest
                    FROM bloomberg_options_surface_history
                    WHERE underlying = ? AND valuation_date = ?
                    ORDER BY expiry, strike
                    LIMIT ?
                    """,
                    [underlying, valuation_date, int(preview_rows)],
                ).fetchall()
            ]
        finally:
            conn.close()

        note_json = self._json_load(memory_row["note_json"], default={})
        diagnostics = {
            "n_surface_rows": int(memory_row["n_surface_rows"] or 0),
            "n_expiries": int(memory_row["n_expiries"] or 0),
            "atm_iv": self._safe_float(memory_row["atm_iv"]),
            "atm_skew": self._safe_float(memory_row["atm_skew"]),
            "method": memory_row["method"],
            "summary_text": memory_row["summary_text"],
            "n_calibration_rows": len(calibration_rows),
            "n_preview_rows": len(surface_preview),
        }

        return OptionsSurfaceMemorySnapshot(
            underlying=str(memory_row["underlying"]),
            valuation_date=valuation_date,
            memory_note=note_json if isinstance(note_json, dict) else {},
            calibration_rows=self._normalize_calibration_rows(calibration_rows),
            surface_preview=self._normalize_surface_rows(surface_preview),
            diagnostics=diagnostics,
        )

    def render_summary(
        self,
        underlying: str = "SPX Index",
        *,
        preview_rows: int = 12,
    ) -> str:
        snap = self.latest_snapshot(underlying=underlying, preview_rows=preview_rows)
        if snap is None:
            return (
                f"No persisted options-surface memory is available for {underlying}. "
                f"Build it first with options_surface_memory_ingestor."
            )

        lines: List[str] = [
            f"Persisted options-surface memory for {snap.underlying}",
            f"Valuation date: {snap.valuation_date}",
            "",
            "Surface diagnostics:",
            f"- n_surface_rows: {snap.diagnostics.get('n_surface_rows')}",
            f"- n_expiries: {snap.diagnostics.get('n_expiries')}",
            f"- atm_iv: {snap.diagnostics.get('atm_iv')}",
            f"- atm_skew: {snap.diagnostics.get('atm_skew')}",
            f"- method: {snap.diagnostics.get('method')}",
            "",
        ]

        calibration_rows = snap.calibration_rows[:5]
        if calibration_rows:
            lines.append("Calibration slices:")
            for row in calibration_rows:
                lines.append(
                    f"- expiry={row.get('expiry')} | tau={row.get('tau_years')} | "
                    f"n_points={row.get('n_points')} | atm_iv={row.get('atm_iv')} | "
                    f"skew={row.get('skew')} | r_squared={row.get('r_squared')} | method={row.get('method')}"
                )
            lines.append("")

        preview = snap.surface_preview[:preview_rows]
        if preview:
            lines.append("Surface preview:")
            for row in preview:
                lines.append(
                    f"- {row.get('option_ticker')} | expiry={row.get('expiry')} | "
                    f"type={row.get('option_type')} | strike={row.get('strike')} | "
                    f"iv={row.get('implied_vol')} | mid={row.get('mid_price')} | oi={row.get('open_interest')}"
                )
            lines.append("")

        summary_text = str(snap.diagnostics.get("summary_text") or "").strip()
        if summary_text:
            lines.append("Memory note:")
            lines.append(summary_text)

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_calibration_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for row in rows:
            raw = dict(row)
            raw["raw_json"] = None
            out.append(raw)
        return out

    @staticmethod
    def _normalize_surface_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for row in rows:
            out.append(dict(row))
        return out

    @staticmethod
    def _json_load(value: Any, default: Any) -> Any:
        try:
            if value is None:
                return default
            return json.loads(value)
        except Exception:
            return default

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        try:
            if value is None:
                return None
            return float(value)
        except Exception:
            return None


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Read persisted options-surface memory.")
    parser.add_argument("--market-db-path", default="data/market_history.sqlite")
    parser.add_argument("--underlying", default="SPX Index")
    parser.add_argument("--preview-rows", type=int, default=12)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    gateway = OptionsSurfaceMemoryGateway(market_db_path=args.market_db_path)
    snapshot = gateway.latest_snapshot(
        underlying=args.underlying,
        preview_rows=args.preview_rows,
    )

    if args.json:
        print(json.dumps(snapshot.as_dict() if snapshot else None, indent=2, default=str))
    else:
        print(gateway.render_summary(args.underlying, preview_rows=args.preview_rows))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
