from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from quantai.reasoning.bloomberg_memory_ingestor import BloombergMemoryIngestor
from quantai.reasoning.feature_store import MarketFeatureStore
from quantai.reasoning.market_data import PhysicalMarketGateway
from quantai.reasoning.spy_volatility_universe import (
    SPY_VOLATILITY_CORE_SECURITIES,
    SPY_VOLATILITY_EXTENDED_SECURITIES,
)


@dataclass(frozen=True)
class SpyVolatilityCoverage:
    security: str
    history_rows: int
    feature_rows: int
    memory_rows: int

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def fully_covered(self) -> bool:
        return self.history_rows > 0 and self.feature_rows > 0 and self.memory_rows > 0


class SpyVolatilityBackfill:
    """
    One-command backfill for the canonical SPY/VIX research universe.

    Why this exists:
    - the universe scheduler is working
    - the missing piece is local empirical coverage for SPX/VIX-family instruments
    - this class backfills only the missing names by default, so repeated runs are cheap

    Coverage target for each symbol:
    - bloomberg_daily_history
    - bloomberg_daily_features
    - bloomberg_research_memory
    """

    DEFAULT_FIELDS = ["PX_LAST", "OPEN", "HIGH", "LOW", "VOLUME"]
    DEFAULT_WINDOWS = (5, 21, 63)

    def __init__(
        self,
        market_db_path: str | Path = "data/market_history.sqlite",
        snapshot_path: str | Path = "artifacts/bloomberg_learning_snapshot.json",
        memory_output_dir: str | Path = "artifacts/bloomberg_memory",
    ) -> None:
        self.market_db_path = Path(market_db_path)
        self.snapshot_path = Path(snapshot_path)
        self.memory_output_dir = Path(memory_output_dir)

    # ------------------------------------------------------------------
    # universe helpers
    # ------------------------------------------------------------------
    @staticmethod
    def universe(extended: bool = False) -> List[str]:
        return list(
            SPY_VOLATILITY_EXTENDED_SECURITIES
            if extended
            else SPY_VOLATILITY_CORE_SECURITIES
        )

    def coverage_report(
        self,
        securities: Sequence[str],
    ) -> Dict[str, SpyVolatilityCoverage]:
        import sqlite3

        report: Dict[str, SpyVolatilityCoverage] = {}
        if not self.market_db_path.exists():
            for sec in securities:
                report[sec] = SpyVolatilityCoverage(sec, 0, 0, 0)
            return report

        conn = sqlite3.connect(str(self.market_db_path))
        try:
            for sec in securities:
                history_rows = self._count_rows(conn, "bloomberg_daily_history", sec)
                feature_rows = self._count_rows(conn, "bloomberg_daily_features", sec)
                memory_rows = self._count_rows(conn, "bloomberg_research_memory", sec)
                report[sec] = SpyVolatilityCoverage(
                    security=sec,
                    history_rows=history_rows,
                    feature_rows=feature_rows,
                    memory_rows=memory_rows,
                )
        finally:
            conn.close()
        return report

    def missing_securities(
        self,
        securities: Sequence[str],
    ) -> List[str]:
        report = self.coverage_report(securities)
        return [sec for sec, cov in report.items() if not cov.fully_covered]

    # ------------------------------------------------------------------
    # backfill
    # ------------------------------------------------------------------
    def backfill(
        self,
        *,
        extended: bool = False,
        securities: Optional[Sequence[str]] = None,
        start_date: str = "19000101",
        end_date: Optional[str] = None,
        fields: Optional[Sequence[str]] = None,
        windows: Optional[Sequence[int]] = None,
        force_all: bool = False,
        replace_history: bool = False,
        replace_features: bool = False,
        replace_memory: bool = False,
    ) -> Dict[str, Any]:
        universe = list(securities) if securities else self.universe(extended=extended)
        coverage_before = {
            sec: cov.as_dict()
            for sec, cov in self.coverage_report(universe).items()
        }

        targets = list(universe) if force_all else self.missing_securities(universe)

        result: Dict[str, Any] = {
            "requested_universe": universe,
            "targets": targets,
            "coverage_before": coverage_before,
            "history": None,
            "features": None,
            "memory": None,
            "coverage_after": None,
        }

        if not targets:
            result["status"] = "no_work_needed"
            result["coverage_after"] = coverage_before
            return result

        fields_final = list(fields or self.DEFAULT_FIELDS)
        windows_final = tuple(int(x) for x in (windows or self.DEFAULT_WINDOWS))

        self.market_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        self.memory_output_dir.mkdir(parents=True, exist_ok=True)

        with PhysicalMarketGateway() as bbg:
            history_result = bbg.backfill_daily_history_to_sqlite(
                securities=targets,
                fields=fields_final,
                db_path=self.market_db_path,
                start_date=start_date,
                end_date=end_date,
                replace=replace_history,
            )
        result["history"] = history_result

        fs = MarketFeatureStore(db_path=self.market_db_path)
        feature_result = fs.build_and_persist_daily_feature_panel(
            securities=targets,
            windows=windows_final,
            replace=replace_features,
        )
        result["features"] = feature_result

        ingestor = BloombergMemoryIngestor(
            market_db_path=self.market_db_path,
            snapshot_path=self.snapshot_path,
            output_dir=self.memory_output_dir,
        )
        memory_result = ingestor.build_and_persist(
            securities=targets,
            windows=windows_final,
            replace=replace_memory,
        )
        result["memory"] = memory_result

        coverage_after = {
            sec: cov.as_dict()
            for sec, cov in self.coverage_report(universe).items()
        }
        result["coverage_after"] = coverage_after
        result["status"] = "completed"
        return result

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------
    @staticmethod
    def _count_rows(conn, table_name: str, security: str) -> int:
        try:
            row = conn.execute(
                f"SELECT COUNT(*) FROM {table_name} WHERE security = ?",
                [security],
            ).fetchone()
            return int(row[0]) if row is not None else 0
        except Exception:
            return 0


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Backfill the canonical SPY/VIX research universe.")
    parser.add_argument("--market-db-path", default="data/market_history.sqlite")
    parser.add_argument("--snapshot-path", default="artifacts/bloomberg_learning_snapshot.json")
    parser.add_argument("--memory-output-dir", default="artifacts/bloomberg_memory")
    parser.add_argument("--extended", action="store_true")
    parser.add_argument("--securities", default="")
    parser.add_argument("--start-date", default="19000101")
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--fields", default="PX_LAST,OPEN,HIGH,LOW,VOLUME")
    parser.add_argument("--windows", default="5,21,63")
    parser.add_argument("--force-all", action="store_true")
    parser.add_argument("--replace-history", action="store_true")
    parser.add_argument("--replace-features", action="store_true")
    parser.add_argument("--replace-memory", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    explicit_securities = [x.strip() for x in str(args.securities).split(",") if x.strip()]
    fields = [x.strip() for x in str(args.fields).split(",") if x.strip()]
    windows = [int(x.strip()) for x in str(args.windows).split(",") if x.strip()]

    backfill = SpyVolatilityBackfill(
        market_db_path=args.market_db_path,
        snapshot_path=args.snapshot_path,
        memory_output_dir=args.memory_output_dir,
    )
    result = backfill.backfill(
        extended=bool(args.extended),
        securities=explicit_securities or None,
        start_date=str(args.start_date),
        end_date=args.end_date,
        fields=fields,
        windows=windows,
        force_all=bool(args.force_all),
        replace_history=bool(args.replace_history),
        replace_features=bool(args.replace_features),
        replace_memory=bool(args.replace_memory),
    )

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print("=" * 72)
        print("SPY Volatility Backfill")
        print("=" * 72)
        print(json.dumps(result, indent=2, default=str))
        print("=" * 72)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
