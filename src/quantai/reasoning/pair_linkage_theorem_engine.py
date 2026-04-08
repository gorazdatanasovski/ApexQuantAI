from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from quantai.reasoning.engine import ApexReasoningCore
from quantai.reasoning.symbolic_solver import SymbolicLogicEngine
from quantai.reasoning.theorem_symbolic_task_builder import TheoremSymbolicTaskBuilder


@dataclass(frozen=True)
class PairLinkageRunResult:
    left_security: str
    right_security: str
    family_matched: bool
    attempt_count: int
    selected_title: Optional[str]
    theorem_registry: Optional[Dict[str, Any]]
    symbolic_execution: Optional[Dict[str, Any]]
    result: Dict[str, Any]
    files: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PairLinkageTheoremEngine:
    """
    Dedicated SPY/VIX pair-linkage theorem generator.

    Why this exists:
    - your latest director run shows many pair jobs still collapse back into the
      rough-variance scaling family instead of producing true pair-linkage theorems
    - this engine forces pair-aware prompts and rejects family-mismatched outputs
    - it also runs symbolic task generation/execution for the accepted pair theorem

    Main behavior:
    1. build a strict pair-linkage prompt
    2. run theorem mode
    3. inspect the selected theorem title / response family
    4. retry with a stronger anti-collapse prompt if it drifted into a single-name roughness theorem
    5. persist the accepted run and symbolic packet
    """

    TARGET_PAIR_TERMS = (
        "spot-volatility coupling",
        "variance scaling transmission",
        "regime dependence",
        "term-structure state",
        "tail-risk state",
        "cross-object linkage",
    )

    def __init__(
        self,
        work_dir: str | Path = "rag_ingest_state",
        market_db_path: str | Path = "data/market_history.sqlite",
        output_dir: str | Path = "artifacts/pair_linkage_theorems",
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
    # public API
    # ------------------------------------------------------------------
    def run_pair(
        self,
        left_security: str,
        right_security: str,
        *,
        acceptance_score: float = 0.84,
        max_attempts: int = 2,
    ) -> Dict[str, Any]:
        attempts: List[Dict[str, Any]] = []
        accepted: Optional[Dict[str, Any]] = None
        family_matched = False

        for attempt in range(1, max_attempts + 1):
            prompt = self._build_prompt(left_security, right_security, attempt=attempt)
            out = self._answer_pair_prompt(
                prompt,
                left_security=left_security,
                right_security=right_security,
                acceptance_score=acceptance_score,
            )
            attempts.append(
                {
                    "attempt": attempt,
                    "prompt": prompt,
                    "selected_title": out.get("selected_title"),
                    "theorem_registry": out.get("theorem_registry"),
                    "mode_used": out.get("mode_used"),
                }
            )

            if self._is_pair_family_match(out, left_security, right_security):
                accepted = out
                family_matched = True
                break

            # keep the best last output even if mismatched
            accepted = out

        symbolic_execution = None
        symbolic_packet = None
        if accepted is not None:
            artifact = self._extract_artifact(accepted, left_security, right_security)
            if artifact is not None:
                packet = self.symbolic_builder.build_from_artifact(artifact)
                packet_files = self.symbolic_builder.persist_packet(
                    packet,
                    stem=f"{self._slugify(left_security)}_{self._slugify(right_security)}_pair_linkage",
                )
                symbolic_packet = {
                    "packet": packet.as_dict(),
                    "files": packet_files,
                }
                symbolic_execution = self.symbolic_builder.execute_packet(
                    packet,
                    symbolic_engine=SymbolicLogicEngine(),
                )

        payload = {
            "created_at": self._utc_now(),
            "left_security": left_security,
            "right_security": right_security,
            "family_matched": family_matched,
            "attempts": attempts,
            "accepted_result": accepted,
            "symbolic_packet": symbolic_packet,
            "symbolic_execution": symbolic_execution,
        }
        files = self._persist_payload(payload)

        return PairLinkageRunResult(
            left_security=left_security,
            right_security=right_security,
            family_matched=family_matched,
            attempt_count=len(attempts),
            selected_title=(accepted or {}).get("selected_title") if accepted else None,
            theorem_registry=(accepted or {}).get("theorem_registry") if accepted else None,
            symbolic_execution=symbolic_execution,
            result=payload,
            files=files,
        ).as_dict()

    def run_default_pairs(
        self,
        *,
        pairs: Optional[Sequence[tuple[str, str]]] = None,
        acceptance_score: float = 0.84,
    ) -> Dict[str, Any]:
        pairs = list(
            pairs
            or [
                ("SPY US Equity", "VIX Index"),
                ("SPY US Equity", "VIX3M Index"),
                ("SPY US Equity", "VVIX Index"),
                ("SPY US Equity", "SKEW Index"),
                ("SPY US Equity", "SPX Index"),
            ]
        )
        runs = []
        for left, right in pairs:
            runs.append(
                self.run_pair(
                    left,
                    right,
                    acceptance_score=acceptance_score,
                )
            )
        summary = {
            "created_at": self._utc_now(),
            "n_pairs": len(runs),
            "n_family_matched": sum(1 for x in runs if bool(x.get("family_matched"))),
            "runs": runs,
        }
        summary_files = self._persist_summary(summary)
        return {"summary": summary, "files": summary_files}

    # ------------------------------------------------------------------
    # core theorem generation
    # ------------------------------------------------------------------
    def _answer_pair_prompt(
        self,
        prompt: str,
        *,
        left_security: str,
        right_security: str,
        acceptance_score: float,
    ) -> Dict[str, Any]:
        core = ApexReasoningCore(
            work_dir=self.work_dir,
            market_db_path=self.market_db_path,
            answer_mode="auto",
        )
        try:
            out = core.answer(
                prompt,
                mode="theorem",
                securities=[left_security, right_security],
                benchmark_security=self.benchmark_security,
                acceptance_score=float(acceptance_score),
            )
            return out
        finally:
            core.close()

    def _build_prompt(self, left_security: str, right_security: str, *, attempt: int) -> str:
        if attempt == 1:
            return (
                f"Propose a pair-linkage theorem for {left_security} and {right_security}. "
                f"The theorem must be genuinely about the interaction between the two objects, not a reused single-name rough-variance theorem. "
                f"Focus on {', '.join(self.TARGET_PAIR_TERMS)}. "
                f"State: "
                f"(1) the pair-level object, "
                f"(2) the predicted relationship or monotonicity, "
                f"(3) empirical Bloomberg feature signatures, "
                f"(4) failure conditions, and "
                f"(5) symbolic structure that can be checked directly."
            )

        return (
            f"Retry with a stricter pair theorem for {left_security} and {right_security}. "
            f"Do not output a single-name rough-variance scaling theorem. "
            f"Do not center the theorem only on {self.benchmark_security}. "
            f"The theorem title and statement must explicitly describe a pair-linkage family for {left_security} and {right_security}, "
            f"such as spot-volatility coupling, term-structure linkage, tail-risk linkage, or vol-of-vol transmission. "
            f"Make the theorem pair-specific, with symbolic and empirical conditions."
        )

    def _is_pair_family_match(
        self,
        out: Dict[str, Any],
        left_security: str,
        right_security: str,
    ) -> bool:
        title = str(out.get("selected_title") or "").lower()
        response = str(out.get("response") or "").lower()

        # reject obvious collapse back into rough single-name theorem family
        if "rough-variance scaling identification theorem" in title:
            return False

        # accept if title or response explicitly signals pair linkage structure
        positive_markers = [
            "pair-linkage",
            "spot-volatility",
            "spot volatility",
            "regime dependence",
            "term-structure",
            "tail-risk",
            "vol-of-vol",
            "linkage theorem",
            "transmission",
        ]
        if any(m in title for m in positive_markers):
            return True
        if any(m in response for m in positive_markers):
            return True

        # fallback: accept if both pair names are materially present and rough-family hijack absent
        left_token = self._security_token(left_security)
        right_token = self._security_token(right_security)
        return left_token in response and right_token in response and "single-name" not in response

    def _extract_artifact(
        self,
        out: Dict[str, Any],
        left_security: str,
        right_security: str,
    ) -> Optional[Dict[str, Any]]:
        theorem_result = out.get("theorem_result") or {}
        selected = theorem_result.get("selected") or {}

        statement = str(selected.get("statement") or out.get("response") or "")
        title = str(selected.get("title") or out.get("selected_title") or f"{left_security} {right_security} pair-linkage theorem")

        if not statement.strip():
            return None

        return {
            "title": title,
            "statement": statement,
            "assumptions": list(selected.get("assumptions") or []),
            "securities": [left_security, right_security],
            "tags": list(selected.get("tags") or []),
        }

    # ------------------------------------------------------------------
    # persistence
    # ------------------------------------------------------------------
    def _persist_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        stem = f"{self._slugify(payload['left_security'])}_{self._slugify(payload['right_security'])}_pair_linkage"
        json_path = self.output_dir / f"{stem}.json"
        md_path = self.output_dir / f"{stem}.md"

        json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        md_path.write_text(self._payload_markdown(payload), encoding="utf-8")

        return {
            "json_path": str(json_path),
            "markdown_path": str(md_path),
            "bytes_json": json_path.stat().st_size,
            "bytes_markdown": md_path.stat().st_size,
        }

    def _persist_summary(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        json_path = self.output_dir / f"pair_linkage_batch_{ts}.json"
        md_path = self.output_dir / f"pair_linkage_batch_{ts}.md"

        json_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
        md_path.write_text(self._summary_markdown(summary), encoding="utf-8")

        return {
            "json_path": str(json_path),
            "markdown_path": str(md_path),
            "bytes_json": json_path.stat().st_size,
            "bytes_markdown": md_path.stat().st_size,
        }

    def _payload_markdown(self, payload: Dict[str, Any]) -> str:
        lines = [
            f"# Pair-Linkage Theorem Run: {payload['left_security']} / {payload['right_security']}",
            "",
            f"- Created at: {payload.get('created_at')}",
            f"- Family matched: {payload.get('family_matched')}",
            "",
            "## Attempts",
        ]
        for attempt in payload.get("attempts", []):
            lines.append(f"### Attempt {attempt['attempt']}")
            lines.append(f"- Selected title: {attempt.get('selected_title')}")
            lines.append(f"- Prompt: {attempt.get('prompt')}")
            lines.append("")
        lines.append("## Accepted result")
        lines.append("```json")
        lines.append(json.dumps(payload.get("accepted_result"), indent=2, default=str)[:20000])
        lines.append("```")
        if payload.get("symbolic_execution"):
            lines.append("")
            lines.append("## Symbolic execution")
            lines.append("```json")
            lines.append(json.dumps(payload.get("symbolic_execution"), indent=2, default=str)[:12000])
            lines.append("```")
        return "\n".join(lines)

    def _summary_markdown(self, summary: Dict[str, Any]) -> str:
        lines = [
            "# Pair-Linkage Theorem Batch",
            "",
            f"- Created at: {summary.get('created_at')}",
            f"- Number of pairs: {summary.get('n_pairs')}",
            f"- Family matched count: {summary.get('n_family_matched')}",
            "",
        ]
        for run in summary.get("runs", []):
            lines.append(f"## {run['left_security']} / {run['right_security']}")
            lines.append(f"- Family matched: {run.get('family_matched')}")
            lines.append(f"- Selected title: {run.get('selected_title')}")
            lines.append(f"- Attempt count: {run.get('attempt_count')}")
            lines.append(f"- Symbolic execution: {json.dumps(run.get('symbolic_execution'), default=str)[:800]}")
            lines.append("")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _security_token(security: str) -> str:
        return str(security).split()[0].lower()

    @staticmethod
    def _slugify(text: str) -> str:
        return re.sub(r"[^A-Za-z0-9]+", "_", str(text)).strip("_").lower() or "pair"

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Generate dedicated SPY/VIX pair-linkage theorems.")
    parser.add_argument("--work-dir", default="rag_ingest_state")
    parser.add_argument("--market-db-path", default="data/market_history.sqlite")
    parser.add_argument("--output-dir", default="artifacts/pair_linkage_theorems")
    parser.add_argument("--symbolic-output-dir", default="artifacts/symbolic_task_packets")
    parser.add_argument("--left-security", default="")
    parser.add_argument("--right-security", default="")
    parser.add_argument("--acceptance-score", type=float, default=0.84)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    engine = PairLinkageTheoremEngine(
        work_dir=args.work_dir,
        market_db_path=args.market_db_path,
        output_dir=args.output_dir,
        symbolic_output_dir=args.symbolic_output_dir,
    )

    if args.left_security and args.right_security:
        result = engine.run_pair(
            args.left_security,
            args.right_security,
            acceptance_score=float(args.acceptance_score),
        )
    else:
        result = engine.run_default_pairs(acceptance_score=float(args.acceptance_score))

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(json.dumps(result, indent=2, default=str))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
