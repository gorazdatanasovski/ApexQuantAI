from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence

import pandas as pd


@dataclass(frozen=True)
class ResolvedSnapshot:
    security: str
    px_last: float
    bid: Optional[float]
    ask: Optional[float]
    bid_size: Optional[float]
    ask_size: Optional[float]
    volume: Optional[float]
    spread: Optional[float]
    spread_source: str
    diagnostics: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IntradayFallbackResult:
    security: str
    status: str
    source: str
    frame_preview: list[dict[str, Any]]
    diagnostics: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LiveDataResilience:
    """
    Harden Bloomberg live-data usage for QuantAI.

    Main goals:
    - normalize inconsistent snapshot payloads
    - infer bid/ask spread when Bloomberg snapshot omits one side
    - provide a deterministic fallback when intraday live bars are unavailable
    """

    def __init__(self, market_db_path: str | Path = "data/market_history.sqlite") -> None:
        self.market_db_path = Path(market_db_path)

    # ------------------------------------------------------------------
    # snapshot normalization
    # ------------------------------------------------------------------
    def resolve_snapshot(
        self,
        row: Mapping[str, Any],
        *,
        security: Optional[str] = None,
        default_spread_bps: float = 5.0,
    ) -> ResolvedSnapshot:
        sec = str(
            security
            or row.get("security")
            or row.get("Security")
            or row.get("ticker")
            or "UNKNOWN"
        )

        px_last = self._as_float(
            row.get("PX_LAST")
            or row.get("px_last")
            or row.get("last_price")
            or row.get("price")
        )
        if px_last is None or px_last <= 0:
            hist = self._load_latest_history_row(sec)
            px_last = self._as_float((hist or {}).get("PX_LAST"))
        if px_last is None or px_last <= 0:
            raise ValueError(f"Could not infer PX_LAST for {sec}")

        bid = self._as_float(row.get("BID") or row.get("bid"))
        ask = self._as_float(row.get("ASK") or row.get("ask"))
        bid_size = self._as_float(row.get("BID_SIZE") or row.get("bid_size"))
        ask_size = self._as_float(row.get("ASK_SIZE") or row.get("ask_size"))
        volume = self._as_float(row.get("VOLUME") or row.get("volume"))

        diagnostics: Dict[str, Any] = {
            "had_bid": bid is not None,
            "had_ask": ask is not None,
            "had_volume": volume is not None,
        }

        spread_source = "live_snapshot"
        spread = None

        if bid is not None and ask is not None and ask >= bid > 0:
            spread = float(ask - bid)
        else:
            hist = self._load_latest_history_row(sec)
            inferred_spread = self._infer_spread_from_history(sec, px_last=px_last, default_spread_bps=default_spread_bps)
            spread = inferred_spread
            spread_source = "history_or_default"

            if bid is None and ask is None:
                bid = float(px_last - spread / 2.0)
                ask = float(px_last + spread / 2.0)
                diagnostics["bid_ask_inferred"] = "both"
            elif bid is None and ask is not None:
                bid = float(ask - spread)
                diagnostics["bid_ask_inferred"] = "bid_only"
            elif ask is None and bid is not None:
                ask = float(bid + spread)
                diagnostics["bid_ask_inferred"] = "ask_only"

        if spread is None and bid is not None and ask is not None:
            spread = float(max(ask - bid, 0.0))

        diagnostics["resolved_px_last"] = px_last
        diagnostics["resolved_bid"] = bid
        diagnostics["resolved_ask"] = ask
        diagnostics["resolved_spread"] = spread
        diagnostics["spread_source"] = spread_source

        return ResolvedSnapshot(
            security=sec,
            px_last=float(px_last),
            bid=bid,
            ask=ask,
            bid_size=bid_size,
            ask_size=ask_size,
            volume=volume,
            spread=spread,
            spread_source=spread_source,
            diagnostics=diagnostics,
        )

    # ------------------------------------------------------------------
    # intraday fallback
    # ------------------------------------------------------------------
    def intraday_fallback_from_history(
        self,
        security: str,
        *,
        periods: int = 60,
    ) -> IntradayFallbackResult:
        frame = self._load_history_frame(security)
        if frame.empty:
            return IntradayFallbackResult(
                security=security,
                status="failed",
                source="history_fallback",
                frame_preview=[],
                diagnostics={"reason": "no historical daily data available"},
            )

        frame = frame.sort_values("date").tail(max(int(periods), 10)).copy()
        if "PX_LAST" not in frame.columns:
            return IntradayFallbackResult(
                security=security,
                status="failed",
                source="history_fallback",
                frame_preview=[],
                diagnostics={"reason": "PX_LAST missing in history"},
            )

        frame["time"] = pd.to_datetime(frame["date"], errors="coerce")
        frame["close"] = pd.to_numeric(frame["PX_LAST"], errors="coerce")
        frame = frame.dropna(subset=["time", "close"])

        preview = frame[["time", "close"]].tail(20).to_dict(orient="records")
        return IntradayFallbackResult(
            security=security,
            status="ok",
            source="history_fallback",
            frame_preview=preview,
            diagnostics={
                "rows_used": int(len(frame)),
                "note": "This is not true intraday data; it is a deterministic daily fallback to keep estimators alive.",
            },
        )

    # ------------------------------------------------------------------
    # database helpers
    # ------------------------------------------------------------------
    def _load_latest_history_row(self, security: str) -> Optional[Dict[str, Any]]:
        frame = self._load_history_frame(security)
        if frame.empty:
            return None
        row = frame.sort_values("date").iloc[-1].to_dict()
        return {str(k): v for k, v in row.items()}

    def _load_history_frame(self, security: str) -> pd.DataFrame:
        if not self.market_db_path.exists():
            return pd.DataFrame()

        conn = sqlite3.connect(str(self.market_db_path))
        try:
            frame = pd.read_sql_query(
                "SELECT * FROM bloomberg_daily_history WHERE security = ?",
                conn,
                params=[security],
            )
        except Exception:
            try:
                frame = pd.read_sql_query(
                    "SELECT * FROM bloomberg_daily_features WHERE security = ?",
                    conn,
                    params=[security],
                )
            except Exception:
                conn.close()
                return pd.DataFrame()
        finally:
            try:
                conn.close()
            except Exception:
                pass

        if frame.empty:
            return frame

        frame.columns = [str(c) for c in frame.columns]

        if {"security", "date", "field", "value"}.issubset(frame.columns):
            wide = (
                frame.pivot_table(
                    index=["security", "date"],
                    columns="field",
                    values="value",
                    aggfunc="last",
                )
                .reset_index()
            )
            wide.columns = [str(c) for c in wide.columns]
            frame = wide

        if "date" in frame.columns:
            frame["date"] = pd.to_datetime(frame["date"], errors="coerce")

        return frame

    def _infer_spread_from_history(
        self,
        security: str,
        *,
        px_last: float,
        default_spread_bps: float,
    ) -> float:
        frame = self._load_history_frame(security)
        if not frame.empty and "PX_LAST" in frame.columns:
            px = pd.to_numeric(frame["PX_LAST"], errors="coerce").dropna().tail(63)
            if len(px) >= 5:
                # Crude microstructure proxy when no bid/ask is available:
                # spread proportional to daily volatility with a floor.
                logret = px.map(math.log).diff().dropna()
                sigma = float(logret.std(ddof=1)) if len(logret) >= 3 else 0.0
                vol_spread = max(px_last * sigma * 0.15, px_last * default_spread_bps / 10000.0)
                return float(max(vol_spread, px_last * 1e-5))

        return float(max(px_last * default_spread_bps / 10000.0, px_last * 1e-5))

    @staticmethod
    def _as_float(value: Any) -> Optional[float]:
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


__all__ = ["LiveDataResilience", "ResolvedSnapshot", "IntradayFallbackResult"]
