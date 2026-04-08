from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if SRC.exists() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from quantai.memory.book_memory import BookMemory
from quantai.reasoning.lean_bridge import LeanBridge
from quantai.reasoning.theorem_lab import TheoremLab


def _split_csv(text: str | None) -> list[str]:
    if not text:
        return []
    return [part.strip() for part in text.split(",") if part.strip()]


def _safe_json(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return _safe_json(asdict(value))
    if isinstance(value, dict):
        return {str(k): _safe_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_safe_json(v) for v in value]
    if hasattr(value, "as_dict"):
        try:
            return _safe_json(value.as_dict())
        except Exception:
            pass
    return str(value)


def _slug(text: str, limit: int = 72) -> str:
    cleaned = []
    prev_dash = False
    for ch in text.lower().strip():
        if ch.isalnum():
            cleaned.append(ch)
            prev_dash = False
        elif not prev_dash:
            cleaned.append("-")
            prev_dash = True
    slug = "".join(cleaned).strip("-")
    return (slug[:limit].rstrip("-")) or "research-artifact"


def _load_text_hits(work_dir: str | Path, query: str, retrieve_k: int) -> list[Any]:
    memory = BookMemory(work_dir)
    try:
        return memory.retrieve(query, top_k=retrieve_k)
    finally:
        memory.close()


def _render_console_summary(payload: dict[str, Any]) -> str:
    selected = payload.get("selected") or {}
    trials = payload.get("trials") or []

    lines = [
        f"Research artifact: {selected.get('title', 'Untitled theorem candidate')}",
        f"Status: {selected.get('status', 'unknown')}",
        f"Score: {float(selected.get('score', 0.0)):.3f}",
        "",
        "Statement:",
        str(selected.get("statement", "No statement produced.")),
        "",
        "Assumptions:",
    ]
    assumptions = [str(x) for x in (selected.get("assumptions") or [])][:8]
    lines.extend([f"- {x}" for x in assumptions] or ["- None recorded"])

    next_actions = [str(x) for x in (selected.get("next_actions") or [])][:8]
    lines.extend(["", "Next actions:"])
    lines.extend([f"- {x}" for x in next_actions] or ["- None recorded"])

    if trials:
        lines.extend(["", f"Verification rounds: {len(trials)}"])
        last = trials[-1]
        verification = last.get("verification") if isinstance(last, dict) else None
        if isinstance(verification, dict):
            lines.append(f"Last verdict: {verification.get('verdict', 'unknown')}")
            lines.append(f"Last score: {float(verification.get('overall_score', 0.0)):.3f}")

    return "\n".join(lines)


def _build_markdown(payload: dict[str, Any], query: str) -> str:
    selected = payload.get("selected") or {}
    trials = payload.get("trials") or []

    lines = [
        f"# {selected.get('title', 'Research Artifact')}",
        "",
        f"**Query:** {query}",
        f"**Status:** {selected.get('status', 'unknown')}",
        f"**Score:** {float(selected.get('score', 0.0)):.3f}",
        "",
        "## Statement",
        str(selected.get("statement", "No statement produced.")),
        "",
        "## Assumptions",
    ]
    assumptions = [str(x) for x in (selected.get("assumptions") or [])]
    lines.extend([f"- {x}" for x in assumptions] or ["- None recorded"])

    lines.extend(["", "## Variables"])
    variables = selected.get("variables") or {}
    if isinstance(variables, dict) and variables:
        lines.extend([f"- **{k}**: {v}" for k, v in variables.items()])
    else:
        lines.append("- None recorded")

    for section_name, key in [
        ("Empirical signature", "empirical_signature"),
        ("Symbolic agenda", "symbolic_agenda"),
        ("Failure conditions", "failure_conditions"),
        ("Next actions", "next_actions"),
    ]:
        lines.extend(["", f"## {section_name}"])
        items = [str(x) for x in (selected.get(key) or [])]
        lines.extend([f"- {x}" for x in items] or ["- None recorded"])

    lines.extend(["", "## Verification rounds"])
    if trials:
        for idx, trial in enumerate(trials, start=1):
            lines.append(f"### Round {idx}")
            if isinstance(trial, dict):
                lines.append(f"- Lab score: {float(trial.get('lab_score', 0.0)):.3f}")
                verification = trial.get("verification") or {}
                if isinstance(verification, dict):
                    lines.append(f"- Verdict: {verification.get('verdict', 'unknown')}")
                    lines.append(f"- Verification score: {float(verification.get('overall_score', 0.0)):.3f}")
                notes = [str(x) for x in (trial.get("notes") or [])]
                if notes:
                    lines.append("- Notes:")
                    lines.extend([f"  - {x}" for x in notes])
    else:
        lines.append("No trials recorded.")

    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run QuantAI theorem research outside the chat/QA loop.")
    parser.add_argument("query", nargs="?", help="Research query. If omitted, interactive mode is used.")
    parser.add_argument("--work-dir", default="rag_ingest_state")
    parser.add_argument("--market-db-path", default="data/market_history.sqlite")
    parser.add_argument("--formal-root", default="formal")
    parser.add_argument("--output-dir", default="research_runs")
    parser.add_argument("--securities", default="")
    parser.add_argument("--benchmark-security", default=None)
    parser.add_argument("--retrieve-k", type=int, default=10)
    parser.add_argument("--max-candidates", type=int, default=3)
    parser.add_argument("--refinement-rounds", type=int, default=2)
    parser.add_argument("--acceptance-score", type=float, default=0.80)
    parser.add_argument("--formal", action="store_true", help="Also export the selected artifact to Lean.")
    parser.add_argument("--run-lean-check", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print the full result payload as JSON.")
    parser.add_argument("--no-memory", action="store_true", help="Skip book-memory retrieval and run from market features only.")
    return parser


def run_once(args: argparse.Namespace, query: str) -> dict[str, Any]:
    securities = _split_csv(args.securities)
    text_hits: list[Any] = []
    if not args.no_memory:
        try:
            text_hits = _load_text_hits(args.work_dir, query, args.retrieve_k)
        except Exception as exc:
            text_hits = []
            print(f"Warning: book-memory retrieval failed: {exc}", file=sys.stderr)

    with TheoremLab(db_path=args.market_db_path) as lab:
        result = lab.run(
            query=query,
            text_hits=text_hits,
            securities=securities,
            benchmark_security=args.benchmark_security,
            max_candidates=args.max_candidates,
            refinement_rounds=args.refinement_rounds,
            acceptance_score=args.acceptance_score,
        )

    payload = _safe_json(result)
    payload["query"] = query
    payload["securities"] = securities
    payload["retrieved_sources"] = [_safe_json(hit) for hit in text_hits]
    payload["run_metadata"] = {
        "work_dir": str(Path(args.work_dir).resolve()),
        "market_db_path": str(Path(args.market_db_path).resolve()),
        "formal_root": str(Path(args.formal_root).resolve()),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "retrieve_k": int(args.retrieve_k),
        "max_candidates": int(args.max_candidates),
        "refinement_rounds": int(args.refinement_rounds),
        "acceptance_score": float(args.acceptance_score),
    }

    if args.formal:
        bridge = LeanBridge(root_dir=args.formal_root)
        exported = bridge.export_lab_result(result, run_check=args.run_lean_check)
        payload["lean_export"] = _safe_json(exported)
    else:
        payload["lean_export"] = None

    return payload


def persist_run(payload: dict[str, Any], output_dir: str | Path) -> dict[str, str]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    query = str(payload.get("query") or "research-artifact")
    base = f"{timestamp}_{_slug(query)}"

    json_path = out_dir / f"{base}.json"
    md_path = out_dir / f"{base}.md"

    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_build_markdown(payload, query), encoding="utf-8")

    return {
        "json_path": str(json_path),
        "markdown_path": str(md_path),
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.query:
        payload = run_once(args, args.query)
        saved = persist_run(payload, args.output_dir)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(_render_console_summary(payload))
            print("")
            print(f"Saved JSON: {saved['json_path']}")
            print(f"Saved Markdown: {saved['markdown_path']}")
            if payload.get("lean_export"):
                lean = payload["lean_export"]
                if isinstance(lean, dict):
                    print(f"Saved Lean: {lean.get('lean_path')}")
        return 0

    print("=" * 72)
    print("QuantAI research runner ready. Type a research prompt, or 'exit' to quit.")
    print("=" * 72)
    while True:
        try:
            query = input("\n[research] > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            return 0
        if not query:
            continue
        if query.lower() in {"exit", "quit"}:
            return 0
        try:
            payload = run_once(args, query)
            saved = persist_run(payload, args.output_dir)
            if args.json:
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            else:
                print("\n" + _render_console_summary(payload))
                print("")
                print(f"Saved JSON: {saved['json_path']}")
                print(f"Saved Markdown: {saved['markdown_path']}")
                if payload.get("lean_export"):
                    lean = payload["lean_export"]
                    if isinstance(lean, dict):
                        print(f"Saved Lean: {lean.get('lean_path')}")
        except Exception as exc:
            print(f"Research run failed: {exc}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
