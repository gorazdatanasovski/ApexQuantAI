from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
import re
from typing import Any, Optional, Sequence

import numpy as np
import pandas as pd

from quantai.reasoning.calibration_engine import CalibrationEngine, CalibrationResult
from quantai.reasoning.market_data import PhysicalMarketGateway


@dataclass(frozen=True)
class SurfaceBuildResult:
    underlying: str
    valuation_date: str
    chain_field_used: str
    n_chain_rows: int
    n_chain_tickers: int
    n_snapshot_rows: int
    n_surface_rows: int
    surface: pd.DataFrame
    diagnostics: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["surface_preview"] = self.surface.head(25).to_dict(orient="records")
        payload["surface_columns"] = list(self.surface.columns)
        del payload["surface"]
        return payload


class OptionsSurfaceBuilder:
    """
    Build an options surface from Bloomberg option-chain data and calibrate ATM skew scaling.

    Superior behavior vs prior versions:
    - uses BDS one bulk field at a time, matching the current gateway
    - retains chain metadata and merges it with BDP quote snapshots
    - parses option metadata from Bloomberg-style option tickers when bulk metadata is sparse
    - returns rich diagnostics even when calibration cannot run
    """

    CHAIN_FIELDS: tuple[str, ...] = ("OPT_TICKERS", "OPT_CHAIN")
    OPTION_META_FIELDS: tuple[str, ...] = (
        "OPT_EXPIRE_DT",
        "OPT_STRIKE_PX",
        "OPT_PUT_CALL",
    )
    OPTION_QUOTE_FIELDS: tuple[str, ...] = (
        "IVOL_MID",
        "IVOL_BID",
        "IVOL_ASK",
        "PX_MID",
        "PX_BID",
        "PX_ASK",
        "PX_LAST",
        "VOLUME",
        "OPEN_INT",
    )
    TICKER_COLUMNS: tuple[str, ...] = (
        "Ticker",
        "ticker",
        "Security Description",
        "security description",
        "Security Identifier",
        "security",
    )
    EXPIRY_COLUMNS: tuple[str, ...] = (
        "OPT_EXPIRE_DT",
        "Expiration Date",
        "Expiry",
        "expiry",
        "EXPIRY",
    )
    STRIKE_COLUMNS: tuple[str, ...] = (
        "OPT_STRIKE_PX",
        "Strike Price",
        "Strike",
        "strike",
        "STRIKE",
    )
    TYPE_COLUMNS: tuple[str, ...] = (
        "OPT_PUT_CALL",
        "Put/Call",
        "Put Call",
        "put_call",
        "type",
        "Type",
    )

    OPTION_TICKER_RE = re.compile(
        r"(?P<expiry>\d{1,2}/\d{1,2}(?:/\d{2,4})?)\s+(?P<cp>[CP])\s*(?P<strike>\d+(?:\.\d+)?)\s+(?P<key>Equity|Index|Comdty|Curncy)\b",
        re.IGNORECASE,
    )

    def __init__(
        self,
        gateway: Optional[PhysicalMarketGateway] = None,
        calibration_engine: Optional[CalibrationEngine] = None,
    ) -> None:
        self.gateway = gateway or PhysicalMarketGateway()
        self.calibration_engine = calibration_engine or CalibrationEngine()

    def build_surface(
        self,
        underlying: str,
        *,
        valuation_date: str | date | datetime | None = None,
        option_type: Optional[str] = None,
        expiry_from: str | date | datetime | None = None,
        expiry_to: str | date | datetime | None = None,
        max_contracts: Optional[int] = None,
        chain_fields: Optional[Sequence[str]] = None,
    ) -> SurfaceBuildResult:
        valuation_ts = self._coerce_date(valuation_date) or pd.Timestamp.utcnow().normalize()
        expiry_from_ts = self._coerce_date(expiry_from)
        expiry_to_ts = self._coerce_date(expiry_to)

        spot = self._fetch_spot(underlying)
        chain_field_used, chain_frame, chain_debug = self._fetch_chain_frame(
            underlying=underlying,
            chain_fields=chain_fields or self.CHAIN_FIELDS,
        )
        chain_meta = self._extract_chain_metadata(chain_frame)
        if max_contracts is not None and not chain_meta.empty:
            chain_meta = chain_meta.head(int(max_contracts)).copy()
        tickers = chain_meta["option_ticker"].dropna().astype(str).tolist() if not chain_meta.empty else []
        if not tickers:
            raise ValueError(
                f"No option tickers could be extracted for {underlying}. Diagnostics: {chain_debug}"
            )

        raw = self._fetch_option_snapshots(tickers)
        surface = self._normalize_surface_frame(
            raw=raw,
            chain_meta=chain_meta,
            underlying=underlying,
            spot=spot,
            valuation_date=valuation_ts,
        )

        if option_type:
            ot = option_type.upper().strip()[:1]
            surface = surface[surface["option_type"].str.upper() == ot].copy()

        if expiry_from_ts is not None:
            surface = surface[surface["expiry"] >= expiry_from_ts].copy()
        if expiry_to_ts is not None:
            surface = surface[surface["expiry"] <= expiry_to_ts].copy()

        surface = surface.sort_values(["expiry", "strike", "option_ticker"]).reset_index(drop=True)

        diagnostics = {
            "spot": spot,
            "chain_frame_columns": list(chain_frame.columns),
            "chain_candidates": len(tickers),
            "rows_chain": int(len(chain_frame)),
            "rows_chain_meta": int(len(chain_meta)),
            "rows_raw": int(len(raw)),
            "rows_surface": int(len(surface)),
            "valuation_date": str(valuation_ts.date()),
            "expiry_min": str(surface["expiry"].min().date()) if not surface.empty else None,
            "expiry_max": str(surface["expiry"].max().date()) if not surface.empty else None,
            "option_types": sorted(surface["option_type"].dropna().astype(str).str.upper().unique().tolist()) if not surface.empty else [],
            "chain_debug": chain_debug,
            "chain_preview": chain_frame.head(10).to_dict(orient="records"),
            "raw_preview": raw.head(10).to_dict(orient="records"),
            "surface_nulls": {c: int(surface[c].isna().sum()) for c in surface.columns} if not surface.empty else {},
        }

        return SurfaceBuildResult(
            underlying=underlying,
            valuation_date=str(valuation_ts.date()),
            chain_field_used=chain_field_used,
            n_chain_rows=len(chain_frame),
            n_chain_tickers=len(tickers),
            n_snapshot_rows=len(raw),
            n_surface_rows=len(surface),
            surface=surface,
            diagnostics=diagnostics,
        )

    def build_and_calibrate_atm_skew(
        self,
        underlying: str,
        *,
        valuation_date: str | date | datetime | None = None,
        option_type: str = "C",
        expiry_from: str | date | datetime | None = None,
        expiry_to: str | date | datetime | None = None,
        max_contracts: Optional[int] = 400,
    ) -> tuple[SurfaceBuildResult, CalibrationResult]:
        surface_result = self.build_surface(
            underlying=underlying,
            valuation_date=valuation_date,
            option_type=option_type,
            expiry_from=expiry_from,
            expiry_to=expiry_to,
            max_contracts=max_contracts,
        )
        if surface_result.surface.empty:
            calibration = CalibrationResult(
                security=underlying,
                valuation_date=surface_result.valuation_date,
                slices=[],
                scaling_fit=None,
                diagnostics={
                    "status": "empty_surface",
                    "message": "Option chain and quote retrieval produced no calibratable option rows.",
                    "surface_build": surface_result.as_dict(),
                },
                surface_preview={"rows": []},
            )
            return surface_result, calibration

        calibration = self.calibration_engine.calibrate_atm_skew_scaling(
            surface_result.surface.rename(columns={"underlying": "security"}),
            security=underlying,
        )
        return surface_result, calibration

    def _fetch_spot(self, underlying: str) -> float:
        result = self.gateway.bdp([underlying], ["PX_LAST"])
        frame = getattr(result, "frame", result)
        if not isinstance(frame, pd.DataFrame) or frame.empty:
            raise ValueError(f"Could not fetch spot for {underlying}")
        if "PX_LAST" not in frame.columns:
            raise ValueError(f"PX_LAST not found in Bloomberg snapshot for {underlying}")
        return float(frame["PX_LAST"].iloc[0])

    def _fetch_chain_frame(
        self,
        *,
        underlying: str,
        chain_fields: Sequence[str],
    ) -> tuple[str, pd.DataFrame, dict[str, Any]]:
        errors: list[str] = []
        debug_rows: dict[str, Any] = {}
        for field in chain_fields:
            try:
                result = self.gateway.bds(underlying, field)
                frame = getattr(result, "frame", result)
                if not isinstance(frame, pd.DataFrame):
                    errors.append(f"{field}: result not DataFrame")
                    continue
                debug_rows[field] = {"rows": int(len(frame)), "columns": list(frame.columns)}
                if not frame.empty:
                    return field, frame.copy(), debug_rows
                errors.append(f"{field}: returned zero rows")
            except Exception as exc:
                errors.append(f"{field}: {exc}")
        raise ValueError(
            f"Unable to retrieve option chain for {underlying}. Tried {list(chain_fields)}. Errors: {' | '.join(errors)}"
        )

    def _fetch_option_snapshots(self, tickers: Sequence[str]) -> pd.DataFrame:
        fields = list(dict.fromkeys(self.OPTION_META_FIELDS + self.OPTION_QUOTE_FIELDS))
        result = self.gateway.bdp(list(tickers), fields)
        frame = getattr(result, "frame", result)
        if not isinstance(frame, pd.DataFrame):
            raise ValueError("Bloomberg option snapshot result is not a DataFrame")
        return frame.copy()

    def _extract_chain_metadata(self, frame: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(frame, pd.DataFrame) or frame.empty:
            return pd.DataFrame(columns=["option_ticker", "expiry", "strike", "option_type"])

        records: list[dict[str, Any]] = []
        for _, row in frame.iterrows():
            ticker = self._extract_ticker_from_row(row)
            if not ticker:
                continue

            expiry = self._extract_first_present(row, self.EXPIRY_COLUMNS)
            strike = self._extract_first_present(row, self.STRIKE_COLUMNS)
            option_type = self._extract_first_present(row, self.TYPE_COLUMNS)

            parsed = self._parse_option_ticker(ticker)
            expiry_ts = self._coerce_date(expiry) if expiry is not None and str(expiry).strip() != "" else parsed.get("expiry")
            strike_val = pd.to_numeric(pd.Series([strike]), errors="coerce").iloc[0] if strike is not None else parsed.get("strike")
            option_type_val = self._normalize_option_type(option_type if option_type is not None else parsed.get("option_type"))

            records.append(
                {
                    "option_ticker": str(ticker).strip(),
                    "expiry": expiry_ts,
                    "strike": None if pd.isna(strike_val) else float(strike_val),
                    "option_type": option_type_val,
                }
            )

        out = pd.DataFrame(records)
        if out.empty:
            return pd.DataFrame(columns=["option_ticker", "expiry", "strike", "option_type"])
        out = out.dropna(subset=["option_ticker"]).drop_duplicates(subset=["option_ticker"]).reset_index(drop=True)
        return out

    def _extract_ticker_from_row(self, row: pd.Series) -> Optional[str]:
        for name in self.TICKER_COLUMNS:
            if name in row.index:
                val = row.get(name)
                if isinstance(val, str) and self._looks_like_option_ticker(val):
                    return val.strip()
        for val in row.tolist():
            if isinstance(val, str) and self._looks_like_option_ticker(val):
                return val.strip()
        return None

    def _looks_like_option_ticker(self, text: str) -> bool:
        s = str(text).strip()
        if not s:
            return False
        return bool(self.OPTION_TICKER_RE.search(s))

    def _parse_option_ticker(self, ticker: str) -> dict[str, Any]:
        m = self.OPTION_TICKER_RE.search(str(ticker))
        if not m:
            return {"expiry": None, "strike": None, "option_type": None}
        expiry_raw = m.group("expiry")
        expiry_ts = pd.to_datetime(expiry_raw, errors="coerce")
        if pd.isna(expiry_ts):
            expiry_norm = None
        else:
            expiry_norm = pd.Timestamp(expiry_ts).normalize()
        strike = float(m.group("strike"))
        option_type = m.group("cp").upper()
        return {"expiry": expiry_norm, "strike": strike, "option_type": option_type}

    def _normalize_surface_frame(
        self,
        *,
        raw: pd.DataFrame,
        chain_meta: pd.DataFrame,
        underlying: str,
        spot: float,
        valuation_date: pd.Timestamp,
    ) -> pd.DataFrame:
        frame = raw.copy()
        if "security" in frame.columns:
            frame = frame.rename(columns={"security": "option_ticker"})
        elif "ticker" in frame.columns:
            frame = frame.rename(columns={"ticker": "option_ticker"})
        else:
            frame.insert(0, "option_ticker", [None] * len(frame))

        if not chain_meta.empty:
            frame = frame.merge(chain_meta, how="left", on="option_ticker", suffixes=("", "_chain"))

        frame["valuation_date"] = pd.Timestamp(valuation_date.date())
        frame["underlying"] = underlying
        frame["spot"] = float(spot)

        expiry_snapshot = self._coerce_series_date(self._pick_first_present(frame, ["OPT_EXPIRE_DT", "EXPIRY", "expiry"]))
        strike_snapshot = pd.to_numeric(self._pick_first_present(frame, ["OPT_STRIKE_PX", "STRIKE_PX", "strike"]), errors="coerce")
        type_snapshot = self._pick_first_present(frame, ["OPT_PUT_CALL", "PUT_CALL", "put_call", "option_type"])\
            .astype(str).map(self._normalize_option_type)

        if "expiry_chain" in frame.columns:
            expiry_chain = self._coerce_series_date(frame["expiry_chain"])
        else:
            expiry_chain = pd.Series(pd.NaT, index=frame.index, dtype="datetime64[ns]")
        if "strike_chain" in frame.columns:
            strike_chain = pd.to_numeric(frame["strike_chain"], errors="coerce")
        else:
            strike_chain = pd.Series(np.nan, index=frame.index, dtype="float64")
        if "option_type_chain" in frame.columns:
            type_chain = frame["option_type_chain"].astype(str).map(self._normalize_option_type)
        else:
            type_chain = pd.Series([None] * len(frame), index=frame.index, dtype="object")

        frame["expiry"] = expiry_snapshot.where(expiry_snapshot.notna(), expiry_chain)
        frame["strike"] = strike_snapshot.where(strike_snapshot.notna(), strike_chain)
        frame["option_type"] = type_snapshot.where(type_snapshot.notna() & (type_snapshot != "N"), type_chain)

        # Final fallback: parse directly from ticker string.
        parsed = frame["option_ticker"].astype(str).map(self._parse_option_ticker)
        parsed_df = pd.DataFrame(parsed.tolist(), index=frame.index)
        frame["expiry"] = frame["expiry"].where(frame["expiry"].notna(), self._coerce_series_date(parsed_df["expiry"]))
        frame["strike"] = frame["strike"].where(frame["strike"].notna(), pd.to_numeric(parsed_df["strike"], errors="coerce"))
        frame["option_type"] = frame["option_type"].where(frame["option_type"].notna(), parsed_df["option_type"])

        iv_mid = pd.to_numeric(self._pick_first_present(frame, ["IVOL_MID"]), errors="coerce")
        iv_bid = pd.to_numeric(self._pick_first_present(frame, ["IVOL_BID"]), errors="coerce")
        iv_ask = pd.to_numeric(self._pick_first_present(frame, ["IVOL_ASK"]), errors="coerce")
        px_mid = pd.to_numeric(self._pick_first_present(frame, ["PX_MID"]), errors="coerce")
        px_bid = pd.to_numeric(self._pick_first_present(frame, ["PX_BID"]), errors="coerce")
        px_ask = pd.to_numeric(self._pick_first_present(frame, ["PX_ASK"]), errors="coerce")
        px_last = pd.to_numeric(self._pick_first_present(frame, ["PX_LAST"]), errors="coerce")
        volume = pd.to_numeric(self._pick_first_present(frame, ["VOLUME"]), errors="coerce")
        open_int = pd.to_numeric(self._pick_first_present(frame, ["OPEN_INT"]), errors="coerce")

        implied = iv_mid.fillna((iv_bid + iv_ask) / 2.0)
        # Bloomberg may return vols in percent points; normalize if clearly too large.
        implied = implied.where((implied.isna()) | (implied <= 3.0), implied / 100.0)

        frame["implied_vol"] = implied
        frame["mid_price"] = px_mid.fillna((px_bid + px_ask) / 2.0).fillna(px_last)
        frame["volume"] = volume
        frame["open_interest"] = open_int
        frame["tau_years"] = ((frame["expiry"] - frame["valuation_date"]).dt.days.astype("float64") / 365.0)

        cols = [
            "valuation_date",
            "underlying",
            "option_ticker",
            "expiry",
            "tau_years",
            "option_type",
            "strike",
            "spot",
            "implied_vol",
            "mid_price",
            "volume",
            "open_interest",
        ]
        surface = frame[cols].copy()
        surface = surface.dropna(subset=["option_ticker", "expiry", "strike", "tau_years"]) 
        surface = surface[surface["tau_years"] > 0].copy()
        surface = surface.drop_duplicates(subset=["option_ticker"]).reset_index(drop=True)
        return surface

    @staticmethod
    def _extract_first_present(row: pd.Series, names: Sequence[str]) -> Any:
        for name in names:
            if name in row.index:
                val = row.get(name)
                if val is not None and str(val).strip() not in {"", "nan", "NaT", "None"}:
                    return val
        return None

    @staticmethod
    def _normalize_option_type(value: Any) -> Optional[str]:
        if value is None:
            return None
        s = str(value).strip().upper()
        if not s or s in {"NAN", "NONE", "NAT"}:
            return None
        if s.startswith("P"):
            return "P"
        if s.startswith("C"):
            return "C"
        return None

    @staticmethod
    def _pick_first_present(frame: pd.DataFrame, names: Sequence[str]) -> pd.Series:
        for name in names:
            if name in frame.columns:
                return frame[name]
        return pd.Series([None] * len(frame), index=frame.index, dtype="object")

    @staticmethod
    def _coerce_series_date(series: pd.Series) -> pd.Series:
        return pd.to_datetime(series, errors="coerce").dt.normalize()

    @staticmethod
    def _coerce_date(value: str | date | datetime | None) -> Optional[pd.Timestamp]:
        if value is None:
            return None
        if isinstance(value, pd.Timestamp):
            return value.normalize()
        if isinstance(value, datetime):
            return pd.Timestamp(value.date())
        if isinstance(value, date):
            return pd.Timestamp(value)
        out = pd.to_datetime(value, errors="coerce")
        if pd.isna(out):
            return None
        return pd.Timestamp(out).normalize()
