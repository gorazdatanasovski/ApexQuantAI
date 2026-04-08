from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence


_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[\.\!\?])\s+|\n+")
_CLAUSE_SPLIT_RE = re.compile(r"\s*[;•·]\s*")
_WHAT_IS_RE = re.compile(r"^(?:what is|what's|define|meaning of|explain|state)\s+", re.I)
_COPULA_RE = re.compile(
    r"\b(is|are|means|denotes|refers to|defined as|can be defined as|may be defined as)\b",
    re.I,
)

_DEFINITION_PATTERNS = (
    "{c} is ",
    "{c} are ",
    "{c} refers to ",
    "{c} denotes ",
    "{c} means ",
    "{c} can be defined as ",
    "{c} may be defined as ",
    "a {c} is ",
    "an {c} is ",
    "the {c} is ",
)

_INDEX_BAD_MARKERS = (
    "chapter ",
    "appendix ",
    "contents",
    "index",
    "bibliography",
    "references",
)

_PREFACE_BAD_MARKERS = (
    "in this chapter",
    "we now",
    "we next",
    "this can be used to",
    "another perspective on",
    "it is useful here",
    "we consider now",
    "we will see",
    "we choose",
    "for our first",
)

_BAD_FRAGMENT_MARKERS = (
    "which we expect",
    "compute its",
    "as well as",
    "this includes",
    "for example",
    "one finds that",
    "looking for",
    "can be plugged back",
    "valid to order",
    "the resulting linear equation",
    "some computations lead us to believe",
)

_STRUCTURE_MARKERS = (
    "equation",
    "process",
    "kernel",
    "convolution",
    "integral",
    "covariance",
    "brownian",
    "martingale",
    "semimartingale",
    "volatility",
    "sde",
    "spde",
    "pde",
    "bsde",
    "=",
    "∫",
)

# Only obvious junk should be blocked here.
# Important difference from earlier versions:
# if a short prompt has no domain tokens at all, it gets rejected.
_NON_DOMAIN_REJECT = {
    "fuck",
    "shit",
    "bitch",
    "damn",
    "wtf",
    "asdf",
    "qwerty",
    "sup",
    "yo",
    "bro",
    "bruh",
    "hello",
    "hi",
    "hey",
    "stop",
    "money",
    "bitches",
    "nigger",
    "niggers",
    "whores",
    "pimp",
}

_DOMAIN_TOKENS = {
    "volterra",
    "riccati",
    "ricatti",
    "girsanov",
    "novikov",
    "malliavin",
    "skorohod",
    "stieltjes",
    "semimartingale",
    "martingale",
    "ito",
    "black",
    "scholes",
    "brownian",
    "fractional",
    "ornstein",
    "uhlenbeck",
    "hurst",
    "kernel",
    "convolution",
    "integral",
    "equation",
    "equations",
    "process",
    "processes",
    "covariance",
    "sde",
    "sdes",
    "spde",
    "spdes",
    "pde",
    "pdes",
    "bsde",
    "bsdes",
    "radon",
    "nykodym",
    "fourier",
    "forier",
    "transform",
    "characteristic",
    "charachteritifucntion",
    "laplace",
    "supremum",
    "infimum",
    "hilbert",
    "sobolev",
    "filtration",
    "adapted",
    "predictable",
    "markov",
    "generator",
    "diffusion",
    "heston",
    "bergomi",
    "rough",
    "volatility",
    "affine",
    "variance",
}

_CANONICAL_MAP = {
    "ricatti": "riccati",
    "ricatti equation": "riccati equation",
    "ricatti equations": "riccati equation",
    "blackscholes": "black-scholes",
    "black scholes": "black-scholes",
    "black scholes merton": "black-scholes-merton",
    "ornstein uhlenbeck": "ornstein-uhlenbeck",
    "fractional ou": "fractional ornstein-uhlenbeck",
    "volterra processes": "volterra process",
    "volterra equations": "volterra equation",
    "riccati equations": "riccati equation",
    "sdes": "sde",
    "spdes": "spde",
    "pdes": "pde",
    "bsdes": "bsde",
    "forier transform": "fourier transform",
    "laplase transform": "laplace transform",
    "forier charachteritifucntion": "fourier characteristic function",
    "radon nykodym": "radon-nykodym",
    "radon nikodym": "radon-nykodym",
}

