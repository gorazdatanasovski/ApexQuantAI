from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
import sqlite3

import pandas as pd

try:
    import blpapi  # type: ignore
except ImportError:
    blpapi = None  # type: ignore


@dataclass(frozen=True)
class BloombergConfig:
    host: str = "localhost"
    port: int = 8194
    timeout_ms: int = 10000
    client_mode: str = "AUTO"  # AUTO, DAPI, SAPI


@dataclass
class BloombergResult:
    frame: pd.DataFrame
    errors: list[dict[str, Any]] = field(default_factory=list)
    request_id: str | None = None


class BloombergUnavailableError(RuntimeError):
    pass


class BloombergRequestError(RuntimeError):
    pass


class PhysicalMarketGateway:
    """
    Bloomberg Desktop/Server API adapter with request-scoped event queues.

    This implementation keeps Bloomberg separated from book-memory retrieval.
    It normalizes responses into pandas DataFrames and supports reference,
    historical, bulk, and intraday bar requests.
    """

    REF_DATA_SERVICE = "//blp/refdata"

    def __init__(self, config: BloombergConfig | None = None):
        self.config = config or BloombergConfig()
        self._session = None
        self._service_cache: dict[str, Any] = {}

    def _require_blpapi(self) -> Any:
        if blpapi is None:
            raise BloombergUnavailableError(
                "blpapi is not installed in this environment. Install Bloomberg's official Python API first."
            )
        return blpapi

    def start(self) -> None:
        if self._session is not None:
            return

        api = self._require_blpapi()
        options = api.SessionOptions()
        options.setServerHost(self.config.host)
        options.setServerPort(int(self.config.port))
        options.setConnectTimeout(int(self.config.timeout_ms))

        mode_name = str(self.config.client_mode).upper()
        if hasattr(options, "setClientMode") and hasattr(api.SessionOptions, mode_name):
            options.setClientMode(getattr(api.SessionOptions, mode_name))

        session = api.Session(options)
        if not session.start():
            raise BloombergUnavailableError("Failed to start Bloomberg session.")
        if not session.openService(self.REF_DATA_SERVICE):
            session.stop()
            raise BloombergUnavailableError(f"Failed to open Bloomberg service {self.REF_DATA_SERVICE}.")

        self._session = session
        self._service_cache[self.REF_DATA_SERVICE] = session.getService(self.REF_DATA_SERVICE)

    def stop(self) -> None:
        if self._session is not None:
            self._session.stop()
            self._session = None
            self._service_cache.clear()

    def __enter__(self) -> "PhysicalMarketGateway":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()

    def ping(self) -> dict[str, Any]:
        self.start()
        return {
            "host": self.config.host,
            "port": self.config.port,
            "client_mode": self.config.client_mode,
            "services": sorted(self._service_cache.keys()),
            "started": self._session is not None,
        }

    def _service(self, service_uri: str | None = None):
        self.start()
        assert self._session is not None
        service_uri = service_uri or self.REF_DATA_SERVICE
        if service_uri not in self._service_cache:
            if not self._session.openService(service_uri):
                raise BloombergUnavailableError(f"Failed to open Bloomberg service {service_uri}.")
            self._service_cache[service_uri] = self._session.getService(service_uri)
        return self._service_cache[service_uri]

    @staticmethod
    def _to_bbg_date(value: date | datetime | str) -> str:
        if isinstance(value, str):
            return value.replace("-", "")
        return value.strftime("%Y%m%d")

    def _send_request(self, request) -> tuple[list[Any], list[dict[str, Any]], str | None]:
        api = self._require_blpapi()
        assert self._session is not None

        queue = api.EventQueue()
        self._session.sendRequest(request, eventQueue=queue)
        messages: list[Any] = []
        errors: list[dict[str, Any]] = []
        request_id: str | None = None

        while True:
            event = queue.nextEvent(self.config.timeout_ms)
            event_type = event.eventType()

            if event_type == api.Event.TIMEOUT:
                raise TimeoutError("Bloomberg request timed out.")

            for message in event:
                if request_id is None:
                    try:
                        rid = message.getRequestId()
                        request_id = str(rid) if rid is not None else None
                    except Exception:
                        request_id = None

                if event_type == api.Event.REQUEST_STATUS:
                    errors.append({
                        "message_type": str(message.messageType()),
                        "message": message.toString(),
                    })
                    continue

                if message.hasElement("responseError"):
                    errors.append(self._extract_error_element(message.getElement("responseError")))

                if message.hasElement("securityData"):
                    sec_data = message.getElement("securityData")
                    if sec_data.isArray():
                        for i in range(sec_data.numValues()):
                            sec = sec_data.getValueAsElement(i)
                            self._collect_security_errors(sec, errors)
                    else:
                        self._collect_security_errors(sec_data, errors)

                messages.append(message)

            if event_type == api.Event.RESPONSE:
                break

        return messages, errors, request_id

    @staticmethod
    def _extract_error_element(element) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for name in ("source", "code", "category", "subcategory", "message"):
            if element.hasElement(name):
                try:
                    out[name] = element.getElement(name).getValue()
                except Exception:
                    out[name] = str(element.getElement(name))
        if not out:
            out["message"] = element.toString()
        return out

    @classmethod
    def _collect_security_errors(cls, sec_element, errors: list[dict[str, Any]]) -> None:
        sec_name = None
        if sec_element.hasElement("security"):
            sec_name = sec_element.getElementAsString("security")
        if sec_element.hasElement("securityError"):
            err = cls._extract_error_element(sec_element.getElement("securityError"))
            if sec_name is not None:
                err["security"] = sec_name
            errors.append(err)
        if sec_element.hasElement("fieldExceptions"):
            fex = sec_element.getElement("fieldExceptions")
            for i in range(fex.numValues()):
                ex = fex.getValueAsElement(i)
                err: dict[str, Any] = {"security": sec_name}
                if ex.hasElement("fieldId"):
                    err["fieldId"] = ex.getElementAsString("fieldId")
                if ex.hasElement("errorInfo"):
                    err.update(cls._extract_error_element(ex.getElement("errorInfo")))
                else:
                    err["message"] = ex.toString()
                errors.append(err)

    @staticmethod
    def _apply_overrides(request, overrides: Mapping[str, Any] | None) -> None:
        if not overrides:
            return
        if not request.asElement().hasElement("overrides"):
            return
        ovrds = request.getElement("overrides")
        for field_id, value in overrides.items():
            override = ovrds.appendElement()
            override.setElement("fieldId", str(field_id))
            override.setElement("value", str(value))

    @staticmethod
    def _set_if_present(request, name: str, value: Any) -> None:
        if value is None:
            return
        elem = request.asElement()
        if elem.hasElement(name):
            request.set(name, value)

    def bdp(
        self,
        securities: Sequence[str],
        fields: Sequence[str],
        overrides: Mapping[str, Any] | None = None,
    ) -> BloombergResult:
        request = self._service().createRequest("ReferenceDataRequest")
        for security in securities:
            request.getElement("securities").appendValue(str(security))
        for field in fields:
            request.getElement("fields").appendValue(str(field))
        self._apply_overrides(request, overrides)

        rows: list[dict[str, Any]] = []
        messages, errors, request_id = self._send_request(request)
        for msg in messages:
            if not msg.hasElement("securityData"):
                continue
            sec_array = msg.getElement("securityData")
            for i in range(sec_array.numValues()):
                sec = sec_array.getValueAsElement(i)
                row = {
                    "security": sec.getElementAsString("security") if sec.hasElement("security") else None,
                    "sequence_number": sec.getElementAsInteger("sequenceNumber") if sec.hasElement("sequenceNumber") else i,
                    "errors": None,
                }
                field_data = sec.getElement("fieldData") if sec.hasElement("fieldData") else None
                for field in fields:
                    if field_data is not None and field_data.hasElement(field):
                        row[str(field)] = field_data.getElement(field).getValue()
                    else:
                        row[str(field)] = None
                rows.append(row)
        return BloombergResult(frame=pd.DataFrame(rows), errors=errors, request_id=request_id)

    def bdh(
        self,
        securities: Sequence[str],
        fields: Sequence[str],
        start_date: date | datetime | str,
        end_date: date | datetime | str,
        periodicity: str = "DAILY",
        overrides: Mapping[str, Any] | None = None,
        periodicity_adjustment: str | None = "ACTUAL",
        non_trading_day_fill_option: str | None = None,
        non_trading_day_fill_method: str | None = None,
        max_data_points: int | None = None,
        return_relative_date: bool | None = None,
    ) -> BloombergResult:
        request = self._service().createRequest("HistoricalDataRequest")
        for security in securities:
            request.getElement("securities").appendValue(str(security))
        for field in fields:
            request.getElement("fields").appendValue(str(field))

        request.set("startDate", self._to_bbg_date(start_date))
        request.set("endDate", self._to_bbg_date(end_date))
        request.set("periodicitySelection", str(periodicity).upper())

        self._set_if_present(request, "periodicityAdjustment", None if periodicity_adjustment is None else str(periodicity_adjustment).upper())
        self._set_if_present(request, "nonTradingDayFillOption", None if non_trading_day_fill_option is None else str(non_trading_day_fill_option).upper())
        self._set_if_present(request, "nonTradingDayFillMethod", None if non_trading_day_fill_method is None else str(non_trading_day_fill_method).upper())
        self._set_if_present(request, "maxDataPoints", max_data_points)
        self._set_if_present(request, "returnRelativeDate", return_relative_date)
        self._apply_overrides(request, overrides)

        rows: list[dict[str, Any]] = []
        messages, errors, request_id = self._send_request(request)
        for msg in messages:
            if not msg.hasElement("securityData"):
                continue
            sec_data = msg.getElement("securityData")
            sec_name = sec_data.getElementAsString("security") if sec_data.hasElement("security") else None
            field_data = sec_data.getElement("fieldData") if sec_data.hasElement("fieldData") else None
            if field_data is None:
                continue
            for i in range(field_data.numValues()):
                obs = field_data.getValueAsElement(i)
                row = {
                    "security": sec_name,
                    "date": obs.getElementAsDatetime("date") if obs.hasElement("date") else None,
                }
                for field in fields:
                    row[str(field)] = obs.getElement(field).getValue() if obs.hasElement(field) else None
                rows.append(row)

        frame = pd.DataFrame(rows)
        if not frame.empty:
            frame = frame.sort_values(["security", "date"]).reset_index(drop=True)
        return BloombergResult(frame=frame, errors=errors, request_id=request_id)

    def bds(
        self,
        security: str,
        field: str,
        overrides: Mapping[str, Any] | None = None,
    ) -> BloombergResult:
        request = self._service().createRequest("ReferenceDataRequest")
        request.getElement("securities").appendValue(str(security))
        request.getElement("fields").appendValue(str(field))
        self._apply_overrides(request, overrides)

        rows: list[dict[str, Any]] = []
        messages, errors, request_id = self._send_request(request)
        for msg in messages:
            if not msg.hasElement("securityData"):
                continue
            sec_array = msg.getElement("securityData")
            for i in range(sec_array.numValues()):
                sec = sec_array.getValueAsElement(i)
                sec_name = sec.getElementAsString("security") if sec.hasElement("security") else security
                if not sec.hasElement("fieldData"):
                    continue
                field_data = sec.getElement("fieldData")
                if not field_data.hasElement(field):
                    continue
                bulk = field_data.getElement(field)
                if bulk.isArray():
                    for j in range(bulk.numValues()):
                        entry = bulk.getValueAsElement(j)
                        row = {"security": sec_name}
                        for k in range(entry.numElements()):
                            sub = entry.getElement(k)
                            row[str(sub.name())] = sub.getValue() if sub.numValues() > 0 else None
                        rows.append(row)
        return BloombergResult(frame=pd.DataFrame(rows), errors=errors, request_id=request_id)

    def intraday_bars(
        self,
        security: str,
        event_type: str,
        start_datetime: datetime | str,
        end_datetime: datetime | str,
        interval: int = 1,
    ) -> BloombergResult:
        request = self._service().createRequest("IntradayBarRequest")
        request.set("security", str(security))
        request.set("eventType", str(event_type).upper())
        request.set("interval", int(interval))
        request.set("startDateTime", start_datetime)
        request.set("endDateTime", end_datetime)

        rows: list[dict[str, Any]] = []
        messages, errors, request_id = self._send_request(request)
        for msg in messages:
            if not msg.hasElement("barData"):
                continue
            bar_data = msg.getElement("barData")
            if not bar_data.hasElement("barTickData"):
                continue
            ticks = bar_data.getElement("barTickData")
            for i in range(ticks.numValues()):
                bar = ticks.getValueAsElement(i)
                rows.append({
                    "security": security,
                    "time": bar.getElementAsDatetime("time") if bar.hasElement("time") else None,
                    "open": bar.getElementAsFloat("open") if bar.hasElement("open") else None,
                    "high": bar.getElementAsFloat("high") if bar.hasElement("high") else None,
                    "low": bar.getElementAsFloat("low") if bar.hasElement("low") else None,
                    "close": bar.getElementAsFloat("close") if bar.hasElement("close") else None,
                    "volume": bar.getElementAsInteger("volume") if bar.hasElement("volume") else None,
                    "num_events": bar.getElementAsInteger("numEvents") if bar.hasElement("numEvents") else None,
                    "value": bar.getElementAsFloat("value") if bar.hasElement("value") else None,
                })
        return BloombergResult(frame=pd.DataFrame(rows), errors=errors, request_id=request_id)

    def earliest_history_date(self, security: str, field: str = "PX_LAST") -> date | None:
        # Request a large enough window starting far back and return first available observation.
        result = self.bdh(
            securities=[security],
            fields=[field],
            start_date="19000101",
            end_date=datetime.utcnow().strftime("%Y%m%d"),
            periodicity="MONTHLY",
            max_data_points=5000,
        )
        frame = result.frame
        if frame.empty:
            return None
        first = frame["date"].dropna().min()
        if first is None or pd.isna(first):
            return None
        if hasattr(first, "date"):
            return first.date() if not isinstance(first, date) or isinstance(first, datetime) else first
        return pd.Timestamp(first).date()

    def backfill_daily_history_to_sqlite(
        self,
        securities: Sequence[str],
        fields: Sequence[str],
        db_path: str | Path,
        start_date: date | datetime | str,
        end_date: date | datetime | str | None = None,
        replace: bool = False,
        chunk_years: int = 10,
    ) -> dict[str, Any]:
        end_date = end_date or datetime.utcnow().strftime("%Y%m%d")
        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS bloomberg_daily_history (
                    security TEXT NOT NULL,
                    date TEXT NOT NULL,
                    field TEXT NOT NULL,
                    value REAL,
                    PRIMARY KEY (security, date, field)
                )
                """
            )
            if replace:
                marks = ",".join("?" for _ in securities)
                conn.execute(f"DELETE FROM bloomberg_daily_history WHERE security IN ({marks})", list(securities))
                conn.commit()

            start_ts = pd.Timestamp(self._to_bbg_date(start_date))
            end_ts = pd.Timestamp(self._to_bbg_date(end_date))
            total_rows = 0
            requests = 0

            current_start = start_ts
            while current_start <= end_ts:
                current_end = min(current_start + pd.DateOffset(years=chunk_years) - pd.DateOffset(days=1), end_ts)
                result = self.bdh(
                    securities=securities,
                    fields=fields,
                    start_date=current_start.strftime("%Y%m%d"),
                    end_date=current_end.strftime("%Y%m%d"),
                    periodicity="DAILY",
                )
                frame = result.frame.copy()
                requests += 1
                if not frame.empty:
                    frame["date"] = pd.to_datetime(frame["date"]).dt.strftime("%Y-%m-%d")
                    long = frame.melt(id_vars=["security", "date"], value_vars=list(fields), var_name="field", value_name="value")
                    rows = [tuple(x) for x in long[["security", "date", "field", "value"]].itertuples(index=False, name=None)]
                    conn.executemany(
                        "INSERT OR REPLACE INTO bloomberg_daily_history (security, date, field, value) VALUES (?, ?, ?, ?)",
                        rows,
                    )
                    conn.commit()
                    total_rows += len(rows)
                current_start = current_end + pd.DateOffset(days=1)

            return {"db_path": str(db_path), "rows_written": total_rows, "requests": requests}
        finally:
            conn.close()
