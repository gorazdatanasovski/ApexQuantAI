from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

import math

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SliceCalibration:
    expiry: str
    tau_years: float
    n_points: int
    atm_iv: float
    skew: float
    intercept: float
    r_squared: float
    method: str = "iv_vs_log_moneyness"

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScalingFit:
    n_slices: int
    intercept: float
    slope: float
    r_squared: float
    hurst: float
    convention: str = "|ATM_skew(T)| ~ c * T^(H - 1/2)"

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CalibrationResult:
    security: Optional[str]
    valuation_date: Optional[str]
    slices: List[SliceCalibration] = field(default_factory=list)
    scaling_fit: Optional[ScalingFit] = None
    diagnostics: Dict[str, Any] = field(default_factory=dict)
    surface_preview: Optional[Dict[str, Any]] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "security": self.security,
            "valuation_date": self.valuation_date,
            "slices": [s.as_dict() for s in self.slices],
            "scaling_fit": None if self.scaling_fit is None else self.scaling_fit.as_dict(),
            "diagnostics": self.diagnostics,
            "surface_preview": self.surface_preview,
        }

    def summary(self) -> str:
        lines = [
            f"Security: {self.security or 'N/A'}",
            f"Valuation date: {self.valuation_date or 'N/A'}",
            f"Calibrated slices: {len(self.slices)}",
        ]
        if self.scaling_fit is None:
            lines.append("Scaling fit: unavailable")
        else:
            lines.extend(
                [
                    "Scaling fit:",
                    f"  slope beta = {self.scaling_fit.slope:.6f}",
                    f"  implied H = {self.scaling_fit.hurst:.6f}",
                    f"  R^2 = {self.scaling_fit.r_squared:.6f}",
                    f"  slices used = {self.scaling_fit.n_slices}",
                ]
            )
        return "\n".join(lines)


