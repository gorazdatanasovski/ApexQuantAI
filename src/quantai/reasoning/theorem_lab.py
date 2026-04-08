from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from quantai.reasoning.conjecture_engine import ConjectureCandidate, ConjectureEngine, ConjecturePacket
from quantai.reasoning.feature_store import MarketFeatureStore
from quantai.reasoning.symbolic_solver import SymbolicLogicEngine
from quantai.reasoning.verification_engine import VerificationEngine, VerificationReport


@dataclass(frozen=True)
class TheoremTrial:
    round_index: int
    candidate_title: str
    candidate_statement: str
    verification: dict[str, Any]
    lab_score: float
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TheoremArtifact:
    title: str
    status: str
    statement: str
    assumptions: list[str]
    variables: dict[str, Any]
    motivation: str
    empirical_signature: list[str]
    symbolic_agenda: list[str]
    failure_conditions: list[str]
    evidence: list[dict[str, Any]] = field(default_factory=list)
    verification: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    score: float = 0.0
    next_actions: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def as_markdown(self) -> str:
        lines = [
            f"# {self.title}",
            "",
            f"**Status:** {self.status}",
            f"**Score:** {self.score:.3f}",
            "",
            "## Statement",
            self.statement,
            "",
            "## Assumptions",
        ]
        lines.extend([f"- {x}" for x in self.assumptions] or ["- None recorded"])
        lines.extend(["", "## Variables"])
        lines.extend([f"- **{k}**: {v}" for k, v in self.variables.items()] or ["- None recorded"])
        lines.extend(["", "## Empirical signature"])
        lines.extend([f"- {x}" for x in self.empirical_signature] or ["- None recorded"])
        lines.extend(["", "## Symbolic agenda"])
        lines.extend([f"- {x}" for x in self.symbolic_agenda] or ["- None recorded"])
        lines.extend(["", "## Failure conditions"])
        lines.extend([f"- {x}" for x in self.failure_conditions] or ["- None recorded"])
        lines.extend(["", "## Next actions"])
        lines.extend([f"- {x}" for x in self.next_actions] or ["- None recorded"])
        return "\n".join(lines)


@dataclass(frozen=True)
class TheoremLabResult:
    query: str
    problem_kind: str
    topics: list[str]
    selected: TheoremArtifact
    trials: list[TheoremTrial]
    packet_metadata: dict[str, Any] = field(default_factory=dict)
    lab_metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "problem_kind": self.problem_kind,
            "topics": list(self.topics),
            "selected": self.selected.as_dict(),
            "trials": [t.as_dict() for t in self.trials],
            "packet_metadata": dict(self.packet_metadata),
            "lab_metadata": dict(self.lab_metadata),
        }


