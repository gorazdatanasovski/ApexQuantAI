from __future__ import annotations

import json
import re
import sqlite3
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal, Mapping, Sequence

import pandas as pd

from quantai.memory.book_memory import BookMemory, RetrievalHit
from quantai.reasoning.definition_answer_engine import DefinitionAnswerEngine
from quantai.reasoning.execution_parameter_calibrator import ExecutionParameterCalibrator
from quantai.reasoning.execution_trajectory_engine import ExecutionTrajectoryEngine
from quantai.reasoning.feature_store import MarketFeatureStore
from quantai.reasoning.intraday_estimation_engine import IntradayEstimationEngine
from quantai.reasoning.lean_bridge import LeanBridge
from quantai.reasoning.live_data_resilience import LiveDataResilience
from quantai.reasoning.research_memory_fusion import FusionHit, ResearchMemoryFusion
from quantai.reasoning.theorem_lab import TheoremLab
from quantai.reasoning.theorem_registry import TheoremRegistry

try:
    from quantai.reasoning.market_data import PhysicalMarketGateway
except Exception:
    PhysicalMarketGateway = None  # type: ignore

try:
    from quantai.reasoning.options_surface_builder import OptionsSurfaceBuilder
except Exception:
    OptionsSurfaceBuilder = None  # type: ignore

try:
    from quantai.reasoning.options_surface_memory_gateway import OptionsSurfaceMemoryGateway
except Exception:
    OptionsSurfaceMemoryGateway = None  # type: ignore

try:
    from quantai.reasoning.research_router import ResearchRouter
except Exception:
    ResearchRouter = None  # type: ignore


AnswerMode = Literal[
    "auto",
    "evidence",
    "synthesis",
    "deep",
    "theorem",
    "formal",
    "market_memory",
    "market_calibration",
    "market_live_snapshot",
    "options_surface_memory",
]
QueryKind = Literal[
    "definition",
    "exact",
    "theorem",
    "derivation",
    "comparison",
    "concept",
    "research",
]

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[\.\!\?])\s+|\n+")
_HOUR_RE = re.compile(r"(?:T\s*=\s*)?(\d+(?:\.\d+)?)\s*hour", re.I)
_MINUTE_RE = re.compile(r"(?:T\s*=\s*)?(\d+(?:\.\d+)?)\s*minute", re.I)
_SHARE_POWER_RE = re.compile(r"10\^(\d+)\s*shares", re.I)
_SHARE_NUM_RE = re.compile(r"(\d[\d,]*)\s*shares", re.I)
_WHAT_IS_RE = re.compile(r"^(?:what is|what's|define|meaning of|explain|state)\s+", re.I)
_SECURITY_TOKEN_RE = re.compile(
    r"\b(?:spx|spy|vix|vvix|vix3m|ndx|qqq|es1|nq1|aapl|msft|nvda|btc|eth|tsla)\b",
    re.I,
)