class CalibrationEngine:
    """
    Calibration layer for options-surface research.

    This module is deliberately adapter-neutral:
    - it calibrates from a supplied options surface DataFrame
    - it can later be wired to Bloomberg option-chain retrieval without rewriting the math

    Expected minimum columns in the surface frame:
    - expiry
    - strike
    - implied_vol

    Recommended additional columns:
    - spot or forward
    - valuation_date
    - option_type
    - delta
    - bid_iv / ask_iv
    """

    def __init__(self, maturity_day_count: float = 365.0):
        self.maturity_day_count = float(maturity_day_count)

    def calibrate_atm_skew_scaling(
        self,
        surface: pd.DataFrame,
        *,
        security: Optional[str] = None,
        valuation_date: Optional[str] = None,
        spot: Optional[float] = None,
        forward_col_preference: Sequence[str] = ("forward", "fwd", "underlier_forward", "F"),
        spot_col_preference: Sequence[str] = ("spot", "underlier_spot", "underlying_price", "S"),
        expiry_col_preference: Sequence[str] = ("expiry", "expiration", "maturity", "expiry_date"),
        strike_col_preference: Sequence[str] = ("strike", "K"),
        iv_col_preference: Sequence[str] = ("implied_vol", "iv", "mid_iv", "mark_iv", "vol"),
        valuation_col_preference: Sequence[str] = ("valuation_date", "as_of", "date"),
        option_type_col_preference: Sequence[str] = ("option_type", "cp", "put_call", "type"),
        atm_log_moneyness_band: float = 0.08,
        min_points_per_slice: int = 5,
        min_slices_for_scaling: int = 3,
        use_puts_only: bool = False,
    ) -> CalibrationResult:
        if surface is None or len(surface) == 0:
            raise ValueError("surface must contain at least one option row")

        df = surface.copy()
        cols = {c.lower(): c for c in df.columns}

        expiry_col = self._pick_column(cols, expiry_col_preference, required=True)
        strike_col = self._pick_column(cols, strike_col_preference, required=True)
        iv_col = self._pick_column(cols, iv_col_preference, required=True)
        valuation_col = self._pick_column(cols, valuation_col_preference, required=False)
        option_type_col = self._pick_column(cols, option_type_col_preference, required=False)
        forward_col = self._pick_column(cols, forward_col_preference, required=False)
        spot_col = self._pick_column(cols, spot_col_preference, required=False)

        if valuation_date is None and valuation_col is not None:
            inferred = pd.to_datetime(df[valuation_col], errors="coerce").dropna()
            if not inferred.empty:
                valuation_date = inferred.iloc[0].date().isoformat()
        if valuation_date is None:
            valuation_date = date.today().isoformat()

        df[expiry_col] = pd.to_datetime(df[expiry_col], errors="coerce")
        df[strike_col] = pd.to_numeric(df[strike_col], errors="coerce")
        df[iv_col] = pd.to_numeric(df[iv_col], errors="coerce")
        if forward_col is not None:
            df[forward_col] = pd.to_numeric(df[forward_col], errors="coerce")
        if spot_col is not None:
            df[spot_col] = pd.to_numeric(df[spot_col], errors="coerce")

        df = df.dropna(subset=[expiry_col, strike_col, iv_col]).copy()
        if df.empty:
            raise ValueError("surface has no rows with valid expiry, strike, and implied_vol")

        if option_type_col is not None and use_puts_only:
            option_series = df[option_type_col].astype(str).str.upper().str[:1]
            df = df.loc[option_series.eq("P")].copy()
            if df.empty:
                raise ValueError("use_puts_only=True but no put options remain after filtering")

        val_ts = pd.Timestamp(valuation_date)
        df["tau_years"] = ((df[expiry_col] - val_ts).dt.days.astype(float) / self.maturity_day_count)
        df = df.loc[df["tau_years"] > 0].copy()
        if df.empty:
            raise ValueError("surface has no positive maturities after valuation-date filtering")

        if forward_col is None and spot_col is None and spot is None:
            raise ValueError(
                "surface needs either a forward column, a spot column, or an explicit spot argument"
            )

        df["_base"] = np.nan
        if forward_col is not None:
            df["_base"] = df[forward_col]
        if spot_col is not None:
            df["_base"] = df["_base"].where(df["_base"].notna(), df[spot_col])
        if spot is not None:
            df["_base"] = df["_base"].fillna(float(spot))

        df = df.loc[df["_base"].notna() & (df["_base"] > 0)].copy()
        if df.empty:
            raise ValueError("surface has no valid forward/spot base for moneyness computation")

        df["log_moneyness"] = np.log(df[strike_col] / df["_base"])
        df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=["log_moneyness", iv_col]).copy()

        slices: List[SliceCalibration] = []
        diagnostics: Dict[str, Any] = {
            "rows_in": int(len(surface)),
            "rows_used": int(len(df)),
            "atm_log_moneyness_band": float(atm_log_moneyness_band),
            "min_points_per_slice": int(min_points_per_slice),
        }

        for expiry, g in df.groupby(expiry_col):
            fit = self._fit_expiry_slice(
                g,
                expiry=expiry,
                iv_col=iv_col,
                atm_log_moneyness_band=float(atm_log_moneyness_band),
                min_points=max(3, int(min_points_per_slice)),
            )
            if fit is not None:
                slices.append(fit)

        slices = sorted(slices, key=lambda x: x.tau_years)
        scaling_fit = None
        if len(slices) >= max(2, int(min_slices_for_scaling)):
            scaling_fit = self._fit_scaling_law(slices)

        preview_cols = [c for c in [expiry_col, strike_col, iv_col, "tau_years", "log_moneyness"] if c in df.columns]
        preview = df[preview_cols].head(10).to_dict(orient="records")

        return CalibrationResult(
            security=security,
            valuation_date=valuation_date,
            slices=slices,
            scaling_fit=scaling_fit,
            diagnostics=diagnostics,
            surface_preview={"rows": preview},
        )

    def summarize_scaling_result(self, result: CalibrationResult) -> Dict[str, Any]:
        payload = result.as_dict()
        scaling = payload.get("scaling_fit")
        if scaling is None:
            return {
                "status": "insufficient_slices",
                "n_slices": len(result.slices),
                "message": "Not enough expiry slices to fit ATM-skew scaling.",
            }
        return {
            "status": "ok",
            "security": result.security,
            "valuation_date": result.valuation_date,
            "n_slices": scaling["n_slices"],
            "beta": scaling["slope"],
            "hurst": scaling["hurst"],
            "r_squared": scaling["r_squared"],
            "convention": scaling["convention"],
        }

    def calibrate_from_csv(
        self,
        csv_path: str | Path,
        **kwargs: Any,
    ) -> CalibrationResult:
        frame = pd.read_csv(csv_path)
        return self.calibrate_atm_skew_scaling(frame, **kwargs)

    def _fit_expiry_slice(
        self,
        g: pd.DataFrame,
        *,
        expiry: pd.Timestamp,
        iv_col: str,
        atm_log_moneyness_band: float,
        min_points: int,
    ) -> Optional[SliceCalibration]:
        tau = float(g["tau_years"].iloc[0])
        band = g.loc[g["log_moneyness"].abs() <= atm_log_moneyness_band].copy()
        if len(band) < min_points:
            band = g.loc[g["log_moneyness"].abs() <= max(atm_log_moneyness_band * 1.75, 0.12)].copy()
        if len(band) < min_points:
            return None

        x = band["log_moneyness"].to_numpy(dtype=float)
        y = band[iv_col].to_numpy(dtype=float)
        weights = 1.0 / (1.0 + (np.abs(x) / max(atm_log_moneyness_band, 1e-6)) ** 2)
        intercept, slope = self._weighted_linear_regression(x, y, weights)
        y_hat = intercept + slope * x
        ss_res = float(np.sum((y - y_hat) ** 2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 1.0
        atm_iv = float(intercept)

        return SliceCalibration(
            expiry=expiry.date().isoformat(),
            tau_years=tau,
            n_points=int(len(band)),
            atm_iv=atm_iv,
            skew=float(slope),
            intercept=float(intercept),
            r_squared=float(r2),
        )

    def _fit_scaling_law(self, slices: Sequence[SliceCalibration]) -> ScalingFit:
        tau = np.asarray([s.tau_years for s in slices], dtype=float)
        skew = np.asarray([s.skew for s in slices], dtype=float)
        mask = (tau > 0) & np.isfinite(tau) & np.isfinite(skew) & (np.abs(skew) > 0)
        tau = tau[mask]
        skew = skew[mask]
        if len(tau) < 2:
            raise ValueError("Need at least two valid slices for scaling calibration")

        x = np.log(tau)
        y = np.log(np.abs(skew))
        intercept, slope = self._weighted_linear_regression(x, y, np.ones_like(x))
        y_hat = intercept + slope * x
        ss_res = float(np.sum((y - y_hat) ** 2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 1.0

        # Convention used here:
        # |ATM skew(T)| ~ c * T^(H - 1/2)  => H = beta + 1/2
        hurst = float(slope + 0.5)

        return ScalingFit(
            n_slices=int(len(tau)),
            intercept=float(intercept),
            slope=float(slope),
            r_squared=float(r2),
            hurst=hurst,
        )

    @staticmethod
    def _weighted_linear_regression(
        x: np.ndarray,
        y: np.ndarray,
        w: np.ndarray,
    ) -> tuple[float, float]:
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        w = np.asarray(w, dtype=float)
        if len(x) != len(y) or len(x) != len(w):
            raise ValueError("x, y, and w must have the same length")
        if len(x) < 2:
            raise ValueError("Need at least two observations for regression")

        sw = np.sum(w)
        if sw <= 0:
            raise ValueError("Regression weights must sum to a positive number")
        x_bar = float(np.sum(w * x) / sw)
        y_bar = float(np.sum(w * y) / sw)
        sxx = float(np.sum(w * (x - x_bar) ** 2))
        if sxx <= 0:
            raise ValueError("Regressor has zero weighted variance")
        sxy = float(np.sum(w * (x - x_bar) * (y - y_bar)))
        slope = sxy / sxx
        intercept = y_bar - slope * x_bar
        return float(intercept), float(slope)

    @staticmethod
    def _pick_column(
        cols_lower_map: Mapping[str, str],
        candidates: Sequence[str],
        *,
        required: bool,
    ) -> Optional[str]:
        for candidate in candidates:
            key = candidate.lower()
            if key in cols_lower_map:
                return cols_lower_map[key]
        if required:
            raise ValueError(f"Missing required column. Tried candidates: {list(candidates)}")
        return None
