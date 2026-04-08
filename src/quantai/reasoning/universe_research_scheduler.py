from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from quantai.reasoning.empirical_research_runner import (
    EmpiricalResearchRunner,
    ResearchTask,
)


@dataclass(frozen=True)
class UniverseSpec:
    name: str
    securities: List[str]
    benchmark_security: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class JobTemplate:
    name: str
    query_template: str
    use_all_securities: bool = False
    min_securities: int = 1
    include_evidence: bool = True
    include_theorem: bool = True
    include_market_memory: bool = True
    include_market_calibration: bool = False
    include_market_live_snapshot: bool = False
    acceptance_score: float = 0.80

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScheduledJobResult:
    universe_name: str
    task_name: str
    security_scope: List[str]
    ok: bool
    summary: Dict[str, Any]
    files: Dict[str, Any]
    warnings: List[str]

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


class UniverseResearchScheduler:
    """
    Batch research orchestrator for QuantAI.

    Purpose:
    - define a security universe once
    - define reusable research templates once
    - generate ResearchTask objects deterministically
    - execute the batch and persist each artifact

    This is the layer that moves QuantAI from one-off experiments
    to a repeatable research program over a maintained universe.
    """

    def __init__(
        self,
        work_dir: str | Path = "rag_ingest_state",
        market_db_path: str | Path = "data/market_history.sqlite",
        output_dir: str | Path = "artifacts/universe_research_runs",
        answer_mode: str = "auto",
    ) -> None:
        self.work_dir = Path(work_dir)
        self.market_db_path = Path(market_db_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.answer_mode = str(answer_mode)

        self.runner = EmpiricalResearchRunner(
            work_dir=self.work_dir,
            market_db_path=self.market_db_path,
            output_dir=self.output_dir,
            answer_mode=self.answer_mode,
        )

    # ------------------------------------------------------------------
    # default templates
    # ------------------------------------------------------------------
    @staticmethod
    def default_templates() -> List[JobTemplate]:
        return [
            JobTemplate(
                name="roughness_scaling",
                query_template="Propose a theorem linking rough-volatility roughness to realized variance scaling for {primary}.",
                use_all_securities=False,
                min_securities=1,
                include_evidence=True,
                include_theorem=True,
                include_market_memory=True,
                include_market_calibration=False,
            ),
            JobTemplate(
                name="single_name_execution",
                query_template="Pull the live Level II limit order book depth for {primary} via the Bloomberg API and formulate the precise Almgren-Chriss liquidating trajectory for 10^5 shares over T=1 hour.",
                use_all_securities=False,
                min_securities=1,
                include_evidence=True,
                include_theorem=False,
                include_market_memory=True,
                include_market_live_snapshot=True,
            ),
            JobTemplate(
                name="pair_ou_spread",
                query_template="Retrieve the {primary} and {secondary} spread over the last 60 minutes and compute the maximum likelihood estimation for the OU mean-reversion speed kappa.",
                use_all_securities=False,
                min_securities=2,
                include_evidence=True,
                include_theorem=True,
                include_market_memory=True,
                include_market_calibration=True,
            ),
            JobTemplate(
                name="universe_state",
                query_template="Summarize the current Bloomberg empirical memory and roughness / mean-reversion signatures for {universe_name}.",
                use_all_securities=True,
                min_securities=1,
                include_evidence=False,
                include_theorem=False,
                include_market_memory=True,
                include_market_calibration=False,
            ),
        ]

    # ------------------------------------------------------------------
    # task generation
    # ------------------------------------------------------------------
    def build_tasks(
        self,
        universe: UniverseSpec,
        templates: Sequence[JobTemplate],
    ) -> List[ResearchTask]:
        tasks: List[ResearchTask] = []
        secs = list(universe.securities)

        for template in templates:
            if template.use_all_securities:
                query = self._render_query(
                    template.query_template,
                    universe_name=universe.name,
                    primary=secs[0] if secs else "",
                    secondary=secs[1] if len(secs) > 1 else "",
                )
                tasks.append(
                    ResearchTask(
                        name=f"{universe.name}_{template.name}",
                        core_query=query,
                        securities=secs,
                        benchmark_security=universe.benchmark_security,
                        include_evidence=template.include_evidence,
                        include_theorem=template.include_theorem,
                        include_market_memory=template.include_market_memory,
                        include_market_calibration=template.include_market_calibration,
                        include_market_live_snapshot=template.include_market_live_snapshot,
                        acceptance_score=template.acceptance_score,
                    )
                )
                continue

            if template.min_securities <= 1:
                for sec in secs:
                    query = self._render_query(
                        template.query_template,
                        universe_name=universe.name,
                        primary=sec,
                        secondary="",
                    )
                    tasks.append(
                        ResearchTask(
                            name=f"{self._slugify(universe.name)}_{self._slugify(sec)}_{template.name}",
                            core_query=query,
                            securities=[sec],
                            benchmark_security=universe.benchmark_security,
                            include_evidence=template.include_evidence,
                            include_theorem=template.include_theorem,
                            include_market_memory=template.include_market_memory,
                            include_market_calibration=template.include_market_calibration,
                            include_market_live_snapshot=template.include_market_live_snapshot,
                            acceptance_score=template.acceptance_score,
                        )
                    )
            elif template.min_securities == 2:
                for i in range(len(secs)):
                    for j in range(i + 1, len(secs)):
                        left, right = secs[i], secs[j]
                        query = self._render_query(
                            template.query_template,
                            universe_name=universe.name,
                            primary=left,
                            secondary=right,
                        )
                        tasks.append(
                            ResearchTask(
                                name=f"{self._slugify(universe.name)}_{self._slugify(left)}_{self._slugify(right)}_{template.name}",
                                core_query=query,
                                securities=[left, right],
                                benchmark_security=universe.benchmark_security,
                                include_evidence=template.include_evidence,
                                include_theorem=template.include_theorem,
                                include_market_memory=template.include_market_memory,
                                include_market_calibration=template.include_market_calibration,
                                include_market_live_snapshot=template.include_market_live_snapshot,
                                acceptance_score=template.acceptance_score,
                            )
                        )
        return tasks

    # ------------------------------------------------------------------
    # execution
    # ------------------------------------------------------------------
    def run_universe(
        self,
        universe: UniverseSpec,
        templates: Optional[Sequence[JobTemplate]] = None,
        *,
        limit_jobs: Optional[int] = None,
    ) -> Dict[str, Any]:
        templates = list(templates or self.default_templates())
        tasks = self.build_tasks(universe, templates)
        if limit_jobs is not None:
            tasks = tasks[: int(limit_jobs)]

        results: List[ScheduledJobResult] = []
        for task in tasks:
            run = self.runner.run_and_persist(task, stem=task.name)
            artifact = run["artifact"]
            files = run["files"]
            summary = artifact.get("summary", {})
            warnings = artifact.get("warnings", [])
            ok = (
                bool(summary.get("coverage_ok"))
                and any(
                    bool(summary.get(flag))
                    for flag in (
                        "evidence_ok",
                        "theorem_ok",
                        "market_memory_ok",
                        "market_calibration_ok",
                        "market_live_snapshot_ok",
                    )
                )
            )
            results.append(
                ScheduledJobResult(
                    universe_name=universe.name,
                    task_name=task.name,
                    security_scope=list(task.securities),
                    ok=ok,
                    summary=summary,
                    files=files,
                    warnings=list(warnings),
                )
            )

        manifest = self._persist_manifest(universe, templates, results)
        return {
            "universe": universe.as_dict(),
            "n_tasks": len(tasks),
            "n_ok": sum(1 for r in results if r.ok),
            "n_fail": sum(1 for r in results if not r.ok),
            "results": [r.as_dict() for r in results],
            "manifest": manifest,
        }

    # ------------------------------------------------------------------
    # persistence
    # ------------------------------------------------------------------
    def _persist_manifest(
        self,
        universe: UniverseSpec,
        templates: Sequence[JobTemplate],
        results: Sequence[ScheduledJobResult],
    ) -> Dict[str, Any]:
        ts = self._utc_now_compact()
        stem = f"{self._slugify(universe.name)}_{ts}_manifest"
        json_path = self.output_dir / f"{stem}.json"
        md_path = self.output_dir / f"{stem}.md"

        payload = {
            "created_at": self._utc_now_iso(),
            "universe": universe.as_dict(),
            "templates": [t.as_dict() for t in templates],
            "results": [r.as_dict() for r in results],
        }
        json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        md_path.write_text(self._manifest_markdown(universe, templates, results), encoding="utf-8")

        return {
            "json_path": str(json_path),
            "markdown_path": str(md_path),
            "bytes_json": json_path.stat().st_size,
            "bytes_markdown": md_path.stat().st_size,
        }

    def _manifest_markdown(
        self,
        universe: UniverseSpec,
        templates: Sequence[JobTemplate],
        results: Sequence[ScheduledJobResult],
    ) -> str:
        lines: List[str] = [
            f"# Universe Research Manifest: {universe.name}",
            "",
            f"- Securities: {', '.join(universe.securities)}",
            f"- Benchmark: {universe.benchmark_security or 'None'}",
            f"- Created at: {self._utc_now_iso()}",
            "",
            "## Templates",
        ]
        for t in templates:
            lines.append(f"- {t.name}: {t.query_template}")

        lines.extend(["", "## Results"])
        for r in results:
            lines.append(f"### {r.task_name}")
            lines.append(f"- OK: {r.ok}")
            lines.append(f"- Scope: {', '.join(r.security_scope)}")
            lines.append("```json")
            lines.append(json.dumps(r.summary, indent=2, default=str))
            lines.append("```")
            if r.warnings:
                lines.append("Warnings:")
                lines.extend([f"- {w}" for w in r.warnings])
            lines.append(f"- JSON: {r.files.get('json_path')}")
            lines.append(f"- Markdown: {r.files.get('markdown_path')}")
            lines.append("")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _render_query(template: str, **kwargs: Any) -> str:
        return str(template).format(**kwargs)

    @staticmethod
    def _slugify(text: str) -> str:
        text = re.sub(r"[^A-Za-z0-9]+", "_", str(text)).strip("_").lower()
        return text or "job"

    @staticmethod
    def _utc_now_iso() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    @staticmethod
    def _utc_now_compact() -> str:
        return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run a scheduled QuantAI research universe.")
    parser.add_argument("--name", required=True)
    parser.add_argument("--securities", required=True)
    parser.add_argument("--benchmark-security", default="")
    parser.add_argument("--work-dir", default="rag_ingest_state")
    parser.add_argument("--market-db-path", default="data/market_history.sqlite")
    parser.add_argument("--output-dir", default="artifacts/universe_research_runs")
    parser.add_argument("--limit-jobs", type=int, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    universe = UniverseSpec(
        name=args.name,
        securities=[x.strip() for x in str(args.securities).split(",") if x.strip()],
        benchmark_security=(args.benchmark_security or None),
    )

    scheduler = UniverseResearchScheduler(
        work_dir=args.work_dir,
        market_db_path=args.market_db_path,
        output_dir=args.output_dir,
    )
    result = scheduler.run_universe(universe, limit_jobs=args.limit_jobs)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print("=" * 72)
        print("Universe Research Scheduler")
        print("=" * 72)
        print(json.dumps({
            "universe": result["universe"]["name"],
            "n_tasks": result["n_tasks"],
            "n_ok": result["n_ok"],
            "n_fail": result["n_fail"],
            "manifest": result["manifest"],
        }, indent=2, default=str))
        print("=" * 72)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
