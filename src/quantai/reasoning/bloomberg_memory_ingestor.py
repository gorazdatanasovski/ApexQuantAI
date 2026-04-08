from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd


@dataclass(frozen=True)
class MemoryNote:
    security: str
    note_type: str
    title: str
    as_of_date: str
    content_markdown: str
    metadata: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BloombergMemoryIngestor:
    """
    Convert Bloomberg learning artifacts + local feature/history tables into
    structured research memory notes that QuantAI can reuse later.

    Output targets:
    - SQLite table: bloomberg_research_memory
    - Markdown notes in artifacts/bloomberg_memory/
    - JSON sidecars for downstream automation

    This does not mutate the book memory store directly. It creates a curated
    intermediate research-memory layer first.
    """

    DEFAULT_WINDOWS = (5, 21, 63)

    def __init__(
        self,
        market_db_path: str | Path = "data/market_history.sqlite",
        snapshot_path: str | Path = "artifacts/bloomberg_learning_snapshot.json",
        output_dir: str | Path = "artifacts/bloomberg_memory",
    ) -> None:
        self.market_db_path = Path(market_db_path)
        self.snapshot_path = Path(snapshot_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build_notes(
        self,
        securities: Optional[Iterable[str]] = None,
        windows: Iterable[int] = DEFAULT_WINDOWS,
    ) -> List[MemoryNote]:
        snapshot = self._load_snapshot()
        windows = tuple(sorted({int(w) for w in windows if int(w) > 1}))

        features = self._load_feature_table()
        history = self._load_history_table()

        if features.empty:
            raise ValueError("bloomberg_daily_features is empty or unavailable")

        if securities:
            securities = [str(s).strip() for s in securities if str(s).strip()]
            features = features[features["security"].isin(securities)].copy()
            history = history[history["security"].isin(securities)].copy()

        notes: List[MemoryNote] = []
        for security, panel in features.groupby("security", sort=True):
            panel = panel.sort_values("date").reset_index(drop=True)
            latest = panel.iloc[-1]
            hist_panel = history[history["security"] == security].sort_values("date").reset_index(drop=True)
            note = self._build_security_note(
                security=security,
                latest=latest,
                panel=panel,
                history=hist_panel,
                snapshot=snapshot,
                windows=windows,
            )
            notes.append(note)

        global_note = self._build_global_note(snapshot=snapshot, features=features, history=history, windows=windows)
        notes.append(global_note)
        return notes

    def persist_notes(
        self,
        notes: List[MemoryNote],
        table_name: str = "bloomberg_research_memory",
        replace: bool = True,
    ) -> Dict[str, Any]:
        rows = []
        for note in notes:
            rows.append(
                {
                    "security": note.security,
                    "note_type": note.note_type,
                    "title": note.title,
                    "as_of_date": note.as_of_date,
                    "content_markdown": note.content_markdown,
                    "metadata_json": json.dumps(note.metadata, default=str),
                }
            )

        df = pd.DataFrame(rows)
        conn = sqlite3.connect(str(self.market_db_path))
        try:
            df.to_sql(table_name, conn, index=False, if_exists="replace" if replace else "append")
        finally:
            conn.close()

        written_files = []
        for note in notes:
            slug = self._slugify(f"{note.note_type}_{note.security}_{note.as_of_date}")
            md_path = self.output_dir / f"{slug}.md"
            json_path = self.output_dir / f"{slug}.json"
            md_path.write_text(note.content_markdown, encoding="utf-8")
            json_path.write_text(json.dumps(note.as_dict(), indent=2, default=str), encoding="utf-8")
            written_files.append({"markdown": str(md_path), "json": str(json_path)})

        return {
            "table": table_name,
            "rows_written": int(len(df)),
            "replace": bool(replace),
            "files_written": written_files,
        }

    def build_and_persist(
        self,
        securities: Optional[Iterable[str]] = None,
        windows: Iterable[int] = DEFAULT_WINDOWS,
        table_name: str = "bloomberg_research_memory",
        replace: bool = True,
    ) -> Dict[str, Any]:
        notes = self.build_notes(securities=securities, windows=windows)
        result = self.persist_notes(notes=notes, table_name=table_name, replace=replace)
        result["n_notes"] = len(notes)
        return result

    def _build_security_note(
        self,
        security: str,
        latest: pd.Series,
        panel: pd.DataFrame,
        history: pd.DataFrame,
        snapshot: Dict[str, Any],
        windows: Iterable[int],
    ) -> MemoryNote:
        as_of = self._safe_date(latest.get("date"))

        realized = {w: self._safe_float(latest.get(f"realized_vol_{w}")) for w in windows}
        hurst = {w: self._safe_float(latest.get(f"hurst_varscale_{w}")) for w in windows}
        ou_speed = {w: self._safe_float(latest.get(f"ou_speed_{w}")) for w in windows}
        jump_share = {w: self._safe_float(latest.get(f"jump_share_{w}")) for w in windows}
        acf_abs = {w: self._safe_float(latest.get(f"acf_abs_return_{w}")) for w in windows}
        autocorr = {w: self._safe_float(latest.get(f"autocorr_return_{w}")) for w in windows}
        volume_z = {w: self._safe_float(latest.get(f"volume_z_{w}")) for w in windows}

        regime = self._infer_regime(realized.get(21), realized.get(63))
        roughness = self._infer_roughness(hurst.get(63) or hurst.get(21))
        mean_reversion = self._infer_mean_reversion(ou_speed.get(21), ou_speed.get(63))

        last_px = self._safe_float(latest.get("PX_LAST"))
        drawdown = self._safe_float(latest.get("drawdown"))
        last_return = self._safe_float(latest.get("return"))

        history_span = {
            "rows": int(len(history)),
            "start": self._safe_date(history["date"].min()) if not history.empty else None,
            "end": self._safe_date(history["date"].max()) if not history.empty else None,
        }

        content = f"""# Bloomberg Research Memory: {security}

## As of
- Date: {as_of}

## Market state
- Last price: {self._fmt(last_px)}
- Last daily return: {self._fmt(last_return)}
- Current drawdown: {self._fmt(drawdown)}
- Volatility regime: {regime}
- Roughness signature: {roughness}
- Mean-reversion signature: {mean_reversion}

## Realized volatility panel
{self._bullet_map('Realized vol', realized)}

## Roughness / Hurst-style panel
{self._bullet_map('Hurst variance scaling', hurst)}

## OU / mean-reversion panel
{self._bullet_map('OU speed', ou_speed)}

## Jump / discontinuity panel
{self._bullet_map('Jump share', jump_share)}

## Volatility clustering panel
{self._bullet_map('Abs-return ACF', acf_abs)}

## Return autocorrelation panel
{self._bullet_map('Return autocorr', autocorr)}

## Volume anomaly panel
{self._bullet_map('Volume z-score', volume_z)}

## Historical coverage
- Rows: {history_span['rows']}
- Start: {history_span['start']}
- End: {history_span['end']}

## Research interpretation
This note summarizes the local Bloomberg-derived empirical state for {security}. It is intended to support theorem generation, empirical falsification, calibration design, and hypothesis ranking inside QuantAI.

Primary current interpretations:
- Volatility regime classification: **{regime}**
- Roughness classification: **{roughness}**
- Mean-reversion classification: **{mean_reversion}**

## Research prompts QuantAI can pursue
1. Test whether roughness estimates co-move with realized-volatility regimes.
2. Test whether jump share rises in high-volatility drawdown states.
3. Compare OU-style speeds across windows for stability or regime breaks.
4. Examine whether absolute-return persistence supports rough-vol style memory.

## Snapshot linkage
- Feature table present: {'yes' if snapshot.get('feature_summary') else 'no'}
- Options snapshot attempted: {'yes' if snapshot.get('options_summary') else 'no'}
"""

        meta = {
            "security": security,
            "as_of_date": as_of,
            "regime": regime,
            "roughness": roughness,
            "mean_reversion": mean_reversion,
            "realized_vol": realized,
            "hurst": hurst,
            "ou_speed": ou_speed,
            "jump_share": jump_share,
            "acf_abs_return": acf_abs,
            "autocorr_return": autocorr,
            "volume_z": volume_z,
            "history_span": history_span,
        }

        return MemoryNote(
            security=security,
            note_type="security_regime_note",
            title=f"{security} empirical research memory",
            as_of_date=as_of,
            content_markdown=content,
            metadata=meta,
        )

    def _build_global_note(
        self,
        snapshot: Dict[str, Any],
        features: pd.DataFrame,
        history: pd.DataFrame,
        windows: Iterable[int],
    ) -> MemoryNote:
        as_of = self._safe_date(features["date"].max()) if not features.empty else "unknown"
        securities = sorted(features["security"].dropna().astype(str).unique().tolist()) if not features.empty else []

        options = snapshot.get("options_summary") or {}
        cap = snapshot.get("capability_report") or {}

        content = f"""# Bloomberg Research Memory: Global Snapshot

## Capabilities
- blpapi available: {cap.get('blpapi_available')}
- BQL available: {cap.get('bql_available')}
- options surface builder available: {cap.get('options_surface_available')}

## Local warehouse status
- History rows written: {((snapshot.get('history_summary') or {}).get('rows_written'))}
- Feature rows written: {((snapshot.get('feature_summary') or {}).get('rows_written'))}
- Securities represented: {", ".join(securities) if securities else "none"}

## Options diagnostics
- Underlying attempted: {options.get('underlying')}
- Chain field used: {options.get('chain_field_used')}
- Chain rows: {options.get('n_chain_rows')}
- Snapshot rows: {options.get('n_snapshot_rows')}
- Surface rows: {options.get('n_surface_rows')}

## Interpretation
QuantAI currently has a working Bloomberg historical warehouse and a working empirical feature layer. BQL is environment-dependent and currently unavailable unless the local environment includes Bloomberg's BQL object model. Options-surface extraction is partially wired but still requires stronger contract selection and normalization when the requested put/call subset is not represented in the sampled chain.

## Next research actions
1. Convert these memory notes into retrieval-ready empirical evidence.
2. Route market-state questions to this Bloomberg memory before invoking theorem synthesis.
3. Strengthen options contract selection so put/call filters do not collapse to zero usable rows.
4. Build calibration-specific memory notes once surface extraction is stable.
"""

        meta = {
            "as_of_date": as_of,
            "securities": securities,
            "history_rows": int(len(history)),
            "feature_rows": int(len(features)),
            "capability_report": cap,
            "options_summary": options,
            "windows": list(windows),
        }

        return MemoryNote(
            security="GLOBAL",
            note_type="global_bloomberg_note",
            title="Global Bloomberg learning snapshot",
            as_of_date=as_of,
            content_markdown=content,
            metadata=meta,
        )

    def _load_snapshot(self) -> Dict[str, Any]:
        if not self.snapshot_path.exists():
            raise FileNotFoundError(f"Snapshot file not found: {self.snapshot_path}")
        return json.loads(self.snapshot_path.read_text(encoding="utf-8"))

    def _load_feature_table(self) -> pd.DataFrame:
        conn = sqlite3.connect(str(self.market_db_path))
        try:
            return pd.read_sql_query("SELECT * FROM bloomberg_daily_features", conn, parse_dates=["date"])
        finally:
            conn.close()

    def _load_history_table(self) -> pd.DataFrame:
        conn = sqlite3.connect(str(self.market_db_path))
        try:
            return pd.read_sql_query("SELECT * FROM bloomberg_daily_history", conn, parse_dates=["date"])
        finally:
            conn.close()

    def _infer_regime(self, rv21: Optional[float], rv63: Optional[float]) -> str:
        if rv21 is None or rv63 is None:
            return "unknown"
        if rv63 <= 0:
            return "unknown"
        ratio = rv21 / rv63
        if ratio > 1.35:
            return "high_volatility"
        if ratio < 0.8:
            return "compressed_volatility"
        return "balanced_volatility"

    def _infer_roughness(self, hurst: Optional[float]) -> str:
        if hurst is None:
            return "unknown"
        if hurst < 0.45:
            return "rough_or_antipersistent"
        if hurst > 0.55:
            return "persistent"
        return "near_brownian"

    def _infer_mean_reversion(self, ou21: Optional[float], ou63: Optional[float]) -> str:
        candidates = [x for x in [ou21, ou63] if x is not None]
        if not candidates:
            return "unknown"
        avg = sum(candidates) / len(candidates)
        if avg > 1.0:
            return "strong_mean_reversion"
        if avg > 0.2:
            return "moderate_mean_reversion"
        return "weak_mean_reversion"

    def _bullet_map(self, label: str, payload: Dict[int, Optional[float]]) -> str:
        lines = []
        for k, v in payload.items():
            lines.append(f"- {label} {k}: {self._fmt(v)}")
        return "\n".join(lines)

    def _fmt(self, value: Optional[float]) -> str:
        if value is None:
            return "NA"
        try:
            return f"{float(value):.6g}"
        except Exception:
            return str(value)

    def _safe_float(self, value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            if pd.isna(value):
                return None
        except Exception:
            pass
        try:
            return float(value)
        except Exception:
            return None

    def _safe_date(self, value: Any) -> str:
        if value is None:
            return "unknown"
        try:
            if pd.isna(value):
                return "unknown"
        except Exception:
            pass
        try:
            return pd.Timestamp(value).strftime("%Y-%m-%d")
        except Exception:
            return str(value)

    def _slugify(self, text: str) -> str:
        out = []
        for ch in str(text):
            if ch.isalnum():
                out.append(ch.lower())
            else:
                out.append("_")
        slug = "".join(out)
        while "__" in slug:
            slug = slug.replace("__", "_")
        return slug.strip("_")
