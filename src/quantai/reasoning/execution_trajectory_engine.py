from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ImpactParameters:
    last_price: float
    bid: Optional[float]
    ask: Optional[float]
    spread: Optional[float]
    sigma_daily: float
    sigma_annual: float
    eta_temp: float
    gamma_perm: float
    adv_shares: Optional[float]
    source: str = "manual_or_snapshot"

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExecutionTrajectoryResult:
    security: str
    model: str
    total_shares: float
    horizon_minutes: float
    dt_minutes: float
    risk_aversion: float
    kappa: float
    expected_cost: float
    variance_cost: float
    objective: float
    diagnostics: Dict[str, Any]
    schedule: pd.DataFrame

    def as_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["schedule_preview"] = self.schedule.head(50).to_dict(orient="records")
        payload["schedule_shape"] = list(self.schedule.shape)
        payload.pop("schedule", None)
        return payload

    def summary(self) -> str:
        return (
            f"Execution | {self.security} | model={self.model} | "
            f"shares={self.total_shares:.0f} | horizon_min={self.horizon_minutes:.3f} | "
            f"kappa={self.kappa:.6g} | expected_cost={self.expected_cost:.6g} | "
            f"variance_cost={self.variance_cost:.6g} | objective={self.objective:.6g}"
        )