_ALIAS_MAP = {
    "volterra": ["volterra", "volterra process", "volterra equation"],
    "volterra process": ["volterra process", "volterra processes", "volterra"],
    "volterra equation": ["volterra equation", "volterra equations", "volterra"],
    "riccati": ["riccati", "riccati equation"],
    "riccati equation": ["riccati equation", "riccati equations", "riccati"],
    "black-scholes": ["black-scholes", "black scholes", "black-scholes-merton", "black scholes merton"],
    "black-scholes-merton": ["black-scholes-merton", "black scholes merton", "black-scholes", "black scholes"],
    "ornstein-uhlenbeck": ["ornstein-uhlenbeck", "ornstein uhlenbeck", "ou process"],
    "fractional ornstein-uhlenbeck": ["fractional ornstein-uhlenbeck", "fractional ou", "fou"],
    "pde": ["pde", "partial differential equation", "partial differential equations"],
    "sde": ["sde", "stochastic differential equation", "stochastic differential equations"],
    "spde": ["spde", "stochastic partial differential equation", "stochastic partial differential equations"],
    "bsde": ["bsde", "backward stochastic differential equation", "backward stochastic differential equations"],
    "supremum": ["supremum"],
    "infimum": ["infimum"],
    "fourier transform": ["fourier transform", "forier transform"],
    "fourier characteristic function": ["fourier characteristic function", "forier charachteritifucntion", "characteristic function"],
    "laplace transform": ["laplace transform", "laplase transform"],
    "radon-nykodym": ["radon-nykodym", "radon nykodym", "radon nikodym"],
}

_GENERIC_PENALTIES = {
    "volterra": ["volterra-heston", "rough heston", "rough bergomi", "affine volterra"],
    "volterra process": ["volterra-heston", "rough heston", "rough bergomi", "affine volterra"],
    "riccati": ["stationary solution of the form"],
    "riccati equation": ["stationary solution of the form"],
}


@dataclass(frozen=True)
class NormalizedHit:
    score: float
    file_name: str
    file_path: str
    page_no: int
    chunk_no: int
    text: str
    dense_score: float
    lexical_score: float

    def as_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "page_no": self.page_no,
            "chunk_no": self.chunk_no,
            "text": self.text,
            "dense_score": self.dense_score,
            "lexical_score": self.lexical_score,
        }


