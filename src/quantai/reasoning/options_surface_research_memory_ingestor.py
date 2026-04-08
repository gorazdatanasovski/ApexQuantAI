from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from quantai.reasoning.options_surface_memory_gateway import OptionsSurfaceMemoryGateway


@dataclass(frozen=True)
class OptionsSurfaceResearchNote:
    security: str
    note_type: str
    title: str
    as_of_date: str
    content_markdown: str
    metadata: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OptionsSurfaceResearchMemoryIngestor:
    """
    Promote persisted options-surface memory into bloomberg_research_memory.

    Why this exists:
    - options_surface_memory is now persisted and queryable
    - the engine can answer direct surface questions from memory
    - fused research retrieval still benefits from bloomberg_research_memory

    This module converts the stored surface + calibration into:
    - an underlying-specific research note
    - a GLOBAL options-surface state note

    That means theorem generation and fusion retrieval can use the surface state
    without rebuilding the surface live.
    """

    def __init__(
        self,
        market_db_path: str | Path = "data/market_history.sqlite",
        output_dir: str | Path = "artifacts/options_surface_research_memory",
    ) -> None:
        self.market_db_path = Path(market_db_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.gateway = OptionsSurfaceMemoryGateway(self.market_db_path)

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def build_and_persist(
        self,
        underlying: str = "SPX Index",
        *,
        preview_rows: int = 400,
    ) -> Dict[str, Any]:
        snapshot = self.gateway.latest_snapshot(
            underlying=underlying,
            preview_rows=preview_rows,
        )
        if snapshot is None:
            raise RuntimeError(
                f"No persisted options-surface memory is available for {underlying}. "
                f"Build it first with options_surface_memory_ingestor."
            )

        surface_df = self._load_full_surface(
            underlying=underlying,
            valuation_date=snapshot.valuation_date,
        )
        derived = self._derive_surface_features(surface_df, snapshot.as_dict())

        local_note = self._build_underlying_note(
            snapshot=snapshot.as_dict(),
            derived=derived,
        )
        global_note = self._build_global_note(
            snapshot=snapshot.as_dict(),
            derived=derived,
        )

        db_stats = self._persist_notes_to_sqlite([local_note, global_note])
        file_stats = self._persist_note_files([local_note, global_note])

        return {
            "underlying": underlying,
            "valuation_date": snapshot.valuation_date,
            "derived_features": derived,
            "notes": [local_note.as_dict(), global_note.as_dict()],
            "db_stats": db_stats,
            "file_stats": file_stats,
        }

    # ------------------------------------------------------------------
    # loading / derivation
    # ------------------------------------------------------------------
    def _load_full_surface(self, *, underlying: str, valuation_date: str) -> pd.DataFrame:
        if not self.market_db_path.exists():
            return pd.DataFrame()

        conn = sqlite3.connect(str(self.market_db_path))
        try:
            df = pd.read_sql_query(
                """
                SELECT option_ticker, expiry, tau_years, option_type, strike, spot,
                       implied_vol, mid_price, volume, open_interest
                FROM bloomberg_options_surface_history
                WHERE underlying = ? AND valuation_date = ?
                ORDER BY expiry, strike
                """,
                conn,
                params=[underlying, valuation_date],
            )
        finally:
            conn.close()

        if df.empty:
            return df

        for col in ("tau_years", "strike", "spot", "implied_vol", "mid_price", "volume", "open_interest"):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        if "expiry" in df.columns:
            df["expiry"] = pd.to_datetime(df["expiry"], errors="coerce")
        return df

    def _derive_surface_features(
        self,
        df: pd.DataFrame,
        snapshot: Dict[str, Any],
    ) -> Dict[str, Any]:
        diagnostics = snapshot.get("diagnostics") or {}
        calibration_rows = snapshot.get("calibration_rows") or []

        if df.empty:
            return {
                "rows_total": 0,
                "rows_with_iv": 0,
                "rows_calls": 0,
                "rows_puts": 0,
                "expiries": [],
                "atm_call_iv": None,
                "atm_put_iv": None,
                "atm_put_minus_call_iv": None,
                "otm_put_iv": None,
                "otm_call_iv": None,
                "wing_put_minus_call_iv": None,
                "term_structure_expiries": 0,
                "term_structure_slope": None,
                "calibration_rows": len(calibration_rows),
            }

        out: Dict[str, Any] = {}
        out["rows_total"] = int(len(df))
        out["rows_with_iv"] = int(df["implied_vol"].notna().sum()) if "implied_vol" in df.columns else 0
        out["rows_calls"] = int((df["option_type"] == "C").sum()) if "option_type" in df.columns else 0
        out["rows_puts"] = int((df["option_type"] == "P").sum()) if "option_type" in df.columns else 0

        expiries = []
        if "expiry" in df.columns:
            expiries = sorted({str(x.date()) for x in df["expiry"].dropna().tolist()})
        out["expiries"] = expiries

        work = df.copy()
        work = work.dropna(subset=[c for c in ("strike", "spot") if c in work.columns])
        if not work.empty:
            work["log_moneyness"] = work.apply(
                lambda r: math.log(float(r["strike"]) / float(r["spot"])) if float(r["strike"]) > 0 and float(r["spot"]) > 0 else None,
                axis=1,
            )
            work["abs_log_moneyness"] = work["log_moneyness"].abs()

        valid_iv = work.dropna(subset=[c for c in ("implied_vol", "log_moneyness") if c in work.columns]) if not work.empty else work

        atm_band = valid_iv[valid_iv["abs_log_moneyness"] <= 0.03] if not valid_iv.empty else valid_iv
        call_atm = atm_band[atm_band["option_type"] == "C"] if not atm_band.empty and "option_type" in atm_band.columns else pd.DataFrame()
        put_atm = atm_band[atm_band["option_type"] == "P"] if not atm_band.empty and "option_type" in atm_band.columns else pd.DataFrame()

        out["atm_call_iv"] = self._safe_float(call_atm["implied_vol"].mean()) if not call_atm.empty else None
        out["atm_put_iv"] = self._safe_float(put_atm["implied_vol"].mean()) if not put_atm.empty else None
        if out["atm_put_iv"] is not None and out["atm_call_iv"] is not None:
            out["atm_put_minus_call_iv"] = out["atm_put_iv"] - out["atm_call_iv"]
        else:
            out["atm_put_minus_call_iv"] = None

        left_wing = valid_iv[(valid_iv["log_moneyness"] < -0.10) & (valid_iv["log_moneyness"] > -0.25)] if not valid_iv.empty else pd.DataFrame()
        right_wing = valid_iv[(valid_iv["log_moneyness"] > 0.10) & (valid_iv["log_moneyness"] < 0.25)] if not valid_iv.empty else pd.DataFrame()

        put_wing = left_wing[left_wing["option_type"] == "P"] if not left_wing.empty and "option_type" in left_wing.columns else pd.DataFrame()
        call_wing = right_wing[right_wing["option_type"] == "C"] if not right_wing.empty and "option_type" in right_wing.columns else pd.DataFrame()

        out["otm_put_iv"] = self._safe_float(put_wing["implied_vol"].mean()) if not put_wing.empty else None
        out["otm_call_iv"] = self._safe_float(call_wing["implied_vol"].mean()) if not call_wing.empty else None
        if out["otm_put_iv"] is not None and out["otm_call_iv"] is not None:
            out["wing_put_minus_call_iv"] = out["otm_put_iv"] - out["otm_call_iv"]
        else:
            out["wing_put_minus_call_iv"] = None

        out["calibration_rows"] = len(calibration_rows)
        out["term_structure_expiries"] = len(calibration_rows)

        if len(calibration_rows) >= 2:
            pts = []
            for row in calibration_rows:
                tau = self._safe_float(row.get("tau_years"))
                atm_iv = self._safe_float(row.get("atm_iv"))
                if tau is None or atm_iv is None:
                    continue
                pts.append((tau, atm_iv))
            if len(pts) >= 2:
                pts.sort()
                x0, y0 = pts[0]
                x1, y1 = pts[-1]
                out["term_structure_slope"] = (y1 - y0) / (x1 - x0) if x1 != x0 else None
            else:
                out["term_structure_slope"] = None
        else:
            out["term_structure_slope"] = None

        out["snapshot_atm_iv"] = self._safe_float(diagnostics.get("atm_iv"))
        out["snapshot_atm_skew"] = self._safe_float(diagnostics.get("atm_skew"))
        out["snapshot_method"] = diagnostics.get("method")
        return out

    # ------------------------------------------------------------------
    # note construction
    # ------------------------------------------------------------------
    def _build_underlying_note(
        self,
        *,
        snapshot: Dict[str, Any],
        derived: Dict[str, Any],
    ) -> OptionsSurfaceResearchNote:
        underlying = str(snapshot.get("underlying") or "UNKNOWN")
        as_of_date = str(snapshot.get("valuation_date") or datetime.now(timezone.utc).date().isoformat())
        diagnostics = snapshot.get("diagnostics") or {}
        calibration_rows = snapshot.get("calibration_rows") or []

        lines: List[str] = [
            f"# Bloomberg Research Memory: {underlying} Options Surface",
            "",
            f"- Valuation date: {as_of_date}",
            f"- Surface rows: {derived.get('rows_total')}",
            f"- Rows with IV: {derived.get('rows_with_iv')}",
            f"- Calls: {derived.get('rows_calls')}",
            f"- Puts: {derived.get('rows_puts')}",
            f"- Expiries: {derived.get('term_structure_expiries')}",
            "",
            "## Primary current interpretations",
        ]

        atm_skew = derived.get("snapshot_atm_skew")
        if atm_skew is not None:
            if atm_skew < -0.5:
                lines.append("- Short-dated ATM skew is strongly negative, consistent with pronounced downside equity skew.")
            elif atm_skew < -0.1:
                lines.append("- Short-dated ATM skew is moderately negative.")
            else:
                lines.append("- Short-dated ATM skew is flat to positive.")

        wing_gap = derived.get("wing_put_minus_call_iv")
        if wing_gap is not None:
            if wing_gap > 0:
                lines.append("- OTM put wing carries richer implied volatility than the OTM call wing.")
            elif wing_gap < 0:
                lines.append("- OTM call wing is richer than the OTM put wing.")
            else:
                lines.append("- Wing vols are nearly symmetric.")

        term_slope = derived.get("term_structure_slope")
        if term_slope is None:
            lines.append("- Term-structure slope is currently unavailable or under-identified from stored calibration slices.")
        elif term_slope > 0:
            lines.append("- ATM implied volatility term structure is upward sloping over stored expiries.")
        elif term_slope < 0:
            lines.append("- ATM implied volatility term structure is downward sloping over stored expiries.")
        else:
            lines.append("- ATM implied volatility term structure is effectively flat.")

        lines.extend(
            [
                "",
                "## Calibration state",
                f"- ATM IV: {diagnostics.get('atm_iv')}",
                f"- ATM skew: {diagnostics.get('atm_skew')}",
                f"- Method: {diagnostics.get('method')}",
                f"- Calibration rows: {len(calibration_rows)}",
                "",
                "## QuantAI usage",
                "- Use this note when the query concerns SPX skew, smile, short-dated surface state, or implied-volatility structure.",
                "- This note is suitable for theorem generation, calibration support, and empirical falsification.",
            ]
        )

        metadata = {
            "source": "options_surface_memory",
            "underlying": underlying,
            "valuation_date": as_of_date,
            "derived_features": derived,
            "diagnostics": diagnostics,
            "calibration_rows": calibration_rows,
        }

        return OptionsSurfaceResearchNote(
            security=underlying,
            note_type="options_surface_state",
            title=f"{underlying} options surface state",
            as_of_date=as_of_date,
            content_markdown="\n".join(lines),
            metadata=metadata,
        )

    def _build_global_note(
        self,
        *,
        snapshot: Dict[str, Any],
        derived: Dict[str, Any],
    ) -> OptionsSurfaceResearchNote:
        underlying = str(snapshot.get("underlying") or "UNKNOWN")
        as_of_date = str(snapshot.get("valuation_date") or datetime.now(timezone.utc).date().isoformat())
        diagnostics = snapshot.get("diagnostics") or {}

        lines = [
            "# Bloomberg Research Memory: Global Options Surface Snapshot",
            "",
            f"- Anchor surface: {underlying}",
            f"- Valuation date: {as_of_date}",
            "",
            "## Current stored options-surface state",
            f"- Surface rows: {derived.get('rows_total')}",
            f"- Rows with IV: {derived.get('rows_with_iv')}",
            f"- ATM IV: {diagnostics.get('atm_iv')}",
            f"- ATM skew: {diagnostics.get('atm_skew')}",
            f"- Method: {diagnostics.get('method')}",
            f"- Expiries represented: {derived.get('term_structure_expiries')}",
            "",
            "## Current interpretation",
            "- Options-surface memory is now persisted and can be routed directly by the engine.",
            "- Use this global note to bias QuantAI toward persisted implied-volatility structure instead of rebuilding live surfaces unnecessarily.",
        ]

        metadata = {
            "source": "options_surface_memory",
            "underlying": underlying,
            "valuation_date": as_of_date,
            "derived_features": derived,
            "diagnostics": diagnostics,
        }

        return OptionsSurfaceResearchNote(
            security="GLOBAL",
            note_type="options_surface_global_state",
            title="Global options surface snapshot",
            as_of_date=as_of_date,
            content_markdown="\n".join(lines),
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    # persistence
    # ------------------------------------------------------------------
    def _persist_notes_to_sqlite(self, notes: List[OptionsSurfaceResearchNote]) -> Dict[str, Any]:
        conn = sqlite3.connect(str(self.market_db_path))
        try:
            self._ensure_bloomberg_memory_table(conn)
            rows_written = 0
            for note in notes:
                conn.execute(
                    """
                    DELETE FROM bloomberg_research_memory
                    WHERE security = ? AND note_type = ? AND title = ? AND as_of_date = ?
                    """,
                    [note.security, note.note_type, note.title, note.as_of_date],
                )
                conn.execute(
                    """
                    INSERT INTO bloomberg_research_memory (
                        security, note_type, title, as_of_date, content_markdown, metadata_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    [
                        note.security,
                        note.note_type,
                        note.title,
                        note.as_of_date,
                        note.content_markdown,
                        json.dumps(note.metadata, default=str),
                    ],
                )
                rows_written += 1
            conn.commit()
        finally:
            conn.close()

        return {
            "rows_written": rows_written,
            "db_path": str(self.market_db_path),
        }

    def _ensure_bloomberg_memory_table(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bloomberg_research_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                security TEXT NOT NULL,
                note_type TEXT NOT NULL,
                title TEXT NOT NULL,
                as_of_date TEXT NOT NULL,
                content_markdown TEXT NOT NULL,
                metadata_json TEXT
            )
            """
        )

    def _persist_note_files(self, notes: List[OptionsSurfaceResearchNote]) -> Dict[str, Any]:
        written: List[Dict[str, Any]] = []
        for note in notes:
            stem = self._slugify(f"{note.security}_{note.note_type}_{note.as_of_date}")
            json_path = self.output_dir / f"{stem}.json"
            md_path = self.output_dir / f"{stem}.md"

            json_path.write_text(json.dumps(note.as_dict(), indent=2, default=str), encoding="utf-8")
            md_path.write_text(note.content_markdown, encoding="utf-8")

            written.append(
                {
                    "security": note.security,
                    "note_type": note.note_type,
                    "json_path": str(json_path),
                    "markdown_path": str(md_path),
                }
            )
        return {"written": written}

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        try:
            if value is None or (isinstance(value, float) and pd.isna(value)):
                return None
            return float(value)
        except Exception:
            return None

    @staticmethod
    def _slugify(text: str) -> str:
        import re
        return re.sub(r"[^A-Za-z0-9]+", "_", str(text)).strip("_").lower() or "options_surface_note"


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Promote persisted options-surface memory into bloomberg_research_memory.")
    parser.add_argument("--underlying", default="SPX Index")
    parser.add_argument("--market-db-path", default="data/market_history.sqlite")
    parser.add_argument("--output-dir", default="artifacts/options_surface_research_memory")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    ingestor = OptionsSurfaceResearchMemoryIngestor(
        market_db_path=args.market_db_path,
        output_dir=args.output_dir,
    )
    result = ingestor.build_and_persist(underlying=args.underlying)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print("=" * 72)
        print("Options Surface Research Memory Ingestor")
        print("=" * 72)
        print(json.dumps(result, indent=2, default=str))
        print("=" * 72)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
