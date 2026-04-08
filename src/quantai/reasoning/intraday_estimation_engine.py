from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Sequence

import numpy as np
import pandas as pd

try:
    from quantai.reasoning.market_data import PhysicalMarketGateway
except Exception:  # pragma: no cover
    PhysicalMarketGateway = None  # type: ignore


@dataclass(frozen=True)
class SeriesBuildResult:
    frame: pd.DataFrame
    metadata: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        payload = dict(self.metadata)
        payload["shape"] = list(self.frame.shape)
        payload["columns"] = list(self.frame.columns)
        payload["preview"] = self.frame.head(20).to_dict(orient="records")
        return payload


@dataclass(frozen=True)
class OUMLEEstimate:
    security: str
    value_column: str
    n_obs: int
    dt_days: float
    dt_years: float
    beta: float
    intercept: float
    theta: Optional[float]
    kappa_per_day: Optional[float]
    kappa_per_year: Optional[float]
    sigma: Optional[float]
    residual_std: Optional[float]
    r_squared: Optional[float]
    half_life_days: Optional[float]
    method: str = "exact_discrete_ou_mle_via_ar1"

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def summary(self) -> str:
        return (
            f"OU MLE | security={self.security} | n={self.n_obs} | "
            f"kappa/day={self._fmt(self.kappa_per_day)} | "
            f"kappa/year={self._fmt(self.kappa_per_year)} | "
            f"theta={self._fmt(self.theta)} | sigma={self._fmt(self.sigma)} | "
            f"beta={self._fmt(self.beta)} | half_life_days={self._fmt(self.half_life_days)}"
        )

    @staticmethod
    def _fmt(value: Optional[float]) -> str:
        if value is None:
            return "NA"
        return f"{float(value):.6g}"


@dataclass(frozen=True)
class JumpIntensityEstimate:
    security: str
    value_column: str
    n_returns: int
    dt_days: float
    threshold_abs_log_return: float
    threshold_method: str
    n_jumps: int
    lambda_per_day: float
    lambda_per_year: float
    jump_mean: Optional[float]
    jump_std: Optional[float]
    positive_jump_probability: Optional[float]
    max_abs_jump: Optional[float]

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def summary(self) -> str:
        return (
            f"Jump intensity | security={self.security} | n_jumps={self.n_jumps} | "
            f"lambda/day={self.lambda_per_day:.6g} | lambda/year={self.lambda_per_year:.6g} | "
            f"threshold={self.threshold_abs_log_return:.6g}"
        )


@dataclass(frozen=True)
class IntradayCalibrationBundle:
    series: Dict[str, Any]
    ou: Optional[Dict[str, Any]]
    jump: Optional[Dict[str, Any]]

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


