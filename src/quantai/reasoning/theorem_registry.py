from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence


@dataclass(frozen=True)
class TheoremRegistryEntry:
    entry_id: str
    title: str
    status: str
    score: float
    statement: str
    assumptions: List[str]
    variables: Dict[str, Any]
    tags: List[str]
    securities: List[str]
    benchmark_security: Optional[str]
    empirical_signature: Any
    symbolic_agenda: Any
    failure_conditions: List[str]
    next_actions: List[str]
    source_kind: str
    source_ref: Optional[str]
    created_at: str
    updated_at: str
    artifact_hash: str
    metadata: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def as_markdown(self) -> str:
        lines = [
            f"# {self.title}",
            "",
            f"- Entry ID: {self.entry_id}",
            f"- Status: {self.status}",
            f"- Score: {self.score:.3f}",
            f"- Source kind: {self.source_kind}",
            f"- Created at: {self.created_at}",
            f"- Updated at: {self.updated_at}",
        ]
        if self.securities:
            lines.append(f"- Securities: {', '.join(self.securities)}")
        if self.benchmark_security:
            lines.append(f"- Benchmark security: {self.benchmark_security}")
        if self.tags:
            lines.append(f"- Tags: {', '.join(self.tags)}")

        lines.extend([
            "",
            "## Statement",
            self.statement or "NA",
            "",
            "## Assumptions",
        ])
        lines.extend([f"- {x}" for x in self.assumptions] or ["- None"])

        lines.extend(["", "## Variables"])
        if self.variables:
            lines.append("```json")
            lines.append(json.dumps(self.variables, indent=2, default=str))
            lines.append("```")
        else:
            lines.append("None")

        lines.extend(["", "## Empirical signature"])
        if self.empirical_signature not in (None, "", [], {}):
            lines.append("```json")
            lines.append(json.dumps(self.empirical_signature, indent=2, default=str))
            lines.append("```")
        else:
            lines.append("None")

        lines.extend(["", "## Symbolic agenda"])
        if self.symbolic_agenda not in (None, "", [], {}):
            lines.append("```json")
            lines.append(json.dumps(self.symbolic_agenda, indent=2, default=str))
            lines.append("```")
        else:
            lines.append("None")

        lines.extend(["", "## Failure conditions"])
        lines.extend([f"- {x}" for x in self.failure_conditions] or ["- None"])

        lines.extend(["", "## Next actions"])
        lines.extend([f"- {x}" for x in self.next_actions] or ["- None"])

        if self.metadata:
            lines.extend(["", "## Metadata", "```json", json.dumps(self.metadata, indent=2, default=str), "```"])
        return "\n".join(lines)


