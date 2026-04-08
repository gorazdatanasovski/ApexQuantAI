from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence


@dataclass(frozen=True)
class SymbolicTask:
    name: str
    kind: str
    payload: Dict[str, Any]
    rationale: str

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SymbolicTaskPacket:
    title: str
    family: str
    securities: List[str]
    assumptions: List[str]
    tasks: List[SymbolicTask]
    notes: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "family": self.family,
            "securities": list(self.securities),
            "assumptions": list(self.assumptions),
            "tasks": [t.as_dict() for t in self.tasks],
            "notes": list(self.notes),
        }


class TheoremSymbolicTaskBuilder:
    """
    Convert theorem artifacts into explicit symbolic verification tasks.

    Superior version:
    - packet assumptions are now passed into every symbolic verification call
    - execution summaries preserve the assumption set actually used
    - this closes the bridge between theorem assumptions and symbolic checking
    """

    def __init__(
        self,
        market_db_path: str | Path = "data/market_history.sqlite",
        output_dir: str | Path = "artifacts/symbolic_task_packets",
    ) -> None:
        self.market_db_path = Path(market_db_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build_from_registry_entry(self, entry_id: str) -> SymbolicTaskPacket:
        artifact = self._load_registry_entry(entry_id)
        if artifact is None:
            raise KeyError(f"Registry entry not found: {entry_id}")
        return self.build_from_artifact(artifact)

    def build_from_artifact(self, artifact: Mapping[str, Any]) -> SymbolicTaskPacket:
        title = str(artifact.get("title") or "Untitled theorem")
        statement = str(artifact.get("statement") or "")
        securities = self._coerce_list(artifact.get("securities"))
        assumptions = self._coerce_list(artifact.get("assumptions"))
        family = self._infer_family(title=title, statement=statement, securities=securities)

        if family == "rough_variance_scaling":
            packet = self._build_rough_variance_scaling_packet(
                title=title,
                statement=statement,
                securities=securities,
                assumptions=assumptions,
            )
        elif family == "spot_vol_linkage":
            packet = self._build_spot_vol_linkage_packet(
                title=title,
                statement=statement,
                securities=securities,
                assumptions=assumptions,
            )
        else:
            packet = self._build_generic_packet(
                title=title,
                statement=statement,
                securities=securities,
                assumptions=assumptions,
            )

        return packet

    def persist_packet(self, packet: SymbolicTaskPacket, stem: Optional[str] = None) -> Dict[str, Any]:
        stem = stem or self._slugify(packet.title)
        json_path = self.output_dir / f"{stem}.json"
        md_path = self.output_dir / f"{stem}.md"

        json_path.write_text(json.dumps(packet.as_dict(), indent=2, default=str), encoding="utf-8")
        md_path.write_text(self._packet_markdown(packet), encoding="utf-8")

        return {
            "json_path": str(json_path),
            "markdown_path": str(md_path),
            "bytes_json": json_path.stat().st_size,
            "bytes_markdown": md_path.stat().st_size,
        }

    def build_persist_and_execute(
        self,
        artifact: Mapping[str, Any],
        symbolic_engine: Any,
        stem: Optional[str] = None,
    ) -> Dict[str, Any]:
        packet = self.build_from_artifact(artifact)
        files = self.persist_packet(packet, stem=stem)
        execution = self.execute_packet(packet, symbolic_engine=symbolic_engine)
        return {
            "packet": packet.as_dict(),
            "files": files,
            "execution": execution,
        }

    def execute_packet(self, packet: SymbolicTaskPacket, symbolic_engine: Any) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []
        assumptions = list(packet.assumptions)

        for task in packet.tasks:
            result = self._execute_task(task, symbolic_engine, assumptions=assumptions)
            results.append(result)

        n_ok = sum(1 for r in results if bool(r.get("ok")))
        return {
            "title": packet.title,
            "family": packet.family,
            "assumptions_used": assumptions,
            "n_tasks": len(packet.tasks),
            "n_ok": n_ok,
            "n_fail": len(packet.tasks) - n_ok,
            "results": results,
        }

    def _execute_task(
        self,
        task: SymbolicTask,
        symbolic_engine: Any,
        *,
        assumptions: Optional[Sequence[str]] = None,
    ) -> Dict[str, Any]:
        kind = task.kind
        payload = task.payload
        assumptions = list(assumptions or [])

        try:
            if kind == "verify_identity" and hasattr(symbolic_engine, "verify_identity"):
                out = symbolic_engine.verify_identity(
                    payload["lhs"],
                    payload["rhs"],
                    assumptions=assumptions,
                )
                return self._normalize_symbolic_result(task, out, assumptions)

            if kind == "verify_nonnegative" and hasattr(symbolic_engine, "verify_nonnegative"):
                out = symbolic_engine.verify_nonnegative(
                    payload["expression"],
                    assumptions=assumptions,
                )
                return self._normalize_symbolic_result(task, out, assumptions)

            if kind == "verify_derivative_zero" and hasattr(symbolic_engine, "verify_derivative_zero"):
                out = symbolic_engine.verify_derivative_zero(
                    payload["expression"],
                    variable=payload["variable"],
                    point=payload["point"],
                    assumptions=assumptions,
                )
                return self._normalize_symbolic_result(task, out, assumptions)

            if kind == "verify_limit_zero" and hasattr(symbolic_engine, "verify_limit_zero"):
                out = symbolic_engine.verify_limit_zero(
                    payload["expression"],
                    variable=payload["variable"],
                    point=payload["point"],
                    direction=payload.get("direction", "+"),
                    assumptions=assumptions,
                )
                return self._normalize_symbolic_result(task, out, assumptions)

            if kind == "simplify" and hasattr(symbolic_engine, "simplify"):
                out = symbolic_engine.simplify(
                    payload["expression"],
                    assumptions=assumptions,
                )
                return self._normalize_symbolic_result(task, out, assumptions)

            if kind == "evaluate_expression" and hasattr(symbolic_engine, "evaluate_expression"):
                out = symbolic_engine.evaluate_expression(
                    payload["expression"],
                    assumptions=assumptions,
                )
                return {
                    "task": task.as_dict(),
                    "ok": True,
                    "assumptions_used": assumptions,
                    "result": out if isinstance(out, str) else str(out),
                }

            return {
                "task": task.as_dict(),
                "ok": False,
                "assumptions_used": assumptions,
                "error": f"Symbolic engine does not support task kind: {kind}",
            }
        except Exception as exc:
            return {
                "task": task.as_dict(),
                "ok": False,
                "assumptions_used": assumptions,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }

    @staticmethod
    def _normalize_symbolic_result(task: SymbolicTask, out: Any, assumptions: Sequence[str]) -> Dict[str, Any]:
        if hasattr(out, "as_dict"):
            payload = out.as_dict()
            ok = bool(payload.get("passed", payload.get("ok", True)))
            return {"task": task.as_dict(), "ok": ok, "assumptions_used": list(assumptions), "result": payload}
        if isinstance(out, dict):
            ok = bool(out.get("passed", out.get("ok", True)))
            return {"task": task.as_dict(), "ok": ok, "assumptions_used": list(assumptions), "result": out}
        return {"task": task.as_dict(), "ok": True, "assumptions_used": list(assumptions), "result": str(out)}

    def _build_rough_variance_scaling_packet(
        self,
        *,
        title: str,
        statement: str,
        securities: Sequence[str],
        assumptions: Sequence[str],
    ) -> SymbolicTaskPacket:
        tasks = [
            SymbolicTask(
                name="variance_scaling_factorization",
                kind="verify_identity",
                payload={
                    "lhs": "C_X*Delta**(2*H) + a0 + a1*Delta**(2*H)",
                    "rhs": "a0 + (C_X + a1)*Delta**(2*H)",
                },
                rationale="Checks algebraic coherence of the scaling-law form used in the theorem candidate.",
            ),
            SymbolicTask(
                name="variance_term_nonnegative",
                kind="verify_nonnegative",
                payload={"expression": "a1*Delta**(2*H)"},
                rationale="Under positive coefficient and positive scale assumptions, the scaling contribution should remain nonnegative.",
            ),
            SymbolicTask(
                name="increment_variance_nonnegative",
                kind="verify_nonnegative",
                payload={"expression": "C_X*Delta**(2*H)"},
                rationale="Variance contribution must remain nonnegative under the roughness scaling ansatz.",
            ),
            SymbolicTask(
                name="scaling_at_origin_consistency",
                kind="verify_derivative_zero",
                payload={
                    "expression": "Delta**(2*H + 1)",
                    "variable": "Delta",
                    "point": 0,
                },
                rationale="Checks a simple origin-consistency proxy for higher-order remainder terms in the small-scale expansion.",
            ),
            SymbolicTask(
                name="exponent_additivity",
                kind="verify_identity",
                payload={
                    "lhs": "Delta**(2*H) * Delta**(2*K)",
                    "rhs": "Delta**(2*(H + K))",
                },
                rationale="Provides a reusable exponent-composition identity for scaling arguments.",
            ),
        ]
        return SymbolicTaskPacket(
            title=title,
            family="rough_variance_scaling",
            securities=list(securities),
            assumptions=self._merge_assumptions(
                assumptions,
                [
                    "Delta > 0",
                    "0 < H < 1/2",
                    "C_X >= 0",
                    "a1 >= 0",
                    "Higher-order remainder is lower order than Delta^(2H)",
                ],
            ),
            tasks=tasks,
            notes=[
                "These tasks do not prove the full theorem.",
                "They turn the current scaling-law candidate into executable symbolic consistency checks.",
                "Packet assumptions are now threaded into symbolic execution.",
            ],
        )

    def _build_spot_vol_linkage_packet(
        self,
        *,
        title: str,
        statement: str,
        securities: Sequence[str],
        assumptions: Sequence[str],
    ) -> SymbolicTaskPacket:
        tasks = [
            SymbolicTask(
                name="covariance_symmetry",
                kind="verify_identity",
                payload={
                    "lhs": "rho*sigma_s*sigma_v",
                    "rhs": "sigma_v*sigma_s*rho",
                },
                rationale="Basic symmetry check for spot-vol covariance style terms.",
            ),
            SymbolicTask(
                name="quadratic_form_nonnegative",
                kind="verify_nonnegative",
                payload={
                    "expression": "(sigma_s - rho*sigma_v)**2",
                },
                rationale="Any squared coupling residual should remain nonnegative.",
            ),
            SymbolicTask(
                name="variance_of_linear_combination",
                kind="verify_nonnegative",
                payload={
                    "expression": "sigma_s**2 + sigma_v**2 - 2*rho*sigma_s*sigma_v",
                },
                rationale="A variance-style quadratic form should remain nonnegative under admissible coupling assumptions.",
            ),
            SymbolicTask(
                name="regime_gap_identity",
                kind="verify_identity",
                payload={
                    "lhs": "(rv_hi - rv_lo) + (iv_hi - iv_lo)",
                    "rhs": "(rv_hi + iv_hi) - (rv_lo + iv_lo)",
                },
                rationale="Checks algebraic coherence of regime-difference decomposition used in pair-linkage narratives.",
            ),
            SymbolicTask(
                name="zero_spread_baseline",
                kind="verify_derivative_zero",
                payload={
                    "expression": "x**2",
                    "variable": "x",
                    "point": 0,
                },
                rationale="Provides a simple baseline zero-point regularity check for local spread/coupling expansions.",
            ),
        ]
        return SymbolicTaskPacket(
            title=title,
            family="spot_vol_linkage",
            securities=list(securities),
            assumptions=self._merge_assumptions(
                assumptions,
                [
                    "sigma_s > 0",
                    "sigma_v > 0",
                    "-1 <= rho <= 1",
                    "Regime labels correspond to empirically observed states",
                    "Observed feature differences are mapped consistently to theorem notation",
                ],
            ),
            tasks=tasks,
            notes=[
                "These are symbolic consistency checks for pair-linkage theorems.",
                "Packet assumptions are threaded into symbolic execution so rho bounds and positivity can actually be used.",
            ],
        )

    def _build_generic_packet(
        self,
        *,
        title: str,
        statement: str,
        securities: Sequence[str],
        assumptions: Sequence[str],
    ) -> SymbolicTaskPacket:
        tasks = [
            SymbolicTask(
                name="commutativity_baseline",
                kind="verify_identity",
                payload={"lhs": "a + b", "rhs": "b + a"},
                rationale="Baseline algebraic sanity check.",
            ),
            SymbolicTask(
                name="square_nonnegative",
                kind="verify_nonnegative",
                payload={"expression": "(x - y)**2"},
                rationale="Baseline nonnegativity check for generic theorem candidates.",
            ),
            SymbolicTask(
                name="origin_regular_point",
                kind="verify_derivative_zero",
                payload={"expression": "x**2", "variable": "x", "point": 0},
                rationale="Baseline local regularity check at the origin.",
            ),
        ]
        return SymbolicTaskPacket(
            title=title,
            family="generic",
            securities=list(securities),
            assumptions=self._merge_assumptions(
                assumptions,
                ["Symbol mapping must be refined before serious proof work."],
            ),
            tasks=tasks,
            notes=[
                "This generic packet is a fallback only.",
            ],
        )

    def _load_registry_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        if not self.market_db_path.exists():
            return None

        conn = sqlite3.connect(str(self.market_db_path))
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                """
                SELECT entry_id, title, status, score, statement,
                       assumptions_json, tags_json, securities_json,
                       updated_at, metadata_json
                FROM theorem_registry
                WHERE entry_id = ?
                """,
                [entry_id],
            ).fetchone()
        finally:
            conn.close()

        if row is None:
            return None

        return {
            "entry_id": str(row["entry_id"]),
            "title": str(row["title"]),
            "status": str(row["status"]),
            "score": float(row["score"] or 0.0),
            "statement": str(row["statement"] or ""),
            "assumptions": self._json_load(row["assumptions_json"], default=[]),
            "tags": self._json_load(row["tags_json"], default=[]),
            "securities": self._json_load(row["securities_json"], default=[]),
            "updated_at": str(row["updated_at"] or ""),
            "metadata": self._json_load(row["metadata_json"], default={}),
        }

    @staticmethod
    def _coerce_list(value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, (list, tuple, set)):
            return [str(x) for x in value if str(x).strip()]
        return [str(value)]

    @staticmethod
    def _merge_assumptions(left: Sequence[str], right: Sequence[str]) -> List[str]:
        out: List[str] = []
        seen = set()
        for item in list(left) + list(right):
            s = str(item).strip()
            if not s:
                continue
            key = s.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(s)
        return out

    @staticmethod
    def _infer_family(title: str, statement: str, securities: Sequence[str]) -> str:
        text = f"{title}\n{statement}".lower()
        if "rough-variance scaling identification theorem" in text or "delta^(2h)" in text or "delta**(2*h)" in text:
            return "rough_variance_scaling"
        if len(securities) >= 2 or any(token in text for token in ("spot-volatility", "spot volatility", "regime transitions", "linking")):
            return "spot_vol_linkage"
        return "generic"

    @staticmethod
    def _json_load(value: Any, default: Any) -> Any:
        try:
            if value is None:
                return default
            return json.loads(value)
        except Exception:
            return default

    @staticmethod
    def _slugify(text: str) -> str:
        import re
        text = re.sub(r"[^A-Za-z0-9]+", "_", str(text)).strip("_").lower()
        return text or "symbolic_task_packet"

    def _packet_markdown(self, packet: SymbolicTaskPacket) -> str:
        lines = [
            f"# Symbolic Task Packet: {packet.title}",
            "",
            f"- Family: {packet.family}",
            f"- Securities: {', '.join(packet.securities) if packet.securities else 'None'}",
            "",
            "## Assumptions",
        ]
        lines.extend([f"- {a}" for a in packet.assumptions] or ["- None"])
        lines.extend(["", "## Tasks"])
        for task in packet.tasks:
            lines.append(f"### {task.name}")
            lines.append(f"- Kind: {task.kind}")
            lines.append(f"- Rationale: {task.rationale}")
            lines.append("```json")
            lines.append(json.dumps(task.payload, indent=2, default=str))
            lines.append("```")
        if packet.notes:
            lines.extend(["", "## Notes"])
            lines.extend([f"- {n}" for n in packet.notes])
        return "\n".join(lines)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Build symbolic task packets from theorem artifacts.")
    parser.add_argument("--market-db-path", default="data/market_history.sqlite")
    parser.add_argument("--output-dir", default="artifacts/symbolic_task_packets")
    parser.add_argument("--entry-id", default=None)
    parser.add_argument("--title", default="")
    parser.add_argument("--statement", default="")
    parser.add_argument("--securities", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    builder = TheoremSymbolicTaskBuilder(
        market_db_path=args.market_db_path,
        output_dir=args.output_dir,
    )

    if args.entry_id:
        packet = builder.build_from_registry_entry(args.entry_id)
    else:
        artifact = {
            "title": args.title,
            "statement": args.statement,
            "securities": [x.strip() for x in str(args.securities).split(",") if x.strip()],
            "assumptions": [],
        }
        packet = builder.build_from_artifact(artifact)

    files = builder.persist_packet(packet)

    result = {
        "packet": packet.as_dict(),
        "files": files,
    }

    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
