from __future__ import annotations

import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class FeaturePanelResult:
    frame: pd.DataFrame
    metadata: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "frame_shape": tuple(self.frame.shape),
            "columns": list(self.frame.columns),
            "metadata": dict(self.metadata),
        }


class MarketFeatureStore:
    """
    Feature layer over Bloomberg backfill data.

    Supported source layouts for bloomberg_daily_history:
    1. Wide: security, date, PX_LAST, OPEN, HIGH, LOW, VOLUME, ...
    2. Long: security, date, field, value

    The current Bloomberg backfill writes long form:
        security | date | field | value
    This class auto-pivots it into wide form before computing features.
    """

    SOURCE_TABLE = "bloomberg_daily_history"
    FEATURE_TABLE = "bloomberg_daily_features"
    _NUMERIC_BASE_FIELDS = ("PX_LAST", "OPEN", "HIGH", "LOW", "VOLUME")

    def __init__(self, db_path: str | Path = "data/market_history.sqlite"):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Market history database not found: {self.db_path}")
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "MarketFeatureStore":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def list_tables(self) -> list[str]:
        rows = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        return [str(r[0]) for r in rows]

    def list_securities(self) -> list[str]:
        q = f"SELECT DISTINCT security FROM {self.SOURCE_TABLE} ORDER BY security"
        df = pd.read_sql_query(q, self.conn)
        if "security" not in df.columns:
            return []
        return df["security"].astype(str).tolist()

    def load_daily_history(self, securities: Sequence[str] | None = None) -> pd.DataFrame:
        where = ""
        params: list[Any] = []
        if securities:
            placeholders = ",".join(["?"] * len(securities))
            where = f" WHERE security IN ({placeholders})"
            params.extend([str(x) for x in securities])

        q = f"SELECT * FROM {self.SOURCE_TABLE}{where} ORDER BY security, date"
        df = pd.read_sql_query(q, self.conn, params=params)
        if df.empty:
            return df

        df.columns = [str(c) for c in df.columns]
        if {"security", "date", "field", "value"}.issubset(df.columns):
            df = self._pivot_long_history(df)
        else:
            df = self._normalize_wide_history(df)

        if "PX_LAST" not in df.columns:
            raise ValueError(
                "PX_LAST column is required after history normalization. "
                f"Available columns: {sorted(df.columns.tolist())}"
            )
        return df.sort_values(["security", "date"]).reset_index(drop=True)

    def build_daily_feature_panel(
        self,
        securities: Sequence[str] | None = None,
        windows: Sequence[int] = (5, 21, 63),
    ) -> FeaturePanelResult:
        df = self.load_daily_history(securities=securities)
        if df.empty:
            return FeaturePanelResult(frame=df, metadata={"n_rows": 0, "securities": []})

        windows_clean = tuple(sorted({int(w) for w in windows if int(w) > 1}))
        panels: list[pd.DataFrame] = []
        for security, g in df.groupby("security", sort=False):
            panels.append(self._build_security_panel(g.copy(), windows_clean))

        panel = pd.concat(panels, ignore_index=True).sort_values(["security", "date"]).reset_index(drop=True)
        metadata = {
            "n_rows": int(len(panel)),
            "n_securities": int(panel["security"].nunique()),
            "securities": sorted(panel["security"].astype(str).unique().tolist()),
            "windows": list(windows_clean),
            "source_table": self.SOURCE_TABLE,
            "feature_table": self.FEATURE_TABLE,
        }
        return FeaturePanelResult(frame=panel, metadata=metadata)

    def build_and_persist_daily_feature_panel(
        self,
        securities: Sequence[str] | None = None,
        windows: Sequence[int] = (5, 21, 63),
        replace: bool = True,
    ) -> dict[str, Any]:
        result = self.build_daily_feature_panel(securities=securities, windows=windows)
        frame = result.frame.copy()
        if frame.empty:
            return {"table": self.FEATURE_TABLE, "rows_written": 0, "replace": bool(replace)}

        frame["date"] = pd.to_datetime(frame["date"]).dt.strftime("%Y-%m-%d")
        if_exists = "replace" if replace else "append"
        frame.to_sql(self.FEATURE_TABLE, self.conn, if_exists=if_exists, index=False)
        self.conn.commit()
        return {
            "table": self.FEATURE_TABLE,
            "rows_written": int(len(frame)),
            "replace": bool(replace),
            "n_securities": int(frame["security"].nunique()),
            "columns": list(frame.columns),
        }

    def summarize_security(self, security: str, windows: Sequence[int] = (5, 21, 63)) -> dict[str, Any]:
        result = self.build_daily_feature_panel(securities=[security], windows=windows)
        df = result.frame
        if df.empty:
            return {"security": security, "status": "no_data"}

        last = df.iloc[-1]
        out: dict[str, Any] = {
            "security": str(security),
            "status": "ok",
            "n_obs": int(len(df)),
            "start_date": str(pd.to_datetime(df["date"]).min().date()),
            "end_date": str(pd.to_datetime(df["date"]).max().date()),
            "last_price": _clean_scalar(last.get("PX_LAST")),
            "last_log_return": _clean_scalar(last.get("log_return")),
            "last_drawdown": _clean_scalar(last.get("drawdown")),
            "hurst_proxy": _clean_scalar(last.get("hurst_varscale_63")),
            "ou_beta_21": _clean_scalar(last.get("ou_beta_21")),
            "ou_kappa_21": _clean_scalar(last.get("ou_kappa_21")),
            "realized_vol_21": _clean_scalar(last.get("realized_vol_21")),
            "jump_share_21": _clean_scalar(last.get("jump_share_21")),
            "acf_abs_return_21": _clean_scalar(last.get("acf_abs_return_21")),
        }
        if "VOLUME" in df.columns:
            out["avg_volume_21"] = _clean_scalar(df["VOLUME"].tail(21).mean())
        return out

    def _pivot_long_history(self, df: pd.DataFrame) -> pd.DataFrame:
        work = df.copy()
        work["security"] = work["security"].astype(str)
        work["date"] = pd.to_datetime(work["date"])
        work["field"] = work["field"].astype(str)
        work["value"] = pd.to_numeric(work["value"], errors="coerce")
        wide = (
            work.pivot_table(
                index=["security", "date"],
                columns="field",
                values="value",
                aggfunc="last",
            )
            .reset_index()
        )
        wide.columns = [str(c) for c in wide.columns]
        return self._normalize_wide_history(wide)

    def _normalize_wide_history(self, df: pd.DataFrame) -> pd.DataFrame:
        work = df.copy()
        work.columns = [str(c) for c in work.columns]
        work["security"] = work["security"].astype(str)
        work["date"] = pd.to_datetime(work["date"])
        for col in self._NUMERIC_BASE_FIELDS:
            if col in work.columns:
                work[col] = pd.to_numeric(work[col], errors="coerce")
        return work

    def _build_security_panel(self, g: pd.DataFrame, windows: tuple[int, ...]) -> pd.DataFrame:
        g = g.sort_values("date").reset_index(drop=True)
        if "PX_LAST" not in g.columns:
            raise ValueError("PX_LAST column is required in normalized history")

        px = pd.to_numeric(g["PX_LAST"], errors="coerce")
        g["PX_LAST"] = px
        g["log_price"] = np.log(px.where(px > 0))
        g["log_return"] = g["log_price"].diff()
        g["return"] = g["log_return"]
        g["ret"] = g["log_return"]
        g["simple_return"] = px.pct_change()
        g["abs_return"] = g["log_return"].abs()
        g["sq_return"] = g["log_return"] ** 2
        g["neg_return"] = (-g["log_return"]).clip(lower=0)

        running_max = px.cummax()
        g["drawdown"] = px / running_max - 1.0

        if {"HIGH", "LOW"}.issubset(g.columns):
            hi = pd.to_numeric(g["HIGH"], errors="coerce")
            lo = pd.to_numeric(g["LOW"], errors="coerce")
            ratio = (hi / lo).replace([np.inf, -np.inf], np.nan)
            g["log_hl_range"] = np.log(ratio.where(ratio > 0))
            g["hl_range"] = (hi - lo) / px.replace(0, np.nan)
            g["range_rel"] = g["hl_range"]
            g["parkinson_var_daily"] = (g["log_hl_range"] ** 2) / (4.0 * math.log(2.0))
            g["parkinson_var"] = g["parkinson_var_daily"]
        else:
            g["log_hl_range"] = np.nan
            g["hl_range"] = np.nan
            g["range_rel"] = np.nan
            g["parkinson_var_daily"] = np.nan
            g["parkinson_var"] = np.nan

        for w in windows:
            g[f"realized_var_{w}"] = g["sq_return"].rolling(w).sum()
            g[f"rv_{w}"] = g[f"realized_var_{w}"]
            g[f"realized_vol_{w}"] = np.sqrt(g[f"realized_var_{w}"])
            g[f"downside_semivar_{w}"] = (g["neg_return"] ** 2).rolling(w).sum()
            g[f"max_drawdown_{w}"] = g["drawdown"].rolling(w).min()
            g[f"bipower_var_{w}"] = _bipower_variation(g["log_return"], w)
            g[f"jump_var_{w}"] = (g[f"realized_var_{w}"] - g[f"bipower_var_{w}"]).clip(lower=0)
            denom = g[f"realized_var_{w}"].replace(0, np.nan)
            g[f"jump_share_{w}"] = g[f"jump_var_{w}"] / denom
            g[f"autocov_return_{w}"] = _rolling_autocov(g["log_return"], w, lag=1)
            g[f"autocorr_return_{w}"] = _rolling_autocorr(g["log_return"], w, lag=1)
            g[f"acf_abs_return_{w}"] = _rolling_autocorr(g["abs_return"], w, lag=1)
            g[f"hurst_variance_scaling_{w}"] = _rolling_hurst_proxy(g["log_return"], w)
            g[f"hurst_varscale_{w}"] = g[f"hurst_variance_scaling_{w}"]
            ou = _rolling_ou_inputs(g["log_price"], w)
            g[f"ou_phi_{w}"] = ou["phi"]
            g[f"ou_speed_{w}"] = ou["speed"]
            g[f"ou_resid_std_{w}"] = ou["resid_std"]
            g[f"ou_beta_{w}"] = g[f"ou_phi_{w}"]
            g[f"ou_kappa_{w}"] = g[f"ou_speed_{w}"]
            g[f"parkinson_var_{w}"] = g["parkinson_var_daily"].rolling(w).sum()
            if "VOLUME" in g.columns:
                vol = pd.to_numeric(g["VOLUME"], errors="coerce")
                g[f"avg_volume_{w}"] = vol.rolling(w).mean()
                std = vol.rolling(w).std(ddof=0)
                g[f"volume_z_{w}"] = (vol - vol.rolling(w).mean()) / std.replace(0, np.nan)

        return g