class TheoremRegistry:
    """
    Persistent registry for QuantAI theorem artifacts.

    Purpose:
    - register theorem candidates from theorem_lab outputs
    - promote accepted artifacts into a durable searchable store
    - track lifecycle status: draft / candidate / accepted / rejected / archived
    - export markdown/json sidecars for human review
    """

    DEFAULT_TABLE = "theorem_registry"

    def __init__(
        self,
        db_path: str | Path = "data/market_history.sqlite",
        artifact_dir: str | Path = "artifacts/theorem_registry",
    ) -> None:
        self.db_path = Path(db_path)
        self.artifact_dir = Path(artifact_dir)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    # ---------------- public API ----------------

    def register_artifact(
        self,
        artifact: Mapping[str, Any] | Any,
        *,
        source_kind: str = "manual",
        source_ref: Optional[str] = None,
        default_status: str = "candidate",
        tags: Sequence[str] | None = None,
        securities: Sequence[str] | None = None,
        benchmark_security: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        dedupe_on_hash: bool = True,
    ) -> Dict[str, Any]:
        payload = self._normalize_artifact_payload(
            artifact,
            source_kind=source_kind,
            source_ref=source_ref,
            default_status=default_status,
            tags=tags,
            securities=securities,
            benchmark_security=benchmark_security,
            metadata=metadata,
        )

        if dedupe_on_hash:
            existing = self.find_by_hash(payload["artifact_hash"])
            if existing is not None:
                return {
                    "action": "existing",
                    "entry_id": existing.entry_id,
                    "artifact_hash": existing.artifact_hash,
                    "status": existing.status,
                    "title": existing.title,
                }

        self._insert_payload(payload)
        entry = self.get_entry(payload["entry_id"])
        self._write_sidecars(entry)

        return {
            "action": "inserted",
            "entry_id": entry.entry_id,
            "artifact_hash": entry.artifact_hash,
            "status": entry.status,
            "title": entry.title,
        }

    def register_from_lab_result(
        self,
        lab_result: Mapping[str, Any] | Any,
        *,
        source_ref: Optional[str] = None,
        default_status: str = "candidate",
        dedupe_on_hash: bool = True,
    ) -> Dict[str, Any]:
        result_payload = self._coerce_mapping(lab_result)
        selected = result_payload.get("selected")
        if selected is None:
            raise ValueError("lab_result does not contain a `selected` artifact")
        source_kind = "theorem_lab"
        metadata = {
            "lab_result_keys": sorted(result_payload.keys()),
            "lab_result_score": result_payload.get("lab_score"),
            "lab_status": result_payload.get("status"),
        }
        return self.register_artifact(
            selected,
            source_kind=source_kind,
            source_ref=source_ref,
            default_status=default_status,
            tags=self._coerce_list((self._coerce_mapping(selected)).get("tags")),
            securities=self._coerce_list((self._coerce_mapping(selected)).get("securities")),
            benchmark_security=(self._coerce_mapping(selected)).get("benchmark_security"),
            metadata=metadata,
            dedupe_on_hash=dedupe_on_hash,
        )

    def get_entry(self, entry_id: str) -> TheoremRegistryEntry:
        row = self._fetch_one("SELECT * FROM theorem_registry WHERE entry_id = ?", [entry_id])
        if row is None:
            raise KeyError(f"No theorem registry entry found for entry_id={entry_id!r}")
        return self._row_to_entry(row)

    def find_by_hash(self, artifact_hash: str) -> Optional[TheoremRegistryEntry]:
        row = self._fetch_one("SELECT * FROM theorem_registry WHERE artifact_hash = ?", [artifact_hash])
        return None if row is None else self._row_to_entry(row)

    def list_entries(
        self,
        *,
        status: Optional[str] = None,
        security: Optional[str] = None,
        tag: Optional[str] = None,
        title_contains: Optional[str] = None,
        limit: int = 50,
    ) -> List[TheoremRegistryEntry]:
        clauses = []
        params: List[Any] = []

        if status:
            clauses.append("status = ?")
            params.append(status)

        if title_contains:
            clauses.append("LOWER(title) LIKE ?")
            params.append(f"%{title_contains.lower()}%")

        if security:
            clauses.append("LOWER(securities_json) LIKE ?")
            params.append(f"%{security.lower()}%")

        if tag:
            clauses.append("LOWER(tags_json) LIKE ?")
            params.append(f"%{tag.lower()}%")

        sql = "SELECT * FROM theorem_registry"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY updated_at DESC, score DESC LIMIT ?"
        params.append(int(limit))

        rows = self._fetch_all(sql, params)
        return [self._row_to_entry(row) for row in rows]

    def search_entries(
        self,
        query: str,
        *,
        limit: int = 20,
    ) -> List[TheoremRegistryEntry]:
        q = str(query).strip().lower()
        if not q:
            return self.list_entries(limit=limit)

        sql = """
        SELECT * FROM theorem_registry
        WHERE LOWER(title) LIKE ?
           OR LOWER(statement) LIKE ?
           OR LOWER(tags_json) LIKE ?
           OR LOWER(securities_json) LIKE ?
           OR LOWER(metadata_json) LIKE ?
        ORDER BY score DESC, updated_at DESC
        LIMIT ?
        """
        like = f"%{q}%"
        rows = self._fetch_all(sql, [like, like, like, like, like, int(limit)])
        return [self._row_to_entry(row) for row in rows]

    def update_status(
        self,
        entry_id: str,
        status: str,
        *,
        note: Optional[str] = None,
        metadata_updates: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        entry = self.get_entry(entry_id)
        metadata = dict(entry.metadata)
        if note:
            metadata.setdefault("status_notes", []).append(note)
        if metadata_updates:
            metadata.update(metadata_updates)

        now = self._utc_now()
        self._execute(
            """
            UPDATE theorem_registry
            SET status = ?, updated_at = ?, metadata_json = ?
            WHERE entry_id = ?
            """,
            [status, now, json.dumps(metadata, default=str), entry_id],
        )
        updated = self.get_entry(entry_id)
        self._write_sidecars(updated)
        return {
            "entry_id": updated.entry_id,
            "status": updated.status,
            "updated_at": updated.updated_at,
        }

    def export_entry(
        self,
        entry_id: str,
        *,
        directory: str | Path | None = None,
    ) -> Dict[str, Any]:
        entry = self.get_entry(entry_id)
        return self._write_sidecars(entry, directory=directory)

    # ---------------- internals ----------------

    def _ensure_schema(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS theorem_registry (
                    entry_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    score REAL NOT NULL,
                    statement TEXT NOT NULL,
                    assumptions_json TEXT NOT NULL,
                    variables_json TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    securities_json TEXT NOT NULL,
                    benchmark_security TEXT,
                    empirical_signature_json TEXT NOT NULL,
                    symbolic_agenda_json TEXT NOT NULL,
                    failure_conditions_json TEXT NOT NULL,
                    next_actions_json TEXT NOT NULL,
                    source_kind TEXT NOT NULL,
                    source_ref TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    artifact_hash TEXT NOT NULL UNIQUE,
                    metadata_json TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_theorem_registry_status ON theorem_registry(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_theorem_registry_score ON theorem_registry(score)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_theorem_registry_updated_at ON theorem_registry(updated_at)")
            conn.commit()
        finally:
            conn.close()

    def _normalize_artifact_payload(
        self,
        artifact: Mapping[str, Any] | Any,
        *,
        source_kind: str,
        source_ref: Optional[str],
        default_status: str,
        tags: Sequence[str] | None,
        securities: Sequence[str] | None,
        benchmark_security: Optional[str],
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        obj = self._coerce_mapping(artifact)
        title = str(
            obj.get("title")
            or obj.get("name")
            or obj.get("theorem_name")
            or "Untitled theorem artifact"
        ).strip()

        statement = str(
            obj.get("statement")
            or obj.get("theorem_statement")
            or obj.get("claim")
            or ""
        ).strip()
        if not statement:
            raise ValueError("artifact does not contain a theorem statement")

        status = str(obj.get("status") or default_status).strip()
        score = self._safe_float(obj.get("score"), default=0.0)

        assumptions = self._coerce_list(obj.get("assumptions"))
        variables = self._coerce_dict(obj.get("variables"))
        tags_final = self._unique(self._coerce_list(obj.get("tags")) + list(tags or []))
        securities_final = self._unique(self._coerce_list(obj.get("securities")) + list(securities or []))
        benchmark_final = (
            benchmark_security
            or obj.get("benchmark_security")
            or obj.get("benchmark")
        )

        empirical_signature = obj.get("empirical_signature")
        if empirical_signature is None:
            empirical_signature = obj.get("empirical_tests")

        symbolic_agenda = obj.get("symbolic_agenda")
        if symbolic_agenda is None:
            symbolic_agenda = obj.get("symbolic_tasks")

        failure_conditions = self._coerce_list(obj.get("failure_conditions"))
        next_actions = self._coerce_list(obj.get("next_actions"))

        meta = dict(metadata or {})
        for key in ("query", "lab_score", "verdict", "warnings", "selected_rank"):
            if key in obj and key not in meta:
                meta[key] = obj.get(key)

        artifact_hash = self._compute_artifact_hash(
            title=title,
            statement=statement,
            assumptions=assumptions,
            variables=variables,
            securities=securities_final,
            benchmark_security=benchmark_final,
        )
        now = self._utc_now()
        entry_id = str(obj.get("entry_id") or f"thm_{uuid.uuid4().hex[:16]}")

        return {
            "entry_id": entry_id,
            "title": title,
            "status": status,
            "score": float(score),
            "statement": statement,
            "assumptions": assumptions,
            "variables": variables,
            "tags": tags_final,
            "securities": securities_final,
            "benchmark_security": benchmark_final,
            "empirical_signature": empirical_signature,
            "symbolic_agenda": symbolic_agenda,
            "failure_conditions": failure_conditions,
            "next_actions": next_actions,
            "source_kind": str(source_kind),
            "source_ref": source_ref,
            "created_at": now,
            "updated_at": now,
            "artifact_hash": artifact_hash,
            "metadata": meta,
        }

    def _insert_payload(self, payload: Dict[str, Any]) -> None:
        self._execute(
            """
            INSERT INTO theorem_registry (
                entry_id, title, status, score, statement,
                assumptions_json, variables_json, tags_json, securities_json, benchmark_security,
                empirical_signature_json, symbolic_agenda_json, failure_conditions_json, next_actions_json,
                source_kind, source_ref, created_at, updated_at, artifact_hash, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                payload["entry_id"],
                payload["title"],
                payload["status"],
                payload["score"],
                payload["statement"],
                json.dumps(payload["assumptions"], default=str),
                json.dumps(payload["variables"], default=str),
                json.dumps(payload["tags"], default=str),
                json.dumps(payload["securities"], default=str),
                payload["benchmark_security"],
                json.dumps(payload["empirical_signature"], default=str),
                json.dumps(payload["symbolic_agenda"], default=str),
                json.dumps(payload["failure_conditions"], default=str),
                json.dumps(payload["next_actions"], default=str),
                payload["source_kind"],
                payload["source_ref"],
                payload["created_at"],
                payload["updated_at"],
                payload["artifact_hash"],
                json.dumps(payload["metadata"], default=str),
            ],
        )

    def _row_to_entry(self, row: sqlite3.Row) -> TheoremRegistryEntry:
        return TheoremRegistryEntry(
            entry_id=row["entry_id"],
            title=row["title"],
            status=row["status"],
            score=float(row["score"]),
            statement=row["statement"],
            assumptions=self._json_load_list(row["assumptions_json"]),
            variables=self._json_load_dict(row["variables_json"]),
            tags=self._json_load_list(row["tags_json"]),
            securities=self._json_load_list(row["securities_json"]),
            benchmark_security=row["benchmark_security"],
            empirical_signature=self._json_load_any(row["empirical_signature_json"]),
            symbolic_agenda=self._json_load_any(row["symbolic_agenda_json"]),
            failure_conditions=self._json_load_list(row["failure_conditions_json"]),
            next_actions=self._json_load_list(row["next_actions_json"]),
            source_kind=row["source_kind"],
            source_ref=row["source_ref"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            artifact_hash=row["artifact_hash"],
            metadata=self._json_load_dict(row["metadata_json"]),
        )

    def _write_sidecars(
        self,
        entry: TheoremRegistryEntry,
        *,
        directory: str | Path | None = None,
    ) -> Dict[str, Any]:
        directory = Path(directory) if directory is not None else self.artifact_dir
        directory.mkdir(parents=True, exist_ok=True)

        slug = self._slugify(f"{entry.title}_{entry.entry_id}")
        md_path = directory / f"{slug}.md"
        json_path = directory / f"{slug}.json"

        md_path.write_text(entry.as_markdown(), encoding="utf-8")
        json_path.write_text(json.dumps(entry.as_dict(), indent=2, default=str), encoding="utf-8")

        return {
            "entry_id": entry.entry_id,
            "markdown": str(md_path),
            "json": str(json_path),
        }

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

    def _execute(self, sql: str, params: Sequence[Any]) -> None:
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute(sql, list(params))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _compute_artifact_hash(
        *,
        title: str,
        statement: str,
        assumptions: Sequence[str],
        variables: Mapping[str, Any],
        securities: Sequence[str],
        benchmark_security: Optional[str],
    ) -> str:
        payload = {
            "title": title,
            "statement": statement,
            "assumptions": list(assumptions),
            "variables": dict(variables),
            "securities": list(securities),
            "benchmark_security": benchmark_security,
        }
        text = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _coerce_mapping(obj: Mapping[str, Any] | Any) -> Dict[str, Any]:
        if isinstance(obj, Mapping):
            return dict(obj)
        if hasattr(obj, "as_dict") and callable(obj.as_dict):
            out = obj.as_dict()
            if isinstance(out, Mapping):
                return dict(out)
        if hasattr(obj, "__dict__"):
            return dict(obj.__dict__)
        raise TypeError("artifact must be a mapping-like object or expose as_dict()")

    @staticmethod
    def _coerce_list(value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, (list, tuple, set)):
            return [str(x) for x in value if str(x).strip()]
        return [str(value)]

    @staticmethod
    def _coerce_dict(value: Any) -> Dict[str, Any]:
        if value is None:
            return {}
        if isinstance(value, Mapping):
            return dict(value)
        return {"value": value}

    @staticmethod
    def _json_load_any(value: str) -> Any:
        try:
            return json.loads(value) if value else None
        except Exception:
            return value

    @classmethod
    def _json_load_list(cls, value: str) -> List[str]:
        out = cls._json_load_any(value)
        return cls._coerce_list(out)

    @classmethod
    def _json_load_dict(cls, value: str) -> Dict[str, Any]:
        out = cls._json_load_any(value)
        return cls._coerce_dict(out)

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except Exception:
            return float(default)

    @staticmethod
    def _utc_now() -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    @staticmethod
    def _slugify(text: str) -> str:
        out = []
        for ch in str(text):
            if ch.isalnum():
                out.append(ch.lower())
            else:
                out.append("_")
        slug = "".join(out)
        while "__" in slug:
            slug = slug.replace("__", "_")
        return slug.strip("_")

    @staticmethod
    def _unique(items: Iterable[str]) -> List[str]:
        out: List[str] = []
        seen: set[str] = set()
        for item in items:
            key = str(item).strip()
            if not key or key.lower() in seen:
                continue
            seen.add(key.lower())
            out.append(key)
        return out


__all__ = ["TheoremRegistry", "TheoremRegistryEntry"]
