from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from quantai.memory.book_memory import BookMemory

try:
    from quantai.reasoning.options_surface_memory_gateway import OptionsSurfaceMemoryGateway
except Exception:
    OptionsSurfaceMemoryGateway = None  # type: ignore


_TOKEN_RE = re.compile(r"[A-Za-z0-9_\-\.]+")
_SURFACE_MARKERS = (
    "implied vol",
    "implied volatility",
    "options surface",
    "surface",
    "smile",
    "skew",
    "atm skew",
    "term structure",
    "spx options",
    "option chain",
    "vol surface",
    "surface memory",
    "persisted surface",
)


@dataclass(frozen=True)
class FusionHit:
    source_type: str
    title: str
    score: float
    excerpt: str
    context_text: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def source_kind(self) -> str:
        return self.source_type

    @property
    def security(self) -> str:
        return str(self.metadata.get("security") or "GLOBAL")

    def as_dict(self) -> Dict[str, Any]:
        return {
            "source_type": self.source_type,
            "source_kind": self.source_type,
            "title": self.title,
            "score": self.score,
            "excerpt": self.excerpt,
            "context_text": self.context_text,
            "metadata": dict(self.metadata),
        }


class ResearchMemoryFusion:
    """
    Unified fusion retrieval for:
    - book memory
    - theorem registry
    - Bloomberg research memory
    - direct persisted options-surface memory gateway

    Superior version:
    - for SPX/options-surface queries, injects the canonical persisted surface memory
      directly from OptionsSurfaceMemoryGateway
    - does not rely on secondary mirrored notes being present in bloomberg_research_memory
    - keeps the exact FusionHit contract engine.py expects
    """

    def __init__(
        self,
        work_dir: str | Path = "rag_ingest_state",
        market_db_path: str | Path = "data/market_history.sqlite",
    ) -> None:
        self.work_dir = Path(work_dir).resolve()
        self.market_db_path = Path(market_db_path)
        self.memory = BookMemory(self.work_dir)
        self.surface_gateway = (
            OptionsSurfaceMemoryGateway(self.market_db_path)
            if OptionsSurfaceMemoryGateway is not None
            else None
        )

    def close(self) -> None:
        try:
            self.memory.close()
        except Exception:
            pass

    def retrieve(
        self,
        query: str,
        *,
        securities: Sequence[str] | None = None,
        top_k: int = 6,
        book_k: int = 3,
        registry_k: int = 2,
        bloomberg_k: int = 3,
    ) -> List[FusionHit]:
        securities = list(securities or [])
        surface_query = self._looks_like_surface_query(query)

        direct_surface_hits: List[FusionHit] = []
        bloomberg_hits: List[FusionHit] = []
        registry_hits: List[FusionHit] = []
        book_hits: List[FusionHit] = []

        if surface_query:
            try:
                direct_surface_hits = self._retrieve_direct_surface_hits(
                    query,
                    securities=securities,
                    limit=max(top_k, 3),
                )
            except Exception:
                direct_surface_hits = []

        try:
            bloomberg_hits = self._retrieve_bloomberg_memory(
                query,
                securities=securities,
                limit=max(bloomberg_k * 4, 8),
            )
        except Exception:
            bloomberg_hits = []

        try:
            registry_hits = self._retrieve_registry(
                query,
                securities=securities,
                limit=max(registry_k * 4, 6),
            )
        except Exception:
            registry_hits = []

        try:
            book_hits = self._retrieve_books(
                query,
                limit=max(book_k * 3, 6),
            )
        except Exception:
            book_hits = []

        candidates = direct_surface_hits + bloomberg_hits + registry_hits + book_hits
        if not candidates:
            return []

        ranked = self._rank_hits(
            query,
            securities,
            candidates,
            surface_query=surface_query,
        )
        ranked = self._dedupe_hits(ranked)

        if surface_query:
            priority = []
            rest = []
            for hit in ranked:
                if hit.source_type == "bloomberg_memory" and (
                    str(hit.metadata.get("note_type") or "") in {"options_surface_memory", "options_surface_state", "options_surface_global_state"}
                    or bool(hit.metadata.get("direct_surface_memory"))
                ):
                    priority.append(hit)
                else:
                    rest.append(hit)

            priority.sort(key=self._surface_priority_key, reverse=True)
            rest.sort(key=lambda h: h.score, reverse=True)
            ranked = priority + rest

        return ranked[: int(top_k)]

    # ------------------------------------------------------------------
    # direct surface-memory lane
    # ------------------------------------------------------------------
    def _retrieve_direct_surface_hits(
        self,
        query: str,
        *,
        securities: Sequence[str],
        limit: int,
    ) -> List[FusionHit]:
        if self.surface_gateway is None:
            return []

        targets = list(securities or ["SPX Index"])
        if "SPX Index" not in targets:
            targets = ["SPX Index"] + targets

        hits: List[FusionHit] = []
        seen = set()

        for underlying in targets:
            snap = self.surface_gateway.latest_snapshot(
                underlying=underlying,
                preview_rows=12,
            )
            if snap is None:
                continue

            text = self.surface_gateway.render_summary(
                underlying=underlying,
                preview_rows=12,
            )
            diagnostics = snap.diagnostics or {}
            key = (snap.underlying, snap.valuation_date)
            if key in seen:
                continue
            seen.add(key)

            title = f"{snap.underlying} persisted options surface memory"
            hits.append(
                FusionHit(
                    source_type="bloomberg_memory",
                    title=title,
                    score=10.0,
                    excerpt=self._make_excerpt(text),
                    context_text=text,
                    metadata={
                        "security": snap.underlying,
                        "note_type": "options_surface_memory",
                        "as_of_date": snap.valuation_date,
                        "direct_surface_memory": True,
                        "n_surface_rows": diagnostics.get("n_surface_rows"),
                        "n_expiries": diagnostics.get("n_expiries"),
                        "atm_iv": diagnostics.get("atm_iv"),
                        "atm_skew": diagnostics.get("atm_skew"),
                        "method": diagnostics.get("method"),
                    },
                )
            )

        return hits[:limit]

    # ------------------------------------------------------------------
    # generic Bloomberg memory lane
    # ------------------------------------------------------------------
    def _retrieve_bloomberg_memory(
        self,
        query: str,
        *,
        securities: Sequence[str],
        limit: int,
    ) -> List[FusionHit]:
        if not self.market_db_path.exists():
            return []

        conn = sqlite3.connect(str(self.market_db_path))
        conn.row_factory = sqlite3.Row
        try:
            existing = {
                row[0]
                for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            }
            if "bloomberg_research_memory" not in existing:
                return []

            rows = conn.execute(
                """
                SELECT security, note_type, title, as_of_date, content_markdown, metadata_json
                FROM bloomberg_research_memory
                ORDER BY as_of_date DESC, id DESC
                """
            ).fetchall()
        finally:
            conn.close()

        allowed = set(securities)
        hits: List[FusionHit] = []
        for row in rows:
            security = str(row["security"])
            if allowed and security not in allowed and security != "GLOBAL":
                continue

            text = str(row["content_markdown"] or "")
            metadata = self._json_load(row["metadata_json"], default={})

            hits.append(
                FusionHit(
                    source_type="bloomberg_memory",
                    title=str(row["title"]),
                    score=0.0,
                    excerpt=self._make_excerpt(text),
                    context_text=text,
                    metadata={
                        "security": security,
                        "note_type": str(row["note_type"]),
                        "as_of_date": row["as_of_date"],
                        "metadata": metadata,
                    },
                )
            )

        return hits[: max(limit * 2, limit)]

    # ------------------------------------------------------------------
    # theorem registry lane
    # ------------------------------------------------------------------
    def _retrieve_registry(
        self,
        query: str,
        *,
        securities: Sequence[str],
        limit: int,
    ) -> List[FusionHit]:
        if not self.market_db_path.exists():
            return []

        conn = sqlite3.connect(str(self.market_db_path))
        conn.row_factory = sqlite3.Row
        try:
            existing = {
                row[0]
                for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            }
            if "theorem_registry" not in existing:
                return []

            rows = conn.execute(
                """
                SELECT entry_id, title, status, score, statement, assumptions_json, tags_json, securities_json, metadata_json
                FROM theorem_registry
                ORDER BY updated_at DESC, score DESC
                """
            ).fetchall()
        finally:
            conn.close()

        hits: List[FusionHit] = []
        for row in rows:
            reg_securities = self._json_load(row["securities_json"], default=[])
            if securities and reg_securities and not any(sec in reg_securities for sec in securities):
                continue

            assumptions = self._json_load(row["assumptions_json"], default=[])
            tags = self._json_load(row["tags_json"], default=[])
            text = (
                f"Statement: {row['statement']}\n"
                f"Assumptions: {'; '.join(str(x) for x in assumptions)}\n"
                f"Tags: {', '.join(str(x) for x in tags)}"
            )

            hits.append(
                FusionHit(
                    source_type="registry",
                    title=str(row["title"]),
                    score=float(row["score"] or 0.0),
                    excerpt=self._make_excerpt(text),
                    context_text=text,
                    metadata={
                        "security": ",".join(reg_securities) if reg_securities else "GLOBAL",
                        "entry_id": row["entry_id"],
                        "status": row["status"],
                        "native_score": float(row["score"] or 0.0),
                        "securities": reg_securities,
                        "metadata": self._json_load(row["metadata_json"], default={}),
                    },
                )
            )

        return hits[: max(limit * 2, limit)]

    # ------------------------------------------------------------------
    # book lane
    # ------------------------------------------------------------------
    def _retrieve_books(self, query: str, *, limit: int) -> List[FusionHit]:
        try:
            raw_hits = self.memory.retrieve(
                query,
                top_k=limit,
                candidate_k=max(limit * 4, 24),
            )
        except Exception:
            return []

        hits: List[FusionHit] = []
        for hit in raw_hits:
            text = str(hit.text)
            hits.append(
                FusionHit(
                    source_type="book",
                    title=f"{hit.file_name} | page {hit.page_no} | chunk {hit.chunk_no}",
                    score=float(getattr(hit, "score", 0.0)),
                    excerpt=self._make_excerpt(text),
                    context_text=text,
                    metadata={
                        "security": "BOOK",
                        "file_name": hit.file_name,
                        "file_path": getattr(hit, "file_path", None),
                        "page_no": hit.page_no,
                        "chunk_no": hit.chunk_no,
                        "dense_score": getattr(hit, "dense_score", None),
                        "lexical_score": getattr(hit, "lexical_score", None),
                    },
                )
            )
        return hits

    # ------------------------------------------------------------------
    # ranking
    # ------------------------------------------------------------------
    def _rank_hits(
        self,
        query: str,
        securities: Sequence[str],
        hits: Sequence[FusionHit],
        *,
        surface_query: bool,
    ) -> List[FusionHit]:
        q_tokens = set(self._tokenize(query))
        securities_set = {str(s) for s in securities}

        ranked: List[FusionHit] = []
        for hit in hits:
            score = float(hit.score or 0.0)
            text = f"{hit.title}\n{hit.context_text}"
            t_tokens = set(self._tokenize(text))
            overlap = len(q_tokens & t_tokens) / max(len(q_tokens), 1)
            score += 0.55 * overlap

            if hit.source_type == "bloomberg_memory":
                score += 0.15
                security = str(hit.metadata.get("security") or "GLOBAL")
                if security in securities_set:
                    score += 0.25
                if security == "GLOBAL":
                    score += 0.05
                if surface_query and hit.metadata.get("direct_surface_memory"):
                    score += 5.0
                elif surface_query:
                    note_type = str(hit.metadata.get("note_type") or "")
                    if note_type in {"options_surface_state", "options_surface_global_state"}:
                        score += 1.0

            elif hit.source_type == "registry":
                score += 0.04
                if surface_query:
                    score -= 0.15

            elif hit.source_type == "book":
                if surface_query:
                    score -= 0.50

            ranked.append(
                FusionHit(
                    source_type=hit.source_type,
                    title=hit.title,
                    score=score,
                    excerpt=hit.excerpt,
                    context_text=hit.context_text,
                    metadata=hit.metadata,
                )
            )

        ranked.sort(key=lambda h: h.score, reverse=True)
        return ranked

    @staticmethod
    def _surface_priority_key(hit: FusionHit) -> tuple:
        return (
            1 if bool(hit.metadata.get("direct_surface_memory")) else 0,
            1 if str(hit.metadata.get("security") or "GLOBAL") != "GLOBAL" else 0,
            hit.score,
        )

    def _dedupe_hits(self, hits: Sequence[FusionHit]) -> List[FusionHit]:
        out: List[FusionHit] = []
        seen: set[tuple[str, str, str]] = set()
        for hit in hits:
            security = str(hit.metadata.get("security") or "GLOBAL")
            key = (hit.source_type, hit.title, security)
            if key in seen:
                continue
            seen.add(key)
            out.append(hit)
        return out

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _make_excerpt(text: str, n: int = 500) -> str:
        flat = " ".join(str(text).split())
        return flat[:n]

    @staticmethod
    def _json_load(value: Any, default: Any) -> Any:
        try:
            if value is None:
                return default
            return json.loads(value)
        except Exception:
            return default

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return [tok.lower() for tok in _TOKEN_RE.findall(str(text)) if len(tok) > 1]

    @staticmethod
    def _looks_like_surface_query(query: str) -> bool:
        q = str(query).lower()
        return any(marker in q for marker in _SURFACE_MARKERS)


__all__ = [
    "FusionHit",
    "ResearchMemoryFusion",
]
