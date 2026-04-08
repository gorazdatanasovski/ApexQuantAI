from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from quantai.reasoning.options_surface_repair_engine import OptionsSurfaceRepairEngine


@dataclass(frozen=True)
class OptionsSurfaceMemoryNote:
    underlying: str
    valuation_date: str
    n_surface_rows: int
    n_expiries: int
    atm_iv: Optional[float]
    atm_skew: Optional[float]
    method: Optional[str]
    summary_text: str
    source_csv: Optional[str]
    source_json: Optional[str]

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OptionsSurfaceMemoryIngestor:
    """
    Promote repaired options surfaces into first-class QuantAI memory.

    Why this exists:
    - surface repair now succeeds for SPX and yields real rows + calibration
    - the next gain is to persist that surface into SQLite and research memory
    - this makes implied-vol structure queryable by the rest of QuantAI

    What it writes:
    - bloomberg_options_surface_history
    - bloomberg_options_surface_calibration
    - bloomberg_options_surface_memory
    - markdown/json research notes under artifacts/options_surface_memory
    """

    def __init__(
        self,
        market_db_path: str | Path = "data/market_history.sqlite",
        repair_output_dir: str | Path = "artifacts/options_surface_repairs",
        memory_output_dir: str | Path = "artifacts/options_surface_memory",
    ) -> None:
        self.market_db_path = Path(market_db_path)
        self.repair_output_dir = Path(repair_output_dir)
        self.memory_output_dir = Path(memory_output_dir)
        self.memory_output_dir.mkdir(parents=True, exist_ok=True)

        self.market_db_path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def build_and_persist(
        self,
        underlying: str = "SPX Index",
        *,
        force_repair: bool = False,
    ) -> Dict[str, Any]:
        repaired = self._load_or_repair(underlying=underlying, force_repair=force_repair)
        summary = repaired["summary"]
        files = repaired["files"]

        best = summary.get("best_attempt") or {}
        csv_path = files.get("csv_path")
        surface_df = self._load_surface_csv(csv_path)
        calibration = best.get("calibration") or {}

        valuation_date = str(
            best.get("diagnostics", {}).get("valuation_date")
            or calibration.get("valuation_date")
            or datetime.now(timezone.utc).date().isoformat()
        )

        note = self._build_memory_note(
            underlying=underlying,
            valuation_date=valuation_date,
            best_attempt=best,
            files=files,
        )

        db_stats = self._persist_to_sqlite(
            underlying=underlying,
            valuation_date=valuation_date,
            surface_df=surface_df,
            calibration=calibration,
            note=note,
        )
        note_files = self._persist_note_files(note)

        return {
            "underlying": underlying,
            "valuation_date": valuation_date,
            "best_attempt": best,
            "db_stats": db_stats,
            "note": note.as_dict(),
            "note_files": note_files,
            "repair_files": files,
        }

    # ------------------------------------------------------------------
    # repair loading
    # ------------------------------------------------------------------
    def _load_or_repair(self, *, underlying: str, force_repair: bool) -> Dict[str, Any]:
        stem = self._slugify(f"{underlying}_surface_repair")
        json_path = self.repair_output_dir / f"{stem}.json"
        csv_path = self.repair_output_dir / f"{stem}.csv"
        md_path = self.repair_output_dir / f"{stem}.md"

        if (not force_repair) and json_path.exists():
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            files = {
                "json_path": str(json_path),
                "markdown_path": str(md_path) if md_path.exists() else None,
                "csv_path": str(csv_path) if csv_path.exists() else None,
                "bytes_json": json_path.stat().st_size,
                "bytes_markdown": md_path.stat().st_size if md_path.exists() else 0,
                "bytes_csv": csv_path.stat().st_size if csv_path.exists() else 0,
            }
            return {"summary": payload, "files": files}

        engine = OptionsSurfaceRepairEngine(output_dir=self.repair_output_dir)
        return engine.repair_underlying(underlying=underlying)

    # ------------------------------------------------------------------
    # note building
    # ------------------------------------------------------------------
    def _build_memory_note(
        self,
        *,
        underlying: str,
        valuation_date: str,
        best_attempt: Dict[str, Any],
        files: Dict[str, Any],
    ) -> OptionsSurfaceMemoryNote:
        calibration = best_attempt.get("calibration") or {}
        slices = calibration.get("slices") or []
        atm_iv = None
        atm_skew = None
        method = None
        if slices:
            first = slices[0] or {}
            atm_iv = self._safe_float(first.get("atm_iv"))
            atm_skew = self._safe_float(first.get("skew"))
            method = first.get("method")

        n_surface_rows = int(best_attempt.get("n_surface_rows", 0) or 0)
        n_expiries = int(best_attempt.get("n_expiries", 0) or 0)

        summary_text = (
            f"{underlying} options surface repaired and persisted for {valuation_date}. "
            f"Recovered {n_surface_rows} surface rows across {n_expiries} expiries. "
            f"Primary calibration method: {method or 'unavailable'}. "
            f"ATM implied volatility: {atm_iv if atm_iv is not None else 'NA'}. "
            f"ATM skew: {atm_skew if atm_skew is not None else 'NA'}."
        )

        return OptionsSurfaceMemoryNote(
            underlying=underlying,
            valuation_date=valuation_date,
            n_surface_rows=n_surface_rows,
            n_expiries=n_expiries,
            atm_iv=atm_iv,
            atm_skew=atm_skew,
            method=method,
            summary_text=summary_text,
            source_csv=files.get("csv_path"),
            source_json=files.get("json_path"),
        )

    # ------------------------------------------------------------------
    # sqlite persistence
    # ------------------------------------------------------------------
    def _persist_to_sqlite(
        self,
        *,
        underlying: str,
        valuation_date: str,
        surface_df: pd.DataFrame,
        calibration: Dict[str, Any],
        note: OptionsSurfaceMemoryNote,
    ) -> Dict[str, Any]:
        conn = sqlite3.connect(str(self.market_db_path))
        try:
            self._ensure_tables(conn)

            # remove same-day snapshot for idempotence
            conn.execute(
                "DELETE FROM bloomberg_options_surface_history WHERE underlying = ? AND valuation_date = ?",
                [underlying, valuation_date],
            )
            conn.execute(
                "DELETE FROM bloomberg_options_surface_calibration WHERE underlying = ? AND valuation_date = ?",
                [underlying, valuation_date],
            )
            conn.execute(
                "DELETE FROM bloomberg_options_surface_memory WHERE underlying = ? AND valuation_date = ?",
                [underlying, valuation_date],
            )

            n_surface_rows = 0
            if surface_df is not None and not surface_df.empty:
                rows = self._surface_rows(surface_df, underlying=underlying, valuation_date=valuation_date)
                conn.executemany(
                    """
                    INSERT INTO bloomberg_options_surface_history (
                        underlying, valuation_date, option_ticker, expiry, tau_years, option_type,
                        strike, spot, implied_vol, mid_price, volume, open_interest, raw_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    rows,
                )
                n_surface_rows = len(rows)

            calib_rows = self._calibration_rows(calibration, underlying=underlying, valuation_date=valuation_date)
            if calib_rows:
                conn.executemany(
                    """
                    INSERT INTO bloomberg_options_surface_calibration (
                        underlying, valuation_date, expiry, tau_years, n_points,
                        atm_iv, skew, intercept, r_squared, method, raw_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    calib_rows,
                )

            conn.execute(
                """
                INSERT INTO bloomberg_options_surface_memory (
                    underlying, valuation_date, n_surface_rows, n_expiries,
                    atm_iv, atm_skew, method, summary_text, note_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    note.underlying,
                    note.valuation_date,
                    note.n_surface_rows,
                    note.n_expiries,
                    note.atm_iv,
                    note.atm_skew,
                    note.method,
                    note.summary_text,
                    json.dumps(note.as_dict(), default=str),
                ],
            )

            conn.commit()
            return {
                "surface_rows_written": n_surface_rows,
                "calibration_rows_written": len(calib_rows),
                "memory_rows_written": 1,
                "db_path": str(self.market_db_path),
            }
        finally:
            conn.close()

    def _ensure_tables(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bloomberg_options_surface_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                underlying TEXT NOT NULL,
                valuation_date TEXT NOT NULL,
                option_ticker TEXT,
                expiry TEXT,
                tau_years REAL,
                option_type TEXT,
                strike REAL,
                spot REAL,
                implied_vol REAL,
                mid_price REAL,
                volume REAL,
                open_interest REAL,
                raw_json TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bloomberg_options_surface_calibration (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                underlying TEXT NOT NULL,
                valuation_date TEXT NOT NULL,
                expiry TEXT,
                tau_years REAL,
                n_points INTEGER,
                atm_iv REAL,
                skew REAL,
                intercept REAL,
                r_squared REAL,
                method TEXT,
                raw_json TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bloomberg_options_surface_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                underlying TEXT NOT NULL,
                valuation_date TEXT NOT NULL,
                n_surface_rows INTEGER,
                n_expiries INTEGER,
                atm_iv REAL,
                atm_skew REAL,
                method TEXT,
                summary_text TEXT,
                note_json TEXT
            )
            """
        )

    def _surface_rows(
        self,
        df: pd.DataFrame,
        *,
        underlying: str,
        valuation_date: str,
    ) -> List[tuple]:
        out: List[tuple] = []
        cols = set(df.columns)

        def get_value(row, name, default=None):
            return row[name] if name in cols else default

        for _, row in df.iterrows():
            raw = {k: self._json_safe(v) for k, v in row.to_dict().items()}
            out.append(
                (
                    underlying,
                    valuation_date,
                    get_value(row, "option_ticker"),
                    self._as_text(get_value(row, "expiry")),
                    self._safe_float(get_value(row, "tau_years")),
                    self._as_text(get_value(row, "option_type")),
                    self._safe_float(get_value(row, "strike")),
                    self._safe_float(get_value(row, "spot")),
                    self._safe_float(get_value(row, "implied_vol")),
                    self._safe_float(get_value(row, "mid_price")),
                    self._safe_float(get_value(row, "volume")),
                    self._safe_float(get_value(row, "open_interest")),
                    json.dumps(raw, default=str),
                )
            )
        return out

    def _calibration_rows(
        self,
        calibration: Dict[str, Any],
        *,
        underlying: str,
        valuation_date: str,
    ) -> List[tuple]:
        rows: List[tuple] = []
        for item in calibration.get("slices") or []:
            rows.append(
                (
                    underlying,
                    valuation_date,
                    self._as_text(item.get("expiry")),
                    self._safe_float(item.get("tau_years")),
                    int(item.get("n_points", 0) or 0),
                    self._safe_float(item.get("atm_iv")),
                    self._safe_float(item.get("skew")),
                    self._safe_float(item.get("intercept")),
                    self._safe_float(item.get("r_squared")),
                    self._as_text(item.get("method")),
                    json.dumps(item, default=str),
                )
            )
        return rows

    # ------------------------------------------------------------------
    # note files
    # ------------------------------------------------------------------
    def _persist_note_files(self, note: OptionsSurfaceMemoryNote) -> Dict[str, Any]:
        stem = self._slugify(f"{note.underlying}_{note.valuation_date}_surface_memory")
        json_path = self.memory_output_dir / f"{stem}.json"
        md_path = self.memory_output_dir / f"{stem}.md"

        json_path.write_text(json.dumps(note.as_dict(), indent=2, default=str), encoding="utf-8")
        md_path.write_text(self._note_markdown(note), encoding="utf-8")

        return {
            "json_path": str(json_path),
            "markdown_path": str(md_path),
            "bytes_json": json_path.stat().st_size,
            "bytes_markdown": md_path.stat().st_size,
        }

    def _note_markdown(self, note: OptionsSurfaceMemoryNote) -> str:
        lines = [
            f"# Options Surface Memory Note: {note.underlying}",
            "",
            f"- Valuation date: {note.valuation_date}",
            f"- Surface rows: {note.n_surface_rows}",
            f"- Expiries: {note.n_expiries}",
            f"- ATM IV: {note.atm_iv}",
            f"- ATM skew: {note.atm_skew}",
            f"- Method: {note.method}",
            "",
            "## Summary",
            note.summary_text,
            "",
            "## Sources",
            f"- Surface CSV: {note.source_csv}",
            f"- Repair JSON: {note.source_json}",
        ]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _load_surface_csv(self, csv_path: Optional[str]) -> pd.DataFrame:
        if not csv_path:
            return pd.DataFrame()
        path = Path(csv_path)
        if not path.exists():
            return pd.DataFrame()
        return pd.read_csv(path)

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        try:
            if value is None or (isinstance(value, float) and pd.isna(value)):
                return None
            return float(value)
        except Exception:
            return None

    @staticmethod
    def _as_text(value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, float) and pd.isna(value):
            return None
        return str(value)

    @staticmethod
    def _json_safe(value: Any) -> Any:
        if isinstance(value, float) and pd.isna(value):
            return None
        return value

    @staticmethod
    def _slugify(text: str) -> str:
        import re
        return re.sub(r"[^A-Za-z0-9]+", "_", str(text)).strip("_").lower() or "surface_memory"

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Persist repaired options surfaces into QuantAI memory.")
    parser.add_argument("--underlying", default="SPX Index")
    parser.add_argument("--market-db-path", default="data/market_history.sqlite")
    parser.add_argument("--repair-output-dir", default="artifacts/options_surface_repairs")
    parser.add_argument("--memory-output-dir", default="artifacts/options_surface_memory")
    parser.add_argument("--force-repair", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    ingestor = OptionsSurfaceMemoryIngestor(
        market_db_path=args.market_db_path,
        repair_output_dir=args.repair_output_dir,
        memory_output_dir=args.memory_output_dir,
    )
    result = ingestor.build_and_persist(
        underlying=args.underlying,
        force_repair=bool(args.force_repair),
    )

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print("=" * 72)
        print("Options Surface Memory Ingestor")
        print("=" * 72)
        print(json.dumps(result, indent=2, default=str))
        print("=" * 72)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
