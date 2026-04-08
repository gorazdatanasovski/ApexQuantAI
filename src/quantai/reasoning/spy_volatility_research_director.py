from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from quantai.reasoning.empirical_research_runner import EmpiricalResearchRunner, ResearchTask
from quantai.reasoning.pair_linkage_theorem_engine import PairLinkageTheoremEngine
from quantai.reasoning.spy_volatility_scoreboard import SpyVolatilityScoreboard
from quantai.reasoning.spy_volatility_universe import SPY_VOLATILITY_CORE_SECURITIES


@dataclass(frozen=True)
class DirectorAction:
    priority: float
    category: str
    task_name: str
    rationale: str
    securities: List[str]
    query: str
    benchmark_security: str = "SPY US Equity"

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SpyVolatilityResearchDirector:
    """
    Promotion-aware research director for the SPY/VIX program.

    Superior version:
    - uses PairLinkageTheoremEngine directly for SPY/VIX pair theorem work
    - keeps EmpiricalResearchRunner for reruns and non-pair empirical lanes
    - exploits promoted symbolic theorem families first
    - ignores stale pre-backfill weak-lane noise
    """

    TARGET_PAIRS: Sequence[tuple[str, str]] = (
        ("SPY US Equity", "VIX Index"),
        ("SPY US Equity", "VIX3M Index"),
        ("SPY US Equity", "VVIX Index"),
        ("SPY US Equity", "SKEW Index"),
        ("SPY US Equity", "SPX Index"),
    )

    PAIR_ENGINE_CATEGORIES = {
        "exploit_promoted_theorem",
        "refine_pair_linkage",
        "extend_top_run",
    }

    def __init__(
        self,
        market_db_path: str | Path = "data/market_history.sqlite",
        runs_dir: str | Path = "artifacts/universe_research_runs",
        scoreboards_dir: str | Path = "artifacts/scoreboards",
        output_dir: str | Path = "artifacts/director_runs",
        work_dir: str | Path = "rag_ingest_state",
        pair_output_dir: str | Path = "artifacts/pair_linkage_theorems",
        symbolic_output_dir: str | Path = "artifacts/symbolic_task_packets",
    ) -> None:
        self.market_db_path = Path(market_db_path)
        self.runs_dir = Path(runs_dir)
        self.scoreboards_dir = Path(scoreboards_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.work_dir = Path(work_dir)

        self.scoreboard = SpyVolatilityScoreboard(
            market_db_path=self.market_db_path,
            runs_dir=self.runs_dir,
            output_dir=self.scoreboards_dir,
            securities=SPY_VOLATILITY_CORE_SECURITIES,
        )
        self.runner = EmpiricalResearchRunner(
            work_dir=self.work_dir,
            market_db_path=self.market_db_path,
            output_dir=self.runs_dir,
            answer_mode="auto",
        )
        self.pair_engine = PairLinkageTheoremEngine(
            work_dir=self.work_dir,
            market_db_path=self.market_db_path,
            output_dir=pair_output_dir,
            symbolic_output_dir=symbolic_output_dir,
            benchmark_security="SPY US Equity",
        )

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def build_plan(self, max_actions: int = 8) -> Dict[str, Any]:
        sb = self.scoreboard.build_scoreboard()
        actions: List[DirectorAction] = []

        top_theorems = sb.get("top_theorems") or []
        top_runs = sb.get("top_runs") or []
        weak_lanes = sb.get("weak_lanes") or []

        actions.extend(self._promoted_theorem_actions(top_theorems))
        actions.extend(self._pair_linkage_refinement_actions(top_theorems))
        actions.extend(self._live_weak_lane_actions(weak_lanes))
        actions.extend(self._top_run_extension_actions(top_runs))

        actions = self._dedupe_actions(actions)
        actions.sort(key=lambda a: (-a.priority, a.category, a.task_name))
        actions = actions[: int(max_actions)]

        plan = {
            "created_at": self._utc_now(),
            "selected_actions": [a.as_dict() for a in actions],
            "scoreboard_snapshot": {
                "top_theorem": top_theorems[0] if top_theorems else None,
                "top_runs": top_runs[:5],
                "weak_lanes": weak_lanes[:10],
            },
        }
        return plan

    def persist_plan(self, plan: Dict[str, Any], stem: str = "spy_volatility_research_director_plan") -> Dict[str, Any]:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        json_path = self.output_dir / f"{stem}_{ts}.json"
        md_path = self.output_dir / f"{stem}_{ts}.md"

        json_path.write_text(json.dumps(plan, indent=2, default=str), encoding="utf-8")
        md_path.write_text(self._plan_markdown(plan), encoding="utf-8")

        return {
            "json_path": str(json_path),
            "markdown_path": str(md_path),
            "bytes_json": json_path.stat().st_size,
            "bytes_markdown": md_path.stat().st_size,
        }

    def build_and_persist_plan(self, max_actions: int = 8) -> Dict[str, Any]:
        plan = self.build_plan(max_actions=max_actions)
        files = self.persist_plan(plan)
        return {"plan": plan, "files": files}

    def execute_plan(self, max_actions: int = 5, *, persist_plan: bool = True) -> Dict[str, Any]:
        bundle = self.build_and_persist_plan(max_actions=max_actions) if persist_plan else {"plan": self.build_plan(max_actions=max_actions)}
        plan = bundle["plan"]

        runs: List[Dict[str, Any]] = []
        for action in plan.get("selected_actions", []):
            executed = self._execute_action(action)
            runs.append(executed)

        out = {
            "plan": plan,
            "plan_files": bundle.get("files"),
            "executed_runs": runs,
        }

        if persist_plan:
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            exec_path = self.output_dir / f"spy_volatility_research_director_execution_{ts}.json"
            exec_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
            out["execution_path"] = str(exec_path)

        return out

    # ------------------------------------------------------------------
    # execution routing
    # ------------------------------------------------------------------
    def _execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        category = str(action.get("category") or "")
        securities = list(action.get("securities") or [])

        if category in self.PAIR_ENGINE_CATEGORIES and len(securities) == 2:
            left, right = securities
            result = self.pair_engine.run_pair(left, right)
            return {
                "execution_mode": "pair_linkage_engine",
                "task_name": action.get("task_name"),
                "category": category,
                "securities": securities,
                "files": result.get("files"),
                "summary": {
                    "family_matched": result.get("family_matched"),
                    "attempt_count": result.get("attempt_count"),
                    "selected_title": result.get("selected_title"),
                    "symbolic_execution": result.get("symbolic_execution"),
                },
                "warnings": [],
            }

        task = self._action_to_task(action)
        run = self.runner.run_and_persist(task, stem=task.name)
        return {
            "execution_mode": "empirical_research_runner",
            "task_name": task.name,
            "category": category,
            "securities": list(task.securities),
            "files": run["files"],
            "summary": run["artifact"].get("summary", {}),
            "warnings": run["artifact"].get("warnings", []),
        }

    # ------------------------------------------------------------------
    # planning primitives
    # ------------------------------------------------------------------
    def _promoted_theorem_actions(self, top_theorems: Sequence[Dict[str, Any]]) -> List[DirectorAction]:
        actions: List[DirectorAction] = []

        for item in top_theorems[:5]:
            details = item.get("details") or {}
            status = str(details.get("status") or "")
            title = str(details.get("title") or item.get("name") or "")
            securities = list(details.get("securities") or [])
            symbolic_pass_rate = float(details.get("symbolic_pass_rate") or 0.0)

            if status != "symbolically_verified_candidate":
                continue
            if symbolic_pass_rate < 1.0:
                continue
            if "rough-variance scaling identification theorem" not in title.lower():
                continue

            anchor = securities[0] if securities else "SPY US Equity"
            for left, right in self.TARGET_PAIRS:
                if left != anchor:
                    continue
                actions.append(
                    DirectorAction(
                        priority=1.00,
                        category="exploit_promoted_theorem",
                        task_name=f"exploit_{self._slugify(left)}_{self._slugify(right)}_rough_variance_family",
                        rationale=(
                            "The top theorem family is already symbolically verified. "
                            "Extend it into a true pair-linkage theorem with the dedicated pair engine."
                        ),
                        securities=[left, right],
                        query=(
                            f"Starting from the symbolically verified rough-variance scaling theorem for {left}, "
                            f"propose a sharper theorem linking {left} and {right} through roughness transmission, "
                            f"variance scaling, and volatility-state dependence. "
                            f"State explicit empirical signatures, symbolic structure, and failure conditions."
                        ),
                    )
                )
        return actions

    def _pair_linkage_refinement_actions(self, top_theorems: Sequence[Dict[str, Any]]) -> List[DirectorAction]:
        actions: List[DirectorAction] = []

        for item in top_theorems[:12]:
            details = item.get("details") or {}
            title = str(details.get("title") or item.get("name") or "")
            status = str(details.get("status") or "")
            securities = list(details.get("securities") or [])
            symbolic_tasks = int(details.get("symbolic_tasks") or 0)

            if len(securities) < 2:
                continue
            if securities[0] != "SPY US Equity":
                continue
            if status not in {"speculative_candidate", "research_conjecture", "candidate"}:
                continue

            if "evidence-anchored structural conjecture" in title.lower():
                left, right = securities[:2]
                actions.append(
                    DirectorAction(
                        priority=0.90,
                        category="refine_pair_linkage",
                        task_name=f"refine_{self._slugify(left)}_{self._slugify(right)}_pair_linkage",
                        rationale=(
                            "This SPY-centered pair theorem is still generic. "
                            "Route it to the dedicated pair engine instead of the generic theorem lane."
                        ),
                        securities=[left, right],
                        query=(
                            f"Refine the theorem linking {left} and {right}. "
                            f"Replace generic structural-conjecture language with a sharper SPY/VIX-style theorem candidate "
                            f"about spot-volatility coupling, realized variance scaling, term-structure state, or tail-risk regime transmission."
                        ),
                    )
                )
            elif "rough-variance scaling identification theorem" in title.lower() and symbolic_tasks == 0:
                left, right = securities[:2]
                actions.append(
                    DirectorAction(
                        priority=0.82,
                        category="refine_pair_linkage",
                        task_name=f"recover_{self._slugify(left)}_{self._slugify(right)}_from_rough_hijack",
                        rationale=(
                            "This pair extension appears hijacked by the single-name roughness family. "
                            "Recover it through the dedicated pair engine."
                        ),
                        securities=[left, right],
                        query=(
                            f"Recover a true pair-linkage theorem for {left} and {right}. "
                            f"Do not return a single-name rough-variance scaling theorem."
                        ),
                    )
                )
        return actions

    def _live_weak_lane_actions(self, weak_lanes: Sequence[Dict[str, Any]]) -> List[DirectorAction]:
        actions: List[DirectorAction] = []

        for item in weak_lanes[:12]:
            details = item.get("details") or {}
            name = str(item.get("name") or "")
            securities = list(details.get("securities") or [])
            failed_flags = list(details.get("failed_flags") or [])
            stale_coverage = bool(details.get("warnings_stale_coverage"))
            path = details.get("path")

            if stale_coverage and failed_flags == ["coverage_ok"]:
                continue
            if not failed_flags:
                continue
            if not securities:
                continue

            query = self._infer_query_from_run_path(path)
            if not query:
                continue

            actions.append(
                DirectorAction(
                    priority=0.55,
                    category="rerun_live_weak_lane",
                    task_name=f"rerun_{self._slugify(name)}",
                    rationale="This lane still has a currently relevant failure and is not just stale pre-backfill noise.",
                    securities=securities,
                    query=query,
                )
            )

        return actions

    def _top_run_extension_actions(self, top_runs: Sequence[Dict[str, Any]]) -> List[DirectorAction]:
        actions: List[DirectorAction] = []
        seen_pairs = set()

        for item in top_runs[:6]:
            details = item.get("details") or {}
            securities = list(details.get("securities") or [])
            if len(securities) != 2:
                continue
            left, right = securities
            key = (left, right)
            if key in seen_pairs:
                continue
            seen_pairs.add(key)

            if left != "SPY US Equity":
                continue

            actions.append(
                DirectorAction(
                    priority=0.48,
                    category="extend_top_run",
                    task_name=f"extend_{self._slugify(left)}_{self._slugify(right)}",
                    rationale=(
                        "This pair already has a strong completed run. The next gain is a sharper pair-linkage theorem."
                    ),
                    securities=[left, right],
                    query=(
                        f"Using the strongest existing evidence for {left} and {right}, "
                        f"propose a stronger second-generation pair-linkage theorem candidate with explicit sign, scaling, or regime-shift content."
                    ),
                )
            )
        return actions

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _infer_query_from_run_path(self, path_str: Optional[str]) -> Optional[str]:
        if not path_str:
            return None
        path = Path(path_str)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
        task = payload.get("task") or {}
        return task.get("core_query")

    def _action_to_task(self, action: Dict[str, Any] | DirectorAction) -> ResearchTask:
        payload = action.as_dict() if hasattr(action, "as_dict") else dict(action)
        securities = list(payload.get("securities") or [])
        task_name = str(payload["task_name"])

        include_market_calibration = len(securities) >= 2
        include_market_memory = len(securities) >= 1
        include_theorem = True
        include_evidence = True

        return ResearchTask(
            name=task_name,
            core_query=str(payload["query"]),
            securities=securities,
            benchmark_security=str(payload.get("benchmark_security") or "SPY US Equity"),
            include_evidence=include_evidence,
            include_theorem=include_theorem,
            include_market_memory=include_market_memory,
            include_market_calibration=include_market_calibration,
            include_market_live_snapshot=False,
            acceptance_score=0.84,
        )

    def _dedupe_actions(self, actions: Sequence[DirectorAction]) -> List[DirectorAction]:
        best: Dict[tuple[str, tuple[str, ...]], DirectorAction] = {}
        for action in actions:
            key = (action.query, tuple(action.securities))
            prev = best.get(key)
            if prev is None or action.priority > prev.priority:
                best[key] = action
        return list(best.values())

    @staticmethod
    def _slugify(text: str) -> str:
        return re.sub(r"[^A-Za-z0-9]+", "_", str(text)).strip("_").lower() or "job"

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    def _plan_markdown(self, plan: Dict[str, Any]) -> str:
        lines: List[str] = [
            "# SPY Volatility Research Director Plan",
            "",
            f"- Created at: {plan.get('created_at')}",
            "",
            "## Selected actions",
        ]
        for action in plan.get("selected_actions", []):
            lines.append(f"### {action['task_name']}")
            lines.append(f"- Priority: {action['priority']}")
            lines.append(f"- Category: {action['category']}")
            lines.append(f"- Securities: {', '.join(action['securities'])}")
            lines.append(f"- Rationale: {action['rationale']}")
            lines.append(f"- Query: {action['query']}")
            lines.append("")
        return "\n".join(lines)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Direct the next SPY/VIX QuantAI research actions.")
    parser.add_argument("--market-db-path", default="data/market_history.sqlite")
    parser.add_argument("--runs-dir", default="artifacts/universe_research_runs")
    parser.add_argument("--scoreboards-dir", default="artifacts/scoreboards")
    parser.add_argument("--output-dir", default="artifacts/director_runs")
    parser.add_argument("--work-dir", default="rag_ingest_state")
    parser.add_argument("--pair-output-dir", default="artifacts/pair_linkage_theorems")
    parser.add_argument("--symbolic-output-dir", default="artifacts/symbolic_task_packets")
    parser.add_argument("--max-actions", type=int, default=8)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    director = SpyVolatilityResearchDirector(
        market_db_path=args.market_db_path,
        runs_dir=args.runs_dir,
        scoreboards_dir=args.scoreboards_dir,
        output_dir=args.output_dir,
        work_dir=args.work_dir,
        pair_output_dir=args.pair_output_dir,
        symbolic_output_dir=args.symbolic_output_dir,
    )

    result = director.execute_plan(max_actions=args.max_actions) if args.execute else director.build_and_persist_plan(max_actions=args.max_actions)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print("=" * 72)
        print("SPY Volatility Research Director")
        print("=" * 72)
        if args.execute:
            print(json.dumps({
                "n_runs": len(result.get("executed_runs", [])),
                "plan_files": result.get("plan_files"),
                "execution_path": result.get("execution_path"),
            }, indent=2, default=str))
        else:
            print(json.dumps({
                "n_actions": len(result["plan"].get("selected_actions", [])),
                "files": result.get("files"),
                "top_action": (result["plan"].get("selected_actions") or [None])[0],
            }, indent=2, default=str))
        print("=" * 72)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