class DefinitionAnswerEngine:
    """
    Strict definition extractor.

    Behavior:
    - return a structured Definition/Structure answer only when a high-confidence
      definition sentence actually exists
    - return a hard rejection only for obvious short non-domain junk
    - otherwise return None so engine.py can use its normal evidence path
    """

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return [tok.lower() for tok in _TOKEN_RE.findall(text) if len(tok) > 1]

    @staticmethod
    def _clean_text(text: str) -> str:
        return " ".join(
            str(text)
            .replace("\x00", " ")
            .replace("mo- tion", "motion")
            .split()
        )

    @classmethod
    def _normalize_query(cls, query: str) -> str:
        return " ".join(str(query).strip().split()).strip('"')

    @classmethod
    def _canonicalize(cls, concept: str) -> str:
        lowered = concept.lower().strip()
        return _CANONICAL_MAP.get(lowered, lowered)

    @classmethod
    def _aliases(cls, concept: str) -> List[str]:
        canon = cls._canonicalize(concept)
        aliases = _ALIAS_MAP.get(canon, [canon])
        out: List[str] = []
        seen: set[str] = set()
        for item in aliases + [canon]:
            key = item.lower().strip()
            if key and key not in seen:
                seen.add(key)
                out.append(key)
        return out

    @classmethod
    def _display_concept(cls, concept: str) -> str:
        if concept == "black-scholes":
            return "Black-Scholes"
        if concept == "black-scholes-merton":
            return "Black-Scholes-Merton"
        if concept == "riccati":
            return "Riccati"
        if concept == "ornstein-uhlenbeck":
            return "Ornstein-Uhlenbeck"
        if concept == "fractional ornstein-uhlenbeck":
            return "Fractional Ornstein-Uhlenbeck"
        if concept == "radon-nykodym":
            return "Radon-Nykodym"
        if concept == "fourier characteristic function":
            return "Fourier characteristic function"
        if concept == "laplace transform":
            return "Laplace transform"
        if concept in {"pde", "sde", "spde", "bsde"}:
            return concept.upper()
        return concept[:1].upper() + concept[1:]

    @classmethod
    def _concept_from_query(cls, query: str) -> str:
        q = cls._normalize_query(query)
        q = _WHAT_IS_RE.sub("", q)
        return cls._canonicalize(q.strip().strip(" ?."))

    @classmethod
    def _hard_reject_non_domain(cls, query: str) -> bool:
        q = cls._concept_from_query(query).lower()
        tokens = cls._tokenize(q)
        if not tokens:
            return True
        if any(tok in _DOMAIN_TOKENS for tok in tokens):
            return False
        if any(tok in _NON_DOMAIN_REJECT for tok in tokens) and len(tokens) <= 3:
            return True
        # Main fix: short prompts with zero domain vocabulary get rejected here.
        if len(tokens) <= 2:
            return True
        return False

    @classmethod
    def _normalize_hit(cls, hit: Any) -> NormalizedHit:
        if hasattr(hit, "as_dict"):
            payload = hit.as_dict()
        elif isinstance(hit, Mapping):
            payload = dict(hit)
        else:
            raise TypeError(f"Unsupported hit type: {type(hit)!r}")

        return NormalizedHit(
            score=float(payload.get("score") or 0.0),
            file_name=str(payload.get("file_name") or "Unknown"),
            file_path=str(payload.get("file_path") or ""),
            page_no=int(payload.get("page_no") or 0),
            chunk_no=int(payload.get("chunk_no") or 0),
            text=cls._clean_text(payload.get("text") or ""),
            dense_score=float(payload.get("dense_score") or 0.0),
            lexical_score=float(payload.get("lexical_score") or 0.0),
        )

    @classmethod
    def _looks_index_like(cls, text: str, file_name: str) -> bool:
        cleaned = cls._clean_text(text)
        lowered = cleaned.lower()

        if "index" in file_name.lower():
            return True
        if len(cleaned) < 120:
            return False

        comma_count = cleaned.count(",")
        digit_count = sum(ch.isdigit() for ch in cleaned)
        verb_like = sum(
            1 for token in (" is ", " are ", " means ", " denotes ", " refers to ")
            if token in f" {lowered} "
        )

        if comma_count >= 12 and digit_count >= 18 and verb_like == 0:
            return True
        if "yamada" in lowered and "wiener integral" in lowered and comma_count >= 6:
            return True
        return False

    @classmethod
    def _looks_heading_like(cls, sentence: str) -> bool:
        sent = cls._clean_text(sentence)
        lowered = sent.lower()

        if any(marker in lowered for marker in _INDEX_BAD_MARKERS):
            return True
        if re.match(r"^\d+(\.\d+)*\s", lowered):
            return True
        if len(sent) <= 18:
            return True
        words = sent.split()
        if len(words) <= 4 and all(word[:1].isupper() for word in words if word):
            return True
        return False

    @classmethod
    def _looks_formula_only(cls, sentence: str) -> bool:
        sent = cls._clean_text(sentence)
        alpha = sum(ch.isalpha() for ch in sent)
        symbol = sum(ch in "=+-/*^[](){}<>∫Σλμσρθφψω" or ch.isdigit() for ch in sent)
        return symbol > alpha * 1.6 and alpha < 30

    @classmethod
    def _strip_formula_prefix(cls, sentence: str, aliases: Sequence[str]) -> str:
        sent = cls._clean_text(sentence)
        lowered = sent.lower()

        candidate_positions: List[int] = []
        for alias in aliases:
            for prefix in (alias, f"a {alias}", f"an {alias}", f"the {alias}"):
                idx = lowered.find(prefix)
                if idx > 0:
                    candidate_positions.append(idx)
        if candidate_positions:
            cut = min(candidate_positions)
            tail = sent[cut:].strip()
            if len(tail) >= 24:
                return tail

        return sent

    @classmethod
    def _hit_score(cls, concept: str, hit: NormalizedHit) -> float:
        lowered = hit.text.lower()
        aliases = cls._aliases(concept)

        score = float(hit.score) + 0.30 * hit.lexical_score + 0.08 * hit.dense_score
        if any(alias in lowered for alias in aliases):
            score += 0.30

        for bad in _GENERIC_PENALTIES.get(concept, []):
            if bad in lowered:
                score -= 0.45

        if any(marker in hit.file_name.lower() for marker in ("glossary", "index")):
            score -= 0.90
        if cls._looks_index_like(hit.text, hit.file_name):
            score -= 0.90
        if any(marker in lowered for marker in _PREFACE_BAD_MARKERS):
            score -= 0.22
        return score

    @classmethod
    def _definition_pattern_bonus(cls, lowered: str, aliases: Sequence[str]) -> float:
        bonus = 0.0
        for alias in aliases:
            for pattern in _DEFINITION_PATTERNS:
                if pattern.format(c=alias) in lowered:
                    bonus += 0.65
                    break
        if "called" in lowered or "defined" in lowered or "refers to" in lowered or "denotes" in lowered:
            bonus += 0.16
        return min(bonus, 0.90)

    @classmethod
    def _definition_confidence(cls, concept: str, sentence: str) -> float:
        aliases = cls._aliases(concept)
        sent = cls._clean_text(sentence)
        lowered = sent.lower()

        score = 0.0
        if any(alias in lowered for alias in aliases):
            score += 0.45
        score += cls._definition_pattern_bonus(lowered, aliases)

        if _COPULA_RE.search(lowered):
            score += 0.20
        if any(marker in lowered for marker in _BAD_FRAGMENT_MARKERS):
            score -= 0.45
        if cls._looks_formula_only(sent):
            score -= 0.60
        if cls._looks_heading_like(sent):
            score -= 0.50

        return score

    @classmethod
    def _sentence_score(cls, concept: str, sentence: str, *, prefer_structure: bool = False) -> float:
        aliases = cls._aliases(concept)
        sent = cls._strip_formula_prefix(sentence, aliases)
        sent = cls._clean_text(sent)
        lowered = sent.lower()

        concept_tokens = set(cls._tokenize(concept))
        sentence_tokens = set(cls._tokenize(sent))
        overlap = len(concept_tokens & sentence_tokens) / max(len(concept_tokens), 1)

        score = overlap
        if any(alias in lowered for alias in aliases):
            score += 0.35

        score += cls._definition_pattern_bonus(lowered, aliases)

        if prefer_structure:
            if any(marker in lowered for marker in _STRUCTURE_MARKERS):
                score += 0.18
        else:
            if any(marker in lowered for marker in ("equation", "process", "kernel", "integral", "model")):
                score += 0.08

        if lowered.startswith("the ") and not _COPULA_RE.search(lowered):
            score -= 0.18
        if any(marker in lowered for marker in _BAD_FRAGMENT_MARKERS):
            score -= 0.45
        if "includes" in lowered or "as well as" in lowered or "for example" in lowered:
            score -= 0.25

        for bad in _GENERIC_PENALTIES.get(concept, []):
            if bad in lowered:
                score -= 0.50

        n_chars = len(sent)
        if n_chars < 35:
            score -= 0.25
        elif n_chars > 420:
            score -= 0.12
        else:
            score += 0.05

        if cls._looks_heading_like(sent):
            score -= 0.45
        if cls._looks_formula_only(sent):
            score -= 0.65
        if any(marker in lowered for marker in _PREFACE_BAD_MARKERS):
            score -= 0.28

        comma_count = sent.count(",")
        digit_count = sum(ch.isdigit() for ch in sent)
        if comma_count >= 10 and digit_count >= 8:
            score -= 0.30

        return score

    @classmethod
    def _candidate_clauses(cls, text: str) -> List[str]:
        cleaned = cls._clean_text(text)
        items: List[str] = []
        for sent in _SENTENCE_SPLIT_RE.split(cleaned):
            sent = cls._clean_text(sent)
            if not sent:
                continue
            items.append(sent)
            for clause in _CLAUSE_SPLIT_RE.split(sent):
                clause = cls._clean_text(clause)
                if len(clause) >= 24:
                    items.append(clause)

        out: List[str] = []
        seen: set[str] = set()
        for item in items:
            if item not in seen:
                seen.add(item)
                out.append(item)
        return out

    @classmethod
    def _top_sentences(
        cls,
        concept: str,
        hits: Sequence[NormalizedHit],
        *,
        prefer_structure: bool,
        limit: int,
    ) -> List[tuple[float, str, NormalizedHit]]:
        scored: List[tuple[float, str, NormalizedHit]] = []

        for hit in hits:
            base = cls._hit_score(concept, hit)
            for raw in cls._candidate_clauses(hit.text):
                sent = cls._clean_text(raw)
                if len(sent) < 24:
                    continue
                stripped = cls._strip_formula_prefix(sent, cls._aliases(concept))
                s_score = base + cls._sentence_score(concept, stripped, prefer_structure=prefer_structure)
                scored.append((s_score, stripped, hit))

        scored.sort(key=lambda x: x[0], reverse=True)

        out: List[tuple[float, str, NormalizedHit]] = []
        seen_sentences: set[str] = set()
        for item in scored:
            sent = item[1]
            if sent in seen_sentences:
                continue
            seen_sentences.add(sent)
            out.append(item)
            if len(out) >= limit:
                break
        return out

    @classmethod
    def build_answer(
        cls,
        query: str,
        hits: Sequence[Any],
        *,
        answer_k: int = 3,
        fusion_hits: Sequence[Any] | None = None,
    ) -> Optional[Dict[str, Any]]:
        concept = cls._concept_from_query(query)
        if not concept:
            return None

        if cls._hard_reject_non_domain(query):
            return {
                "mode_used": "definition_answer_engine",
                "response": "No valid mathematical or finance concept was detected in the query.",
                "sources": [],
                "fusion_hits": [],
                "llm_stats": None,
            }

        if not hits:
            return None

        normalized_hits = [cls._normalize_hit(h) for h in hits]
        ranked_hits = sorted(normalized_hits, key=lambda h: cls._hit_score(concept, h), reverse=True)

        definition_candidates = cls._top_sentences(
            concept,
            ranked_hits[: max(answer_k + 5, 10)],
            prefer_structure=False,
            limit=10,
        )
        structure_candidates = cls._top_sentences(
            concept,
            ranked_hits[: max(answer_k + 5, 10)],
            prefer_structure=True,
            limit=10,
        )

        if not definition_candidates:
            return None

        top_def_score, def_sentence, def_hit = definition_candidates[0]
        hard_conf = cls._definition_confidence(concept, def_sentence)

        # Key handoff: weak definition => engine.py handles it with normal evidence path.
        if top_def_score < 1.20 or hard_conf < 0.85:
            return None

        structure_sentence = ""
        structure_hit: Optional[NormalizedHit] = None
        for score, sent, hit in structure_candidates:
            if sent != def_sentence and score >= 0.90:
                structure_sentence = sent
                structure_hit = hit
                break

        response_lines = [cls._display_concept(concept), "", "Definition:", def_sentence]
        if structure_sentence:
            response_lines.extend(["", "Structure:", structure_sentence])

        normalized_fusion_hits = []
        for item in fusion_hits or []:
            if hasattr(item, "as_dict"):
                normalized_fusion_hits.append(dict(item.as_dict()))
            elif isinstance(item, Mapping):
                normalized_fusion_hits.append(dict(item))

        selected_hits: List[NormalizedHit] = [def_hit]
        if structure_hit is not None and (
            structure_hit.file_name,
            structure_hit.page_no,
            structure_hit.chunk_no,
        ) != (
            def_hit.file_name,
            def_hit.page_no,
            def_hit.chunk_no,
        ):
            selected_hits.append(structure_hit)

        existing = {(h.file_name, h.page_no, h.chunk_no) for h in selected_hits}
        for hit in ranked_hits:
            key = (hit.file_name, hit.page_no, hit.chunk_no)
            if key in existing:
                continue
            selected_hits.append(hit)
            existing.add(key)
            if len(selected_hits) >= answer_k:
                break

        return {
            "mode_used": "definition_answer_engine",
            "response": "\n".join(response_lines),
            "sources": [h.as_dict() for h in selected_hits],
            "fusion_hits": normalized_fusion_hits,
            "llm_stats": None,
        }