def _clean_scalar(x: Any) -> Any:
    if x is None:
        return None
    if isinstance(x, (np.floating, float)):
        if np.isnan(x) or np.isinf(x):
            return None
        return float(x)
    if isinstance(x, (np.integer, int)):
        return int(x)
    return x


def _bipower_variation(r: pd.Series, window: int) -> pd.Series:
    abs_r = r.abs()
    prod = abs_r * abs_r.shift(1)
    mu1 = math.sqrt(2.0 / math.pi)
    return prod.rolling(window).sum() / (mu1 ** 2)


def _rolling_autocov(x: pd.Series, window: int, lag: int = 1) -> pd.Series:
    def func(arr: np.ndarray) -> float:
        if len(arr) <= lag:
            return np.nan
        a = arr[:-lag]
        b = arr[lag:]
        mask = np.isfinite(a) & np.isfinite(b)
        if mask.sum() < 3:
            return np.nan
        a = a[mask]
        b = b[mask]
        return float(np.mean((a - a.mean()) * (b - b.mean())))

    return x.rolling(window).apply(func, raw=True)


def _rolling_autocorr(x: pd.Series, window: int, lag: int = 1) -> pd.Series:
    def func(arr: np.ndarray) -> float:
        if len(arr) <= lag:
            return np.nan
        a = arr[:-lag]
        b = arr[lag:]
        mask = np.isfinite(a) & np.isfinite(b)
        if mask.sum() < 3:
            return np.nan
        a = a[mask]
        b = b[mask]
        denom = np.std(a) * np.std(b)
        if denom == 0 or not np.isfinite(denom):
            return np.nan
        return float(np.corrcoef(a, b)[0, 1])

    return x.rolling(window).apply(func, raw=True)


