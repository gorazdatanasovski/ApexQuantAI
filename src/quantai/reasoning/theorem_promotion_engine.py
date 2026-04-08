from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class PromotionCandidate:
    title: str
    current_status: str
    proposed_status: str
    symbolic_pass_rate: float
    symbolic_tasks: int
    symbolic_ok: int
    symbolic_fail: int
    theorem_score: float
    registry_entry_id: Optional[str]
    source_file: str
    rationale: str

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TheoremPromotionEngine:
    """
    Promote strong theorem artifacts based on refinement outputs.

    Purpose:
    - read theorem refinement artifacts
    - extract symbolic execution quality
    - recommend stronger registry statuses
    - optionally apply the promotion to theorem_registry

    Promotion philosophy:
    - symbolic consistency is necessary but not treated as a full proof
    - promotions are conservative
    - default mode is dry-run
    """

    STATUS_ORDER = {
        "rejected": 0,
        "failed": 0,
        "archived": 1,
        "draft": 2,
        "proposed": 3,
        "unverified_hypothesis": 4,
        "research_conjecture": 5,
        "speculative_candidate": 6,
        "candidate": 7,
        "symbolically_verified_candidate": 8,
        "accepted": 9,
    }

    def __init__(
        self,
        market_db_path: str | Path = "data/market_history.sqlite",
        refinements_dir: str | Path = "artifacts/theorem_refinements",
        output_dir: str | Path = "artifacts/theorem_promotions",
    ) -> None:
        self.market_db_path = Path(market_db_path)
        self.refinements_dir = Path(refinements_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def scan_candidates(self) -> Dict[str, Any]:
        latest = self._latest_refinement_runs_by_title()
        candidates: List[PromotionCandidate] = []

        for title, payload in latest.items():
            candidate = self._build_candidate_from_payload(title, payload)
            if candidate is not None:
                candidates.append(candidate)

        candidates.sort(
            key=lambda c: (self.STATUS_ORDER.get(c.proposed_status, -1), c.symbolic_pass_rate, c.theorem_score),
            reverse=True,
        )

        return {
            "created_at": self._utc_now(),
            "n_candidates": len(candidates),
            "candidates": [c.as_dict() for c in candidates],
        }

    def persist_report(self, report: Dict[str, Any], stem: str = "theorem_promotion_report") -> Dict[str, Any]:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        json_path = self.output_dir / f"{stem}_{ts}.json"
        md_path = self.output_dir / f"{stem}_{ts}.md"

        json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        md_path.write_text(self._to_markdown(report), encoding="utf-8")

        return {
            "json_path": str(json_path),
            "markdown_path": str(md_path),
            "bytes_json": json_path.stat().st_size,
            "bytes_markdown": md_path.stat().st_size,
        }

    def scan_and_persist(self) -> Dict[str, Any]:
        report = self.scan_candidates()
        files = self.persist_report(report)
        return {"report": report, "files": files}

    def apply_promotions(self, *, dry_run: bool = True) -> Dict[str, Any]:
        report = self.scan_candidates()
        applied: List[Dict[str, Any]] = []

        if not self.market_db_path.exists():
            return {
                "dry_run": dry_run,
                "report": report,
                "applied": [],
                "error": f"Market DB not found: {self.market_db_path}",
            }

        conn = sqlite3.connect(str(self.market_db_path))
        try:
            for cand in report["candidates"]:
                entry_id = cand.get("registry_entry_id")
                if not entry_id:
                    continue

                current_status = str(cand["current_status"])
                proposed_status = str(cand["proposed_status"])
                if self.STATUS_ORDER.get(proposed_status, -1) <= self.STATUS_ORDER.get(current_status, -1):
                    continue

                row = conn.execute(
                    "SELECT metadata_json FROM theorem_registry WHERE entry_id = ?",
                    [entry_id],
                ).fetchone()
                metadata = self._json_load(row[0], default={}) if row else {}

                metadata["promotion_engine"] = {
                    "last_promotion_scan_at": self._utc_now(),
                    "symbolic_pass_rate": cand["symbolic_pass_rate"],
                    "symbolic_tasks": cand["symbolic_tasks"],
                    "symbolic_ok": cand["symbolic_ok"],
                    "symbolic_fail": cand["symbolic_fail"],
                    "source_file": cand["source_file"],
                    "rationale": cand["rationale"],
                }

                applied_item = {
                    "entry_id": entry_id,
                    "title": cand["title"],
                    "current_status": current_status,
                    "proposed_status": proposed_status,
                    "dry_run": dry_run,
                }

                if not dry_run:
                    conn.execute(
                        """
                        UPDATE theorem_registry
                        SET status = ?, metadata_json = ?, updated_at = ?
                        WHERE entry_id = ?
                        """,
                        [
                            proposed_status,
                            json.dumps(metadata, default=str),
                            self._utc_now(),
                            entry_id,
                        ],
                    )

                applied.append(applied_item)

            if not dry_run:
                conn.commit()
        finally:
            conn.close()

        out = {
            "dry_run": dry_run,
            "report": report,
            "applied": applied,
        }
        files = self.persist_report(
            {
                "created_at": self._utc_now(),
                "mode": "dry_run" if dry_run else "apply",
                "applied": applied,
                "report": report,
            },
            stem="theorem_promotion_apply",
        )
        out["files"] = files
        return out

    # ------------------------------------------------------------------
    # candidate building
    # ------------------------------------------------------------------
    def _build_candidate_from_payload(self, title: str, payload: Dict[str, Any]) -> Optional[PromotionCandidate]:
        result = payload.get("result") or {}
        symbolic = result.get("symbolic_execution") or payload.get("symbolic_execution") or {}
        theorem_registry = result.get("theorem_registry") or {}
        theorem_result = result.get("theorem_result") or {}

        n_tasks = int(symbolic.get("n_tasks", 0) or 0)
        n_ok = int(symbolic.get("n_ok", 0) or 0)
        n_fail = int(symbolic.get("n_fail", 0) or 0)
        if n_tasks <= 0:
            return None

        symbolic_pass_rate = n_ok / max(n_tasks, 1)
        current_status = str((theorem_registry or {}).get("status") or "")
        theorem_score = float(((theorem_result.get("selected") or {}).get("score")) or 0.0)
        registry_entry_id = (theorem_registry or {}).get("entry_id")

        proposed_status, rationale = self._promotion_policy(
            current_status=current_status,
            symbolic_pass_rate=symbolic_pass_rate,
            theorem_score=theorem_score,
            n_tasks=n_tasks,
            n_fail=n_fail,
            title=title,
        )

        if proposed_status == current_status or not proposed_status:
            return None

        return PromotionCandidate(
            title=title,
            current_status=current_status,
            proposed_status=proposed_status,
            symbolic_pass_rate=symbolic_pass_rate,
            symbolic_tasks=n_tasks,
            symbolic_ok=n_ok,
            symbolic_fail=n_fail,
            theorem_score=theorem_score,
            registry_entry_id=registry_entry_id,
            source_file=str(payload.get("_source_file") or ""),
            rationale=rationale,
        )

    def _promotion_policy(
        self,
        *,
        current_status: str,
        symbolic_pass_rate: float,
        theorem_score: float,
        n_tasks: int,
        n_fail: int,
        title: str,
    ) -> Tuple[str, str]:
        current_status = str(current_status or "candidate")

        if n_tasks >= 4 and n_fail == 0 and symbolic_pass_rate >= 1.0:
            if current_status in {"speculative_candidate", "research_conjecture", "unverified_hypothesis", "candidate", "draft", "proposed"}:
                return (
                    "symbolically_verified_candidate",
                    "Theorem passed all symbolic tasks in the latest refinement run and should be promoted above purely empirical candidates.",
                )

        if symbolic_pass_rate >= 0.80 and theorem_score >= 0.85:
            if current_status in {"unverified_hypothesis", "research_conjecture", "draft", "proposed"}:
                return (
                    "candidate",
                    "Theorem has strong refinement score and high symbolic pass rate, enough to promote into candidate status.",
                )

        return current_status, "No promotion recommended."

    # ------------------------------------------------------------------
    # refinement artifact loading
    # ------------------------------------------------------------------
    def _latest_refinement_runs_by_title(self) -> Dict[str, Dict[str, Any]]:
        latest: Dict[str, Dict[str, Any]] = {}
        if not self.refinements_dir.exists():
            return latest

        paths = sorted(self.refinements_dir.glob("*.json"))
        for path in paths:
            if "theorem_refinement_batch_" in path.name:
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue

            plan = payload.get("plan") or {}
            result = payload.get("result") or {}
            title = str(plan.get("title") or result.get("selected_title") or path.stem)

            candidate = dict(payload)
            candidate["_source_file"] = str(path)

            prev = latest.get(title)
            if prev is None:
                latest[title] = candidate
                continue

            prev_mtime = Path(prev["_source_file"]).stat().st_mtime if prev.get("_source_file") and Path(prev["_source_file"]).exists() else 0.0
            cur_mtime = path.stat().st_mtime
            if cur_mtime >= prev_mtime:
                latest[title] = candidate

        return latest

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
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

    def _to_markdown(self, report: Dict[str, Any]) -> str:
        lines: List[str] = [
            "# Theorem Promotion Report",
            "",
            f"- Created at: {report.get('created_at', self._utc_now())}",
            "",
            "## Candidates",
        ]
        candidates = report.get("candidates") or report.get("report", {}).get("candidates") or []
        if not candidates:
            lines.append("- None")
            return "\n".join(lines)

        for cand in candidates:
            lines.append(f"### {cand['title']}")
            lines.append(f"- Current status: {cand['current_status']}")
            lines.append(f"- Proposed status: {cand['proposed_status']}")
            lines.append(f"- Symbolic pass rate: {cand['symbolic_pass_rate']:.4f}")
            lines.append(f"- Symbolic tasks: {cand['symbolic_tasks']}")
            lines.append(f"- Theorem score: {cand['theorem_score']:.4f}")
            lines.append(f"- Registry entry: {cand['registry_entry_id']}")
            lines.append(f"- Rationale: {cand['rationale']}")
            lines.append("")
        return "\n".join(lines)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Promote strong theorem artifacts based on symbolic refinement results.")
    parser.add_argument("--market-db-path", default="data/market_history.sqlite")
    parser.add_argument("--refinements-dir", default="artifacts/theorem_refinements")
    parser.add_argument("--output-dir", default="artifacts/theorem_promotions")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    engine = TheoremPromotionEngine(
        market_db_path=args.market_db_path,
        refinements_dir=args.refinements_dir,
        output_dir=args.output_dir,
    )

    result = engine.apply_promotions(dry_run=not bool(args.apply)) if (args.apply or True) else engine.scan_and_persist()

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print("=" * 72)
        print("Theorem Promotion Engine")
        print("=" * 72)
        print(json.dumps({
            "dry_run": result.get("dry_run"),
            "n_candidates": len((result.get("report") or {}).get("candidates", [])),
            "n_applied": len(result.get("applied", [])),
            "files": result.get("files"),
        }, indent=2, default=str))
        print("=" * 72)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
