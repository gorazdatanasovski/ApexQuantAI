from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from quantai.reasoning.engine import ApexReasoningCore
from quantai.reasoning.spy_volatility_universe import SPY_VOLATILITY_CORE_SECURITIES
from quantai.reasoning.symbolic_solver import SymbolicLogicEngine
from quantai.reasoning.theorem_symbolic_task_builder import TheoremSymbolicTaskBuilder


@dataclass(frozen=True)
class TheoremArtifact:
    entry_id: str
    title: str
    status: str
    native_score: float
    securities: List[str]
    statement: str
    assumptions: List[str]
    tags: List[str]
    updated_at: str
    metadata: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RefinementPlanItem:
    priority: float
    entry_id: str
    title: str
    securities: List[str]
    refinement_query: str
    rationale: str
    target_family: str

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RefinementRun:
    plan: Dict[str, Any]
    result: Dict[str, Any]
    symbolic_packet: Optional[Dict[str, Any]]
    symbolic_execution: Optional[Dict[str, Any]]
    persisted_files: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TheoremRefinementEngine:
    """
    Refine existing SPY/VIX theorem artifacts into sharper candidates.

    Superior version:
    - reads theorem_registry
    - ranks the relevant weakly verified SPY/VIX artifacts
    - reruns theorem mode or formal mode with sharper instructions
    - automatically builds symbolic task packets from the refined artifact
    - executes those symbolic tasks through SymbolicLogicEngine
    - persists both theorem refinement output and symbolic verification output

    Why this matters:
    - current theorem quality is still bottlenecked by "no symbolic checks supplied"
    - this engine closes that loop by making symbolic work a first-class part
      of the refinement batch instead of a manual step
    """

    DEFAULT_TARGET_STATUSES = (
        "speculative_candidate",
        "unverified_hypothesis",
        "candidate",
        "draft",
        "proposed",
        "research_conjecture",
    )

    def __init__(
        self,
        work_dir: str | Path = "rag_ingest_state",
        market_db_path: str | Path = "data/market_history.sqlite",
        output_dir: str | Path = "artifacts/theorem_refinements",
        symbolic_output_dir: str | Path = "artifacts/symbolic_task_packets",
        benchmark_security: str = "SPY US Equity",
    ) -> None:
        self.work_dir = Path(work_dir)
        self.market_db_path = Path(market_db_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.symbolic_output_dir = Path(symbolic_output_dir)
        self.symbolic_output_dir.mkdir(parents=True, exist_ok=True)
        self.benchmark_security = benchmark_security

        self.symbolic_builder = TheoremSymbolicTaskBuilder(
            market_db_path=self.market_db_path,
            output_dir=self.symbolic_output_dir,
        )

    # ------------------------------------------------------------------
    # registry loading
    # ------------------------------------------------------------------
    def load_registry_artifacts(self, limit: int = 200) -> List[TheoremArtifact]:
        if not self.market_db_path.exists():
            return []

        conn = sqlite3.connect(str(self.market_db_path))
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                """
                SELECT entry_id, title, status, score, statement,
                       assumptions_json, tags_json, securities_json,
                       updated_at, metadata_json
                FROM theorem_registry
                ORDER BY updated_at DESC, score DESC
                LIMIT ?
                """,
                [int(limit)],
            ).fetchall()
        finally:
            conn.close()

        artifacts: List[TheoremArtifact] = []
        for row in rows:
            artifacts.append(
                TheoremArtifact(
                    entry_id=str(row["entry_id"]),
                    title=str(row["title"]),
                    status=str(row["status"]),
                    native_score=float(row["score"] or 0.0),
                    securities=self._json_load(row["securities_json"], default=[]),
                    statement=str(row["statement"] or ""),
                    assumptions=self._json_load(row["assumptions_json"], default=[]),
                    tags=self._json_load(row["tags_json"], default=[]),
                    updated_at=str(row["updated_at"] or ""),
                    metadata=self._json_load(row["metadata_json"], default={}),
                )
            )
        return artifacts

    # ------------------------------------------------------------------
    # planning
    # ------------------------------------------------------------------
    def build_plan(
        self,
        *,
        max_items: int = 8,
        target_statuses: Sequence[str] | None = None,
    ) -> Dict[str, Any]:
        target_statuses = tuple(target_statuses or self.DEFAULT_TARGET_STATUSES)
        artifacts = self.load_registry_artifacts(limit=300)

        relevant: List[TheoremArtifact] = []
        for art in artifacts:
            if art.status not in target_statuses:
                continue
            if not self._is_relevant_security_set(art.securities):
                continue
            relevant.append(art)

        deduped = self._dedupe_by_family(relevant)
        planned: List[RefinementPlanItem] = []
        for art in deduped:
            query, rationale = self._build_refinement_query(art)
            priority = self._priority_score(art)
            family = self._infer_family(art)
            planned.append(
                RefinementPlanItem(
                    priority=priority,
                    entry_id=art.entry_id,
                    title=art.title,
                    securities=list(art.securities),
                    refinement_query=query,
                    rationale=rationale,
                    target_family=family,
                )
            )

        planned.sort(key=lambda x: x.priority, reverse=True)
        planned = planned[: int(max_items)]

        return {
            "created_at": self._utc_now(),
            "target_statuses": list(target_statuses),
            "n_registry_artifacts": len(artifacts),
            "n_relevant_artifacts": len(relevant),
            "selected": [p.as_dict() for p in planned],
        }

    def _priority_score(self, art: TheoremArtifact) -> float:
        family_bonus = 0.0
        title_lower = art.title.lower()
        if "rough-variance scaling identification theorem" in title_lower:
            family_bonus += 0.40
        if "evidence-anchored structural conjecture" in title_lower:
            family_bonus += 0.25
        if self.benchmark_security in art.securities:
            family_bonus += 0.20
        if any(sec in {"VIX Index", "VVIX Index", "VIX3M Index", "SKEW Index", "SPX Index"} for sec in art.securities):
            family_bonus += 0.18
        status_bonus = {
            "speculative_candidate": 0.32,
            "unverified_hypothesis": 0.24,
            "research_conjecture": 0.22,
            "candidate": 0.18,
            "draft": 0.10,
            "proposed": 0.10,
        }.get(art.status, 0.0)
        return 0.5 * art.native_score + family_bonus + status_bonus

    def _build_refinement_query(self, art: TheoremArtifact) -> tuple[str, str]:
        title_lower = art.title.lower()
        securities = list(art.securities)
        primary = securities[0] if securities else self.benchmark_security

        if "rough-variance scaling identification theorem" in title_lower:
            query = (
                f"Refine the rough-variance scaling theorem for {primary}. "
                f"Replace generic conjectural phrasing with a sharper theorem candidate. "
                f"Tighten the assumptions on the Volterra kernel singularity and roughness exponent. "
                f"State the observable realized-variance proxy precisely, connect it to the Bloomberg feature panel, "
                f"list explicit empirical signatures and failure conditions, "
                f"and produce a theorem whose symbolic structure can be checked by explicit algebraic identities or nonnegativity constraints. "
                f"Make the theorem specific to {primary}, not a generic placeholder."
            )
            rationale = "Strongest current theorem family; now needs symbolic checkability, tighter assumptions, and clearer observables."
            return query, rationale

        if "evidence-anchored structural conjecture" in title_lower and len(securities) >= 2:
            left, right = securities[:2]
            query = (
                f"Refine the SPY-volatility linkage theorem for {left} and {right}. "
                f"Replace generic structural language with a sharper theorem candidate about spot-volatility coupling, "
                f"roughness transmission, regime dependence, or term-structure state. "
                f"State the core object, the sign or monotonicity prediction if supported, the empirical Bloomberg feature signature, "
                f"explicit failure conditions, and a symbolic structure that can be checked through covariance symmetry, quadratic-form nonnegativity, "
                f"or regime-difference identities. Avoid generic placeholder language."
            )
            rationale = "Pair-linkage theorem exists but is still too generic; it should become a real SPY/VIX-specific theorem candidate with symbolic structure."
            return query, rationale

        if len(securities) >= 2:
            left, right = securities[:2]
            query = (
                f"Refine the theorem linking {left} and {right}. "
                f"Sharpen the assumptions, make the statement SPY/VIX-specific, identify the precise empirical signature, "
                f"explicit failure conditions, and a symbolic form that can be checked directly."
            )
            rationale = "Relevant pair artifact requires more specific structure, clearer empirical implications, and symbolic checkability."
            return query, rationale

        query = (
            f"Refine the theorem candidate for {primary}. "
            f"Tighten the assumptions, make the statement precise, add explicit empirical signatures and failure conditions, "
            f"and expose a symbolic form that can be checked directly."
        )
        rationale = "Single-name artifact requires sharper assumptions, more explicit empirical testability, and symbolic structure."
        return query, rationale

    def _dedupe_by_family(self, artifacts: Sequence[TheoremArtifact]) -> List[TheoremArtifact]:
        best: Dict[tuple[str, tuple[str, ...]], TheoremArtifact] = {}
        for art in artifacts:
            key = (art.title.strip().lower(), tuple(sorted(art.securities)))
            prev = best.get(key)
            if prev is None or art.native_score > prev.native_score:
                best[key] = art
        return list(best.values())

    def _infer_family(self, art: TheoremArtifact) -> str:
        text = f"{art.title}\n{art.statement}".lower()
        if "rough-variance scaling identification theorem" in text or "delta^(2h)" in text or "delta**(2*h)" in text:
            return "rough_variance_scaling"
        if len(art.securities) >= 2 or "spot-volatility" in text or "linking" in text:
            return "spot_vol_linkage"
        return "generic"

    # ------------------------------------------------------------------
    # execution
    # ------------------------------------------------------------------
    def refine_plan(
        self,
        *,
        max_items: int = 5,
        target_statuses: Sequence[str] | None = None,
        formal: bool = False,
        acceptance_score: float = 0.84,
        execute_symbolics: bool = True,
    ) -> Dict[str, Any]:
        plan = self.build_plan(max_items=max_items, target_statuses=target_statuses)
        selected = plan.get("selected") or []

        runs: List[Dict[str, Any]] = []
        for item in selected:
            run = self._execute_plan_item(
                item,
                formal=formal,
                acceptance_score=acceptance_score,
                execute_symbolics=execute_symbolics,
            )
            runs.append(run.as_dict())

        payload = {
            "plan": plan,
            "formal": bool(formal),
            "acceptance_score": float(acceptance_score),
            "execute_symbolics": bool(execute_symbolics),
            "runs": runs,
        }
        files = self._persist_payload(payload)
        return {"payload": payload, "files": files}

    def _execute_plan_item(
        self,
        item: Dict[str, Any],
        *,
        formal: bool,
        acceptance_score: float,
        execute_symbolics: bool,
    ) -> RefinementRun:
        securities = list(item.get("securities") or [])
        query = str(item["refinement_query"])

        core = ApexReasoningCore(
            work_dir=self.work_dir,
            market_db_path=self.market_db_path,
            answer_mode="auto",
        )
        try:
            result = core.answer(
                query,
                mode="formal" if formal else "theorem",
                securities=securities,
                benchmark_security=self.benchmark_security,
                acceptance_score=float(acceptance_score),
            )
        finally:
            core.close()

        selected_artifact = self._extract_selected_artifact(result)
        symbolic_packet = None
        symbolic_execution = None

        if selected_artifact is not None:
            packet = self.symbolic_builder.build_from_artifact(selected_artifact)
            packet_files = self.symbolic_builder.persist_packet(
                packet,
                stem=f"{self._slugify(item.get('title', 'refinement'))}_{self._slugify(packet.family)}",
            )
            symbolic_packet = {
                "packet": packet.as_dict(),
                "files": packet_files,
            }

            if execute_symbolics:
                symbolic_engine = SymbolicLogicEngine()
                symbolic_execution = self.symbolic_builder.execute_packet(
                    packet,
                    symbolic_engine=symbolic_engine,
                )

        enriched_result = dict(result)
        if symbolic_packet is not None:
            enriched_result["symbolic_packet"] = symbolic_packet
        if symbolic_execution is not None:
            enriched_result["symbolic_execution"] = symbolic_execution

        persisted = self._persist_single_run(item, enriched_result)
        return RefinementRun(
            plan=dict(item),
            result=enriched_result,
            symbolic_packet=symbolic_packet,
            symbolic_execution=symbolic_execution,
            persisted_files=persisted,
        )

    def _extract_selected_artifact(self, result: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
        theorem_result = result.get("theorem_result")
        if isinstance(theorem_result, Mapping):
            selected = theorem_result.get("selected")
            if isinstance(selected, Mapping):
                payload = dict(selected)
                payload["securities"] = result.get("market_summary", {}).keys() if isinstance(result.get("market_summary"), Mapping) else []
                return {
                    "title": payload.get("title"),
                    "statement": payload.get("statement"),
                    "assumptions": payload.get("assumptions") or [],
                    "securities": list(payload.get("securities") or []),
                    "tags": payload.get("tags") or [],
                }

        title = result.get("selected_title")
        if title:
            return {
                "title": title,
                "statement": str(result.get("response") or ""),
                "assumptions": [],
                "securities": [],
                "tags": [],
            }
        return None

    # ------------------------------------------------------------------
    # persistence
    # ------------------------------------------------------------------
    def _persist_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        json_path = self.output_dir / f"theorem_refinement_batch_{ts}.json"
        md_path = self.output_dir / f"theorem_refinement_batch_{ts}.md"

        json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        md_path.write_text(self._payload_markdown(payload), encoding="utf-8")

        return {
            "json_path": str(json_path),
            "markdown_path": str(md_path),
            "bytes_json": json_path.stat().st_size,
            "bytes_markdown": md_path.stat().st_size,
        }

    def _persist_single_run(self, item: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        stem = self._slugify(item.get("title") or "refinement")
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        json_path = self.output_dir / f"{stem}_{ts}.json"
        md_path = self.output_dir / f"{stem}_{ts}.md"

        payload = {"plan": item, "result": result}
        json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        md_path.write_text(self._single_run_markdown(payload), encoding="utf-8")

        return {
            "json_path": str(json_path),
            "markdown_path": str(md_path),
            "bytes_json": json_path.stat().st_size,
            "bytes_markdown": md_path.stat().st_size,
        }

    def _payload_markdown(self, payload: Dict[str, Any]) -> str:
        lines: List[str] = [
            "# Theorem Refinement Batch",
            "",
            f"- Created at: {payload['plan'].get('created_at')}",
            f"- Formal mode: {payload.get('formal')}",
            f"- Acceptance score: {payload.get('acceptance_score')}",
            f"- Execute symbolics: {payload.get('execute_symbolics')}",
            "",
            "## Selected refinements",
        ]
        for item in payload["plan"].get("selected", []):
            lines.append(f"### {item['title']}")
            lines.append(f"- Priority: {item['priority']}")
            lines.append(f"- Family: {item.get('target_family')}")
            lines.append(f"- Securities: {', '.join(item['securities'])}")
            lines.append(f"- Rationale: {item['rationale']}")
            lines.append(f"- Query: {item['refinement_query']}")
            lines.append("")
        lines.append("## Runs")
        for run in payload.get("runs", []):
            result = run.get("result", {})
            sym = run.get("symbolic_execution") or {}
            lines.append(f"### {run['plan']['title']}")
            lines.append(f"- Mode used: {result.get('mode_used')}")
            lines.append(f"- Selected theorem title: {result.get('selected_title')}")
            lines.append(f"- Registry: {json.dumps(result.get('theorem_registry'), default=str)}")
            if sym:
                lines.append(f"- Symbolic tasks: {sym.get('n_tasks')}")
                lines.append(f"- Symbolic pass count: {sym.get('n_ok')}")
                lines.append(f"- Symbolic fail count: {sym.get('n_fail')}")
            lines.append("")
        return "\n".join(lines)

    def _single_run_markdown(self, payload: Dict[str, Any]) -> str:
        plan = payload["plan"]
        result = payload["result"]
        symbolic_execution = result.get("symbolic_execution")
        lines = [
            f"# Refinement: {plan.get('title')}",
            "",
            f"- Securities: {', '.join(plan.get('securities', []))}",
            f"- Family: {plan.get('target_family')}",
            f"- Rationale: {plan.get('rationale')}",
            f"- Query: {plan.get('refinement_query')}",
            "",
            "## Result",
            "```json",
            json.dumps(result, indent=2, default=str)[:20000],
            "```",
        ]
        if symbolic_execution:
            lines.extend([
                "",
                "## Symbolic execution summary",
                "```json",
                json.dumps(symbolic_execution, indent=2, default=str)[:12000],
                "```",
            ])
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _is_relevant_security_set(self, securities: Sequence[str]) -> bool:
        target = set(SPY_VOLATILITY_CORE_SECURITIES)
        secset = {str(x) for x in securities}
        return bool(target & secset)

    @staticmethod
    def _json_load(value: Any, default: Any) -> Any:
        try:
            if value is None:
                return default
            return json.loads(value)
        except Exception:
            return default

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    @staticmethod
    def _slugify(text: str) -> str:
        import re
        text = re.sub(r"[^A-Za-z0-9]+", "_", str(text)).strip("_").lower()
        return text or "refinement"


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Refine SPY/VIX theorem artifacts.")
    parser.add_argument("--work-dir", default="rag_ingest_state")
    parser.add_argument("--market-db-path", default="data/market_history.sqlite")
    parser.add_argument("--output-dir", default="artifacts/theorem_refinements")
    parser.add_argument("--symbolic-output-dir", default="artifacts/symbolic_task_packets")
    parser.add_argument("--max-items", type=int, default=5)
    parser.add_argument("--formal", action="store_true")
    parser.add_argument("--acceptance-score", type=float, default=0.84)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--skip-symbolics", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    engine = TheoremRefinementEngine(
        work_dir=args.work_dir,
        market_db_path=args.market_db_path,
        output_dir=args.output_dir,
        symbolic_output_dir=args.symbolic_output_dir,
    )

    if args.execute:
        result = engine.refine_plan(
            max_items=args.max_items,
            formal=bool(args.formal),
            acceptance_score=float(args.acceptance_score),
            execute_symbolics=not bool(args.skip_symbolics),
        )
    else:
        result = {"plan": engine.build_plan(max_items=args.max_items)}

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print("=" * 72)
        print("Theorem Refinement Engine")
        print("=" * 72)
        if args.execute:
            print(json.dumps({
                "n_runs": len(result["payload"].get("runs", [])),
                "files": result.get("files"),
                "top_refinement": (result["payload"]["plan"].get("selected") or [None])[0],
            }, indent=2, default=str))
        else:
            print(json.dumps({
                "n_selected": len(result["plan"].get("selected", [])),
                "top_refinement": (result["plan"].get("selected") or [None])[0],
            }, indent=2, default=str))
        print("=" * 72)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