class TheoremLab:
    _EVIDENCE_ONLY_KINDS = {"definition", "exact_statement", "theorem_statement"}

    def __init__(
        self,
        db_path: str | Path = "data/market_history.sqlite",
        feature_store: Optional[MarketFeatureStore] = None,
        conjecture_engine: Optional[ConjectureEngine] = None,
        verification_engine: Optional[VerificationEngine] = None,
        symbolic_engine: Optional[SymbolicLogicEngine] = None,
    ):
        self.db_path = Path(db_path)
        self.feature_store = feature_store or MarketFeatureStore(self.db_path)
        self.conjecture_engine = conjecture_engine or ConjectureEngine(feature_store=self.feature_store)
        self.verification_engine = verification_engine or VerificationEngine(db_path=self.db_path)
        self.symbolic_engine = symbolic_engine or SymbolicLogicEngine()

    def close(self) -> None:
        self.verification_engine.close()
        if hasattr(self.feature_store, "close"):
            self.feature_store.close()

    def __enter__(self) -> "TheoremLab":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def run(
        self,
        query: str,
        *,
        text_hits: Sequence[Any] | None = None,
        securities: Sequence[str] | None = None,
        benchmark_security: str | None = None,
        empirical_summary: Mapping[str, Any] | None = None,
        max_candidates: int = 3,
        refinement_rounds: int = 2,
        acceptance_score: float = 0.80,
    ) -> TheoremLabResult:
        securities = list(securities or [])
        market_summary = dict(empirical_summary or self._build_empirical_summary(securities))
        packet = self.conjecture_engine.build_packet(
            query=query,
            text_hits=text_hits or [],
            securities=securities,
            empirical_summary=market_summary,
            max_candidates=max_candidates,
        )

        trials: list[TheoremTrial] = []
        best_artifact: Optional[TheoremArtifact] = None
        best_score = float("-inf")

        for candidate in packet.candidates:
            artifact, candidate_trials = self._run_candidate_rounds(
                candidate=candidate,
                problem_kind=packet.problem_kind,
                topics=packet.topics,
                securities=securities,
                benchmark_security=benchmark_security,
                refinement_rounds=refinement_rounds,
                acceptance_score=acceptance_score,
            )
            trials.extend(candidate_trials)
            if artifact.score > best_score:
                best_score = artifact.score
                best_artifact = artifact

        if best_artifact is None:
            best_artifact = TheoremArtifact(
                title="No viable theorem candidate",
                status="unverified",
                statement="No theorem candidate could be assembled from the current evidence.",
                assumptions=[],
                variables={},
                motivation="The current evidence packet did not yield a usable candidate.",
                empirical_signature=[],
                symbolic_agenda=[],
                failure_conditions=["Insufficient evidence or malformed candidate packet."],
                evidence=[],
                verification={},
                tags=["empty_result"],
                score=0.0,
                next_actions=[
                    "Provide stronger book excerpts or exact theorem statements.",
                    "Attach one or more securities so empirical falsification can run.",
                ],
            )

        lab_metadata = {
            "db_path": str(self.db_path),
            "n_candidates": len(packet.candidates),
            "n_trials": len(trials),
            "securities": securities,
            "benchmark_security": benchmark_security,
            "acceptance_score": float(acceptance_score),
        }
        return TheoremLabResult(
            query=str(query),
            problem_kind=str(packet.problem_kind),
            topics=list(packet.topics),
            selected=best_artifact,
            trials=trials,
            packet_metadata=dict(packet.metadata),
            lab_metadata=lab_metadata,
        )

    def _run_candidate_rounds(
        self,
        *,
        candidate: ConjectureCandidate,
        problem_kind: str,
        topics: Sequence[str],
        securities: Sequence[str],
        benchmark_security: str | None,
        refinement_rounds: int,
        acceptance_score: float,
    ) -> tuple[TheoremArtifact, list[TheoremTrial]]:
        security = securities[0] if securities else None
        working = self._candidate_to_mapping(candidate, problem_kind=problem_kind, topics=topics)
        candidate_trials: list[TheoremTrial] = []

        for round_index in range(max(1, refinement_rounds + 1)):
            report = self.verification_engine.verify_candidate(
                working,
                security=security,
                benchmark_security=benchmark_security,
            )
            lab_score = self._lab_score(working, report)
            notes = self._build_round_notes(working, report, problem_kind=problem_kind)
            candidate_trials.append(
                TheoremTrial(
                    round_index=round_index,
                    candidate_title=str(working.get("title", "Untitled candidate")),
                    candidate_statement=str(working.get("statement", "")),
                    verification=report.as_dict(),
                    lab_score=lab_score,
                    notes=notes,
                )
            )
            if self._is_accepted(report, lab_score, acceptance_score=acceptance_score):
                break
            if round_index >= refinement_rounds:
                break
            working = self._refine_candidate(working, report, problem_kind=problem_kind, topics=topics, security=security)

        artifact = self._build_artifact(working, candidate, candidate_trials[-1].verification, candidate_trials[-1].lab_score)
        return artifact, candidate_trials

    def _build_empirical_summary(self, securities: Sequence[str]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for security in securities:
            try:
                out[str(security)] = self.feature_store.summarize_security(str(security))
            except Exception as exc:
                out[str(security)] = {"security": str(security), "error": str(exc)}
        return out

    def _candidate_to_mapping(self, candidate: ConjectureCandidate, *, problem_kind: str, topics: Sequence[str]) -> dict[str, Any]:
        payload = {
            "title": candidate.title,
            "statement": candidate.statement,
            "theorem_statement": candidate.statement,
            "assumptions": list(candidate.assumptions),
            "variables": dict(candidate.variables),
            "motivation": candidate.motivation,
            "empirical_tests": self._normalize_empirical_tests(candidate.empirical_tests, topics=topics),
            "symbolic_tasks": self._normalize_symbolic_tasks(candidate.symbolic_tasks),
            "failure_conditions": list(candidate.failure_conditions),
            "tags": list(candidate.tags),
            "confidence": float(candidate.confidence),
            "problem_kind": str(problem_kind),
            "evidence": [e.as_dict() for e in candidate.evidence],
        }
        if problem_kind in self._EVIDENCE_ONLY_KINDS:
            payload["symbolic_tasks"] = []
        return payload

    def _normalize_empirical_tests(self, tests: Sequence[Any], *, topics: Sequence[str]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for raw in tests:
            if isinstance(raw, Mapping) and raw.get("kind"):
                out.append(dict(raw))
                continue
            text = str(raw).strip().lower()
            if not text:
                continue
            if any(k in text for k in ["hurst", "scal", "roughness"]):
                out.append({"kind": "hurst_persistence", "name": text})
            elif any(k in text for k in ["cluster", "volatility", "realized"]):
                out.append({"kind": "vol_clustering", "name": text})
            elif any(k in text for k in ["mean reversion", "ou", "reversion"]):
                out.append({"kind": "mean_reversion", "name": text})
            elif any(k in text for k in ["jump", "bipower"]):
                out.append({"kind": "jump_share", "name": text})
        if not out:
            topic_set = {str(t) for t in topics}
            if "rough_volatility" in topic_set:
                out.extend([
                    {"kind": "hurst_persistence", "name": "default_hurst_persistence"},
                    {"kind": "vol_clustering", "name": "default_vol_clustering"},
                ])
            else:
                out.append({"kind": "vol_clustering", "name": "default_vol_clustering"})
        return out

    def _normalize_symbolic_tasks(self, tasks: Sequence[Any]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for raw in tasks:
            if isinstance(raw, Mapping) and raw.get("kind"):
                out.append(dict(raw))
        return out

    def _refine_candidate(self, candidate: Mapping[str, Any], report: VerificationReport, *, problem_kind: str, topics: Sequence[str], security: str | None) -> dict[str, Any]:
        refined = dict(candidate)
        assumptions = list(refined.get("assumptions") or [])
        failures = list(refined.get("failure_conditions") or [])
        for suggestion in report.recommended_refinements:
            if suggestion not in failures:
                failures.append(suggestion)
        if security:
            anchor = f"Empirical scope anchored to {security}."
            if anchor not in assumptions:
                assumptions.append(anchor)
        if report.verdict in {"weak_or_incomplete", "rejected_or_unverified"}:
            stmt = str(refined.get("statement") or "")
            if not stmt.lower().startswith("conjecture:"):
                refined["statement"] = "Conjecture: " + stmt
        refined["assumptions"] = self._dedupe(assumptions)
        refined["failure_conditions"] = self._dedupe(failures)
        return refined

    def _build_artifact(self, candidate_mapping: Mapping[str, Any], original_candidate: ConjectureCandidate, verification_payload: Mapping[str, Any], lab_score: float) -> TheoremArtifact:
        verdict = str(verification_payload.get("verdict", "unverified"))
        status = self._artifact_status(verdict, lab_score)
        next_actions = self._next_actions(verification_payload)
        empirical_signature = [str(x.get("name") or x.get("kind") or x) for x in (candidate_mapping.get("empirical_tests") or [])]
        return TheoremArtifact(
            title=str(candidate_mapping.get("title") or original_candidate.title),
            status=status,
            statement=str(candidate_mapping.get("statement") or original_candidate.statement),
            assumptions=list(candidate_mapping.get("assumptions") or original_candidate.assumptions),
            variables=dict(candidate_mapping.get("variables") or original_candidate.variables),
            motivation=str(candidate_mapping.get("motivation") or original_candidate.motivation),
            empirical_signature=empirical_signature,
            symbolic_agenda=[str(x) for x in original_candidate.symbolic_tasks],
            failure_conditions=list(candidate_mapping.get("failure_conditions") or original_candidate.failure_conditions),
            evidence=[e.as_dict() for e in original_candidate.evidence],
            verification=dict(verification_payload),
            tags=list(candidate_mapping.get("tags") or original_candidate.tags),
            score=float(lab_score),
            next_actions=next_actions,
        )

    def _lab_score(self, candidate: Mapping[str, Any], report: VerificationReport) -> float:
        base_conf = float(candidate.get("confidence", 0.0))
        warning_penalty = 0.03 * len(report.warnings)
        refine_penalty = 0.015 * len(report.recommended_refinements)
        score = 0.40 * base_conf + 0.60 * float(report.overall_score) - warning_penalty - refine_penalty
        return float(max(0.0, min(1.0, score)))

    def _is_accepted(self, report: VerificationReport, lab_score: float, *, acceptance_score: float) -> bool:
        return report.verdict == "provisionally_supported" or lab_score >= float(acceptance_score)

    def _artifact_status(self, verdict: str, score: float) -> str:
        if verdict == "provisionally_supported" or score >= 0.85:
            return "provisional_theorem"
        if verdict == "partially_supported" or score >= 0.65:
            return "research_conjecture"
        if verdict == "weak_or_incomplete" or score >= 0.40:
            return "speculative_candidate"
        return "unverified_hypothesis"

    def _next_actions(self, verification_payload: Mapping[str, Any]) -> list[str]:
        actions = list(verification_payload.get("recommended_refinements") or [])
        verdict = str(verification_payload.get("verdict") or "")
        if verdict != "provisionally_supported":
            actions.append("Collect stronger exact excerpts from the book-memory layer.")
            actions.append("Add a formal symbolic derivation or export the candidate to Lean for proof work.")
        return self._dedupe(actions)

    def _build_round_notes(self, candidate: Mapping[str, Any], report: VerificationReport, *, problem_kind: str) -> list[str]:
        notes = [f"Problem kind: {problem_kind}", f"Verdict: {report.verdict}"]
        if not candidate.get("symbolic_tasks"):
            notes.append("No executable symbolic tasks were available in this round; score is driven mainly by empirical evidence.")
        if report.warnings:
            notes.extend([f"Warning: {w}" for w in report.warnings])
        return self._dedupe(notes)

    @staticmethod
    def _dedupe(items: Sequence[str]) -> list[str]:
        seen = set()
        out: list[str] = []
        for item in items:
            text = str(item).strip()
            if not text or text in seen:
                continue
            seen.add(text)
            out.append(text)
        return out


__all__ = ["TheoremArtifact", "TheoremLab", "TheoremLabResult", "TheoremTrial"]