class ApexReasoningCore:
    """
    Integrated QuantAI engine with strictly enforced routing discipline.
    """

    _RESEARCH_MARKERS: Sequence[str] = (
        "conjecture", "hypothesis", "invent", "new theorem", "new law",
        "research agenda", "theory", "propose a theorem", "propose a law",
        "empirical law", "stylized fact", "feature relationship", "scaling law",
        "theorem lab", "formalize",
    )
    _MARKET_MEMORY_MARKERS: Sequence[str] = (
        "regime", "drawdown", "realized vol", "realized variance", "jump share",
        "mean reversion", "feature panel", "bloomberg memory", "market state",
        "roughness signature", "volume anomaly", "hurst estimate", "ou speed",
        "autocorrelation", "volatility clustering", "empirical memory",
        "research memory", "current bloomberg empirical memory",
    )
    _CALIBRATION_MARKERS: Sequence[str] = (
        "implied vol", "implied volatility", "options surface", "atm skew",
        "skew scaling", "surface calibration", "spx options", "option chain",
        "calibrate", "smile", "term structure", "maximum likelihood", "mle",
        "jump intensity", "lambda_j", "mean-reversion speed", "kappa",
    )
    _OPTIONS_SURFACE_MEMORY_MARKERS: Sequence[str] = (
        "implied vol", "implied volatility", "options surface", "atm skew",
        "skew scaling", "surface memory", "stored surface", "persisted surface",
        "smile", "term structure", "spx options", "option chain",
    )
    _LIVE_CALIBRATION_MARKERS: Sequence[str] = (
        "maximum likelihood", "mle", "jump intensity", "lambda_j",
        "mean-reversion speed", "kappa", "rebuild surface", "recalibrate surface",
        "fresh surface", "live surface", "repair surface",
    )
    _LIVE_MARKET_MARKERS: Sequence[str] = (
        "live", "latest", "current quote", "snapshot", "bid", "ask",
        "spread", "order book", "level ii", "limit order book", "top of book", "bbo",
    )
    _MARKET_EXPLICIT_MARKERS: Sequence[str] = (
        "market", "price", "quote", "quotes", "return", "returns",
        "security", "securities", "equity", "index", "ticker",
        "volatility regime", "market state", "bloomberg", "surface",
        "skew", "smile", "term structure", "drawdown", "volume",
        "bid", "ask", "options", "option chain", "spread", "live",
        "snapshot", "current", "latest",
    )
    _MATH_CONCEPT_MARKERS: Sequence[str] = (
        "volterra", "riccati", "girsanov", "novikov", "malliavin", "skorohod",
        "stieltjes", "semimartingale", "local martingale", "fractional", "hurst",
        "ornstein-uhlenbeck", "ou process", "fou", "rfsv", "fbm", "brownian motion",
        "ito", "kernel", "convolution", "integral", "covariance", "derivation",
        "derive", "prove", "theorem", "lemma", "proposition", "corollary",
        "definition", "define", "what is", "what's", "equation", "sde", "spde",
        "affine", "self-affine", "forward variance", "rough path", "regularity structure",
    )
    _TOPIC_RULES: Sequence[dict[str, object]] = (
        {
            "contains_any": [
                "rough volatility", "rfsv", "fou", "fractional ou", "volterra",
                "fractional brownian", "fbm", "hurst", "riccati",
            ],
            "preferred_books": ["rough volatility"],
            "required_terms": [
                "volterra", "hurst", "fractional", "brownian", "covariance",
                "kernel", "ou", "riccati",
            ],
            "extra_phrases": [
                "fractional brownian motion", "fractional ornstein-uhlenbeck",
                "rough fractional stochastic volatility", "volterra process",
                "stochastic convolution volterra equation", "riccati equation",
            ],
        },
        {
            "contains_any": [
                "skorohod", "malliavin", "stieltjes", "anticipating", "wiener chaos",
            ],
            "preferred_books": ["malliavin", "nualart"],
            "required_terms": [
                "skorohod", "malliavin", "integral", "wiener", "chaos", "stieltjes",
            ],
            "extra_phrases": [
                "skorohod integral", "malliavin derivative", "wiener integral",
            ],
        },
        {
            "contains_any": [
                "hjb", "optimal execution", "market impact", "temporary impact",
                "permanent impact", "limit order", "alpha", "inventory",
            ],
            "preferred_books": ["cartea", "algorithmic and high-frequency trading"],
            "required_terms": [
                "hjb", "execution", "impact", "inventory", "terminal", "boundary",
                "value function",
            ],
            "extra_phrases": [
                "temporary market impact", "permanent market impact",
                "terminal boundary condition",
            ],
        },
        {
            "contains_any": [
                "girsanov", "novikov", "martingale", "brownian", "ito",
                "black-scholes", "replicating", "hedging", "ornstein-uhlenbeck",
                "ou process",
            ],
            "preferred_books": [
                "karatzas", "shreve", "brownian motion and stochastic calculus",
                "rough volatility",
            ],
            "required_terms": [
                "martingale", "measure", "brownian", "girsanov", "novikov",
                "replicating", "hedging", "ornstein", "uhlenbeck", "sde",
            ],
            "extra_phrases": [
                "equivalent martingale measure", "girsanov theorem",
                "replicating strategy", "ornstein-uhlenbeck process",
            ],
        },
    )

    def __init__(
        self,
        work_dir: str | Path = "rag_ingest_state",
        model_name: str = "llama3",
        ollama_base_url: str = "http://localhost:11434",
        retrieve_k: int = 10,
        answer_k: int = 3,
        request_timeout: int = 900,
        num_ctx: int = 4096,
        num_predict: int = 256,
        keep_alive: str | int = -1,
        answer_mode: AnswerMode = "evidence",
        market_db_path: str | Path = "data/market_history.sqlite",
        formal_root: str | Path = "formal",
    ) -> None:
        self.work_dir = Path(work_dir).resolve()
        self.model_name = model_name
        self.ollama_base_url = ollama_base_url.rstrip("/")
        self.retrieve_k = int(retrieve_k)
        self.answer_k = int(answer_k)
        self.request_timeout = int(request_timeout)
        self.num_ctx = int(num_ctx)
        self.num_predict = int(num_predict)
        self.keep_alive = keep_alive
        self.answer_mode: AnswerMode = answer_mode
        self.market_db_path = Path(market_db_path)
        self.formal_root = Path(formal_root)

        self.memory = BookMemory(self.work_dir)
        self.live_data_resilience = LiveDataResilience(self.market_db_path)
        self.lean_bridge = LeanBridge(root_dir=self.formal_root)
        self.research_router = ResearchRouter() if ResearchRouter is not None else None
        self.intraday_engine = IntradayEstimationEngine(self.market_db_path)
        self.execution_engine = ExecutionTrajectoryEngine(self.market_db_path)
        self.execution_calibrator = ExecutionParameterCalibrator(self.market_db_path)
        self.definition_answer_engine = DefinitionAnswerEngine()

    def close(self) -> None:
        self.memory.close()

    def _make_feature_store(self) -> MarketFeatureStore | None:
        if not self.market_db_path.exists():
            return None
        try:
            return MarketFeatureStore(db_path=self.market_db_path)
        except Exception:
            return None

    def _make_research_memory_fusion(self) -> ResearchMemoryFusion | None:
        try:
            return ResearchMemoryFusion(self.work_dir, self.market_db_path)
        except Exception:
            return None

    def _make_theorem_lab(self) -> TheoremLab | None:
        if not self.market_db_path.exists():
            return None
        try:
            return TheoremLab(db_path=self.market_db_path)
        except Exception:
            return None

    def _make_theorem_registry(self) -> TheoremRegistry | None:
        if not self.market_db_path.exists():
            return None
        try:
            return TheoremRegistry(db_path=self.market_db_path)
        except Exception:
            return None

    def _make_options_surface_memory(self) -> Any:
        if OptionsSurfaceMemoryGateway is None or not self.market_db_path.exists():
            return None
        try:
            return OptionsSurfaceMemoryGateway(self.market_db_path)
        except Exception:
            return None

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return [tok.lower() for tok in _TOKEN_RE.findall(text) if len(tok) > 1]

    @staticmethod
    def _normalize_query(query: str) -> str:
        return " ".join(str(query).strip().split()).strip('"')

    @staticmethod
    def _unique(items: Sequence[str]) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for item in items:
            key = item.lower().strip()
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(item)
        return out

    def _has_explicit_market_intent(self, query: str, securities: Sequence[str]) -> bool:
        q = query.lower()
        if any(marker in q for marker in self._MARKET_EXPLICIT_MARKERS):
            return True
        if _SECURITY_TOKEN_RE.search(q):
            return True
        for sec in securities:
            name = sec.lower().strip()
            if not name:
                continue
            short = name.split()[0]
            if short and short in q:
                return True
        return False

    def _looks_pure_math_query(self, query: str, securities: Sequence[str]) -> bool:
        q = query.lower()
        tokens = self._tokenize(query)
        if any(marker in q for marker in self._MATH_CONCEPT_MARKERS):
            return not self._has_explicit_market_intent(query, securities)
        if len(tokens) <= 3 and not self._has_explicit_market_intent(query, securities):
            return True
        return False

    @classmethod
    def _classify_query(cls, query: str) -> QueryKind:
        q = cls._normalize_query(query).lower()
        tokens = cls._tokenize(q)

        if any(marker in q for marker in cls._RESEARCH_MARKERS):
            return "research"
        if any(x in q for x in ["compare", "difference between", "versus", " vs "]):
            return "comparison"
        if any(q.startswith(p) or p in q for p in ["define ", "what is ", "what's ", "meaning of ", "interpret ", "explain "]):
            return "definition"
        if any(q.startswith(p) or p in q for p in ["state ", "formulate ", "specify ", "precise ", "exact ", "terminal boundary condition", "covariance", "representation", "sde under"]):
            return "exact"
        if any(p in q for p in ["theorem", "lemma", "proposition", "corollary", "iff", "if and only if"]):
            return "theorem"
        if any(p in q for p in ["derive ", "prove ", "show ", "solve ", "replicating strategy", "hedging strategy"]):
            return "derivation"
        if len(tokens) <= 3:
            return "definition"
        return "concept"

    def _expand_concept_query(self, query: str, kind: QueryKind) -> str:
        q_norm = self._normalize_query(query).lower()
        if kind == "definition":
            q_norm = _WHAT_IS_RE.sub("", q_norm).strip().strip(" ?.")

        mapping = {
            "volterra": "volterra process volterra equation",
            "ricatti": "riccati equation",
            "riccati": "riccati equation",
            "pde": "partial differential equation",
            "pdes": "partial differential equation",
            "sde": "stochastic differential equation",
            "sdes": "stochastic differential equation",
            "spde": "stochastic partial differential equation",
            "bsde": "backward stochastic differential equation",
            "radon nykodym": "radon-nykodym derivative",
            "forier transform": "fourier transform",
            "laplase transform": "laplace transform",
            "forier charachteritifucntion": "fourier characteristic function",
            "characteristic function": "characteristic function",
            "supremum": "supremum",
            "infimum": "infimum",
        }
        return mapping.get(q_norm, q_norm or query)

    @classmethod
    def _retrieval_plan(cls, query: str, kind: QueryKind) -> dict[str, list[str]]:
        q = cls._normalize_query(query).lower()
        preferred_books: list[str] = []
        required_terms: list[str] = []
        extra_phrases: list[str] = []

        for rule in cls._TOPIC_RULES:
            markers = rule["contains_any"]  # type: ignore[index]
            if any(str(marker) in q for marker in markers):
                preferred_books.extend(rule["preferred_books"])  # type: ignore[arg-type]
                required_terms.extend(rule["required_terms"])  # type: ignore[arg-type]
                extra_phrases.extend(rule["extra_phrases"])  # type: ignore[arg-type]

        if kind in {"exact", "theorem", "research", "definition", "derivation", "concept"}:
            phrases = re.findall(r'"([^"]+)"', query)
            extra_phrases.extend(phrases)
            required_terms.extend(
                [
                    tok for tok in cls._tokenize(query)
                    if tok in {
                        "covariance", "representation", "integral", "theorem", "boundary",
                        "condition", "volterra", "fractional", "ornstein", "uhlenbeck",
                        "skorohod", "malliavin", "girsanov", "novikov", "hjb", "rough",
                        "hurst", "almgren", "chriss", "bates", "jump", "kappa", "lambda",
                        "execution", "riccati", "kernel", "convolution", "semimartingale",
                        "martingale", "pde", "sde", "supremum", "infimum", "fourier", "laplace"
                    }
                ]
            )
            new_phrases = [
                "volterra equation", "volterra process", "radon-nykodym derivative",
                "fourier transform", "characteristic function", "partial differential equation",
                "stochastic differential equation", "supremum", "infimum"
            ]
            for p in new_phrases:
                if any(w in q for w in cls._tokenize(p)):
                    extra_phrases.append(p)

        return {
            "preferred_books": cls._unique(preferred_books),
            "required_terms": cls._unique(required_terms),
            "extra_phrases": cls._unique(extra_phrases),
        }

    def retrieve(self, query: str) -> List[RetrievalHit]:
        kind = self._classify_query(query)
        plan = self._retrieval_plan(query, kind)
        retrieval_query = self._expand_concept_query(query, kind)

        return self.memory.retrieve(
            retrieval_query,
            top_k=self.retrieve_k,
            candidate_k=max(self.retrieve_k * 8, 40),
            preferred_books=plan["preferred_books"],
            required_terms=plan["required_terms"],
            extra_phrases=plan["extra_phrases"],
            query_kind=kind,
        )

    def retrieve_fusion(
        self,
        query: str,
        securities: Sequence[str] | None = None,
        top_k: int = 6,
    ) -> List[FusionHit]:
        fusion = self._make_research_memory_fusion()
        if fusion is None:
            return []

        pure_math = self._looks_pure_math_query(query, securities or [])
        try:
            try:
                hits = fusion.retrieve(
                    query,
                    securities=securities or [],
                    top_k=top_k,
                    book_k=max(min(top_k, 4), 2),
                    registry_k=max(min(top_k, 3), 1),
                    bloomberg_k=0 if pure_math else max(min(top_k, 3), 1),
                )
            except TypeError:
                hits = fusion.retrieve(
                    query,
                    securities=securities or [],
                    top_k=top_k,
                    book_k=max(min(top_k, 4), 2),
                    registry_k=max(min(top_k, 3), 1),
                    bloomberg_k=max(min(top_k, 3), 1),
                )
                if pure_math:
                    hits = [
                        h for h in hits
                        if str(getattr(h, "source_type", "")).lower() in {"book", "registry"}
                    ]
            return hits
        except Exception:
            return []
        finally:
            try:
                fusion.close()
            except Exception:
                pass

    @staticmethod
    def _select_context(hits: Iterable[RetrievalHit], answer_k: int) -> List[RetrievalHit]:
        selected: List[RetrievalHit] = []
        seen_pages: set[tuple[str, int]] = set()
        for hit in hits:
            key = (hit.file_name, hit.page_no)
            if key in seen_pages:
                continue
            seen_pages.add(key)
            selected.append(hit)
            if len(selected) >= answer_k:
                break
        return selected

    @classmethod
    def _best_sentences(
        cls,
        query: str,
        text: str,
        limit: int = 3,
        exact_bias: bool = False,
    ) -> list[str]:
        q_tokens = set(cls._tokenize(query))
        candidates: list[tuple[float, str]] = []
        for raw in _SENTENCE_SPLIT_RE.split(text):
            sent = " ".join(raw.split())
            if len(sent) < 24:
                continue
            s_tokens = set(cls._tokenize(sent))
            overlap = len(q_tokens & s_tokens) / max(len(q_tokens), 1)
            eq_bonus = 0.22 if any(sym in sent for sym in ("=", "\u222b", "Cov", "mathbb", "H(", "V(", "dS", "dv", "dW", "dB")) else 0.0
            theorem_bonus = 0.18 if any(word in sent.lower() for word in ("theorem", "lemma", "proposition", "corollary", "iff", "if and only if")) else 0.0
            phrase_bonus = 0.20 if query.lower().strip('"') in sent.lower() else 0.0
            long_bonus = min(len(sent) / 750.0, 0.08)
            score = overlap + long_bonus + phrase_bonus
            if exact_bias:
                score += eq_bonus + theorem_bonus
            candidates.append((score, sent))
        candidates.sort(key=lambda x: x[0], reverse=True)

        out: list[str] = []
        seen: set[str] = set()
        for _, sent in candidates:
            if sent in seen:
                continue
            seen.add(sent)
            out.append(sent)
            if len(out) >= limit:
                break
        return out

    @classmethod
    def _best_supported_excerpt_global(
        cls,
        query: str,
        hits: List[RetrievalHit],
        exact_bias: bool = False,
    ) -> str:
        q_tokens = set(cls._tokenize(query))
        q_lower = query.lower()
        candidates: list[tuple[float, str]] = []

        is_generic_volterra = "volterra" in q_lower and not any(x in q_lower for x in ["affine", "rough", "heston", "bergomi"])
        is_generic_riccati = "riccati" in q_lower and not any(x in q_lower for x in ["solution", "stationary"])

        for hit in hits:
            for raw in _SENTENCE_SPLIT_RE.split(hit.text):
                sent = " ".join(raw.split())
                if len(sent) < 24:
                    continue
                s_lower = sent.lower()

                penalty = 0.0
                if is_generic_volterra and any(x in s_lower for x in ["affine volterra", "rough heston", "rough bergomi", "volterra-heston"]):
                    penalty -= 2.0
                if is_generic_riccati and ("looking for a stationary solution" in s_lower or "we look for" in s_lower):
                    penalty -= 2.0

                s_tokens = set(cls._tokenize(sent))
                overlap = len(q_tokens & s_tokens) / max(len(q_tokens), 1)
                eq_bonus = 0.22 if any(sym in sent for sym in ("=", "\u222b", "Cov", "mathbb", "H(", "V(", "dS", "dv", "dW", "dB")) else 0.0
                theorem_bonus = 0.18 if any(word in s_lower for word in ("theorem", "lemma", "proposition", "corollary", "iff", "if and only if", "definition")) else 0.0
                phrase_bonus = 0.20 if query.lower().strip('"') in s_lower else 0.0
                long_bonus = min(len(sent) / 750.0, 0.08)

                score = overlap + long_bonus + phrase_bonus + penalty
                if exact_bias:
                    score += eq_bonus + theorem_bonus
                candidates.append((score, sent))

        candidates.sort(key=lambda x: x[0], reverse=True)
        if not candidates:
            return ""

        out = []
        seen = set()
        limit = 2 if exact_bias else 3
        for _, sent in candidates:
            if sent in seen:
                continue
            seen.add(sent)
            out.append(sent)
            if len(out) >= limit:
                break
        return " ".join(out)

    @staticmethod
    def _support_strength(hits: List[RetrievalHit]) -> float:
        if not hits:
            return 0.0
        top = hits[:4]
        score = 0.0
        for hit in top:
            dense = float(hit.dense_score or 0.0)
            lexical = float(hit.lexical_score or 0.0)
            score += dense + 0.30 * lexical
        return score / len(top)

    @staticmethod
    def _needs_exact_support(kind: QueryKind) -> bool:
        return kind in {"exact", "theorem", "definition"}

    @classmethod
    def _looks_like_options_surface_memory_query(cls, query: str) -> bool:
        q = query.lower()
        if any(marker in q for marker in ("rebuild surface", "recalibrate surface", "fresh surface", "live surface", "repair surface")):
            return False
        return any(marker in q for marker in cls._OPTIONS_SURFACE_MEMORY_MARKERS)

    def _route_auto_mode(
        self,
        query: str,
        kind: QueryKind,
        securities: Sequence[str],
    ) -> AnswerMode:
        q = query.lower()
        if self._looks_pure_math_query(query, securities):
            return "theorem" if kind == "research" else "evidence"

        if self._looks_like_options_surface_memory_query(query):
            return "options_surface_memory"

        if any(marker in q for marker in self._LIVE_MARKET_MARKERS) and self._has_explicit_market_intent(query, securities):
            return "market_live_snapshot"

        if self.research_router is not None and self._has_explicit_market_intent(query, securities):
            try:
                decision = self.research_router.route(query, securities=list(securities))
                route_name = str(getattr(decision, "route", "") or getattr(decision, "lane", "")).lower()
                mapping: dict[str, AnswerMode] = {
                    "market_features": "market_memory",
                    "market_live_snapshot": "market_live_snapshot",
                    "market_calibration": "market_calibration",
                    "options_surface_memory": "options_surface_memory",
                    "theorem_lab": "theorem",
                    "theorem_bridge": "theorem",
                    "formal_export": "formal",
                    "book_evidence": "evidence",
                    "exact_statement": "evidence",
                }
                mapped = mapping.get(route_name)
                if mapped:
                    if mapped == "market_calibration" and self._looks_like_options_surface_memory_query(query):
                        return "options_surface_memory"
                    return mapped
            except Exception:
                pass

        if any(marker in q for marker in self._LIVE_CALIBRATION_MARKERS) and self._has_explicit_market_intent(query, securities):
            return "market_calibration"
        if securities and any(marker in q for marker in self._MARKET_MEMORY_MARKERS) and self._has_explicit_market_intent(query, securities):
            return "market_memory"
        if kind == "research":
            return "theorem"
        if kind in {"definition", "exact", "theorem", "concept", "derivation", "comparison"}:
            return "evidence"
        return "synthesis"

    def preload_llm(self) -> None:
        payload = {
            "model": self.model_name,
            "prompt": "",
            "stream": False,
            "keep_alive": self.keep_alive,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.ollama_base_url}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=min(self.request_timeout, 60)):
            pass

    def _call_ollama_generate(self, prompt: str, deep: bool = False) -> Dict[str, Any]:
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "keep_alive": self.keep_alive,
            "options": {
                "temperature": 0,
                "num_ctx": self.num_ctx if not deep else max(self.num_ctx, 8192),
                "num_predict": self.num_predict if not deep else max(self.num_predict, 512),
            },
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.ollama_base_url}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.request_timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Ollama HTTP error {exc.code}: {error_body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Could not reach Ollama at {self.ollama_base_url}.") from exc

        if "response" not in body:
            raise RuntimeError(f"Unexpected Ollama response payload: {body}")
        return body

    def _build_prompt(
        self,
        query: str,
        hits: List[RetrievalHit],
        kind: QueryKind,
        deep: bool = False,
        fusion_hits: Sequence[FusionHit] | None = None,
    ) -> str:
        context_blocks = []
        for i, hit in enumerate(hits, start=1):
            context_blocks.append(f"[S{i}] {hit.file_name} p.{hit.page_no} c.{hit.chunk_no}\n{hit.text}")

        fusion_blocks = []
        for i, hit in enumerate(list(fusion_hits or []), start=1):
            fusion_blocks.append(f"[F{i}] {hit.source_type.upper()} | {hit.title}\n{hit.context_text[:1800]}")

        context = "\n\n".join(context_blocks)
        fusion_context = "\n\n".join(fusion_blocks)
        length_rule = "Be concise and structured." if not deep else "Be rigorous and complete, but do not repeat yourself."
        task_rule = {
            "derivation": "Derive only what is directly supported or standardly implied by the supplied context.",
            "comparison": "Compare the concepts only using the supplied context.",
            "concept": "Explain the concept using the supplied context.",
            "research": "Synthesize only a narrow research implication from the supplied context.",
            "definition": "Start with a direct definition, then explain only what is supported by the supplied context.",
        }.get(kind, "Answer from the supplied context only.")
        return (
            "Answer from the supplied book excerpts and fused research memory only. "
            "Never fabricate equations, theorem statements, or citations. "
            "If the requested exact formula or theorem statement is not explicitly supported by the context, say INSUFFICIENT CONTEXT. "
            f"{task_rule} {length_rule}\n\n"
            f"Question:\n{query}\n\n"
            f"Book excerpts:\n{context or 'None'}\n\n"
            f"Fused research memory:\n{fusion_context or 'None'}\n\n"
            "Required structure:\n"
            "1) Directly supported\n"
            "2) Research-memory alignment\n"
            "3) Standard inference\n"
            "4) Unknown from supplied context"
        )

    def _render_fusion_hits(self, hits: Sequence[FusionHit]) -> str:
        if not hits:
            return "None."
        lines: List[str] = []
        for hit in hits:
            lines.append(f"- [{hit.source_type}] {hit.title} | score={hit.score:.3f}")
            lines.append(f"  {hit.excerpt[:500]}")
        return "\n".join(lines)

    @staticmethod
    def _summarize_from_evidence(
        query: str, hits: List[RetrievalHit], kind: QueryKind
    ) -> str:
        snippets: list[str] = []
        for hit in hits[:2]:
            text = " ".join(hit.text.split())
            if len(text) > 220:
                text = text[:220].rsplit(" ", 1)[0] + "..."
            snippets.append(text)
        if not snippets:
            return "The retrieved evidence is too weak to support a concise interpretation."
        if kind == "comparison" and len(snippets) >= 2:
            return f"The strongest retrieved passages emphasize two different aspects of the query. First: {snippets[0]} Second: {snippets[1]}"
        return snippets[0]

    def _build_evidence_response(
        self,
        query: str,
        hits: List[RetrievalHit],
        kind: QueryKind,
        synthesis_skipped: bool = False,
        fusion_hits: Sequence[FusionHit] | None = None,
    ) -> str:
        lines: list[str] = []
        top = self._select_context(hits, self.answer_k)
        if not top and not fusion_hits:
            return "Best supported answer: no relevant evidence was retrieved."

        exact_bias = kind in {"exact", "theorem", "definition"}

        if top:
            best_supported = self._best_supported_excerpt_global(query, top, exact_bias=exact_bias)
            if not best_supported:
                best_supported = top[0].text[:500].replace("\n", " ")
            lines.append("Best supported excerpt:" if exact_bias else "Best supported answer:")
            lines.append(best_supported)
            lines.append("")

        if fusion_hits:
            lines.append("Fused research memory:")
            lines.append(self._render_fusion_hits(fusion_hits))
            lines.append("")

        if kind in {"definition", "concept", "comparison"} and top:
            lines.append("Short interpretation:")
            lines.append(self._summarize_from_evidence(query, top, kind))
            lines.append("")

        if top:
            lines.append("Supporting excerpts:")
            for idx, hit in enumerate(top, start=1):
                sentences = self._best_sentences(query, hit.text, limit=2, exact_bias=exact_bias)
                excerpt = " ".join(sentences) if sentences else hit.text[:500].replace("\n", " ")
                lines.append(f"[S{idx}] {hit.file_name} p.{hit.page_no}: {excerpt}")
            lines.append("")

        if synthesis_skipped:
            lines.append("LLM synthesis skipped: the retrieved context is too weak for a trustworthy long-form derivation, so the system returned evidence first.")
        elif exact_bias:
            lines.append("Note: this question asks for an exact statement or formula, so the safest answer is evidence-first rather than free-form synthesis.")
        else:
            lines.append("Note: this answer is limited to the retrieved evidence and fused research memory, and avoids unsupported extrapolation.")
        return "\n".join(lines)

    def _should_skip_llm(
        self,
        query: str,
        hits: List[RetrievalHit],
        mode: AnswerMode,
        kind: QueryKind,
    ) -> bool:
        if mode == "evidence":
            return True
        strength = self._support_strength(hits)
        if self._needs_exact_support(kind):
            return True
        if kind == "comparison":
            return strength < 0.82
        if kind == "derivation":
            return strength < 0.86
        return strength < 0.78

    def _build_market_summary(self, securities: Sequence[str]) -> dict[str, Any]:
        if not securities:
            return {}
        store = self._make_feature_store()
        if store is None:
            return {}
        try:
            out: dict[str, Any] = {}
            for sec in securities:
                try:
                    out[sec] = store.summarize_security(sec)
                except Exception as exc:
                    out[sec] = {"error": str(exc)}
            return out
        finally:
            try:
                store.close()
            except Exception:
                pass

    def _load_bloomberg_memory_notes(
        self,
        securities: Sequence[str] | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        if not self.market_db_path.exists():
            return []
        try:
            conn = sqlite3.connect(str(self.market_db_path))
            conn.row_factory = sqlite3.Row
            clauses = []
            params: list[Any] = []
            if securities:
                placeholders = ",".join("?" for _ in securities)
                clauses.append(f"(security IN ({placeholders}) OR security='GLOBAL')")
                params.extend(securities)
            sql = "SELECT security, note_type, title, as_of_date, content_markdown, metadata_json FROM bloomberg_research_memory"
            if clauses:
                sql += " WHERE " + " AND ".join(clauses)
            sql += " ORDER BY CASE WHEN security='GLOBAL' THEN 1 ELSE 0 END, security LIMIT ?"
            params.append(int(limit))
            rows = conn.execute(sql, params).fetchall()
            conn.close()
        except Exception:
            return []

        notes = []
        for row in rows:
            try:
                meta = json.loads(row["metadata_json"]) if row["metadata_json"] else {}
            except Exception:
                meta = {}
            notes.append({
                "security": row["security"],
                "note_type": row["note_type"],
                "title": row["title"],
                "as_of_date": row["as_of_date"],
                "content_markdown": row["content_markdown"],
                "metadata": meta,
            })
        return notes

    def _render_market_memory_response(self, query: str, securities: Sequence[str]) -> str:
        notes = self._load_bloomberg_memory_notes(securities=securities or None, limit=6)
        summary = self._build_market_summary(securities)
        if not notes and not summary:
            return "Bloomberg research memory is not available yet."

        lines = ["Bloomberg empirical memory summary", ""]
        if securities:
            lines.append("Securities:")
            for sec in securities:
                lines.append(f"- {sec}")
            lines.append("")

        for note in notes:
            title = note.get("title") or "Untitled note"
            sec = note.get("security") or "UNKNOWN"
            as_of = note.get("as_of_date") or "unknown"
            lines.append(f"[{sec}] {title} ({as_of})")
            text = str(note.get("content_markdown") or "")
            blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
            excerpt = ""
            for block in blocks[1:]:
                if len(block) > 40:
                    excerpt = block
                    break
            excerpt = excerpt[:600].rstrip() if excerpt else text[:600].rstrip()
            lines.append(excerpt)
            lines.append("")

        if summary:
            lines.append("Feature-store summaries:")
            for sec, payload in summary.items():
                if isinstance(payload, Mapping):
                    lines.append(f"- {sec}: {json.dumps(payload, default=str)[:500]}")
                else:
                    lines.append(f"- {sec}: {payload}")
            lines.append("")

        lines.append("Use theorem mode for new conjectures. Use evidence mode for exact book statements.")
        return "\n".join(lines)

    def _fetch_live_market_snapshot(
        self,
        query: str,
        securities: Sequence[str],
    ) -> Dict[str, Any]:
        if PhysicalMarketGateway is None:
            return {"status": "unavailable", "reason": "PhysicalMarketGateway is not importable in this environment."}
        if not securities:
            return {"status": "unavailable", "reason": "No securities supplied for live Bloomberg query."}

        fields = ["PX_LAST", "BID", "ASK", "VOLUME"]
        q = query.lower()
        if "spread" in q and len(securities) >= 2:
            fields = ["PX_LAST", "BID", "ASK"]
        if "order book" in q or "level ii" in q or "limit order book" in q:
            fields = ["PX_LAST", "BID", "ASK", "BID_SIZE", "ASK_SIZE", "VOLUME"]

        try:
            with PhysicalMarketGateway() as bbg:
                ping = bbg.ping()
                snapshot = None
                bdp = getattr(bbg, "bdp", None)
                if callable(bdp):
                    try:
                        snapshot_result = bdp(list(securities), fields)
                        snapshot = snapshot_result.frame.to_dict(orient="records") if hasattr(snapshot_result, "frame") else str(snapshot_result)
                    except Exception as exc:
                        snapshot = {"status": "failed", "error": str(exc), "fields": fields}
                out: Dict[str, Any] = {"status": "ok", "ping": ping, "snapshot_fields": fields, "snapshot": snapshot}

                if "spread" in q and isinstance(snapshot, list) and len(snapshot) >= 2:
                    try:
                        px: dict[str, float] = {}
                        for row in snapshot:
                            sec = str(row.get("security") or row.get("Security") or "")
                            val = row.get("PX_LAST")
                            if sec and val is not None:
                                px[sec] = float(val)
                        if len(px) >= 2:
                            keys = list(px.keys())[:2]
                            out["spread"] = {"securities": keys, "px_last_spread": px[keys[0]] - px[keys[1]]}
                    except Exception:
                        pass
                return out
        except Exception as exc:
            return {"status": "failed", "error": str(exc), "snapshot_fields": fields}

    @staticmethod
    def _pick_first_snapshot_row(live_payload: Mapping[str, Any]) -> Dict[str, Any] | None:
        snapshot = live_payload.get("snapshot")
        if isinstance(snapshot, list) and snapshot:
            row = snapshot[0]
            if isinstance(row, dict):
                return row
        return None

    @staticmethod
    def _parse_total_shares(query: str, default: float = 100_000.0) -> float:
        m = _SHARE_POWER_RE.search(query)
        if m:
            try:
                return float(10 ** int(m.group(1)))
            except Exception:
                pass
        m = _SHARE_NUM_RE.search(query)
        if m:
            try:
                return float(m.group(1).replace(",", ""))
            except Exception:
                pass
        return float(default)

    @staticmethod
    def _parse_horizon_minutes(query: str, default: float = 60.0) -> float:
        m = _HOUR_RE.search(query)
        if m:
            try:
                return float(m.group(1)) * 60.0
            except Exception:
                pass
        m = _MINUTE_RE.search(query)
        if m:
            try:
                return float(m.group(1))
            except Exception:
                pass
        return float(default)

    def _fetch_intraday_series(self, security: str) -> dict[str, Any]:
        try:
            bars = self.intraday_engine.fetch_intraday_bars(
                security, start_datetime=None, end_datetime=None, event_type="TRADE", interval_minutes=1
            )
            frame = bars.frame.copy()
            return {"status": "ok", "source": "live_bloomberg", "frame": frame, "result": bars.as_dict() if hasattr(bars, "as_dict") else None, "diagnostics": {"rows": int(len(frame))}}
        except Exception as exc:
            fallback = self.live_data_resilience.intraday_fallback_from_history(security, periods=60)
            if fallback.status == "ok":
                frame = pd.DataFrame(fallback.frame_preview)
                if not frame.empty:
                    if "time" in frame.columns:
                        frame["time"] = pd.to_datetime(frame["time"], errors="coerce")
                    if "close" in frame.columns:
                        frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
                    frame = frame.dropna(subset=[c for c in ["time", "close"] if c in frame.columns]).reset_index(drop=True)
                if not frame.empty and {"time", "close"}.issubset(frame.columns):
                    return {"status": "ok", "source": fallback.source, "frame": frame, "result": fallback.as_dict(), "diagnostics": fallback.diagnostics}
            return {"status": "failed", "source": "live_and_history_failed", "error": str(exc), "fallback": fallback.as_dict() if "fallback" in dir() else None}

    def _register_theorem_result(
        self,
        theorem_payload: Mapping[str, Any],
        *,
        query: str,
        securities: Sequence[str],
        benchmark_security: str | None,
        acceptance_score: float,
    ) -> Dict[str, Any] | None:
        registry = self._make_theorem_registry()
        if registry is None:
            return None

        selected = theorem_payload.get("selected")
        if not isinstance(selected, Mapping):
            return None

        status_raw = str(selected.get("status") or "").lower()
        score = float(selected.get("score") or 0.0)
        registry_status = "accepted" if (status_raw in {"accepted", "approved"} or score >= float(acceptance_score)) else "candidate"

        try:
            return registry.register_artifact(
                selected,
                source_kind="theorem_lab",
                source_ref=query,
                default_status=registry_status,
                tags=self._unique([str(x) for x in (selected.get("tags") or [])]),
                securities=list(securities),
                benchmark_security=benchmark_security,
                metadata={
                    "query": query,
                    "lab_status": theorem_payload.get("status"),
                    "lab_score": theorem_payload.get("lab_score"),
                    "selected_status": selected.get("status"),
                    "selected_score": selected.get("score"),
                },
                dedupe_on_hash=True,
            )
        finally:
            try:
                registry.close()
            except Exception:
                pass

    def _render_theorem_response(
        self,
        theorem_payload: Mapping[str, Any],
        lean_payload: Mapping[str, Any] | None = None,
        registry_payload: Mapping[str, Any] | None = None,
        fusion_hits: Sequence[FusionHit] | None = None,
    ) -> str:
        selected = theorem_payload.get("selected") or {}
        title = str(selected.get("title") or "Untitled theorem candidate")
        status = str(selected.get("status") or "unverified")
        score = float(selected.get("score") or 0.0)
        statement = str(selected.get("statement") or "No statement produced.")
        assumptions = [str(x) for x in (selected.get("assumptions") or [])][:6]
        next_actions = [str(x) for x in (selected.get("next_actions") or [])][:6]

        lines = [f"Research artifact: {title}", f"Status: {status}", f"Score: {score:.3f}", "", "Statement:", statement, ""]
        if fusion_hits:
            lines.append("Fused research memory:")
            lines.append(self._render_fusion_hits(fusion_hits))
            lines.append("")

        lines.append("Assumptions:")
        lines.extend([f"- {x}" for x in assumptions] or ["- None recorded"])
        lines.extend(["", "Next actions:"])
        lines.extend([f"- {x}" for x in next_actions] or ["- None recorded"])

        if registry_payload is not None:
            lines.extend(["", "Theorem registry:", f"- action: {registry_payload.get('action')}", f"- entry_id: {registry_payload.get('entry_id')}", f"- status: {registry_payload.get('status')}"])
        if lean_payload is not None:
            lines.extend(["", "Lean export:", f"- theorem_name: {lean_payload.get('theorem_name')}", f"- lean_path: {lean_payload.get('lean_path')}", f"- metadata_path: {lean_payload.get('metadata_path')}"])
        return "\n".join(lines)

    def _run_theorem_mode(
        self,
        query: str,
        *,
        securities: Sequence[str] | None = None,
        benchmark_security: str | None = None,
        export_lean: bool = False,
        run_lean_check: bool = False,
        refinement_rounds: int = 2,
        max_candidates: int = 3,
        acceptance_score: float = 0.80,
    ) -> Dict[str, Any]:
        theorem_lab = self._make_theorem_lab()
        if theorem_lab is None:
            raise RuntimeError(f"Theorem mode requires a market history database at {self.market_db_path}.")

        fusion_hits = self.retrieve_fusion(query, securities=securities or [], top_k=6)
        hits = self.retrieve(query)
        selected_hits = self._select_context(hits, self.answer_k)

        try:
            theorem_result = theorem_lab.run(
                query=query, text_hits=selected_hits, securities=list(securities or []), benchmark_security=benchmark_security,
                max_candidates=max_candidates, refinement_rounds=refinement_rounds, acceptance_score=acceptance_score,
            )
        finally:
            try:
                theorem_lab.close()
            except Exception:
                pass

        lean_payload: dict[str, Any] | None = None
        if export_lean:
            lean_payload = self.lean_bridge.export_lab_result(theorem_result, root_dir=self.formal_root, run_check=run_lean_check).as_dict()

        theorem_payload = theorem_result.as_dict()
        registry_payload = self._register_theorem_result(
            theorem_payload, query=query, securities=list(securities or []), benchmark_security=benchmark_security, acceptance_score=acceptance_score,
        )

        return {
            "mode_used": "formal" if export_lean else "theorem",
            "response": self._render_theorem_response(theorem_payload, lean_payload, registry_payload, fusion_hits),
            "sources": [hit.as_dict() for hit in hits],
            "used_context": [hit.as_dict() for hit in selected_hits],
            "fusion_hits": [h.as_dict() for h in fusion_hits],
            "llm_stats": None,
            "theorem_result": theorem_payload,
            "theorem_registry": registry_payload,
            "lean_export": lean_payload,
            "market_summary": self._build_market_summary(securities or []),
            "bloomberg_memory": self._load_bloomberg_memory_notes(securities=list(securities or []) or None, limit=4),
            "selected_title": (theorem_payload.get("selected") or {}).get("title"),
        }

    def _run_market_live_snapshot(
        self,
        query: str,
        securities: Sequence[str],
    ) -> Dict[str, Any]:
        hits = self.retrieve(query)
        selected = self._select_context(hits, self.answer_k)
        live_payload = self._fetch_live_market_snapshot(query, securities)
        diagnostics: dict[str, Any] = {}
        if self.research_router is not None:
            try:
                diagnostics = self.research_router.build_execution_plan(query, securities=list(securities))
            except Exception:
                diagnostics = {}

        response_lines: List[str] = ["Hybrid market + theory response", ""]
        if securities:
            response_lines.append("Securities:")
            for sec in securities:
                response_lines.append(f"- {sec}")
            response_lines.append("")

        response_lines.append("Live Bloomberg diagnostics:")
        for key, value in live_payload.items():
            text = json.dumps(value, default=str) if isinstance(value, (dict, list)) else str(value)
            response_lines.append(f"- {key}: {text[:1500]}")
        response_lines.append("")

        execution_payload = None
        calibration_payload = None
        resolved_snapshot_payload = None
        q = query.lower()

        if any(marker in q for marker in ("almgren", "chriss", "liquidating trajectory", "liquidation trajectory", "optimal execution")) and securities:
            raw_row = self._pick_first_snapshot_row(live_payload) or {}
            try:
                resolved_snapshot = self.live_data_resilience.resolve_snapshot(raw_row, security=securities[0])
                resolved_snapshot_payload = resolved_snapshot.as_dict()
                live_payload["resolved_snapshot"] = resolved_snapshot_payload

                total_shares = self._parse_total_shares(query)
                horizon_minutes = self._parse_horizon_minutes(query)
                calibration = self.execution_calibrator.calibrate(
                    security=securities[0], order_size=total_shares, horizon_minutes=horizon_minutes,
                    snapshot={
                        "security": resolved_snapshot.security, "PX_LAST": resolved_snapshot.px_last,
                        "BID": resolved_snapshot.bid, "ASK": resolved_snapshot.ask, "BID_SIZE": resolved_snapshot.bid_size,
                        "ASK_SIZE": resolved_snapshot.ask_size, "VOLUME": resolved_snapshot.volume,
                    },
                )
                traj = self.execution_engine.almgren_chriss_trajectory(
                    security=securities[0], total_shares=total_shares, horizon_minutes=horizon_minutes,
                    params=calibration.as_impact_parameters(), dt_minutes=5.0,
                )
                calibration_payload = calibration.as_dict()
                execution_payload = traj.as_dict()

                response_lines.extend([
                    "Resolved live snapshot:", json.dumps(resolved_snapshot_payload, default=str)[:1500], "",
                    "Execution parameter calibration:", calibration.summary(), "",
                    "Execution trajectory summary:", traj.summary(), "", "Schedule preview:"
                ])
                for item in execution_payload["schedule_preview"][:8]:
                    response_lines.append(str(item))
                response_lines.append("")
            except Exception as exc:
                execution_payload = {"status": "failed", "error": str(exc)}
                response_lines.extend([f"Execution trajectory failed: {exc}", ""])

        if selected:
            response_lines.append("Exact/supporting book excerpts:")
            for idx, hit in enumerate(selected, start=1):
                excerpt = " ".join(self._best_sentences(query, hit.text, limit=2, exact_bias=True))
                if not excerpt:
                    excerpt = " ".join(hit.text.split())[:500]
                response_lines.append(f"[S{idx}] {hit.file_name} p.{hit.page_no}: {excerpt}")
            response_lines.append("")

        if diagnostics:
            response_lines.append("Execution diagnostics:")
            for key, value in diagnostics.items():
                response_lines.append(f"- {key}: {value}")
            response_lines.append("")

        response_lines.append("Interpretation: QuantAI treated this as a hybrid request. It pulled live Bloomberg diagnostics, repaired incomplete snapshots when needed, calibrated execution parameters from Bloomberg-derived data, produced a concrete execution schedule when the prompt was execution-oriented, and kept the exact theoretical side evidence-first.")

        return {
            "mode_used": "market_live_snapshot", "response": "\n".join(response_lines),
            "sources": [hit.as_dict() for hit in hits], "used_context": [hit.as_dict() for hit in selected],
            "llm_stats": None, "live_market": live_payload, "resolved_snapshot": resolved_snapshot_payload,
            "execution_parameter_calibration": calibration_payload, "execution_trajectory": execution_payload, "diagnostics": diagnostics,
        }

    def _run_options_surface_memory(
        self,
        query: str,
        securities: Sequence[str],
    ) -> Dict[str, Any]:
        hits = self.retrieve(query)
        selected = self._select_context(hits, self.answer_k)
        fusion_hits = self.retrieve_fusion(query, securities=securities, top_k=4)
        market_summary = self._build_market_summary(securities)

        requested_underlying = securities[0] if securities else "SPX Index"
        gateway = self._make_options_surface_memory()

        if gateway is None:
            return {"mode_used": "options_surface_memory", "response": "OptionsSurfaceMemoryGateway is not available in this environment.", "sources": [hit.as_dict() for hit in hits], "used_context": [hit.as_dict() for hit in selected], "fusion_hits": [h.as_dict() for h in fusion_hits], "llm_stats": None, "market_summary": market_summary, "options_surface_memory": None}

        snapshot = gateway.latest_snapshot(underlying=requested_underlying, preview_rows=12)
        resolved_underlying = requested_underlying
        if snapshot is None and requested_underlying != "SPX Index":
            snapshot = gateway.latest_snapshot(underlying="SPX Index", preview_rows=12)
            if snapshot is not None:
                resolved_underlying = "SPX Index"

        if snapshot is None:
            return {"mode_used": "options_surface_memory", "response": f"No persisted options-surface memory is available for {requested_underlying}. Build it first with options_surface_memory_ingestor, or use market_calibration for a live rebuild.", "sources": [hit.as_dict() for hit in hits], "used_context": [hit.as_dict() for hit in selected], "fusion_hits": [h.as_dict() for h in fusion_hits], "llm_stats": None, "market_summary": market_summary, "options_surface_memory": None}

        snapshot_payload = snapshot.as_dict()
        lines: List[str] = [gateway.render_summary(underlying=resolved_underlying, preview_rows=12), ""]

        if fusion_hits:
            lines.append("Fused research memory:")
            lines.append(self._render_fusion_hits(fusion_hits))
            lines.append("")

        if selected:
            lines.append("Exact/theoretical support:")
            for idx, hit in enumerate(selected, start=1):
                excerpt = " ".join(self._best_sentences(query, hit.text, limit=2, exact_bias=True))
                if not excerpt:
                    excerpt = " ".join(hit.text.split())[:400]
                lines.append(f"[S{idx}] {hit.file_name} p.{hit.page_no}: {excerpt}")
            lines.append("")

        lines.append("Interpretation: QuantAI answered this from persisted options-surface memory rather than rebuilding a live surface. This makes SPX skew / smile / term-structure queries deterministic and fast.")

        return {
            "mode_used": "options_surface_memory", "response": "\n".join(lines), "sources": [hit.as_dict() for hit in hits], "used_context": [hit.as_dict() for hit in selected], "fusion_hits": [h.as_dict() for h in fusion_hits], "llm_stats": None, "market_summary": market_summary, "options_surface_memory": snapshot_payload, "bloomberg_memory": self._load_bloomberg_memory_notes(securities=[resolved_underlying], limit=4),
        }

    def _run_market_calibration(
        self,
        query: str,
        securities: Sequence[str],
    ) -> Dict[str, Any]:
        q = query.lower()
        hits = self.retrieve(query)
        selected = self._select_context(hits, self.answer_k)
        market_summary = self._build_market_summary(securities)
        live_snapshot = self._fetch_live_market_snapshot(query, securities)

        if any(marker in q for marker in ("implied vol", "implied volatility", "surface", "skew", "smile", "option chain", "spx options")):
            use_memory = (
                OptionsSurfaceMemoryGateway is not None
                and self.market_db_path.exists()
                and not any(marker in q for marker in ("rebuild surface", "recalibrate surface", "fresh surface", "live surface", "repair surface"))
            )
            if use_memory:
                return self._run_options_surface_memory(query, securities)

            if OptionsSurfaceBuilder is None:
                return {"mode_used": "market_calibration", "response": "OptionsSurfaceBuilder is not available in this environment.", "sources": [hit.as_dict() for hit in hits], "used_context": [hit.as_dict() for hit in selected], "llm_stats": None, "market_summary": market_summary, "live_market": live_snapshot, "options_surface": None, "calibration": None}

            try:
                underlying = securities[0] if securities else "SPX Index"
                builder = OptionsSurfaceBuilder()
                surface = builder.build_surface(underlying=underlying, option_type="P", max_contracts=300)
                calibration_payload = None
                summary_text = f"Options surface diagnostics for {underlying}: {json.dumps(surface.as_dict(), default=str)[:2000]}"
                if getattr(surface, "surface", None) is not None and len(surface.surface) > 0:
                    try:
                        _, calibration = builder.build_and_calibrate_atm_skew(underlying=underlying, option_type="P", max_contracts=300)
                        calibration_payload = calibration.as_dict()
                        summary_text += "\n\nCalibration summary:\n" + calibration.summary()
                    except Exception as exc:
                        calibration_payload = {"status": "failed", "error": str(exc)}
                        summary_text += f"\n\nCalibration failed: {exc}"

                if selected:
                    summary_text += "\n\nExact/theoretical support:\n"
                    for idx, hit in enumerate(selected, start=1):
                        excerpt = " ".join(self._best_sentences(query, hit.text, limit=2, exact_bias=True))
                        if not excerpt:
                            excerpt = " ".join(hit.text.split())[:400]
                        summary_text += f"[S{idx}] {hit.file_name} p.{hit.page_no}: {excerpt}\n"

                return {"mode_used": "market_calibration", "response": summary_text, "sources": [hit.as_dict() for hit in hits], "used_context": [hit.as_dict() for hit in selected], "llm_stats": None, "market_summary": market_summary, "live_market": live_snapshot, "options_surface": surface.as_dict(), "calibration": calibration_payload}
            except Exception as exc:
                return {"mode_used": "market_calibration", "response": f"Options-surface workflow failed: {exc}", "sources": [hit.as_dict() for hit in hits], "used_context": [hit.as_dict() for hit in selected], "llm_stats": None, "market_summary": market_summary, "live_market": live_snapshot, "options_surface": None, "calibration": {"status": "failed", "error": str(exc)}}

        if len(securities) >= 2 and any(marker in q for marker in ("spread", "ornstein-uhlenbeck", "mean-reversion speed", "kappa", "mle")):
            left = self._fetch_intraday_series(securities[0])
            right = self._fetch_intraday_series(securities[1])

            if left["status"] == "ok" and right["status"] == "ok":
                try:
                    spread, est = self.intraday_engine.estimate_spread_ou_mle(left["frame"], right["frame"], left_name=securities[0], right_name=securities[1], use_log_ratio=False)
                    response_lines = ["Market calibration / intraday spread estimation", "", est.summary(), "", f"Left source: {left.get('source')}", f"Right source: {right.get('source')}", "", "Spread series preview:"]
                    for row in spread.as_dict()["preview"][:10]:
                        response_lines.append(str(row))
                    response_lines.append("")

                    if selected:
                        response_lines.append("Exact/theoretical support:")
                        for idx, hit in enumerate(selected, start=1):
                            excerpt = " ".join(self._best_sentences(query, hit.text, limit=2, exact_bias=True))
                            if not excerpt:
                                excerpt = " ".join(hit.text.split())[:400]
                            response_lines.append(f"[S{idx}] {hit.file_name} p.{hit.page_no}: {excerpt}")

                    return {"mode_used": "market_calibration", "response": "\n".join(response_lines), "sources": [hit.as_dict() for hit in hits], "used_context": [hit.as_dict() for hit in selected], "llm_stats": None, "market_summary": market_summary, "live_market": live_snapshot, "calibration": {"series": spread.as_dict(), "ou": est.as_dict(), "left_source": left.get("source"), "right_source": right.get("source"), "left_diagnostics": left.get("diagnostics"), "right_diagnostics": right.get("diagnostics")}}
                except Exception as exc:
                    intraday_payload: dict[str, Any] = {"left": left, "right": right, "status": "failed", "error": str(exc)}
            else:
                intraday_payload = {"left": left, "right": right, "status": "failed"}

            return {"mode_used": "market_calibration", "response": "Intraday spread calibration could not be completed from live bars or deterministic history fallback in the current environment.", "sources": [hit.as_dict() for hit in hits], "used_context": [hit.as_dict() for hit in selected], "llm_stats": None, "market_summary": market_summary, "live_market": live_snapshot, "calibration": intraday_payload}

        if len(securities) >= 1 and any(marker in q for marker in ("jump intensity", "lambda_j", "variance spikes", "bates")):
            bars = self._fetch_intraday_series(securities[0])
            if bars["status"] == "ok":
                try:
                    est = self.intraday_engine.estimate_jump_intensity(bars["frame"], security=securities[0], value_column="close", time_column="time")
                    response_lines = ["Market calibration / intraday jump estimation", "", est.summary(), "", f"Series source: {bars.get('source')}", ""]
                    if selected:
                        response_lines.append("Exact/theoretical support:")
                        for idx, hit in enumerate(selected, start=1):
                            excerpt = " ".join(self._best_sentences(query, hit.text, limit=2, exact_bias=True))
                            if not excerpt:
                                excerpt = " ".join(hit.text.split())[:400]
                            response_lines.append(f"[S{idx}] {hit.file_name} p.{hit.page_no}: {excerpt}")
                    return {"mode_used": "market_calibration", "response": "\n".join(response_lines), "sources": [hit.as_dict() for hit in hits], "used_context": [hit.as_dict() for hit in selected], "llm_stats": None, "market_summary": market_summary, "live_market": live_snapshot, "calibration": {"series": bars.get("result"), "jump": est.as_dict(), "series_source": bars.get("source"), "series_diagnostics": bars.get("diagnostics")}}
                except Exception as exc:
                    cal: dict[str, Any] = {"status": "failed", "error": str(exc), "series": bars.get("result"), "series_source": bars.get("source")}
            else:
                cal = bars

            return {"mode_used": "market_calibration", "response": "Intraday jump estimation could not be completed from live bars or deterministic history fallback in the current environment.", "sources": [hit.as_dict() for hit in hits], "used_context": [hit.as_dict() for hit in selected], "llm_stats": None, "market_summary": market_summary, "live_market": live_snapshot, "calibration": cal}

        lines = ["Market calibration / empirical-estimation lane", "", "Live diagnostics:", json.dumps(live_snapshot, default=str)[:1800], "", "Feature-store summaries:", json.dumps(market_summary, default=str)[:1800], ""]
        if selected:
            lines.append("Exact/theoretical support:")
            for idx, hit in enumerate(selected, start=1):
                excerpt = " ".join(self._best_sentences(query, hit.text, limit=2, exact_bias=True))
                if not excerpt:
                    excerpt = " ".join(hit.text.split())[:400]
                lines.append(f"[S{idx}] {hit.file_name} p.{hit.page_no}: {excerpt}")
            lines.append("")
        lines.append("Interpretation: QuantAI treated this as a live empirical calibration request. No specialized estimator path matched strongly enough, so it returned live diagnostics, feature summaries, and exact theoretical support.")
        return {"mode_used": "market_calibration", "response": "\n".join(lines), "sources": [hit.as_dict() for hit in hits], "used_context": [hit.as_dict() for hit in selected], "llm_stats": None, "market_summary": market_summary, "live_market": live_snapshot, "calibration": None}

    def answer(
        self,
        query: str,
        mode: AnswerMode | None = None,
        *,
        securities: Sequence[str] | None = None,
        benchmark_security: str | None = None,
        export_lean: bool = False,
        run_lean_check: bool = False,
        refinement_rounds: int = 2,
        max_candidates: int = 3,
        acceptance_score: float = 0.80,
    ) -> Dict[str, Any]:
        
        # 1. Structural Junk/Toxicity Guard
        q_norm = self._normalize_query(query).lower()
        if "nigger" in q_norm or "faggot" in q_norm or q_norm.strip() in {"fuck", "shit", "cunt", "bitch"}:
            return {
                "mode_used": mode or self.answer_mode,
                "response": "Query rejected: obvious junk or profanity.",
                "sources": [],
                "used_context": [],
                "fusion_hits": [],
                "llm_stats": None,
            }

        mode = mode or self.answer_mode
        kind = self._classify_query(query)
        securities = list(securities or [])

        if mode == "auto":
            mode = self._route_auto_mode(query, kind, securities)

        if mode == "market_memory":
            return {"mode_used": "market_memory", "response": self._render_market_memory_response(query, securities), "sources": [], "used_context": [], "llm_stats": None, "market_summary": self._build_market_summary(securities), "bloomberg_memory": self._load_bloomberg_memory_notes(securities=securities or None, limit=6)}

        if mode == "market_live_snapshot":
            return self._run_market_live_snapshot(query, securities)

        if mode == "options_surface_memory":
            return self._run_options_surface_memory(query, securities)

        if mode == "market_calibration":
            return self._run_market_calibration(query, securities)

        if mode in {"theorem", "formal"}:
            return self._run_theorem_mode(query, securities=securities, benchmark_security=benchmark_security, export_lean=(mode == "formal") or export_lean, run_lean_check=run_lean_check, refinement_rounds=refinement_rounds, max_candidates=max_candidates, acceptance_score=acceptance_score)

        hits = self.retrieve(query)
        fusion_hits = self.retrieve_fusion(query, securities=securities, top_k=6)

        # 2. Strict Definition Intercept - Fall-through on weak outputs
        if kind == "definition" or (kind == "concept" and self._looks_pure_math_query(query, securities)):
            rendered = self.definition_answer_engine.build_answer(
                query, hits, answer_k=self.answer_k, fusion_hits=fusion_hits
            )
            if rendered is not None and "Definition:" in rendered.get("response", ""):
                return rendered

        if not hits and not fusion_hits:
            return {"mode_used": mode, "response": "No relevant book-memory chunks or fused research-memory artifacts were retrieved.", "sources": [], "used_context": [], "fusion_hits": [], "llm_stats": None}

        selected = self._select_context(hits, self.answer_k)
        if self._should_skip_llm(query, selected, mode, kind):
            return {"mode_used": "evidence" if mode != "deep" else mode, "response": self._build_evidence_response(query, selected, kind, synthesis_skipped=(mode in {"synthesis", "deep"}), fusion_hits=fusion_hits), "sources": [hit.as_dict() for hit in hits], "used_context": [hit.as_dict() for hit in selected], "fusion_hits": [h.as_dict() for h in fusion_hits], "llm_stats": None}

        deep = mode == "deep"
        prompt = self._build_prompt(query, selected, kind, deep=deep, fusion_hits=fusion_hits)
        body = self._call_ollama_generate(prompt, deep=deep)
        return {"mode_used": mode, "response": str(body.get("response", "")).strip(), "sources": [hit.as_dict() for hit in hits], "used_context": [hit.as_dict() for hit in selected], "fusion_hits": [h.as_dict() for h in fusion_hits], "llm_stats": {"total_duration_ns": body.get("total_duration"), "load_duration_ns": body.get("load_duration"), "prompt_eval_count": body.get("prompt_eval_count"), "prompt_eval_duration_ns": body.get("prompt_eval_duration"), "eval_count": body.get("eval_count"), "eval_duration_ns": body.get("eval_duration"), "done_reason": body.get("done_reason")}}


__all__ = ["ApexReasoningCore", "AnswerMode", "QueryKind"]