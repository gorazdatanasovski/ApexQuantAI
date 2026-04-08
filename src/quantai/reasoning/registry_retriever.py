from __future__ import annotations

import json
import math
import re
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


@dataclass(frozen=True)
class RegistryHit:
    score: float
    entry_id: str
    title: str
    status: str
    statement: str
    assumptions: List[str]
    tags: List[str]
    securities: List[str]
    benchmark_security: Optional[str]
    excerpt: str
    metadata: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TheoremRegistryRetriever:
    """
    Retrieval layer over theorem_registry.

    Purpose:
    - search previously generated theorem artifacts
    - rank accepted artifacts above weaker candidates when relevance is similar
    - return compact retrieval hits that can be injected into engine prompts

    Retrieval model:
    - lexical token overlap on title + statement + assumptions + tags + securities
    - phrase bonus for exact substring match
    - status prior:
        accepted > candidate/speculative_candidate > draft > rejected/archived
    """

    DEFAULT_TABLE = "theorem_registry"

    def __init__(
        self,
        db_path: str | Path = "data/market_history.sqlite",
        table_name: str = DEFAULT_TABLE,
    ) -> None:
        self.db_path = Path(db_path)
        self.table_name = str(table_name)
        if not self.db_path.exists():
            raise FileNotFoundError(f"theorem registry database not found: {self.db_path}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 5,
        candidate_k: int = 100,
        allowed_statuses: Optional[Sequence[str]] = None,
        security: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[RegistryHit]:
        query = str(query).strip()
        if not query:
            return []

        rows = self._load_rows(
            limit=max(int(candidate_k), int(top_k)),
            allowed_statuses=allowed_statuses,
            security=security,
            tag=tag,
        )
        q_tokens = self._tokenize(query)
        q_phrase = query.lower()

        scored: List[tuple[float, Dict[str, Any]]] = []
        for row in rows:
            score = self._score_row(query_tokens=q_tokens, query_phrase=q_phrase, row=row)
            if score <= 0:
                continue
            scored.append((score, row))

        scored.sort(key=lambda x: x[0], reverse=True)

        hits: List[RegistryHit] = []
        for score, row in scored[: int(top_k)]:
            hits.append(self._row_to_hit(row=row, score=score, query_tokens=q_tokens))
        return hits

    def list_recent(
        self,
        *,
        top_k: int = 10,
        allowed_statuses: Optional[Sequence[str]] = None,
    ) -> List[RegistryHit]:
        rows = self._load_rows(limit=int(top_k), allowed_statuses=allowed_statuses)
        hits: List[RegistryHit] = []
        for row in rows[: int(top_k)]:
            hits.append(self._row_to_hit(row=row, score=0.0, query_tokens=[]))
        return hits

    def get_entry_context(self, entry_id: str) -> Dict[str, Any]:
        row = self._fetch_one(
            f"SELECT * FROM {self.table_name} WHERE entry_id = ?",
            [entry_id],
        )
        if row is None:
            raise KeyError(f"no theorem registry entry found for entry_id={entry_id!r}")
        parsed = self._parse_row(row)
        parsed["context_text"] = self._compose_context(parsed)
        return parsed

    # ------------------------------------------------------------------
    # SQL loading
    # ------------------------------------------------------------------
    def _load_rows(
        self,
        *,
        limit: int,
        allowed_statuses: Optional[Sequence[str]] = None,
        security: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        clauses = []
        params: List[Any] = []

        if allowed_statuses:
            placeholders = ",".join("?" for _ in allowed_statuses)
            clauses.append(f"status IN ({placeholders})")
            params.extend(list(allowed_statuses))

        if security:
            clauses.append("LOWER(securities_json) LIKE ?")
            params.append(f"%{str(security).lower()}%")

        if tag:
            clauses.append("LOWER(tags_json) LIKE ?")
            params.append(f"%{str(tag).lower()}%")

        sql = f"SELECT * FROM {self.table_name}"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY updated_at DESC, score DESC LIMIT ?"
        params.append(int(limit))

        rows = self._fetch_all(sql, params)
        return [self._parse_row(r) for r in rows]

    def _fetch_one(self, sql: str, params: Sequence[Any]) -> Optional[sqlite3.Row]:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            return conn.execute(sql, list(params)).fetchone()
        finally:
            conn.close()

    def _fetch_all(self, sql: str, params: Sequence[Any]) -> List[sqlite3.Row]:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            return conn.execute(sql, list(params)).fetchall()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Parsing / ranking
    # ------------------------------------------------------------------
    def _parse_row(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "entry_id": row["entry_id"],
            "title": row["title"],
            "status": row["status"],
            "score": float(row["score"]),
            "statement": row["statement"],
            "assumptions": self._json_load_list(row["assumptions_json"]),
            "variables": self._json_load_dict(row["variables_json"]),
            "tags": self._json_load_list(row["tags_json"]),
            "securities": self._json_load_list(row["securities_json"]),
            "benchmark_security": row["benchmark_security"],
            "empirical_signature": self._json_load_any(row["empirical_signature_json"]),
            "symbolic_agenda": self._json_load_any(row["symbolic_agenda_json"]),
            "failure_conditions": self._json_load_list(row["failure_conditions_json"]),
            "next_actions": self._json_load_list(row["next_actions_json"]),
            "source_kind": row["source_kind"],
            "source_ref": row["source_ref"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "artifact_hash": row["artifact_hash"],
            "metadata": self._json_load_dict(row["metadata_json"]),
        }

    def _score_row(
        self,
        *,
        query_tokens: List[str],
        query_phrase: str,
        row: Dict[str, Any],
    ) -> float:
        haystack_fields = [
            row["title"],
            row["statement"],
            " ".join(row["assumptions"]),
            " ".join(row["tags"]),
            " ".join(row["securities"]),
            json.dumps(row["variables"], default=str),
            json.dumps(row["metadata"], default=str),
        ]
        haystack = "\n".join(str(x) for x in haystack_fields if x)
        h_tokens = set(self._tokenize(haystack))
        q_token_set = set(query_tokens)

        if not q_token_set:
            return 0.0

        overlap = len(q_token_set & h_tokens) / max(len(q_token_set), 1)
        title_tokens = set(self._tokenize(str(row["title"])))
        statement_tokens = set(self._tokenize(str(row["statement"])))

        title_overlap = len(q_token_set & title_tokens) / max(len(q_token_set), 1)
        statement_overlap = len(q_token_set & statement_tokens) / max(len(q_token_set), 1)

        phrase_bonus = 0.0
        low_hay = haystack.lower()
        if query_phrase and query_phrase in low_hay:
            phrase_bonus += 0.30

        exact_token_bonus = 0.0
        for tok in query_tokens:
            if tok in str(row["title"]).lower():
                exact_token_bonus += 0.015
            if tok in str(row["statement"]).lower():
                exact_token_bonus += 0.010

        status_prior = self._status_prior(str(row["status"]))
        native_score = float(row.get("score", 0.0))

        return (
            0.55 * overlap
            + 0.20 * title_overlap
            + 0.15 * statement_overlap
            + phrase_bonus
            + exact_token_bonus
            + 0.08 * status_prior
            + 0.02 * min(max(native_score, 0.0), 1.0)
        )

    @staticmethod
    def _status_prior(status: str) -> float:
        s = str(status).lower().strip()
        if s == "accepted":
            return 1.0
        if s in {"candidate", "speculative_candidate", "approved_candidate"}:
            return 0.75
        if s in {"draft", "proposed"}:
            return 0.40
        if s in {"archived"}:
            return 0.10
        if s in {"rejected", "failed"}:
            return -0.20
        return 0.25

    def _row_to_hit(
        self,
        *,
        row: Dict[str, Any],
        score: float,
        query_tokens: Sequence[str],
    ) -> RegistryHit:
        context = self._compose_context(row)
        excerpt = self._best_excerpt(context, query_tokens=query_tokens, limit_chars=700)
        return RegistryHit(
            score=float(score),
            entry_id=row["entry_id"],
            title=str(row["title"]),
            status=str(row["status"]),
            statement=str(row["statement"]),
            assumptions=list(row["assumptions"]),
            tags=list(row["tags"]),
            securities=list(row["securities"]),
            benchmark_security=row["benchmark_security"],
            excerpt=excerpt,
            metadata={
                "source_kind": row["source_kind"],
                "source_ref": row["source_ref"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "artifact_hash": row["artifact_hash"],
                "variables": row["variables"],
                "empirical_signature": row["empirical_signature"],
                "symbolic_agenda": row["symbolic_agenda"],
                "next_actions": row["next_actions"],
            },
        )

    @staticmethod
    def _compose_context(row: Dict[str, Any]) -> str:
        blocks = [
            f"Title: {row['title']}",
            f"Status: {row['status']}",
            f"Statement: {row['statement']}",
        ]
        if row["assumptions"]:
            blocks.append("Assumptions: " + "; ".join(str(x) for x in row["assumptions"]))
        if row["tags"]:
            blocks.append("Tags: " + ", ".join(str(x) for x in row["tags"]))
        if row["securities"]:
            blocks.append("Securities: " + ", ".join(str(x) for x in row["securities"]))
        if row["empirical_signature"] not in (None, "", [], {}):
            blocks.append("Empirical signature: " + json.dumps(row["empirical_signature"], default=str))
        if row["symbolic_agenda"] not in (None, "", [], {}):
            blocks.append("Symbolic agenda: " + json.dumps(row["symbolic_agenda"], default=str))
        if row["failure_conditions"]:
            blocks.append("Failure conditions: " + "; ".join(str(x) for x in row["failure_conditions"]))
        if row["next_actions"]:
            blocks.append("Next actions: " + "; ".join(str(x) for x in row["next_actions"]))
        return "\n".join(blocks)

    @classmethod
    def _best_excerpt(
        cls,
        text: str,
        *,
        query_tokens: Sequence[str],
        limit_chars: int = 700,
    ) -> str:
        parts = re.split(r"(?<=[\.\!\?])\s+|\n+", str(text))
        q = set(tok.lower() for tok in query_tokens if tok)
        scored: List[tuple[float, str]] = []
        for part in parts:
            sent = " ".join(part.split())
            if len(sent) < 20:
                continue
            toks = set(cls._tokenize(sent))
            overlap = len(q & toks) / max(len(q), 1) if q else 0.0
            score = overlap + min(len(sent) / 500.0, 0.10)
            scored.append((score, sent))
        scored.sort(key=lambda x: x[0], reverse=True)

        out: List[str] = []
        n_chars = 0
        for _, sent in scored:
            if n_chars + len(sent) > limit_chars and out:
                break
            out.append(sent)
            n_chars += len(sent) + 1
            if n_chars >= limit_chars:
                break

        if not out:
            return text[:limit_chars].rstrip()
        return " ".join(out).rstrip()

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return [tok.lower() for tok in _TOKEN_RE.findall(str(text)) if len(tok) > 1]

    @staticmethod
    def _json_load_any(value: str) -> Any:
        try:
            return json.loads(value) if value else None
        except Exception:
            return value

    @classmethod
    def _json_load_list(cls, value: str) -> List[str]:
        out = cls._json_load_any(value)
        if out is None:
            return []
        if isinstance(out, (list, tuple, set)):
            return [str(x) for x in out if str(x).strip()]
        return [str(out)]

    @classmethod
    def _json_load_dict(cls, value: str) -> Dict[str, Any]:
        out = cls._json_load_any(value)
        if isinstance(out, dict):
            return dict(out)
        if out is None:
            return {}
        return {"value": out}


__all__ = ["TheoremRegistryRetriever", "RegistryHit"]