class ExecutionTrajectoryEngine:
    """
    Almgren–Chriss style execution engine.

    Main capabilities:
    - infer impact parameters from a live snapshot or manual inputs
    - compute continuous-time Almgren–Chriss liquidation trajectory
    - discretize trajectory into child orders
    - compute expected temporary/permanent impact cost and variance proxy
    - persist schedules for later QuantAI retrieval/research

    Notes:
    - This is a practical execution layer, not a full market simulator.
    - The engine is intentionally transparent: all inputs and formulas are surfaced.
    """

    TRADING_DAYS_PER_YEAR = 252.0
    MINUTES_PER_TRADING_DAY = 390.0

    def __init__(self, market_db_path: str | Path = "data/market_history.sqlite") -> None:
        self.market_db_path = Path(market_db_path)

    # ------------------------------------------------------------------
    # Parameter inference
    # ------------------------------------------------------------------
    def infer_impact_parameters(
        self,
        *,
        security: str,
        last_price: float,
        bid: Optional[float] = None,
        ask: Optional[float] = None,
        sigma_daily: Optional[float] = None,
        sigma_annual: Optional[float] = None,
        adv_shares: Optional[float] = None,
        eta_temp: Optional[float] = None,
        gamma_perm: Optional[float] = None,
    ) -> ImpactParameters:
        last_price = float(last_price)
        if last_price <= 0:
            raise ValueError("last_price must be positive")

        spread = None
        if bid is not None and ask is not None:
            bid = float(bid)
            ask = float(ask)
            if ask >= bid and bid > 0:
                spread = float(ask - bid)

        if sigma_daily is None and sigma_annual is None:
            # conservative default if not supplied
            sigma_daily = 0.02
        if sigma_daily is None and sigma_annual is not None:
            sigma_daily = float(sigma_annual) / math.sqrt(self.TRADING_DAYS_PER_YEAR)
        if sigma_annual is None and sigma_daily is not None:
            sigma_annual = float(sigma_daily) * math.sqrt(self.TRADING_DAYS_PER_YEAR)

        sigma_daily = float(sigma_daily)
        sigma_annual = float(sigma_annual)

        # Temporary impact coefficient eta:
        # if not given, anchor it to half-spread per share in price units.
        if eta_temp is None:
            if spread is not None and spread > 0:
                eta_temp = max(spread / 2.0, 1e-6)
            else:
                eta_temp = max(last_price * 1e-4, 1e-6)

        # Permanent impact coefficient gamma:
        # if not given, use a small fraction of temporary impact.
        if gamma_perm is None:
            gamma_perm = max(float(eta_temp) * 0.05, 1e-8)

        return ImpactParameters(
            last_price=last_price,
            bid=bid,
            ask=ask,
            spread=spread,
            sigma_daily=sigma_daily,
            sigma_annual=sigma_annual,
            eta_temp=float(eta_temp),
            gamma_perm=float(gamma_perm),
            adv_shares=float(adv_shares) if adv_shares is not None else None,
            source="manual_or_snapshot",
        )

    # ------------------------------------------------------------------
    # Main trajectory computation
    # ------------------------------------------------------------------
    def almgren_chriss_trajectory(
        self,
        *,
        security: str,
        total_shares: float,
        horizon_minutes: float,
        params: ImpactParameters,
        risk_aversion: float = 1e-6,
        dt_minutes: float = 1.0,
    ) -> ExecutionTrajectoryResult:
        X = float(total_shares)
        T_min = float(horizon_minutes)
        dt_min = float(dt_minutes)
        lam = float(risk_aversion)

        if X <= 0:
            raise ValueError("total_shares must be positive")
        if T_min <= 0:
            raise ValueError("horizon_minutes must be positive")
        if dt_min <= 0 or dt_min > T_min:
            raise ValueError("dt_minutes must be positive and no larger than horizon_minutes")

        n_steps = max(int(round(T_min / dt_min)), 1)
        T_days = T_min / self.MINUTES_PER_TRADING_DAY
        dt_days = dt_min / self.MINUTES_PER_TRADING_DAY

        sigma = float(params.sigma_daily)
        eta = max(float(params.eta_temp), 1e-12)
        gamma = max(float(params.gamma_perm), 0.0)

        # Standard AC urgency parameter:
        # kappa = sqrt(lambda * sigma^2 / eta)
        # in day^-1/2-like units after our normalization.
        raw = lam * sigma * sigma / eta
        kappa = float(math.sqrt(max(raw, 0.0)))

        times_min = np.linspace(0.0, T_min, n_steps + 1)
        times_days = times_min / self.MINUTES_PER_TRADING_DAY

        if kappa <= 1e-12 or T_days <= 1e-12:
            inventory = X * (1.0 - times_min / T_min)
        else:
            denom = math.sinh(kappa * T_days)
            inventory = np.array(
                [X * math.sinh(kappa * max(T_days - t, 0.0)) / denom for t in times_days],
                dtype=float,
            )

        trades = -(np.diff(inventory))
        trade_rates = trades / dt_days if dt_days > 0 else np.full_like(trades, np.nan)

        schedule = pd.DataFrame(
            {
                "step": np.arange(n_steps + 1, dtype=int),
                "time_minutes": times_min,
                "time_days": times_days,
                "inventory": inventory,
            }
        )
        child = pd.DataFrame(
            {
                "step": np.arange(1, n_steps + 1, dtype=int),
                "time_minutes": times_min[1:],
                "time_days": times_days[1:],
                "child_trade": trades,
                "trade_rate_shares_per_day": trade_rates,
            }
        )
        schedule = schedule.merge(child, on=["step", "time_minutes", "time_days"], how="left")

        expected_cost = self._expected_cost_ac(
            inventory=inventory,
            trades=trades,
            dt_days=dt_days,
            eta=eta,
            gamma=gamma,
        )
        variance_cost = self._variance_cost_ac(
            inventory=inventory,
            dt_days=dt_days,
            sigma=sigma,
        )
        objective = float(expected_cost + lam * variance_cost)

        diagnostics = {
            "n_steps": int(n_steps),
            "T_days": float(T_days),
            "dt_days": float(dt_days),
            "last_price": float(params.last_price),
            "sigma_daily": float(params.sigma_daily),
            "sigma_annual": float(params.sigma_annual),
            "eta_temp": float(params.eta_temp),
            "gamma_perm": float(params.gamma_perm),
            "spread": float(params.spread) if params.spread is not None else None,
            "adv_shares": float(params.adv_shares) if params.adv_shares is not None else None,
        }

        return ExecutionTrajectoryResult(
            security=security,
            model="almgren_chriss",
            total_shares=X,
            horizon_minutes=T_min,
            dt_minutes=dt_min,
            risk_aversion=lam,
            kappa=kappa,
            expected_cost=float(expected_cost),
            variance_cost=float(variance_cost),
            objective=float(objective),
            diagnostics=diagnostics,
            schedule=schedule,
        )

    def trajectory_from_live_snapshot(
        self,
        *,
        security: str,
        total_shares: float,
        horizon_minutes: float,
        snapshot: Dict[str, Any],
        risk_aversion: float = 1e-6,
        dt_minutes: float = 1.0,
        sigma_daily: Optional[float] = None,
        sigma_annual: Optional[float] = None,
        adv_shares: Optional[float] = None,
    ) -> ExecutionTrajectoryResult:
        last_price = self._extract_snapshot_field(snapshot, ["PX_LAST", "px_last", "last_price", "price"])
        bid = self._extract_snapshot_field(snapshot, ["BID", "bid"])
        ask = self._extract_snapshot_field(snapshot, ["ASK", "ask"])
        volume = self._extract_snapshot_field(snapshot, ["VOLUME", "volume"])

        params = self.infer_impact_parameters(
            security=security,
            last_price=float(last_price),
            bid=bid,
            ask=ask,
            sigma_daily=sigma_daily,
            sigma_annual=sigma_annual,
            adv_shares=adv_shares if adv_shares is not None else volume,
        )
        return self.almgren_chriss_trajectory(
            security=security,
            total_shares=total_shares,
            horizon_minutes=horizon_minutes,
            params=params,
            risk_aversion=risk_aversion,
            dt_minutes=dt_minutes,
        )

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def persist_trajectory(
        self,
        result: ExecutionTrajectoryResult,
        *,
        table_name: str = "execution_trajectory_runs",
        schedule_table_name: str = "execution_trajectory_schedule",
        replace: bool = False,
    ) -> Dict[str, Any]:
        self.market_db_path.parent.mkdir(parents=True, exist_ok=True)

        run_payload = {
            "security": result.security,
            "model": result.model,
            "total_shares": result.total_shares,
            "horizon_minutes": result.horizon_minutes,
            "dt_minutes": result.dt_minutes,
            "risk_aversion": result.risk_aversion,
            "kappa": result.kappa,
            "expected_cost": result.expected_cost,
            "variance_cost": result.variance_cost,
            "objective": result.objective,
            "diagnostics_json": json.dumps(result.diagnostics, default=str),
        }
        run_df = pd.DataFrame([run_payload])

        schedule = result.schedule.copy()
        schedule["security"] = result.security
        schedule["model"] = result.model
        schedule["run_objective"] = result.objective

        conn = sqlite3.connect(str(self.market_db_path))
        try:
            run_df.to_sql(table_name, conn, index=False, if_exists="replace" if replace else "append")
            schedule.to_sql(schedule_table_name, conn, index=False, if_exists="replace" if replace else "append")
        finally:
            conn.close()

        return {
            "db_path": str(self.market_db_path),
            "run_table": table_name,
            "schedule_table": schedule_table_name,
            "run_rows_written": 1,
            "schedule_rows_written": int(len(schedule)),
            "replace": bool(replace),
        }

    def save_json_artifact(self, result: ExecutionTrajectoryResult, path: str | Path) -> Dict[str, Any]:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result.as_dict(), indent=2, default=str), encoding="utf-8")
        return {"path": str(path), "bytes": path.stat().st_size}

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    @staticmethod
    def _expected_cost_ac(
        *,
        inventory: np.ndarray,
        trades: np.ndarray,
        dt_days: float,
        eta: float,
        gamma: float,
    ) -> float:
        # Simplified AC expected implementation shortfall approximation:
        # temporary impact: eta * sum(v_i^2) * dt
        # permanent impact: 0.5 * gamma * X^2
        if len(trades) == 0:
            return 0.0
        rates = trades / max(dt_days, 1e-12)
        temp = float(eta * np.sum((rates ** 2) * dt_days))
        perm = float(0.5 * gamma * (inventory[0] ** 2))
        return temp + perm

    @staticmethod
    def _variance_cost_ac(
        *,
        inventory: np.ndarray,
        dt_days: float,
        sigma: float,
    ) -> float:
        if len(inventory) <= 1:
            return 0.0
        # Discrete proxy: sigma^2 * sum(X_i^2 * dt)
        return float((sigma ** 2) * np.sum((inventory[:-1] ** 2) * dt_days))

    @staticmethod
    def _extract_snapshot_field(snapshot: Dict[str, Any], candidates: List[str]) -> Optional[float]:
        for key in candidates:
            if key in snapshot and snapshot[key] is not None:
                try:
                    return float(snapshot[key])
                except Exception:
                    continue
        return None


__all__ = [
    "ExecutionTrajectoryEngine",
    "ImpactParameters",
    "ExecutionTrajectoryResult",
]
