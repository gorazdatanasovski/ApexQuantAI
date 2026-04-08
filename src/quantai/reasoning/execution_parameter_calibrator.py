from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

import numpy as np
import pandas as pd

from quantai.reasoning.execution_trajectory_engine import ImpactParameters


@dataclass(frozen=True)
class ExecutionParameterCalibration:
    security: str
    as_of_date: str
    order_size: float
    horizon_minutes: float
    last_price: float
    bid: Optional[float]
    ask: Optional[float]
    spread: Optional[float]
    half_spread: float
    sigma_daily: float
    sigma_annual: float
    adv_shares: float
    participation_rate_horizon: float
    participation_rate_daily: float
    temp_cost_per_share_ref: float
    eta_temp: float
    gamma_perm: float
    diagnostics: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def as_impact_parameters(self) -> ImpactParameters:
        return ImpactParameters(
            last_price=self.last_price,
            bid=self.bid,
            ask=self.ask,
            spread=self.spread,
            sigma_daily=self.sigma_daily,
            sigma_annual=self.sigma_annual,
            eta_temp=self.eta_temp,
            gamma_perm=self.gamma_perm,
            adv_shares=self.adv_shares,
            source="execution_parameter_calibrator",
        )

    def summary(self) -> str:
        return (
            f"Execution calibration | {self.security} | px={self.last_price:.6g} | "
            f"ADV={self.adv_shares:.6g} | sigma_daily={self.sigma_daily:.6g} | "
            f"spread={self._fmt(self.spread)} | eta={self.eta_temp:.6g} | gamma={self.gamma_perm:.6g} | "
            f"rho_horizon={self.participation_rate_horizon:.6g}"
        )

    @staticmethod
    def _fmt(value: Optional[float]) -> str:
        if value is None:
            return "NA"
        return f"{float(value):.6g}"