def _rolling_hurst_proxy(r: pd.Series, window: int) -> pd.Series:
    def func(arr: np.ndarray) -> float:
        arr = arr[np.isfinite(arr)]
        n = len(arr)
        if n < 16:
            return np.nan
        lags = [1, 2, 4, 8]
        vars_: list[float] = []
        valid_lags: list[int] = []
        for lag in lags:
            usable = n - (n % lag)
            if usable <= lag:
                continue
            agg = np.add.reduceat(arr[:usable], np.arange(0, usable, lag))
            if len(agg) < 2:
                continue
            v = np.var(agg, ddof=1)
            if v > 0 and np.isfinite(v):
                valid_lags.append(lag)
                vars_.append(v)
        if len(valid_lags) < 2:
            return np.nan
        slope = np.polyfit(np.log(valid_lags), np.log(vars_), 1)[0]
        return float(max(0.0, min(1.5, slope / 2.0)))

    return r.rolling(window).apply(func, raw=True)


def _rolling_ou_inputs(log_price: pd.Series, window: int) -> pd.DataFrame:
    phi_vals = np.full(len(log_price), np.nan)
    speed_vals = np.full(len(log_price), np.nan)
    resid_vals = np.full(len(log_price), np.nan)
    x = log_price.to_numpy(dtype=float)
    for i in range(window - 1, len(x)):
        seg = x[i - window + 1 : i + 1]
        if np.isnan(seg).any():
            continue
        y = seg[1:]
        xlag = seg[:-1]
        if len(xlag) < 3:
            continue
        X = np.column_stack([np.ones_like(xlag), xlag])
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        phi = beta[1]
        resid = y - X @ beta
        phi_vals[i] = phi
        if np.isfinite(phi) and phi > 0:
            speed_vals[i] = float(-math.log(phi))
        resid_vals[i] = float(np.std(resid, ddof=1)) if len(resid) > 1 else np.nan
    return pd.DataFrame({"phi": phi_vals, "speed": speed_vals, "resid_std": resid_vals})


__all__ = ["FeaturePanelResult", "MarketFeatureStore"]
