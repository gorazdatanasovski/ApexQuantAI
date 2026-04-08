from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from quantai.reasoning.engine import ApexReasoningCore


VALID_MODES = [
    "auto",
    "evidence",
    "theorem",
    "formal",
    "market_memory",
    "market_calibration",
    "market_live_snapshot",
    "synthesis",
    "deep",
]


def _parse_csv(value: str | None) -> List[str]:
    if not value:
        return []
    return [part.strip() for part in str(value).split(",") if part.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Interactive CLI for QuantAI across book evidence, theorem lab, Bloomberg memory, and calibration."
    )
    parser.add_argument("--work-dir", default="rag_ingest_state")
    parser.add_argument("--market-db-path", default="data/market_history.sqlite")
    parser.add_argument("--model", default="llama3")
    parser.add_argument("--ollama-url", default="http://localhost:11434")
    parser.add_argument("--retrieve-k", type=int, default=10)
    parser.add_argument("--answer-k", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--num-ctx", type=int, default=4096)
    parser.add_argument("--num-predict", type=int, default=220)
    parser.add_argument("--keep-alive", default="-1")
    parser.add_argument("--mode", choices=VALID_MODES, default="auto")
    parser.add_argument(
        "--securities",
        default="",
        help='Comma-separated Bloomberg securities, e.g. "SPY US Equity,AAPL US Equity"',
    )
    parser.add_argument("--preload-llm", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def _render_answer(answer: dict) -> None:
    response = answer.get("response")
    if response:
        print("\n" + "-" * 72)
        print(response)

    if answer.get("mode_used"):
        print(f"\nMode used: {answer['mode_used']}")

    if answer.get("selected_title"):
        print(f"Selected title: {answer['selected_title']}")

    if answer.get("lean_export"):
        print("\nLean export:")
        print(answer["lean_export"])

    sources = answer.get("sources") or []
    if sources:
        print("\nSources:")
        for hit in sources:
            file_name = hit.get("file_name", "unknown")
            page_no = hit.get("page_no", "NA")
            chunk_no = hit.get("chunk_no", "NA")
            score = hit.get("score")
            dense = hit.get("dense_score")
            lexical = hit.get("lexical_score")

            score_s = f"{float(score):.4f}" if isinstance(score, (int, float)) else "NA"
            dense_s = f" dense={float(dense):.4f}" if isinstance(dense, (int, float)) else ""
            lexical_s = f" lexical={float(lexical):.4f}" if isinstance(lexical, (int, float)) else ""

            print(
                f"  - {file_name} | page {page_no} | chunk {chunk_no} | "
                f"score={score_s}{dense_s}{lexical_s}"
            )

    llm_stats = answer.get("llm_stats")
    if llm_stats:
        print("\nLLM stats:")
        for key, value in llm_stats.items():
            print(f"  - {key}: {value}")

    diagnostics = answer.get("diagnostics")
    if diagnostics:
        print("\nDiagnostics:")
        if isinstance(diagnostics, dict):
            for key, value in diagnostics.items():
                print(f"  - {key}: {value}")
        else:
            print(diagnostics)

    if answer.get("market_summary"):
        print("\nMarket summary:")
        print(json.dumps(answer["market_summary"], indent=2, default=str)[:3000])

    if answer.get("live_market"):
        print("\nLive market:")
        print(json.dumps(answer["live_market"], indent=2, default=str)[:3000])

    if answer.get("calibration"):
        print("\nCalibration:")
        print(json.dumps(answer["calibration"], indent=2, default=str)[:3000])

    if answer.get("execution_trajectory"):
        print("\nExecution trajectory:")
        print(json.dumps(answer["execution_trajectory"], indent=2, default=str)[:3000])

    print("-" * 72)


def main() -> int:
    args = build_parser().parse_args()
    securities = _parse_csv(args.securities)

    try:
        core = ApexReasoningCore(
            work_dir=args.work_dir,
            market_db_path=args.market_db_path,
            model_name=args.model,
            ollama_base_url=args.ollama_url,
            retrieve_k=args.retrieve_k,
            answer_k=args.answer_k,
            request_timeout=args.timeout,
            num_ctx=args.num_ctx,
            num_predict=args.num_predict,
            keep_alive=args.keep_alive,
            answer_mode=args.mode,
        )
        if args.preload_llm and hasattr(core, "preload_llm"):
            core.preload_llm()
    except Exception as exc:
        print(f"Initialization failed: {exc}", file=sys.stderr)
        return 1

    print("=" * 72)
    print("QuantAI ready. Type a query, or 'exit' to quit.")
    if securities:
        print(f"Default securities: {', '.join(securities)}")
    print("=" * 72)

    try:
        while True:
            try:
                query = input("\n[query] > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting.")
                return 0

            if not query:
                continue
            if query.lower() in {"exit", "quit"}:
                return 0

            try:
                answer = core.answer(
                    query,
                    securities=securities or None,
                    mode=args.mode,
                )
            except Exception as exc:
                print(f"Query failed: {exc}", file=sys.stderr)
                continue

            if args.json:
                print(json.dumps(answer, ensure_ascii=False, indent=2, default=str))
            else:
                _render_answer(answer)
    finally:
        try:
            core.close()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