class ExecutionParameterCalibrator:
    """
    Data-driven execution-parameter calibrator for QuantAI.

    Goal:
    Replace heuristic temporary/permanent impact coefficients with coefficients
    inferred from:
    - Bloomberg daily history
    - Bloomberg-derived feature store
    - optional live snapshot fields (PX_LAST, BID, ASK, VOLUME)

    Output:
    - calibrated eta_temp and gamma_perm
    - a drop-in ImpactParameters object for ExecutionTrajectoryEngine

    Main modeling choice:
    We linearize a spread + volatility participation model around the requested
    execution horizon/size:

        temp_cost_per_share_ref
            = half_spread + alpha * sigma_daily * price * sqrt(rho_horizon)

        eta_temp
            = temp_cost_per_share_ref / v_ref

    where
        rho_horizon = Q / (ADV * T_days)
        v_ref       = Q / T_days     [shares/day]

    and permanent impact is calibrated as

        gamma_perm = beta * sigma_daily * price / ADV

    so that total permanent shift at full size Q becomes approximately

        gamma_perm * Q ≈ beta * sigma_daily * price * (Q / ADV)

    which scales with daily participation.
    """

    TRADING_DAYS_PER_YEAR = 252.0
    MINUTES_PER_TRADING_DAY = 390.0

    def __init__(self, market_db_path: str | Path = "data/market_history.sqlite") -> None:
        self.market_db_path = Path(market_db_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def calibrate(
        self,
        *,
        security: str,
        order_size: float,
        horizon_minutes: float,
        snapshot: Mapping[str, Any] | None = None,
        lookback_days: int = 63,
        spread_bps_default: float = 5.0,
        temp_vol_scale: float = 0.50,
        perm_vol_scale: float = 0.10,
        min_adv_shares: float = 1_000_000.0,
    ) -> ExecutionParameterCalibration:
        security = str(security).strip()
        if not security:
            raise ValueError("security must be non-empty")
        order_size = float(order_size)
        horizon_minutes = float(horizon_minutes)
        if order_size <= 0:
            raise ValueError("order_size must be positive")
        if horizon_minutes <= 0:
            raise ValueError("horizon_minutes must be positive")

        history = self._load_history_wide(security)
        features = self._load_features(security)

        if history.empty and (features is None or features.empty):
            raise ValueError(
                f"No Bloomberg history/features were found for {security!r}. "
                f"Build the history warehouse and feature store first."
            )

        latest_row = None
        if not history.empty:
            latest_row = history.sort_values("date").iloc[-1]

        as_of_date = self._safe_date(
            self._snapshot_value(snapshot, ["DATE", "date", "as_of_date"])
            or (latest_row["date"] if latest_row is not None and "date" in latest_row else None)
            or (features.iloc[-1]["date"] if features is not None and not features.empty and "date" in features.columns else None)
        )

        last_price, price_source = self._infer_last_price(snapshot, latest_row, features)
        bid = self._safe_float(self._snapshot_value(snapshot, ["BID", "bid"]))
        ask = self._safe_float(self._snapshot_value(snapshot, ["ASK", "ask"]))

        spread = None
        if bid is not None and ask is not None and ask >= bid > 0:
            spread = float(ask - bid)

        sigma_daily, sigma_source = self._infer_sigma_daily(history, features, lookback_days=lookback_days)
        sigma_annual = float(sigma_daily * math.sqrt(self.TRADING_DAYS_PER_YEAR))

        adv_shares, adv_source = self._infer_adv_shares(snapshot, history, features, lookback_days=lookback_days)
        adv_shares = max(float(adv_shares), float(min_adv_shares))

        if spread is None or not np.isfinite(spread) or spread <= 0:
            spread = float(last_price * (float(spread_bps_default) / 10000.0))
            spread_source = "spread_bps_default"
        else:
            spread_source = "live_snapshot_bid_ask"

        half_spread = float(spread / 2.0)

        T_days = float(horizon_minutes / self.MINUTES_PER_TRADING_DAY)
        v_ref = float(order_size / max(T_days, 1e-12))  # shares/day
        rho_horizon = float(order_size / max(adv_shares * T_days, 1e-12))
        rho_horizon = max(rho_horizon, 1e-8)
        rho_daily = float(order_size / max(adv_shares, 1e-12))

        temp_cost_per_share_ref = float(
            half_spread + float(temp_vol_scale) * sigma_daily * last_price * math.sqrt(rho_horizon)
        )
        eta_temp = float(temp_cost_per_share_ref / max(v_ref, 1e-12))
        gamma_perm = float(float(perm_vol_scale) * sigma_daily * last_price / max(adv_shares, 1e-12))

        diagnostics = {
            "price_source": price_source,
            "sigma_source": sigma_source,
            "adv_source": adv_source,
            "spread_source": spread_source,
            "T_days": T_days,
            "v_ref_shares_per_day": v_ref,
            "spread_bps_default": float(spread_bps_default),
            "temp_vol_scale": float(temp_vol_scale),
            "perm_vol_scale": float(perm_vol_scale),
            "lookback_days": int(lookback_days),
        }

        return ExecutionParameterCalibration(
            security=security,
            as_of_date=as_of_date,
            order_size=float(order_size),
            horizon_minutes=float(horizon_minutes),
            last_price=float(last_price),
            bid=bid,
            ask=ask,
            spread=float(spread) if spread is not None else None,
            half_spread=float(half_spread),
            sigma_daily=float(sigma_daily),
            sigma_annual=float(sigma_annual),
            adv_shares=float(adv_shares),
            participation_rate_horizon=float(rho_horizon),
            participation_rate_daily=float(rho_daily),
            temp_cost_per_share_ref=float(temp_cost_per_share_ref),
            eta_temp=float(eta_temp),
            gamma_perm=float(gamma_perm),
            diagnostics=diagnostics,
        )

    def persist_calibration(
        self,
        calibration: ExecutionParameterCalibration,
        *,
        table_name: str = "execution_parameter_calibrations",
        replace: bool = False,
    ) -> Dict[str, Any]:
        self.market_db_path.parent.mkdir(parents=True, exist_ok=True)
        payload = calibration.as_dict()
        payload["diagnostics_json"] = json.dumps(payload.pop("diagnostics"), default=str)
        frame = pd.DataFrame([payload])

        conn = sqlite3.connect(str(self.market_db_path))
        try:
            frame.to_sql(table_name, conn, index=False, if_exists="replace" if replace else "append")
        finally:
            conn.close()

        return {
            "db_path": str(self.market_db_path),
            "table_name": table_name,
            "rows_written": 1,
            "replace": bool(replace),
        }

    def save_json_artifact(
        self,
        calibration: ExecutionParameterCalibration,
        path: str | Path,
    ) -> Dict[str, Any]:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(calibration.as_dict(), indent=2, default=str), encoding="utf-8")
        return {"path": str(path), "bytes": path.stat().st_size}

    # ------------------------------------------------------------------
    # Data loading / inference
    # ------------------------------------------------------------------
    def _load_history_wide(self, security: str) -> pd.DataFrame:
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

        for col in frame.columns:
            if col not in {"security", "date"}:
                frame[col] = pd.to_numeric(frame[col], errors="ignore")

        return frame.sort_values("date").reset_index(drop=True)

    def _load_features(self, security: str) -> pd.DataFrame:
        if not self.market_db_path.exists():
            return pd.DataFrame()

        conn = sqlite3.connect(str(self.market_db_path))
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
        if "date" in frame.columns:
            frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
        for col in frame.columns:
            if col not in {"security", "date"}:
                frame[col] = pd.to_numeric(frame[col], errors="ignore")
        return frame.sort_values("date").reset_index(drop=True)

    def _infer_last_price(
        self,
        snapshot: Mapping[str, Any] | None,
        latest_history_row: pd.Series | None,
        features: pd.DataFrame | None,
    ) -> tuple[float, str]:
        snap_px = self._safe_float(self._snapshot_value(snapshot, ["PX_LAST", "px_last", "last_price", "price"]))
        if snap_px is not None and snap_px > 0:
            return float(snap_px), "live_snapshot"

        if latest_history_row is not None:
            for key in ("PX_LAST", "close", "last_price"):
                if key in latest_history_row.index:
                    val = self._safe_float(latest_history_row.get(key))
                    if val is not None and val > 0:
                        return float(val), f"history.{key}"

        if features is not None and not features.empty:
            latest = features.iloc[-1]
            for key in ("PX_LAST",):
                if key in latest.index:
                    val = self._safe_float(latest.get(key))
                    if val is not None and val > 0:
                        return float(val), f"features.{key}"

        raise ValueError("Could not infer last price from snapshot/history/features")

    def _infer_sigma_daily(
        self,
        history: pd.DataFrame,
        features: pd.DataFrame,
        *,
        lookback_days: int,
    ) -> tuple[float, str]:
        if features is not None and not features.empty:
            latest = features.iloc[-1]
            for key in ("realized_vol_21", "realized_vol_63", "rv_21", "rv_63"):
                if key in latest.index:
                    val = self._safe_float(latest.get(key))
                    if val is not None and val > 0:
                        return float(val), f"features.{key}"

        if history is not None and not history.empty:
            price_col = self._pick_price_column(history)
            if price_col is not None:
                hist = history.tail(max(int(lookback_days), 5)).copy()
                px = pd.to_numeric(hist[price_col], errors="coerce")
                ret = np.log(px).diff().dropna()
                if len(ret) >= 5:
                    return float(ret.std(ddof=1)), f"history.log_returns.{price_col}"

        return 0.02, "default"

    def _infer_adv_shares(
        self,
        snapshot: Mapping[str, Any] | None,
        history: pd.DataFrame,
        features: pd.DataFrame,
        *,
        lookback_days: int,
    ) -> tuple[float, str]:
        snap_vol = self._safe_float(self._snapshot_value(snapshot, ["VOLUME", "volume"]))
        if snap_vol is not None and snap_vol > 0:
            return float(snap_vol), "live_snapshot.volume"

        if features is not None and not features.empty:
            latest = features.iloc[-1]
            for key in ("avg_volume_21", "avg_volume_63", "VOLUME"):
                if key in latest.index:
                    val = self._safe_float(latest.get(key))
                    if val is not None and val > 0:
                        return float(val), f"features.{key}"

        if history is not None and not history.empty and "VOLUME" in history.columns:
            vol = pd.to_numeric(history["VOLUME"], errors="coerce").tail(max(int(lookback_days), 5)).dropna()
            if len(vol) >= 3:
                return float(vol.mean()), "history.VOLUME.mean"

        return 10_000_000.0, "default"

    @staticmethod
    def _pick_price_column(history: pd.DataFrame) -> Optional[str]:
        for key in ("PX_LAST", "close", "last_price"):
            if key in history.columns:
                return key
        return None

    @staticmethod
    def _snapshot_value(snapshot: Mapping[str, Any] | None, keys: list[str]) -> Any:
        if snapshot is None:
            return None
        for key in keys:
            if key in snapshot:
                return snapshot[key]
        return None

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
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

    @staticmethod
    def _safe_date(value: Any) -> str:
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


__all__ = ["ExecutionParameterCalibrator", "ExecutionParameterCalibration"]
