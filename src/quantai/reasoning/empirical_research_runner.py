from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from quantai.reasoning.engine import ApexReasoningCore


@dataclass(frozen=True)
class ResearchTask:
    name: str
    core_query: str
    securities: List[str] = field(default_factory=list)
    benchmark_security: Optional[str] = None
    include_evidence: bool = True
    include_theorem: bool = True
    include_market_memory: bool = True
    include_market_calibration: bool = False
    include_market_live_snapshot: bool = False
    include_formal_export: bool = False
    acceptance_score: float = 0.80

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResearchRunArtifact:
    task: Dict[str, Any]
    created_at: str
    coverage: Dict[str, Any]
    evidence: Optional[Dict[str, Any]]
    theorem: Optional[Dict[str, Any]]
    market_memory: Optional[Dict[str, Any]]
    market_calibration: Optional[Dict[str, Any]]
    market_live_snapshot: Optional[Dict[str, Any]]
    summary: Dict[str, Any]
    warnings: List[str]

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EmpiricalResearchRunner:
    """
    Repeatable research job runner for QuantAI.

    What it does:
    - checks warehouse coverage before expensive research steps
    - runs a structured multi-lane research job
    - persists a JSON + Markdown artifact
    - makes missing prerequisites explicit instead of silently failing later

    Designed around the current QuantAI stack:
    - books / fused evidence
    - theorem registry + theorem lab
    - Bloomberg research memory
    - market calibration
    - market live snapshot
    """

    def __init__(
        self,
        work_dir: str | Path = "rag_ingest_state",
        market_db_path: str | Path = "data/market_history.sqlite",
        output_dir: str | Path = "artifacts/empirical_research_runs",
        answer_mode: str = "auto",
    ) -> None:
        self.work_dir = Path(work_dir)
        self.market_db_path = Path(market_db_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.answer_mode = str(answer_mode)

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def run_task(self, task: ResearchTask) -> ResearchRunArtifact:
        coverage = self.coverage_report(task.securities)
        warnings: List[str] = self._warnings_from_coverage(task, coverage)

        with self._core() as core:
            evidence = None
            theorem = None
            market_memory = None
            market_calibration = None
            market_live_snapshot = None

            if task.include_evidence:
                evidence = self._safe_answer(
                    core,
                    query=task.core_query,
                    mode="evidence",
                    securities=task.securities,
                    benchmark_security=task.benchmark_security,
                )

            if task.include_theorem:
                theorem = self._safe_answer(
                    core,
                    query=task.core_query,
                    mode="theorem",
                    securities=task.securities,
                    benchmark_security=task.benchmark_security,
                    acceptance_score=task.acceptance_score,
                )

            if task.include_market_memory and task.securities:
                market_memory = self._safe_answer(
                    core,
                    query=f"What is the current Bloomberg empirical memory for {task.securities[0]}?",
                    mode="market_memory",
                    securities=task.securities,
                    benchmark_security=task.benchmark_security,
                )

            if task.include_market_calibration and task.securities:
                market_calibration = self._safe_answer(
                    core,
                    query=task.core_query,
                    mode="market_calibration",
                    securities=task.securities,
                    benchmark_security=task.benchmark_security,
                )

            if task.include_market_live_snapshot and task.securities:
                market_live_snapshot = self._safe_answer(
                    core,
                    query=task.core_query,
                    mode="market_live_snapshot",
                    securities=task.securities,
                    benchmark_security=task.benchmark_security,
                )

        summary = self._build_summary(
            task=task,
            coverage=coverage,
            evidence=evidence,
            theorem=theorem,
            market_memory=market_memory,
            market_calibration=market_calibration,
            market_live_snapshot=market_live_snapshot,
        )

        artifact = ResearchRunArtifact(
            task=task.as_dict(),
            created_at=self._utc_now(),
            coverage=coverage,
            evidence=evidence,
            theorem=theorem,
            market_memory=market_memory,
            market_calibration=market_calibration,
            market_live_snapshot=market_live_snapshot,
            summary=summary,
            warnings=warnings,
        )
        return artifact

    def persist_run(
        self,
        artifact: ResearchRunArtifact,
        *,
        stem: Optional[str] = None,
    ) -> Dict[str, Any]:
        stem = stem or self._default_stem(artifact)
        json_path = self.output_dir / f"{stem}.json"
        md_path = self.output_dir / f"{stem}.md"

        json_path.write_text(
            json.dumps(artifact.as_dict(), indent=2, default=str),
            encoding="utf-8",
        )
        md_path.write_text(
            self._to_markdown(artifact),
            encoding="utf-8",
        )
        return {
            "json_path": str(json_path),
            "markdown_path": str(md_path),
            "bytes_json": json_path.stat().st_size,
            "bytes_markdown": md_path.stat().st_size,
        }

    def run_and_persist(
        self,
        task: ResearchTask,
        *,
        stem: Optional[str] = None,
    ) -> Dict[str, Any]:
        artifact = self.run_task(task)
        paths = self.persist_run(artifact, stem=stem)
        return {
            "artifact": artifact.as_dict(),
            "files": paths,
        }

    def coverage_report(self, securities: Sequence[str]) -> Dict[str, Any]:
        report: Dict[str, Any] = {
            "db_exists": self.market_db_path.exists(),
            "securities": {},
        }
        if not self.market_db_path.exists():
            return report

        conn = sqlite3.connect(str(self.market_db_path))
        try:
            for sec in securities:
                report["securities"][sec] = {
                    "history_rows": self._count_rows(conn, "bloomberg_daily_history", sec),
                    "feature_rows": self._count_rows(conn, "bloomberg_daily_features", sec),
                    "memory_rows": self._count_rows(conn, "bloomberg_research_memory", sec),
                }
        finally:
            conn.close()
        return report

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------
    class _CoreContext:
        def __init__(self, outer: "EmpiricalResearchRunner") -> None:
            self.outer = outer
            self.core: Optional[ApexReasoningCore] = None

        def __enter__(self) -> ApexReasoningCore:
            self.core = ApexReasoningCore(
                work_dir=self.outer.work_dir,
                market_db_path=self.outer.market_db_path,
                answer_mode=self.outer.answer_mode,
            )
            return self.core

        def __exit__(self, exc_type, exc, tb) -> None:
            if self.core is not None:
                self.core.close()

    def _core(self) -> "_CoreContext":
        return EmpiricalResearchRunner._CoreContext(self)

    def _safe_answer(
        self,
        core: ApexReasoningCore,
        *,
        query: str,
        mode: str,
        securities: Sequence[str],
        benchmark_security: Optional[str],
        acceptance_score: Optional[float] = None,
    ) -> Dict[str, Any]:
        try:
            kwargs: Dict[str, Any] = {
                "query": query,
                "mode": mode,
                "securities": list(securities),
                "benchmark_security": benchmark_security,
            }
            if acceptance_score is not None:
                kwargs["acceptance_score"] = float(acceptance_score)
            out = core.answer(**kwargs)
            return {
                "ok": True,
                "mode_used": out.get("mode_used"),
                "selected_title": out.get("selected_title"),
                "response": out.get("response"),
                "n_sources": len(out.get("sources", [])),
                "n_fusion_hits": len(out.get("fusion_hits", [])),
                "theorem_registry": out.get("theorem_registry"),
                "execution_parameter_calibration": out.get("execution_parameter_calibration"),
                "execution_trajectory": out.get("execution_trajectory"),
                "calibration": out.get("calibration"),
                "market_summary": out.get("market_summary"),
                "live_market": out.get("live_market"),
                "resolved_snapshot": out.get("resolved_snapshot"),
            }
        except Exception as exc:
            return {
                "ok": False,
                "mode_used": mode,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }

    def _build_summary(
        self,
        *,
        task: ResearchTask,
        coverage: Dict[str, Any],
        evidence: Optional[Dict[str, Any]],
        theorem: Optional[Dict[str, Any]],
        market_memory: Optional[Dict[str, Any]],
        market_calibration: Optional[Dict[str, Any]],
        market_live_snapshot: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return {
            "task_name": task.name,
            "securities": list(task.securities),
            "coverage_ok": self._coverage_ok(coverage, task.securities),
            "evidence_ok": bool(evidence and evidence.get("ok")),
            "theorem_ok": bool(theorem and theorem.get("ok")),
            "market_memory_ok": bool(market_memory and market_memory.get("ok")),
            "market_calibration_ok": bool(market_calibration and market_calibration.get("ok")),
            "market_live_snapshot_ok": bool(market_live_snapshot and market_live_snapshot.get("ok")),
            "selected_theorem_title": theorem.get("selected_title") if theorem else None,
            "theorem_registry": theorem.get("theorem_registry") if theorem else None,
        }

    def _warnings_from_coverage(self, task: ResearchTask, coverage: Dict[str, Any]) -> List[str]:
        warnings: List[str] = []
        if not coverage.get("db_exists"):
            warnings.append("Market database does not exist. Bloomberg-derived empirical steps will be unreliable.")
            return warnings

        for sec in task.securities:
            sec_info = (coverage.get("securities") or {}).get(sec, {})
            if int(sec_info.get("history_rows", 0) or 0) == 0:
                warnings.append(f"{sec}: no rows in bloomberg_daily_history.")
            if int(sec_info.get("feature_rows", 0) or 0) == 0:
                warnings.append(f"{sec}: no rows in bloomberg_daily_features.")
            if int(sec_info.get("memory_rows", 0) or 0) == 0:
                warnings.append(f"{sec}: no rows in bloomberg_research_memory.")
        return warnings

    @staticmethod
    def _count_rows(conn: sqlite3.Connection, table_name: str, security: str) -> int:
        try:
            row = conn.execute(
                f"SELECT COUNT(*) FROM {table_name} WHERE security = ?",
                [security],
            ).fetchone()
            return int(row[0]) if row is not None else 0
        except Exception:
            return 0

    @staticmethod
    def _coverage_ok(coverage: Dict[str, Any], securities: Sequence[str]) -> bool:
        if not coverage.get("db_exists"):
            return False
        secs = coverage.get("securities") or {}
        for sec in securities:
            sec_info = secs.get(sec, {})
            if int(sec_info.get("history_rows", 0) or 0) <= 0:
                return False
        return True

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    @staticmethod
    def _slugify(text: str) -> str:
        text = re.sub(r"[^A-Za-z0-9]+", "_", str(text)).strip("_").lower()
        return text or "research_run"

    def _default_stem(self, artifact: ResearchRunArtifact) -> str:
        name = artifact.task.get("name") or "research_run"
        ts = artifact.created_at.replace(":", "").replace("-", "").replace("+00:00", "z")
        return f"{self._slugify(name)}_{ts}"

    def _to_markdown(self, artifact: ResearchRunArtifact) -> str:
        lines: List[str] = [
            f"# {artifact.task.get('name', 'Research Run')}",
            "",
            f"- Created at: {artifact.created_at}",
            f"- Securities: {', '.join(artifact.task.get('securities', [])) or 'None'}",
            f"- Core query: {artifact.task.get('core_query', '')}",
            "",
            "## Summary",
            "```json",
            json.dumps(artifact.summary, indent=2, default=str),
            "```",
            "",
            "## Coverage",
            "```json",
            json.dumps(artifact.coverage, indent=2, default=str),
            "```",
        ]

        if artifact.warnings:
            lines.extend(["", "## Warnings"])
            lines.extend([f"- {w}" for w in artifact.warnings])

        for label, payload in [
            ("Evidence", artifact.evidence),
            ("Theorem", artifact.theorem),
            ("Market memory", artifact.market_memory),
            ("Market calibration", artifact.market_calibration),
            ("Market live snapshot", artifact.market_live_snapshot),
        ]:
            lines.extend(["", f"## {label}"])
            if payload is None:
                lines.append("None")
            else:
                lines.append("```json")
                lines.append(json.dumps(payload, indent=2, default=str)[:16000])
                lines.append("```")

        return "\n".join(lines)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run a repeatable empirical research job in QuantAI.")
    parser.add_argument("--name", required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--securities", default="")
    parser.add_argument("--benchmark-security", default="")
    parser.add_argument("--work-dir", default="rag_ingest_state")
    parser.add_argument("--market-db-path", default="data/market_history.sqlite")
    parser.add_argument("--output-dir", default="artifacts/empirical_research_runs")
    parser.add_argument("--with-calibration", action="store_true")
    parser.add_argument("--with-live-snapshot", action="store_true")
    parser.add_argument("--no-evidence", action="store_true")
    parser.add_argument("--no-theorem", action="store_true")
    parser.add_argument("--no-market-memory", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    securities = [x.strip() for x in str(args.securities).split(",") if x.strip()]
    task = ResearchTask(
        name=args.name,
        core_query=args.query,
        securities=securities,
        benchmark_security=(args.benchmark_security or None),
        include_evidence=not args.no_evidence,
        include_theorem=not args.no_theorem,
        include_market_memory=not args.no_market_memory,
        include_market_calibration=bool(args.with_calibration),
        include_market_live_snapshot=bool(args.with_live_snapshot),
    )

    runner = EmpiricalResearchRunner(
        work_dir=args.work_dir,
        market_db_path=args.market_db_path,
        output_dir=args.output_dir,
    )
    result = runner.run_and_persist(task)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print("=" * 72)
        print("Empirical Research Runner")
        print("=" * 72)
        print(json.dumps(result["artifact"]["summary"], indent=2, default=str))
        print(json.dumps(result["files"], indent=2, default=str))
        print("=" * 72)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