class IntradayEstimationEngine:
    """
    Live/intraday estimation layer for QuantAI.

    Main capabilities:
    - normalize intraday bar frames
    - align two intraday series into a spread panel
    - estimate OU parameters by exact discrete-time MLE via AR(1) mapping
    - estimate jump intensity from intraday log-return spikes
    - persist results for downstream theorem / calibration workflows
    """

    TRADING_DAYS_PER_YEAR = 252.0
    MINUTES_PER_TRADING_DAY = 390.0

    def __init__(self, market_db_path: str | Path = "data/market_history.sqlite") -> None:
        self.market_db_path = Path(market_db_path)

    def fetch_intraday_bars(
        self,
        security: str,
        *,
        start_datetime: Any = None,
        end_datetime: Any = None,
        event_type: str = "TRADE",
        interval_minutes: int = 1,
    ) -> SeriesBuildResult:
        if PhysicalMarketGateway is None:
            raise RuntimeError("PhysicalMarketGateway is not importable in this environment.")

        with PhysicalMarketGateway() as bbg:
            intraday = getattr(bbg, "intraday_bars", None)
            if not callable(intraday):
                raise RuntimeError(
                    "PhysicalMarketGateway does not expose intraday_bars(). "
                    "Add that method or pass a DataFrame directly to IntradayEstimationEngine."
                )

            result = intraday(
                security=security,
                event_type=event_type,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                interval=interval_minutes,
            )

        frame = result.frame if hasattr(result, "frame") else pd.DataFrame(result)
        normalized = self.normalize_intraday_frame(frame, security=security)
        meta = {
            "security": security,
            "source": "bloomberg_intraday_bars",
            "event_type": event_type,
            "interval_minutes": int(interval_minutes),
            "start_datetime": str(start_datetime) if start_datetime is not None else None,
            "end_datetime": str(end_datetime) if end_datetime is not None else None,
        }
        return SeriesBuildResult(frame=normalized, metadata=meta)

    def normalize_intraday_frame(
        self,
        frame: pd.DataFrame,
        *,
        security: str = "UNKNOWN",
    ) -> pd.DataFrame:
        if frame is None or len(frame) == 0:
            raise ValueError("intraday frame is empty")

        out = frame.copy()
        out.columns = [str(c) for c in out.columns]

        time_col = self._choose_first_existing(
            out.columns,
            ["time", "datetime", "timestamp", "dateTime", "bar_time"],
        )
        if time_col is None:
            raise ValueError(f"Could not identify a time column in frame columns={list(out.columns)}")

        value_col = self._choose_first_existing(
            out.columns,
            ["close", "PX_LAST", "last_price", "price", "value", "mid"],
        )
        if value_col is None:
            raise ValueError(f"Could not identify a value column in frame columns={list(out.columns)}")

        rename_map = {time_col: "time"}
        if value_col != "close":
            rename_map[value_col] = "close"

        for src, dst in [
            ("open", "open"),
            ("high", "high"),
            ("low", "low"),
            ("volume", "volume"),
            ("numEvents", "num_events"),
            ("numberOfEvents", "num_events"),
        ]:
            if src in out.columns and src != dst:
                rename_map[src] = dst

        out = out.rename(columns=rename_map)
        out["time"] = pd.to_datetime(out["time"], errors="coerce")
        out = out.dropna(subset=["time"]).sort_values("time").drop_duplicates(subset=["time"]).reset_index(drop=True)

        for col in ["close", "open", "high", "low", "volume"]:
            if col in out.columns:
                out[col] = pd.to_numeric(out[col], errors="coerce")

        out = out.dropna(subset=["close"]).reset_index(drop=True)
        if out.empty:
            raise ValueError("No valid price observations remained after normalization")

        out["security"] = security
        out["log_price"] = np.log(out["close"].astype(float))
        out["log_return"] = out["log_price"].diff()
        out["return"] = out["close"].pct_change()
        return out

    def build_spread_series(
        self,
        left: pd.DataFrame,
        right: pd.DataFrame,
        *,
        left_name: str = "LEFT",
        right_name: str = "RIGHT",
        left_value_col: str = "close",
        right_value_col: str = "close",
        how: str = "inner",
    ) -> SeriesBuildResult:
        lf = self.normalize_intraday_frame(left, security=left_name)
        rf = self.normalize_intraday_frame(right, security=right_name)

        merged = lf[["time", left_value_col]].rename(columns={left_value_col: "left_value"}).merge(
            rf[["time", right_value_col]].rename(columns={right_value_col: "right_value"}),
            on="time",
            how=how,
        )
        if merged.empty:
            raise ValueError("spread merge produced no overlapping timestamps")

        merged["spread"] = merged["left_value"] - merged["right_value"]
        merged["log_ratio"] = np.log(merged["left_value"].astype(float)) - np.log(merged["right_value"].astype(float))
        merged["spread_return"] = merged["spread"].diff()
        merged = merged.sort_values("time").reset_index(drop=True)

        meta = {
            "security": f"{left_name}-{right_name}",
            "left_security": left_name,
            "right_security": right_name,
            "merge_how": how,
            "value_definition": "left_value - right_value",
        }
        return SeriesBuildResult(frame=merged, metadata=meta)

    def estimate_ou_mle(
        self,
        frame: pd.DataFrame,
        *,
        security: str = "UNKNOWN",
        value_column: str = "close",
        time_column: str = "time",
        trading_minutes_per_day: float = MINUTES_PER_TRADING_DAY,
        trading_days_per_year: float = TRADING_DAYS_PER_YEAR,
    ) -> OUMLEEstimate:
        if frame is None or len(frame) < 3:
            raise ValueError("At least 3 observations are required for OU estimation")
        if value_column not in frame.columns:
            raise ValueError(f"value_column={value_column!r} is not in frame")
        if time_column not in frame.columns:
            raise ValueError(f"time_column={time_column!r} is not in frame")

        df = frame[[time_column, value_column]].copy()
        df[time_column] = pd.to_datetime(df[time_column], errors="coerce")
        df[value_column] = pd.to_numeric(df[value_column], errors="coerce")
        df = df.dropna().sort_values(time_column).reset_index(drop=True)
        if len(df) < 3:
            raise ValueError("Too few clean observations after dropping NA rows")

        x = df[value_column].to_numpy(dtype=float)
        x_lag = x[:-1]
        x_next = x[1:]
        n = len(x_next)

        beta, intercept = self._ols_ar1(x_lag, x_next)
        residuals = x_next - (intercept + beta * x_lag)
        resid_std = float(np.std(residuals, ddof=1)) if n > 1 else None

        dt_days = self._infer_dt_days(df[time_column], trading_minutes_per_day=trading_minutes_per_day)
        dt_years = dt_days * trading_days_per_year / trading_days_per_year

        theta = None
        kappa_per_day = None
        kappa_per_year = None
        sigma = None
        half_life_days = None

        if 0.0 < beta < 1.0 and dt_days > 0:
            kappa_per_day = float(-math.log(beta) / dt_days)
            kappa_per_year = float(kappa_per_day * trading_days_per_year)
            if abs(1.0 - beta) > 1e-12:
                theta = float(intercept / (1.0 - beta))
            denom = 1.0 - beta * beta
            if resid_std is not None and kappa_per_day > 0 and denom > 1e-12:
                sigma2 = (resid_std ** 2) * (2.0 * kappa_per_day) / denom
                sigma = float(math.sqrt(max(sigma2, 0.0)))
            if kappa_per_day > 1e-12:
                half_life_days = float(math.log(2.0) / kappa_per_day)

        y_hat = intercept + beta * x_lag
        ss_res = float(np.sum((x_next - y_hat) ** 2))
        ss_tot = float(np.sum((x_next - np.mean(x_next)) ** 2))
        r_squared = None if ss_tot <= 0 else float(1.0 - ss_res / ss_tot)

        return OUMLEEstimate(
            security=security,
            value_column=value_column,
            n_obs=int(len(df)),
            dt_days=float(dt_days),
            dt_years=float(dt_years),
            beta=float(beta),
            intercept=float(intercept),
            theta=theta,
            kappa_per_day=kappa_per_day,
            kappa_per_year=kappa_per_year,
            sigma=sigma,
            residual_std=resid_std,
            r_squared=r_squared,
            half_life_days=half_life_days,
        )

    def estimate_spread_ou_mle(
        self,
        left: pd.DataFrame,
        right: pd.DataFrame,
        *,
        left_name: str = "LEFT",
        right_name: str = "RIGHT",
        use_log_ratio: bool = False,
    ) -> tuple[SeriesBuildResult, OUMLEEstimate]:
        spread = self.build_spread_series(left, right, left_name=left_name, right_name=right_name)
        value_col = "log_ratio" if use_log_ratio else "spread"
        est = self.estimate_ou_mle(
            spread.frame,
            security=f"{left_name}-{right_name}",
            value_column=value_col,
            time_column="time",
        )
        return spread, est

    def estimate_jump_intensity(
        self,
        frame: pd.DataFrame,
        *,
        security: str = "UNKNOWN",
        value_column: str = "close",
        time_column: str = "time",
        z_threshold: float = 5.0,
        threshold_method: str = "mad",
        trading_minutes_per_day: float = MINUTES_PER_TRADING_DAY,
        trading_days_per_year: float = TRADING_DAYS_PER_YEAR,
    ) -> JumpIntensityEstimate:
        if frame is None or len(frame) < 3:
            raise ValueError("At least 3 observations are required for jump estimation")
        if value_column not in frame.columns or time_column not in frame.columns:
            raise ValueError("Required columns are missing from frame")

        df = frame[[time_column, value_column]].copy()
        df[time_column] = pd.to_datetime(df[time_column], errors="coerce")
        df[value_column] = pd.to_numeric(df[value_column], errors="coerce")
        df = df.dropna().sort_values(time_column).reset_index(drop=True)
        if len(df) < 3:
            raise ValueError("Too few clean observations after dropping NA rows")

        log_price = np.log(df[value_column].astype(float).to_numpy())
        log_ret = np.diff(log_price)
        n_ret = len(log_ret)

        if threshold_method.lower() == "std":
            scale = float(np.std(log_ret, ddof=1))
        else:
            med = float(np.median(log_ret))
            mad = float(np.median(np.abs(log_ret - med)))
            scale = 1.4826 * mad

        if not np.isfinite(scale) or scale <= 0:
            scale = float(np.std(log_ret, ddof=1))

        threshold = float(z_threshold * max(scale, 1e-12))
        jump_mask = np.abs(log_ret) >= threshold
        jumps = log_ret[jump_mask]
        n_jumps = int(jump_mask.sum())

        dt_days = self._infer_dt_days(df[time_column], trading_minutes_per_day=trading_minutes_per_day)
        total_days = max(dt_days * n_ret, 1e-12)
        total_years = total_days / trading_days_per_year

        lambda_per_day = float(n_jumps / total_days)
        lambda_per_year = float(n_jumps / total_years) if total_years > 0 else float("nan")

        jump_mean = float(np.mean(jumps)) if n_jumps > 0 else None
        jump_std = float(np.std(jumps, ddof=1)) if n_jumps > 1 else (0.0 if n_jumps == 1 else None)
        positive_jump_probability = float(np.mean(jumps > 0)) if n_jumps > 0 else None
        max_abs_jump = float(np.max(np.abs(jumps))) if n_jumps > 0 else None

        return JumpIntensityEstimate(
            security=security,
            value_column=value_column,
            n_returns=int(n_ret),
            dt_days=float(dt_days),
            threshold_abs_log_return=threshold,
            threshold_method=threshold_method,
            n_jumps=n_jumps,
            lambda_per_day=lambda_per_day,
            lambda_per_year=lambda_per_year,
            jump_mean=jump_mean,
            jump_std=jump_std,
            positive_jump_probability=positive_jump_probability,
            max_abs_jump=max_abs_jump,
        )

    def calibrate_intraday_bundle(
        self,
        frame: pd.DataFrame,
        *,
        security: str = "UNKNOWN",
        value_column: str = "close",
        time_column: str = "time",
        include_jump: bool = True,
    ) -> IntradayCalibrationBundle:
        normalized = self.normalize_intraday_frame(frame, security=security)
        series_result = SeriesBuildResult(
            frame=normalized,
            metadata={"security": security, "source": "supplied_frame"},
        )
        ou = self.estimate_ou_mle(normalized, security=security, value_column=value_column, time_column=time_column)
        jump = None
        if include_jump:
            jump = self.estimate_jump_intensity(normalized, security=security, value_column=value_column, time_column=time_column)

        return IntradayCalibrationBundle(
            series=series_result.as_dict(),
            ou=ou.as_dict() if ou is not None else None,
            jump=jump.as_dict() if jump is not None else None,
        )

    def persist_estimate(
        self,
        payload: Dict[str, Any],
        *,
        table_name: str,
        replace: bool = False,
    ) -> Dict[str, Any]:
        self.market_db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.market_db_path))
        try:
            frame = pd.DataFrame([payload])
            frame.to_sql(table_name, conn, index=False, if_exists="replace" if replace else "append")
        finally:
            conn.close()
        return {
            "db_path": str(self.market_db_path),
            "table_name": table_name,
            "rows_written": 1,
            "replace": bool(replace),
        }

    def save_json_artifact(self, payload: Dict[str, Any], path: str | Path) -> Dict[str, Any]:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        return {"path": str(path), "bytes": path.stat().st_size}

    @staticmethod
    def _choose_first_existing(columns: Iterable[str], candidates: Sequence[str]) -> Optional[str]:
        col_set = {str(c) for c in columns}
        for cand in candidates:
            if cand in col_set:
                return cand
        return None

    @staticmethod
    def _ols_ar1(x_lag: np.ndarray, x_next: np.ndarray) -> tuple[float, float]:
        x_bar = float(np.mean(x_lag))
        y_bar = float(np.mean(x_next))
        denom = float(np.sum((x_lag - x_bar) ** 2))
        if denom <= 1e-18:
            raise ValueError("AR(1) regression denominator is zero; the series is effectively constant.")
        beta = float(np.sum((x_lag - x_bar) * (x_next - y_bar)) / denom)
        intercept = float(y_bar - beta * x_bar)
        return beta, intercept

    @classmethod
    def _infer_dt_days(cls, times: pd.Series, *, trading_minutes_per_day: float) -> float:
        diffs = times.diff().dropna()
        if diffs.empty:
            raise ValueError("Cannot infer time step from fewer than 2 timestamps")
        minutes = diffs.dt.total_seconds().to_numpy(dtype=float) / 60.0
        minutes = minutes[np.isfinite(minutes) & (minutes > 0)]
        if len(minutes) == 0:
            raise ValueError("No positive timestamp differences found")
        median_minutes = float(np.median(minutes))
        return median_minutes / float(trading_minutes_per_day)


__all__ = [
    "IntradayEstimationEngine",
    "SeriesBuildResult",
    "OUMLEEstimate",
    "JumpIntensityEstimate",
    "IntradayCalibrationBundle",
]
