from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from quantai.reasoning.spy_volatility_universe import SPY_VOLATILITY_CORE_SECURITIES


@dataclass(frozen=True)
class ScoreboardItem:
    name: str
    score: float
    details: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SpyVolatilityScoreboard:
    """
    Task-aware SPY/VIX scoreboard.

    Superior change:
    - only penalizes a lane if the originating task explicitly requested that lane
    - keeps symbolic-promotion-aware theorem ranking
    - treats stale pre-backfill warnings as low-value noise when current coverage is healthy
    """

    STATUS_PRIOR = {
        "rejected": 0.00,
        "failed": 0.00,
        "archived": 0.05,
        "draft": 0.15,
        "proposed": 0.20,
        "unverified_hypothesis": 0.30,
        "research_conjecture": 0.40,
        "speculative_candidate": 0.55,
        "candidate": 0.68,
        "symbolically_verified_candidate": 0.90,
        "accepted": 1.00,
    }

    TASK_FLAG_TO_SUMMARY_FLAG = {
        "include_evidence": "evidence_ok",
        "include_theorem": "theorem_ok",
        "include_market_memory": "market_memory_ok",
        "include_market_calibration": "market_calibration_ok",
        "include_market_live_snapshot": "market_live_snapshot_ok",
    }

    def __init__(
        self,
        market_db_path: str | Path = "data/market_history.sqlite",
        runs_dir: str | Path = "artifacts/universe_research_runs",
        output_dir: str | Path = "artifacts/scoreboards",
        securities: Optional[Sequence[str]] = None,
    ) -> None:
        self.market_db_path = Path(market_db_path)
        self.runs_dir = Path(runs_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.securities = list(securities or SPY_VOLATILITY_CORE_SECURITIES)

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def build_scoreboard(self) -> Dict[str, Any]:
        coverage = self.coverage_report(self.securities)
        theorem_rankings = self.rank_theorem_registry(limit=25)
        run_rankings = self.rank_research_runs(limit=50)
        weak_lanes = self.find_weak_lanes(run_rankings, coverage)
        coverage_gaps = self.find_coverage_gaps(coverage)

        return {
            "created_at": self._utc_now(),
            "securities": list(self.securities),
            "coverage": coverage,
            "coverage_gaps": coverage_gaps,
            "top_theorems": [x.as_dict() for x in theorem_rankings[:10]],
            "top_runs": [x.as_dict() for x in run_rankings[:10]],
            "weak_lanes": [x.as_dict() for x in weak_lanes[:15]],
        }

    def persist_scoreboard(self, payload: Dict[str, Any], stem: str = "spy_volatility_scoreboard") -> Dict[str, Any]:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        json_path = self.output_dir / f"{stem}_{ts}.json"
        md_path = self.output_dir / f"{stem}_{ts}.md"

        json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        md_path.write_text(self._to_markdown(payload), encoding="utf-8")

        return {
            "json_path": str(json_path),
            "markdown_path": str(md_path),
            "bytes_json": json_path.stat().st_size,
            "bytes_markdown": md_path.stat().st_size,
        }

    def build_and_persist(self) -> Dict[str, Any]:
        payload = self.build_scoreboard()
        files = self.persist_scoreboard(payload)
        return {"scoreboard": payload, "files": files}

    # ------------------------------------------------------------------
    # coverage
    # ------------------------------------------------------------------
    def coverage_report(self, securities: Sequence[str]) -> Dict[str, Any]:
        report: Dict[str, Any] = {"db_exists": self.market_db_path.exists(), "securities": {}}
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

    def find_coverage_gaps(self, coverage: Dict[str, Any]) -> List[ScoreboardItem]:
        out: List[ScoreboardItem] = []
        for sec, stats in (coverage.get("securities") or {}).items():
            history_rows = int(stats.get("history_rows", 0) or 0)
            feature_rows = int(stats.get("feature_rows", 0) or 0)
            memory_rows = int(stats.get("memory_rows", 0) or 0)
            if history_rows > 0 and feature_rows > 0 and memory_rows > 0:
                continue
            missing = []
            if history_rows <= 0:
                missing.append("history")
            if feature_rows <= 0:
                missing.append("features")
            if memory_rows <= 0:
                missing.append("memory")
            out.append(
                ScoreboardItem(
                    name=sec,
                    score=float(len(missing)),
                    details={
                        "missing": missing,
                        "history_rows": history_rows,
                        "feature_rows": feature_rows,
                        "memory_rows": memory_rows,
                    },
                )
            )
        out.sort(key=lambda x: x.score, reverse=True)
        return out

    # ------------------------------------------------------------------
    # theorem ranking
    # ------------------------------------------------------------------
    def rank_theorem_registry(self, limit: int = 25) -> List[ScoreboardItem]:
        if not self.market_db_path.exists():
            return []

        conn = sqlite3.connect(str(self.market_db_path))
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                """
                SELECT entry_id, title, status, score, statement, securities_json, updated_at, metadata_json
                FROM theorem_registry
                ORDER BY updated_at DESC
                """
            ).fetchall()
        except Exception:
            conn.close()
            return []
        finally:
            try:
                conn.close()
            except Exception:
                pass

        items: List[ScoreboardItem] = []
        for row in rows:
            securities = self._json_load(row["securities_json"], default=[])
            if securities and not self._is_relevant_security_set(securities):
                continue

            status = str(row["status"])
            native_score = float(row["score"] or 0.0)
            metadata = self._json_load(row["metadata_json"], default={})
            promo = metadata.get("promotion_engine") or {}
            symbolic_pass_rate = float(promo.get("symbolic_pass_rate", 0.0) or 0.0)
            symbolic_tasks = int(promo.get("symbolic_tasks", 0) or 0)

            rank_score = (
                0.58 * self._status_prior(status)
                + 0.22 * native_score
                + 0.20 * self._symbolic_quality(symbolic_pass_rate, symbolic_tasks)
            )

            details = {
                "entry_id": row["entry_id"],
                "title": row["title"],
                "status": status,
                "native_score": native_score,
                "updated_at": row["updated_at"],
                "securities": securities,
                "statement_head": str(row["statement"] or "")[:500],
                "metadata": metadata,
                "symbolic_pass_rate": symbolic_pass_rate,
                "symbolic_tasks": symbolic_tasks,
            }
            items.append(
                ScoreboardItem(
                    name=str(row["title"]),
                    score=rank_score,
                    details=details,
                )
            )

        items.sort(key=lambda x: x.score, reverse=True)
        return items[: int(limit)]

    # ------------------------------------------------------------------
    # run ranking
    # ------------------------------------------------------------------
    def rank_research_runs(self, limit: int = 50) -> List[ScoreboardItem]:
        if not self.runs_dir.exists():
            return []

        items: List[ScoreboardItem] = []
        for path in sorted(self.runs_dir.glob("*.json")):
            if path.name.endswith("_manifest.json"):
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue

            summary = payload.get("summary") or {}
            task = payload.get("task") or {}
            securities = task.get("securities") or []
            if securities and not self._is_relevant_security_set(securities):
                continue

            requested_summary_flags = self._requested_summary_flags(task)
            warnings = payload.get("warnings") or []
            score = self._run_score(summary, warnings, requested_summary_flags=requested_summary_flags)
            items.append(
                ScoreboardItem(
                    name=str(task.get("name") or path.stem),
                    score=score,
                    details={
                        "task_name": task.get("name"),
                        "securities": securities,
                        "core_query": task.get("core_query"),
                        "summary": summary,
                        "warnings": warnings,
                        "path": str(path),
                        "requested_summary_flags": requested_summary_flags,
                        "task": task,
                    },
                )
            )

        items.sort(key=lambda x: x.score, reverse=True)
        return items[: int(limit)]

    def find_weak_lanes(
        self,
        ranked_runs: Sequence[ScoreboardItem],
        coverage: Dict[str, Any],
    ) -> List[ScoreboardItem]:
        weak: List[ScoreboardItem] = []
        securities_coverage = coverage.get("securities") or {}

        for item in ranked_runs:
            summary = (item.details or {}).get("summary") or {}
            warnings = list((item.details or {}).get("warnings") or [])
            securities = list((item.details or {}).get("securities") or [])
            requested_summary_flags = list((item.details or {}).get("requested_summary_flags") or [])

            # coverage_ok is always relevant, others only if requested
            relevant_flags = ["coverage_ok"] + requested_summary_flags
            failed_flags = [flag for flag in relevant_flags if flag in summary and not bool(summary.get(flag))]
            stale_coverage = self._warnings_are_stale_coverage(warnings, securities, securities_coverage)

            effective_warning_count = 0 if stale_coverage and not failed_flags else len(warnings)
            penalty = len(failed_flags) + 0.5 * effective_warning_count

            if penalty > 0:
                weak.append(
                    ScoreboardItem(
                        name=item.name,
                        score=penalty,
                        details={
                            "failed_flags": failed_flags,
                            "warnings": warnings,
                            "warnings_stale_coverage": stale_coverage,
                            "securities": securities,
                            "path": item.details.get("path"),
                            "requested_summary_flags": requested_summary_flags,
                        },
                    )
                )

        weak.sort(key=lambda x: x.score, reverse=True)
        return weak

    # ------------------------------------------------------------------
    # scoring helpers
    # ------------------------------------------------------------------
    def _requested_summary_flags(self, task: Dict[str, Any]) -> List[str]:
        out: List[str] = []
        for task_flag, summary_flag in self.TASK_FLAG_TO_SUMMARY_FLAG.items():
            if bool(task.get(task_flag)):
                out.append(summary_flag)
        return out

    @staticmethod
    def _run_score(
        summary: Dict[str, Any],
        warnings: Sequence[str],
        *,
        requested_summary_flags: Sequence[str],
    ) -> float:
        score = 0.0
        weights = {
            "coverage_ok": 0.25,
            "evidence_ok": 0.15,
            "theorem_ok": 0.20,
            "market_memory_ok": 0.15,
            "market_calibration_ok": 0.15,
            "market_live_snapshot_ok": 0.10,
        }

        # coverage is always relevant
        if bool(summary.get("coverage_ok")):
            score += weights["coverage_ok"]

        for key in requested_summary_flags:
            if bool(summary.get(key)):
                score += weights.get(key, 0.0)

        score -= 0.03 * len(list(warnings))
        return score

    @classmethod
    def _status_prior(cls, status: str) -> float:
        return float(cls.STATUS_PRIOR.get(str(status).lower().strip(), 0.20))

    @staticmethod
    def _symbolic_quality(pass_rate: float, n_tasks: int) -> float:
        if n_tasks <= 0:
            return 0.0
        depth_bonus = min(n_tasks / 5.0, 1.0)
        return float(pass_rate) * depth_bonus

    def _warnings_are_stale_coverage(
        self,
        warnings: Sequence[str],
        securities: Sequence[str],
        securities_coverage: Dict[str, Any],
    ) -> bool:
        if not warnings or not securities:
            return False
        for sec in securities:
            stats = securities_coverage.get(sec) or {}
            if not (
                int(stats.get("history_rows", 0) or 0) > 0
                and int(stats.get("feature_rows", 0) or 0) > 0
                and int(stats.get("memory_rows", 0) or 0) > 0
            ):
                return False
        return True

    def _is_relevant_security_set(self, securities: Sequence[str]) -> bool:
        target = set(self.securities)
        secset = {str(x) for x in securities}
        return bool(target & secset)

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

    def _to_markdown(self, payload: Dict[str, Any]) -> str:
        lines: List[str] = [
            "# SPY Volatility Scoreboard",
            "",
            f"- Created at: {payload.get('created_at')}",
            f"- Securities: {', '.join(payload.get('securities', []))}",
            "",
            "## Coverage",
            "```json",
            json.dumps(payload.get("coverage"), indent=2, default=str),
            "```",
        ]

        lines.extend(["", "## Coverage gaps"])
        gaps = payload.get("coverage_gaps") or []
        if not gaps:
            lines.append("- None")
        else:
            for item in gaps:
                lines.append(f"- {item['name']}: {json.dumps(item['details'], default=str)}")

        lines.extend(["", "## Top theorems"])
        for item in payload.get("top_theorems", []):
            lines.append(f"### {item['name']}")
            lines.append(f"- Score: {item['score']:.4f}")
            lines.append(f"- Status: {item['details'].get('status')}")
            lines.append(f"- Symbolic pass rate: {item['details'].get('symbolic_pass_rate', 0.0):.4f}")
            lines.append("```json")
            lines.append(json.dumps(item["details"], indent=2, default=str))
            lines.append("```")

        lines.extend(["", "## Top runs"])
        for item in payload.get("top_runs", []):
            lines.append(f"### {item['name']}")
            lines.append(f"- Score: {item['score']:.4f}")
            lines.append("```json")
            lines.append(json.dumps(item["details"], indent=2, default=str))
            lines.append("```")

        lines.extend(["", "## Weak lanes"])
        weak = payload.get("weak_lanes") or []
        if not weak:
            lines.append("- None")
        else:
            for item in weak:
                lines.append(f"### {item['name']}")
                lines.append(f"- Penalty: {item['score']:.4f}")
                lines.append("```json")
                lines.append(json.dumps(item["details"], indent=2, default=str))
                lines.append("```")

        return "\n".join(lines)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Build a SPY/VIX research scoreboard.")
    parser.add_argument("--market-db-path", default="data/market_history.sqlite")
    parser.add_argument("--runs-dir", default="artifacts/universe_research_runs")
    parser.add_argument("--output-dir", default="artifacts/scoreboards")
    parser.add_argument("--securities", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    securities = [x.strip() for x in str(args.securities).split(",") if x.strip()]
    scoreboard = SpyVolatilityScoreboard(
        market_db_path=args.market_db_path,
        runs_dir=args.runs_dir,
        output_dir=args.output_dir,
        securities=securities or None,
    )
    result = scoreboard.build_and_persist()

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print("=" * 72)
        print("SPY Volatility Scoreboard")
        print("=" * 72)
        print(json.dumps({
            "files": result["files"],
            "top_theorem": (result["scoreboard"].get("top_theorems") or [None])[0],
            "top_run": (result["scoreboard"].get("top_runs") or [None])[0],
            "coverage_gaps": result["scoreboard"].get("coverage_gaps"),
        }, indent=2, default=str))
        print("=" * 72)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
