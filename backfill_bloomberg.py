from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from quantai.reasoning.market_data import PhysicalMarketGateway


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Backfill Bloomberg daily history into SQLite.")
    p.add_argument("--securities", required=True, help="Comma-separated Bloomberg tickers")
    p.add_argument("--fields", required=True, help="Comma-separated Bloomberg field mnemonics")
    p.add_argument("--db-path", default="data/market_history.sqlite")
    p.add_argument("--start-date", default=None)
    p.add_argument("--end-date", default=None)
    p.add_argument("--from-inception", action="store_true")
    p.add_argument("--replace", action="store_true")
    return p


def main() -> int:
    args = build_parser().parse_args()
    securities = [x.strip() for x in args.securities.split(",") if x.strip()]
    fields = [x.strip() for x in args.fields.split(",") if x.strip()]
    if not securities or not fields:
        raise SystemExit("Provide at least one security and one field.")

    with PhysicalMarketGateway() as bbg:
        if args.from_inception:
            starts = []
            for sec in securities:
                dt = bbg.earliest_history_date(sec, fields[0])
                starts.append(dt)
            starts = [x for x in starts if x is not None]
            if not starts:
                raise SystemExit("Could not determine any inception date from Bloomberg.")
            start_date = min(starts).strftime("%Y%m%d")
        else:
            if not args.start_date:
                raise SystemExit("Use --start-date or --from-inception.")
            start_date = args.start_date

        result = bbg.backfill_daily_history_to_sqlite(
            securities=securities,
            fields=fields,
            db_path=args.db_path,
            start_date=start_date,
            end_date=args.end_date,
            replace=args.replace,
        )
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
