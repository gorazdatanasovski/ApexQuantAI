
from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import faiss  # type: ignore
import numpy as np
from sentence_transformers import SentenceTransformer


_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[\.\!\?])\s+|\n+")
_BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

_DEFINITION_PREFIX_RE = re.compile(
    r"^\s*(?:what\s+is|what['’]s|define|definition\s+of|meaning\s+of|explain)\s+",
    re.I,
)

_PREFACE_MARKERS = (
    "preface",
    "introduction",
    "contents",
    "table of contents",
)

_INDEX_MARKERS = (
    "index",
    "volterra process",
    "wiener integral",
    "yamada",
    "stochastic exponential",
    "rough heston",
)

_DEFINITION_PATTERNS = (
    "{concept} is ",
    "{concept} are ",
    "{concept} refers to ",
    "{concept} denotes ",
    "{concept} means ",
    "{concept} can be written as ",
    "we call {concept} ",
    "we say that {concept} ",
    "{concept} may be defined as ",
)

_CONCEPT_BOOK_HINTS: dict[str, tuple[str, ...]] = {
    "volterra": ("rough volatility",),
    "volterra process": ("rough volatility",),
    "volterra equation": ("rough volatility",),
    "convolution": ("rough volatility", "nualart"),
    "girsanov": ("shreve", "karatzas", "brownian"),
    "malliavin": ("malliavin", "nualart"),
    "stieltjes": ("malliavin", "nualart"),
    "semimartingale": ("shreve", "karatzas"),
    "ornstein": ("rough volatility", "shreve"),
    "ornstein uhlenbeck": ("rough volatility", "shreve"),
    "fbm": ("rough volatility", "nualart"),
    "fractional brownian motion": ("rough volatility", "nualart"),
}


