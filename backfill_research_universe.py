from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from quantai.reasoning.bloomberg_memory_ingestor import BloombergMemoryIngestor
from quantai.reasoning.feature_store import MarketFeatureStore
from quantai.reasoning.market_data import PhysicalMarketGateway


def _parse_csv(value: str) -> List[str]:
    return [x.strip() for x in str(value).split(",") if x.strip()]


def _default_start_date(from_inception: bool, start_date: str | None) -> str:
    if start_date:
        return str(start_date)
    if from_inception:
        return "19000101"
    raise ValueError("Provide --start-date or use --from-inception")


def run_backfill_universe(
    *,
    securities: List[str],
    fields: List[str],
    db_path: Path,
    start_date: str,
    end_date: str | None,
    windows: List[int],
    replace_history: bool,
    replace_features: bool,
    replace_memory: bool,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "db_path": str(db_path),
        "securities": securities,
        "fields": fields,
        "start_date": start_date,
        "end_date": end_date,
        "history": None,
        "features": None,
        "memory": None,
    }

    db_path.parent.mkdir(parents=True, exist_ok=True)

    with PhysicalMarketGateway() as bbg:
        history = bbg.backfill_daily_history_to_sqlite(
            securities=securities,
            fields=fields,
            db_path=db_path,
            start_date=start_date,
            end_date=end_date,
            replace=replace_history,
        )
    result["history"] = history

    fs = MarketFeatureStore(db_path=db_path)
    features = fs.build_and_persist_daily_feature_panel(
        securities=securities,
        windows=tuple(windows),
        replace=replace_features,
    )
    result["features"] = features

    snapshot_path = ROOT / "artifacts" / "bloomberg_learning_snapshot.json"
    output_dir = ROOT / "artifacts" / "bloomberg_memory"
    ing = BloombergMemoryIngestor(
        market_db_path=db_path,
        snapshot_path=snapshot_path,
        output_dir=output_dir,
    )
    memory = ing.build_and_persist(
        securities=securities,
        windows=tuple(windows),
        replace=replace_memory,
    )
    result["memory"] = memory

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill a Bloomberg research universe for QuantAI."
    )
    parser.add_argument("--securities", required=True, help="Comma-separated Bloomberg securities.")
    parser.add_argument("--fields", default="PX_LAST,OPEN,HIGH,LOW,VOLUME")
    parser.add_argument("--db-path", default="data/market_history.sqlite")
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--from-inception", action="store_true")
    parser.add_argument("--windows", default="5,21,63")
    parser.add_argument("--replace-history", action="store_true")
    parser.add_argument("--replace-features", action="store_true")
    parser.add_argument("--replace-memory", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    securities = _parse_csv(args.securities)
    if not securities:
        raise SystemExit("No securities were provided.")
    fields = _parse_csv(args.fields)
    windows = [int(x) for x in _parse_csv(args.windows)]
    db_path = Path(args.db_path)
    start_date = _default_start_date(args.from_inception, args.start_date)

    result = run_backfill_universe(
        securities=securities,
        fields=fields,
        db_path=db_path,
        start_date=start_date,
        end_date=args.end_date,
        windows=windows,
        replace_history=bool(args.replace_history),
        replace_features=bool(args.replace_features),
        replace_memory=bool(args.replace_memory),
    )

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print("=" * 72)
        print("QuantAI Universe Backfill")
        print("=" * 72)
        print(json.dumps(result, indent=2, default=str))
        print("=" * 72)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
