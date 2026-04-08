from __future__ import annotations

import inspect
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from quantai.reasoning.feature_store import MarketFeatureStore
from quantai.reasoning.market_data import PhysicalMarketGateway

try:
    from quantai.reasoning.bql_adapter import BQLAdapter, BQLUnavailableError
except Exception:  # pragma: no cover
    BQLAdapter = None  # type: ignore

    class BQLUnavailableError(RuntimeError):
        pass


try:
    from quantai.reasoning.options_surface_builder import OptionsSurfaceBuilder
except Exception:  # pragma: no cover
    OptionsSurfaceBuilder = None  # type: ignore


@dataclass(frozen=True)
class CapabilityReport:
    blpapi_available: bool
    bql_available: bool
    options_surface_available: bool
    market_db_path: str
    notes: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LearningRunResult:
    history_summary: Dict[str, Any]
    feature_summary: Optional[Dict[str, Any]]
    bql_summary: Optional[Dict[str, Any]]
    options_summary: Optional[Dict[str, Any]]
    capability_report: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BloombergLearningHub:
    """
    QuantAI Bloomberg orchestration layer.

    Design goals:
    - use the working blpapi path as the default production lane
    - use BQL only when it is truly available in the environment
    - build local history + feature panels that theorem/research layers can reuse
    - tolerate different versions of the user's PhysicalMarketGateway methods
    """

    def __init__(
        self,
        market_db_path: str | Path = "data/market_history.sqlite",
        work_dir: str | Path = "rag_ingest_state",
    ) -> None:
        self.market_db_path = Path(market_db_path)
        self.work_dir = Path(work_dir)
        self.gateway = PhysicalMarketGateway()
        self.feature_store = MarketFeatureStore(self.market_db_path)
        self._bql = None

    def capability_report(self) -> CapabilityReport:
        notes: List[str] = []

        blpapi_ok = False
        try:
            ping = self.gateway.ping()
            blpapi_ok = bool(ping.get("started"))
            if not blpapi_ok:
                notes.append("Physical Bloomberg session did not report started=True.")
        except Exception as exc:
            notes.append(f"blpapi unavailable: {exc}")

        bql_ok = False
        if BQLAdapter is None:
            notes.append("BQL adapter import unavailable in this environment.")
        else:
            try:
                self._bql = self._bql or BQLAdapter()
                bql_ok = True
            except Exception as exc:
                notes.append(f"BQL unavailable: {exc}")

        options_ok = OptionsSurfaceBuilder is not None
        if not options_ok:
            notes.append("OptionsSurfaceBuilder not importable.")

        return CapabilityReport(
            blpapi_available=blpapi_ok,
            bql_available=bql_ok,
            options_surface_available=options_ok,
            market_db_path=str(self.market_db_path),
            notes=notes,
        )

    def backfill_history(
        self,
        securities: Iterable[str],
        fields: Iterable[str],
        from_inception: bool = True,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        replace: bool = False,
    ) -> Dict[str, Any]:
        securities = [str(s).strip() for s in securities if str(s).strip()]
        fields = [str(f).strip() for f in fields if str(f).strip()]
        if not securities:
            raise ValueError("At least one security is required")
        if not fields:
            raise ValueError("At least one field is required")

        today = datetime.now().strftime("%Y%m%d")
        if end_date is None:
            end_date = today

        with self.gateway as bbg:
            backfill = getattr(bbg, "backfill_daily_history_to_sqlite", None)
            if backfill is None or not callable(backfill):
                raise RuntimeError("PhysicalMarketGateway does not expose backfill_daily_history_to_sqlite().")

            sig = inspect.signature(backfill)
            kwargs: Dict[str, Any] = {
                "securities": securities,
                "fields": fields,
                "db_path": self.market_db_path,
                "replace": replace,
            }

            # Make this robust to differing gateway signatures across earlier patches.
            if "start_date" in sig.parameters:
                if from_inception:
                    inferred_start = self._infer_inception_start(
                        bbg=bbg,
                        securities=securities,
                        primary_field=fields[0],
                    )
                    kwargs["start_date"] = inferred_start
                else:
                    if not start_date:
                        raise ValueError("start_date is required when from_inception=False")
                    kwargs["start_date"] = start_date

            if "end_date" in sig.parameters:
                kwargs["end_date"] = end_date

            if "from_inception" in sig.parameters:
                kwargs["from_inception"] = from_inception

            try:
                result = backfill(**kwargs)
            except TypeError:
                # Fallback: some older variants may not accept replace or db_path keywords the same way.
                fallback_kwargs = dict(kwargs)
                if "replace" in fallback_kwargs:
                    fallback_kwargs.pop("replace")
                result = backfill(**fallback_kwargs)

        return result

    def _infer_inception_start(
        self,
        bbg: PhysicalMarketGateway,
        securities: List[str],
        primary_field: str,
    ) -> str:
        """
        Infer a conservative earliest start date.

        If the gateway exposes earliest_history_date(), use it.
        Otherwise fall back to a very early date.
        """
        earliest_fn = getattr(bbg, "earliest_history_date", None)
        if callable(earliest_fn):
            dates: List[str] = []
            for security in securities:
                try:
                    value = earliest_fn(security=security, field=primary_field)
                    if value:
                        dates.append(str(value).replace("-", ""))
                except Exception:
                    continue
            if dates:
                return min(dates)
        return "19000101"

    def build_features(
        self,
        securities: Iterable[str],
        windows: Iterable[int] = (5, 21, 63),
    ) -> Dict[str, Any]:
        securities = [str(s).strip() for s in securities if str(s).strip()]
        return self.feature_store.build_and_persist_daily_feature_panel(
            securities=securities,
            windows=tuple(int(w) for w in windows),
        )

    def run_bql_query(
        self,
        query: str,
        save_table: Optional[str] = None,
    ) -> Dict[str, Any]:
        if BQLAdapter is None:
            raise BQLUnavailableError("BQL adapter cannot be imported in this environment.")
        self._bql = self._bql or BQLAdapter()
        result = self._bql.execute(query)
        payload = result.as_dict()
        if save_table:
            save_meta = self._bql.save_result_to_sqlite(
                result=result,
                db_path=self.market_db_path,
                table_name=save_table,
                replace=True,
            )
            payload["saved"] = save_meta
        return payload

    def build_options_surface(
        self,
        underlying: str,
        option_type: str = "P",
        max_contracts: int = 300,
    ) -> Dict[str, Any]:
        if OptionsSurfaceBuilder is None:
            raise RuntimeError("OptionsSurfaceBuilder is not available in this environment.")
        builder = OptionsSurfaceBuilder()
        surface_result = builder.build_surface(
            underlying=underlying,
            option_type=option_type,
            max_contracts=max_contracts,
        )
        return surface_result.as_dict()

    def bootstrap_learning_snapshot(
        self,
        securities: Iterable[str],
        history_fields: Iterable[str] = ("PX_LAST", "OPEN", "HIGH", "LOW", "VOLUME"),
        windows: Iterable[int] = (5, 21, 63),
        bql_queries: Optional[Dict[str, str]] = None,
        try_options_underlying: Optional[str] = None,
    ) -> LearningRunResult:
        securities = [str(s).strip() for s in securities if str(s).strip()]

        cap = self.capability_report()

        history_summary = self.backfill_history(
            securities=securities,
            fields=history_fields,
            from_inception=True,
            replace=False,
        )

        feature_summary = self.build_features(
            securities=securities,
            windows=windows,
        )

        bql_summary = None
        if bql_queries and cap.bql_available:
            bql_payload: Dict[str, Any] = {}
            for table_name, query in bql_queries.items():
                bql_payload[table_name] = self.run_bql_query(query=query, save_table=table_name)
            bql_summary = bql_payload
        elif bql_queries and not cap.bql_available:
            bql_summary = {
                "skipped": True,
                "reason": "BQL unavailable in this environment",
                "requested_tables": list(bql_queries.keys()),
            }

        options_summary = None
        if try_options_underlying:
            try:
                options_summary = self.build_options_surface(
                    underlying=try_options_underlying,
                    option_type="P",
                    max_contracts=300,
                )
            except Exception as exc:
                options_summary = {
                    "underlying": try_options_underlying,
                    "status": "failed",
                    "error": str(exc),
                }

        return LearningRunResult(
            history_summary=history_summary,
            feature_summary=feature_summary,
            bql_summary=bql_summary,
            options_summary=options_summary,
            capability_report=cap.as_dict(),
        )

    def save_learning_snapshot(
        self,
        result: LearningRunResult,
        path: str | Path,
    ) -> Dict[str, Any]:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result.as_dict(), indent=2, default=str), encoding="utf-8")
        return {"path": str(path), "bytes": path.stat().st_size}