@dataclass(frozen=True)
class RetrievalHit:
    score: float
    file_name: str
    file_path: str
    page_no: int
    chunk_no: int
    text: str
    dense_score: float | None = None
    lexical_score: float | None = None

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BookMemory:
    """
    Read-only query interface over the SQLite + FAISS state produced by the
    ingestion pipeline.

    Query-time goals:
    - keep retrieval fast
    - improve exact-definition/theorem lookup with cheap lexical reranking
    - favor the most likely books for topic-specific quantitative questions
    - avoid repeated model export work whenever a local exported model path exists

    Stability goals:
    - no persistent sqlite connection shared across threads
    - keep FAISS + embedding model resident in memory
    - open SQLite connections only inside fetch operations
    """

    def __init__(self, work_dir: str | Path = "rag_ingest_state"):
        self.work_dir = Path(work_dir).resolve()
        self.sqlite_path = self.work_dir / "state.sqlite3"
        self.runtime_profile_path = self.work_dir / "runtime_profile.json"
        self.faiss_path = self.work_dir / "final" / "index.faiss"

        self._validate_layout()
        self.profile = self._load_profile()
        self.index = faiss.read_index(str(self.faiss_path))
        self.model_ref, self.backend = self._resolve_model_reference()
        self.model = SentenceTransformer(
            self.model_ref,
            backend=self.backend,
            device="cpu",
        )
        self.query_prefix = self._infer_query_prefix()

    def close(self) -> None:
        # Compatibility method. SQLite connections are opened per fetch and
        # immediately closed, so there is no persistent DB handle to close.
        return None

    def _validate_layout(self) -> None:
        required = [self.sqlite_path, self.runtime_profile_path, self.faiss_path]
        missing = [str(path) for path in required if not path.exists()]
        if missing:
            raise FileNotFoundError(
                "QuantAI memory is incomplete. Missing: " + ", ".join(missing)
            )

    def _load_profile(self) -> Dict[str, Any]:
        payload = json.loads(self.runtime_profile_path.read_text(encoding="utf-8"))
        expected = {"model_name", "backend"}
        if not expected.issubset(payload):
            raise ValueError(
                f"runtime_profile.json is invalid. Expected keys {sorted(expected)}, got {sorted(payload)}"
            )
        return payload

    def _resolve_model_reference(self) -> tuple[str, str | None]:
        candidates: list[str] = []
        for key in ("exported_model_dir", "model_dir", "local_model_dir"):
            value = self.profile.get(key)
            if isinstance(value, str) and value.strip():
                candidates.append(value.strip())

        for raw in candidates:
            path = Path(raw)
            if not path.is_absolute():
                path = (self.work_dir / raw).resolve()
            if path.exists():
                return str(path), str(self.profile.get("backend") or "openvino")

        return str(self.profile["model_name"]), str(self.profile.get("backend") or "openvino")

    def _infer_query_prefix(self) -> str:
        ref = f"{self.model_ref} {self.profile.get('model_name', '')}".lower()
        if "bge" in ref:
            return _BGE_QUERY_PREFIX
        return ""

    @staticmethod
    def _normalize_query(query: str) -> str:
        return " ".join(str(query).split()).strip().strip('"').strip("'")

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return [tok.lower() for tok in _TOKEN_RE.findall(text) if len(tok) > 1]

    @classmethod
    def _concept_from_query(cls, query: str) -> str:
        q = cls._normalize_query(query)
        q = _DEFINITION_PREFIX_RE.sub("", q)
        return q.strip(" ?.!")

    @classmethod
    def _infer_query_kind(cls, query: str, query_kind: str | None) -> str:
        if query_kind:
            return query_kind

        q = cls._normalize_query(query)
        q_lower = q.lower()
        tokens = cls._tokenize(q)

        if _DEFINITION_PREFIX_RE.match(q):
            return "definition"

        # One-word and short noun-phrase prompts should default to definition.
        if len(tokens) <= 3:
            return "definition"

        if q_lower.startswith(("what ", "who ", "where ", "when ", "why ", "how ")):
            return "concept"

        return "concept"

    def _encode_query(self, query: str) -> np.ndarray:
        query_text = f"{self.query_prefix}{query}" if self.query_prefix else query
        emb = self.model.encode(
            [query_text],
            batch_size=1,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        arr = np.asarray(emb, dtype=np.float32)
        if arr.ndim != 2 or arr.shape[0] != 1:
            raise RuntimeError(f"Unexpected query embedding shape: {arr.shape}")
        return arr

    def _open_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.sqlite_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _fetch_rows(self, chunk_ids: Sequence[int]) -> Dict[int, sqlite3.Row]:
        valid_ids = [int(x) for x in chunk_ids if int(x) >= 0]
        if not valid_ids:
            return {}

        placeholders = ",".join("?" for _ in valid_ids)
        sql = (
            "SELECT id, file_name, file_path, page_no, chunk_no, text "
            f"FROM chunks WHERE id IN ({placeholders})"
        )

        conn = self._open_connection()
        try:
            rows = conn.execute(sql, valid_ids).fetchall()
        finally:
            conn.close()

        return {int(row["id"]): row for row in rows}

    @classmethod
    def _lexical_score(cls, query_terms: Sequence[str], text: str) -> float:
        if not query_terms:
            return 0.0
        t_tokens = set(cls._tokenize(text))
        overlap = sum(1 for tok in query_terms if tok in t_tokens) / max(len(query_terms), 1)
        return float(overlap)

    @classmethod
    def _phrase_bonus(cls, phrases: Sequence[str], text: str) -> float:
        if not phrases:
            return 0.0
        text_lower = text.lower()
        bonus = 0.0
        for phrase in phrases:
            p = phrase.lower().strip().strip('"')
            if len(p) >= 5 and p in text_lower:
                bonus += 0.18 if len(p.split()) >= 2 else 0.08
        return min(bonus, 0.42)

    @staticmethod
    def _equation_bonus(text: str, query_kind: str | None) -> float:
        if query_kind not in {"exact", "theorem", "derivation", "definition", "concept"}:
            return 0.0
        hits = 0
        for marker in ("=", "∫", "Cov", "mathbb", "dB", "dW", "dS", "H(", "V(", "K(", "Riccati"):
            if marker in text:
                hits += 1
        return min(0.03 * hits, 0.15)

    @staticmethod
    def _book_prior(file_name: str, preferred_books: Sequence[str]) -> float:
        if not preferred_books:
            return 0.0
        f = file_name.lower()
        score = 0.0
        for pref in preferred_books:
            p = pref.lower()
            if p in f:
                score += 0.22
        return min(score, 0.44)

    @staticmethod
    def _required_term_penalty(text: str, required_terms: Sequence[str]) -> float:
        if not required_terms:
            return 0.0
        lower = text.lower()
        hits = sum(1 for term in required_terms if term.lower() in lower)
        if hits == 0:
            return -0.18
        coverage = hits / max(len(required_terms), 1)
        return min(0.08 * coverage * len(required_terms), 0.20)

    @staticmethod
    def _dense_component(score: float) -> float:
        return float(score)

    @classmethod
    def _definition_bonus(
        cls,
        query: str,
        text: str,
        query_kind: str,
        extra_phrases: Sequence[str] | None = None,
    ) -> float:
        if query_kind not in {"definition", "concept"}:
            return 0.0

        lower = text.lower()
        concept = cls._concept_from_query(query).lower()
        phrases = [concept, *(extra_phrases or [])]

        bonus = 0.0
        for phrase in phrases:
            p = phrase.lower().strip().strip('"').strip("'")
            if not p:
                continue
            if p in lower:
                bonus += 0.08
            for pattern in _DEFINITION_PATTERNS:
                if pattern.format(concept=p) in lower:
                    bonus += 0.22
                    break

        if any(marker in lower for marker in ("definition", "we say", "is called", "consists of", "special role")):
            bonus += 0.08

        return min(bonus, 0.46)

    @staticmethod
    def _preface_penalty(text: str, file_name: str, query_kind: str) -> float:
        if query_kind not in {"definition", "concept"}:
            return 0.0

        lower = text.lower()
        name_lower = file_name.lower()

        if any(marker in name_lower for marker in _PREFACE_MARKERS):
            return -0.25
        if any(marker in lower[:180] for marker in _PREFACE_MARKERS):
            return -0.22
        return 0.0

    @staticmethod
    def _looks_index_like(text: str, file_name: str) -> bool:
        t = " ".join(str(text).split())
        lower = t.lower()

        if len(t) < 140:
            return False

        comma_count = t.count(",")
        digit_count = sum(ch.isdigit() for ch in t)

        if "index" in file_name.lower():
            return True

        if comma_count >= 12 and digit_count >= 18:
            return True

        if "chapter" not in lower and comma_count >= 16 and ";" not in t and "." not in t[:220]:
            return True

        if all(marker in lower for marker in _INDEX_MARKERS[:3]):
            return True

        return False

    @classmethod
    def _index_penalty(cls, text: str, file_name: str, query_kind: str) -> float:
        if query_kind not in {"definition", "exact", "concept"}:
            return 0.0
        return -0.65 if cls._looks_index_like(text, file_name) else 0.0

    @classmethod
    def _sentence_density_bonus(cls, text: str, query_kind: str) -> float:
        if query_kind not in {"definition", "concept"}:
            return 0.0

        sentences = [s for s in _SENTENCE_SPLIT_RE.split(text) if len(s.strip()) >= 30]
        if not sentences:
            return -0.06
        if len(sentences) >= 2:
            return 0.04
        return 0.0

    @classmethod
    def _concept_book_hints(cls, query: str) -> list[str]:
        concept = cls._concept_from_query(query).lower()
        hints: list[str] = []
        for marker, books in _CONCEPT_BOOK_HINTS.items():
            if marker in concept:
                hints.extend(books)
        return list(dict.fromkeys(hints))

    @classmethod
    def _auto_required_terms(cls, query: str, required_terms: Sequence[str]) -> list[str]:
        if required_terms:
            return [t.lower() for t in required_terms if t]

        concept = cls._concept_from_query(query)
        tokens = cls._tokenize(concept)

        # keep the most meaningful few terms for precision without over-constraining
        return tokens[:4]

    @staticmethod
    def _deduplicate(hits: Iterable[RetrievalHit], top_k: int) -> list[RetrievalHit]:
        out: list[RetrievalHit] = []
        seen_text: set[tuple[str, int, int]] = set()
        for hit in hits:
            key = (hit.file_name, hit.page_no, hit.chunk_no)
            if key in seen_text:
                continue
            seen_text.add(key)
            out.append(hit)
            if len(out) >= top_k:
                break
        return out

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        candidate_k: int | None = None,
        *,
        preferred_books: Sequence[str] | None = None,
        required_terms: Sequence[str] | None = None,
        extra_phrases: Sequence[str] | None = None,
        query_kind: str | None = None,
    ) -> List[RetrievalHit]:
        if top_k <= 0:
            return []

        normalized_query = self._normalize_query(query)
        inferred_kind = self._infer_query_kind(normalized_query, query_kind)

        preferred_books = list(preferred_books or [])
        preferred_books.extend(self._concept_book_hints(normalized_query))
        preferred_books = list(dict.fromkeys(preferred_books))

        required_terms = self._auto_required_terms(normalized_query, required_terms or [])
        extra_phrases = [p for p in (extra_phrases or []) if p]

        query_terms = self._tokenize(normalized_query)

        default_candidate_k = top_k * 12 if inferred_kind == "definition" else top_k * 8
        candidate_k = max(int(candidate_k or default_candidate_k), top_k)

        q = self._encode_query(normalized_query)
        scores, ids = self.index.search(q, int(candidate_k))
        rows = self._fetch_rows(ids[0].tolist())

        ranked: list[tuple[float, RetrievalHit]] = []
        for dense_score, chunk_id in zip(scores[0].tolist(), ids[0].tolist()):
            cid = int(chunk_id)
            if cid < 0:
                continue

            row = rows.get(cid)
            if row is None:
                continue

            text = str(row["text"])
            file_name = str(row["file_name"])

            dense = self._dense_component(float(dense_score))
            lexical = self._lexical_score(query_terms, text)
            phrase = self._phrase_bonus([normalized_query, *extra_phrases, *required_terms], text)
            prior = self._book_prior(file_name, preferred_books)
            required = self._required_term_penalty(text, required_terms)
            equation = self._equation_bonus(text, inferred_kind)
            definition = self._definition_bonus(
                query=normalized_query,
                text=text,
                query_kind=inferred_kind,
                extra_phrases=extra_phrases,
            )
            index_penalty = self._index_penalty(text, file_name, inferred_kind)
            preface_penalty = self._preface_penalty(text, file_name, inferred_kind)
            sentence_bonus = self._sentence_density_bonus(text, inferred_kind)

            hybrid = (
                dense
                + 0.24 * lexical
                + phrase
                + prior
                + required
                + equation
                + definition
                + sentence_bonus
                + index_penalty
                + preface_penalty
            )

            ranked.append(
                (
                    hybrid,
                    RetrievalHit(
                        score=float(hybrid),
                        file_name=file_name,
                        file_path=str(row["file_path"]),
                        page_no=int(row["page_no"]),
                        chunk_no=int(row["chunk_no"]),
                        text=text,
                        dense_score=float(dense_score),
                        lexical_score=float(lexical),
                    ),
                )
            )

        ranked.sort(key=lambda x: x[0], reverse=True)
        return self._deduplicate((hit for _, hit in ranked), top_k=top_k)
