from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd


@dataclass(frozen=True)
class BQLQueryResult:
    query: str
    frame: pd.DataFrame
    metadata: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["frame_preview"] = self.frame.head(20).to_dict(orient="records")
        payload["shape"] = list(self.frame.shape)
        payload.pop("frame", None)
        return payload


class BQLUnavailableError(RuntimeError):
    pass


class BQLAdapter:
    """
    Thin adapter around Bloomberg's BQL Python object model.

    Design goals:
    - fail clearly if the BQL object model is not installed in the current environment
    - normalize common response shapes into pandas DataFrames
    - persist query outputs locally so QuantAI can learn from curated Bloomberg panels
    - stay separate from raw blpapi request/response plumbing

    Notes:
    - This adapter expects the Bloomberg BQL Python package to be available
      in the running environment (commonly within BQuant/Desktop-aligned setups).
    - Different environments may expose slightly different response objects, so
      normalization is defensive.
    """

    def __init__(self) -> None:
        try:
            import bql  # type: ignore
        except Exception as exc:
            raise BQLUnavailableError(
                "Bloomberg BQL Python object model is not available in this environment. "
                "Use BQuant/Desktop or an environment where the `bql` package is installed."
            ) from exc

        self._bql = bql
        self._service = self._build_service()

    def _build_service(self):
        # Bloomberg's BQL object model is commonly used via bql.Service()
        try:
            return self._bql.Service()
        except Exception as exc:
            raise BQLUnavailableError(
                "Imported `bql`, but failed to initialize bql.Service(). "
                "Check Bloomberg/BQuant/BQL environment setup."
            ) from exc

    def ping(self) -> Dict[str, Any]:
        return {
            "available": True,
            "service_type": type(self._service).__name__,
            "module": getattr(self._bql, "__name__", "bql"),
        }

    def execute(self, query: str) -> BQLQueryResult:
        query = str(query).strip()
        if not query:
            raise ValueError("BQL query must be non-empty")

        response = self._service.execute(query)
        frame = self._response_to_frame(response)
        metadata = {
            "rows": int(len(frame)),
            "columns": list(frame.columns),
        }
        return BQLQueryResult(query=query, frame=frame, metadata=metadata)

    def execute_many(self, queries: Iterable[str]) -> List[BQLQueryResult]:
        results: List[BQLQueryResult] = []
        for q in queries:
            results.append(self.execute(str(q)))
        return results

    def save_result_to_sqlite(
        self,
        result: BQLQueryResult,
        db_path: str | Path,
        table_name: str,
        replace: bool = True,
    ) -> Dict[str, Any]:
        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(db_path))
        try:
            if_exists = "replace" if replace else "append"
            result.frame.to_sql(table_name, conn, index=False, if_exists=if_exists)
        finally:
            conn.close()

        meta_path = db_path.with_suffix(db_path.suffix + f".{table_name}.meta.json")
        meta_path.write_text(json.dumps(result.as_dict(), indent=2, default=str), encoding="utf-8")

        return {
            "db_path": str(db_path),
            "table_name": table_name,
            "rows_written": int(len(result.frame)),
            "metadata_path": str(meta_path),
            "replace": bool(replace),
        }

    def save_result_to_parquet(
        self,
        result: BQLQueryResult,
        path: str | Path,
    ) -> Dict[str, Any]:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        result.frame.to_parquet(path, index=False)

        meta_path = path.with_suffix(path.suffix + ".meta.json")
        meta_path.write_text(json.dumps(result.as_dict(), indent=2, default=str), encoding="utf-8")

        return {
            "path": str(path),
            "rows_written": int(len(result.frame)),
            "metadata_path": str(meta_path),
        }

    def build_history_query(
        self,
        universe: str,
        fields: Iterable[str],
        date_range: str,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Build a simple BQL string query.

        Example output:
        get(px_last, volume) for(members('SPX Index')) with(dates=range(-1Y,0D))
        """
        fields_str = ", ".join(str(f).strip() for f in fields if str(f).strip())
        if not fields_str:
            raise ValueError("At least one field is required")

        prefs = preferences or {}
        pref_bits = [f"{k}={v}" for k, v in prefs.items()]
        pref_bits.append(f"dates={date_range}")
        pref_str = ", ".join(pref_bits)

        return f"get({fields_str}) for({universe}) with({pref_str})"

    def _response_to_frame(self, response: Any) -> pd.DataFrame:
        # Best-case path used by Bloomberg BQL object model examples
        if hasattr(self._bql, "combined_df"):
            try:
                frame = self._bql.combined_df(response)
                if isinstance(frame, pd.DataFrame):
                    return self._clean_frame(frame)
            except Exception:
                pass

        # Common shape: iterable of items each exposing .df() / .to_frame()
        if isinstance(response, (list, tuple)):
            pieces: List[pd.DataFrame] = []
            for item in response:
                part = self._item_to_frame(item)
                if part is not None and not part.empty:
                    pieces.append(part)
            if pieces:
                return self._clean_frame(pd.concat(pieces, ignore_index=True, sort=False))

        # Single object cases
        part = self._item_to_frame(response)
        if part is not None:
            return self._clean_frame(part)

        raise RuntimeError(
            "Unable to normalize BQL response into a DataFrame. "
            "Inspect the response type in your local environment."
        )

    def _item_to_frame(self, item: Any) -> Optional[pd.DataFrame]:
        if isinstance(item, pd.DataFrame):
            return item

        for attr in ("df", "to_frame", "dataframe"):
            candidate = getattr(item, attr, None)
            if callable(candidate):
                try:
                    out = candidate()
                    if isinstance(out, pd.DataFrame):
                        return out
                except Exception:
                    pass

        if hasattr(item, "__iter__") and not isinstance(item, (str, bytes, dict)):
            try:
                return pd.DataFrame(list(item))
            except Exception:
                pass

        if isinstance(item, dict):
            try:
                return pd.DataFrame([item])
            except Exception:
                pass

        return None

    def _clean_frame(self, frame: pd.DataFrame) -> pd.DataFrame:
        out = frame.copy()
        out.columns = [str(c) for c in out.columns]
        return out.reset_index(drop=True)
