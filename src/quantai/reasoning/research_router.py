from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
from typing import Any, Dict, Iterable, List, Literal, Mapping, Sequence

RouteName = Literal[
    "book_evidence",
    "exact_statement",
    "theorem_lab",
    "theorem_bridge",
    "market_features",
    "market_calibration",
    "market_live_snapshot",
    "formal_export",
]

_TOKEN_RE = re.compile(r"[A-Za-z0-9_./:-]+")
_TICKER_RE = re.compile(r"\b([A-Z]{1,5})(?:\s+US)?\s+(Equity|Index|Comdty|Curncy|Govt)\b")


@dataclass(frozen=True)
class RouteDecision:
    route: RouteName
    confidence: float
    reasons: List[str] = field(default_factory=list)
    problem_kind: str = "general"
    topics: List[str] = field(default_factory=list)
    requires_book_memory: bool = False
    requires_feature_store: bool = False
    requires_live_bloomberg: bool = False
    requires_theorem_lab: bool = False
    requires_formal_export: bool = False
    securities: List[str] = field(default_factory=list)
    retrieval_hints: Dict[str, Any] = field(default_factory=dict)
    market_tasks: List[str] = field(default_factory=list)
    theorem_tasks: List[str] = field(default_factory=list)
    calibration_tasks: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ResearchRouter:
    """
    Superior router for QuantAI research workflows.

    Main fix vs earlier version:
    - mixed Bloomberg + exact-formula prompts must not collapse into plain evidence mode
    - live empirical estimation / MLE / calibration language now outranks exact-statement routing
    - market-memory queries are detected explicitly
    """

    _EXACT_MARKERS: Sequence[str] = (
        "state ",
        "give the exact",
        "exact statement",
        "exact covariance",
        "exact representation",
        "exact stochastic differential equation",
        "exact empirical estimation",
        "formulate ",
        "precise ",
        "quote the theorem",
        "what is the definition",
        "definition of",
    )

    _FORMAL_MARKERS: Sequence[str] = (
        "export to lean",
        "formal proof",
        "formalize",
        "lean",
        "proof assistant",
    )

    _THEOREM_MARKERS: Sequence[str] = (
        "propose a theorem",
        "invent a theorem",
        "conjecture",
        "invent a law",
        "new law",
        "new theorem",
        "research agenda",
        "structural law",
        "identification theorem",
    )

    _BRIDGE_MARKERS: Sequence[str] = (
        "connect",
        "bridge",
        "link",
        "relate",
        "how they all connect",
        "transfer principle",
        "modification",
        "indistinguishability",
        "equivalent representation",
        "integral-consistency",
    )

    _LIVE_MARKET_MARKERS: Sequence[str] = (
        "today",
        "right now",
        "live",
        "latest",
        "real-time",
        "intraday",
        "tick",
        "tick-level",
        "level ii",
        "limit order book",
        "order book",
        "spread over the last",
        "current",
        "current live",
        "via the bloomberg api",
        "from the bloomberg session",
    )

    _CALIBRATION_MARKERS: Sequence[str] = (
        "calibrate",
        "fit",
        "estimate",
        "estimation",
        "maximum likelihood",
        "mle",
        "infer",
        "regress",
        "compute the maximum likelihood",
        "calibration",
        "surface",
        "vol surface",
        "implied vol",
        "implied volatility",
        "smile",
        "skew",
        "30-day expiry",
        "expiry",
        "maturity",
        "hurst from skew",
        "log-log slope",
        "asymptotic skew",
        "options chain",
        "option chain",
        "jump intensity",
        "lambda_j",
        "mean-reversion speed",
        "kappa",
    )

    _MARKET_FEATURE_MARKERS: Sequence[str] = (
        "realized variance",
        "realized volatility",
        "drawdown",
        "hurst",
        "autocovariance",
        "autocorrelation",
        "mean reversion",
        "ou",
        "fractional ou",
        "feature panel",
        "empirical signature",
        "historical",
    )

    _MARKET_MEMORY_MARKERS: Sequence[str] = (
        "empirical memory",
        "bloomberg empirical memory",
        "market memory",
        "research memory",
        "current bloomberg empirical memory",
    )

    _TOPIC_RULES: Sequence[tuple[str, Sequence[str]]] = (
        (
            "rough_volatility",
            (
                "rough volatility",
                "rfsv",
                "fou",
                "fractional ou",
                "fractional ornstein",
                "volterra",
                "fractional brownian",
                "hurst",
                "rough bergomi",
            ),
        ),
        (
            "stochastic_calculus",
            (
                "ito",
                "stieltjes",
                "malliavin",
                "skorohod",
                "girsanov",
                "novikov",
                "semimartingale",
                "martingale",
            ),
        ),
        (
            "optimal_execution",
            (
                "optimal execution",
                "almgren-chriss",
                "temporary impact",
                "permanent impact",
                "hjb",
                "inventory",
                "liquidating trajectory",
                "market impact",
            ),
        ),
        (
            "options_surface",
            (
                "implied vol",
                "implied volatility",
                "skew",
                "surface",
                "smile",
                "expiry",
                "maturity",
                "atm",
                "spx options",
            ),
        ),
        (
            "microstructure",
            (
                "order flow",
                "queue",
                "lob",
                "limit order",
                "level ii",
                "order book",
                "microstructure",
                "impact",
            ),
        ),
    )

    _BOOK_HINTS: Mapping[str, Sequence[str]] = {
        "rough_volatility": ("rough volatility",),
        "stochastic_calculus": ("nualart", "malliavin", "karatzas", "shreve", "protter"),
        "optimal_execution": ("cartea", "algorithmic and high-frequency trading"),
        "microstructure": ("bouchaud", "trades, quotes and prices"),
    }

    def route(
        self,
        query: str,
        *,
        securities: Sequence[str] | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> RouteDecision:
        text = self._normalize(query)
        q = text.lower()
        context = dict(context or {})

        inferred_securities = self._extract_securities(text)
        if securities:
            inferred_securities = self._merge_unique(list(securities), inferred_securities)

        topics = self._infer_topics(q)
        problem_kind = self._infer_problem_kind(q, topics)

        live_score = self._score_markers(q, self._LIVE_MARKET_MARKERS)
        calibration_score = self._score_markers(q, self._CALIBRATION_MARKERS)
        theorem_score = self._score_markers(q, self._THEOREM_MARKERS)
        bridge_score = self._score_markers(q, self._BRIDGE_MARKERS)
        exact_score = self._score_markers(q, self._EXACT_MARKERS)
        formal_score = self._score_markers(q, self._FORMAL_MARKERS)
        market_feature_score = self._score_markers(q, self._MARKET_FEATURE_MARKERS)
        market_memory_score = self._score_markers(q, self._MARKET_MEMORY_MARKERS)

        reasons: List[str] = []
        theorem_tasks: List[str] = []
        market_tasks: List[str] = []
        calibration_tasks: List[str] = []

        if formal_score > 0:
            reasons.append("Prompt explicitly asks for formalization / Lean export.")
            return self._decision(
                route="formal_export",
                confidence=self._cap_conf(0.90),
                reasons=reasons,
                problem_kind="formal_export",
                topics=topics,
                securities=inferred_securities,
                requires_book_memory=True,
                requires_feature_store=bool(inferred_securities),
                requires_theorem_lab=True,
                requires_formal_export=True,
                retrieval_hints=self._build_retrieval_hints(topics, q, exact_mode=True),
                theorem_tasks=[
                    "assemble theorem artifact",
                    "normalize assumptions and variables",
                    "export selected theorem to Lean skeleton",
                ],
            )

        if market_memory_score > 0:
            reasons.append("Prompt explicitly asks for Bloomberg empirical/research memory.")
            market_tasks.extend(
                [
                    "load bloomberg_research_memory notes for requested securities",
                    "summarize current empirical regime / roughness / mean-reversion state",
                ]
            )
            return self._decision(
                route="market_features",
                confidence=self._cap_conf(0.90),
                reasons=reasons,
                problem_kind="market_memory",
                topics=topics,
                securities=inferred_securities,
                requires_feature_store=True,
                market_tasks=market_tasks,
            )

        # Critical precedence fix:
        # if the prompt asks for live Bloomberg data AND empirical estimation/calibration,
        # do NOT let exact-formula wording downgrade it to evidence mode.
        if live_score > 0 and calibration_score > 0:
            reasons.append("Prompt mixes live Bloomberg data with empirical estimation/calibration.")
            market_tasks.extend(self._build_calibration_market_tasks(q, inferred_securities))
            theorem_tasks.extend(
                [
                    "retrieve exact supporting formula/theory from book memory",
                    "keep theoretical statement separate from empirical estimator",
                ]
            )
            calibration_tasks.extend(self._build_calibration_tasks(q))
            return self._decision(
                route="market_calibration",
                confidence=self._cap_conf(0.93),
                reasons=reasons,
                problem_kind="market_calibration",
                topics=topics,
                securities=inferred_securities,
                requires_book_memory=True,
                requires_feature_store=True,
                requires_live_bloomberg=True,
                requires_theorem_lab=False,
                retrieval_hints=self._build_retrieval_hints(topics, q, exact_mode=True),
                market_tasks=market_tasks,
                theorem_tasks=theorem_tasks,
                calibration_tasks=calibration_tasks,
            )

        # Hybrid market + exact formula requests (e.g. live LOB + exact Almgren-Chriss trajectory)
        if live_score > 0 and exact_score > 0 and calibration_score == 0:
            reasons.append("Prompt mixes live Bloomberg state with an exact theoretical formula.")
            market_tasks.extend(self._build_live_snapshot_tasks(q, inferred_securities))
            theorem_tasks.extend(
                [
                    "retrieve exact excerpt(s) from book memory",
                    "apply live market parameter(s) only after exact formula retrieval",
                ]
            )
            return self._decision(
                route="market_live_snapshot",
                confidence=self._cap_conf(0.88),
                reasons=reasons,
                problem_kind="hybrid_market_theory",
                topics=topics,
                securities=inferred_securities,
                requires_book_memory=True,
                requires_live_bloomberg=True,
                retrieval_hints=self._build_retrieval_hints(topics, q, exact_mode=True),
                market_tasks=market_tasks,
                theorem_tasks=theorem_tasks,
            )

        if theorem_score > 0 and bridge_score > 0:
            reasons.append("Prompt explicitly asks to connect or bridge multiple mathematical objects.")
            theorem_tasks.extend(
                [
                    "propose bridge theorem candidates",
                    "state invariance or transfer mechanism explicitly",
                    "attach symbolic and empirical falsification tasks",
                ]
            )
            return self._decision(
                route="theorem_bridge",
                confidence=self._cap_conf(0.88),
                reasons=reasons,
                problem_kind="bridge",
                topics=topics,
                securities=inferred_securities,
                requires_book_memory=True,
                requires_feature_store=bool(inferred_securities),
                requires_theorem_lab=True,
                retrieval_hints=self._build_retrieval_hints(topics, q, exact_mode=False),
                theorem_tasks=theorem_tasks,
            )

        if theorem_score > 0 or problem_kind == "theorem":
            reasons.append("Prompt is invention/conjecture oriented, so theorem lab should lead.")
            theorem_tasks.extend(
                [
                    "generate named theorem candidates",
                    "verify with symbolic and empirical checks",
                    "rank and refine candidates",
                ]
            )
            return self._decision(
                route="theorem_lab",
                confidence=self._cap_conf(0.84),
                reasons=reasons,
                problem_kind="theorem",
                topics=topics,
                securities=inferred_securities,
                requires_book_memory=True,
                requires_feature_store=bool(inferred_securities or market_feature_score > 0),
                requires_theorem_lab=True,
                retrieval_hints=self._build_retrieval_hints(topics, q, exact_mode=False),
                theorem_tasks=theorem_tasks,
            )

        if bridge_score > 0:
            reasons.append("Prompt is relational/bridge-oriented.")
            theorem_tasks.extend(
                [
                    "compare representations",
                    "locate invariants preserved under different definitions",
                    "state bridge candidate if evidence is strong enough",
                ]
            )
            return self._decision(
                route="theorem_bridge",
                confidence=self._cap_conf(0.79),
                reasons=reasons,
                problem_kind="bridge",
                topics=topics,
                securities=inferred_securities,
                requires_book_memory=True,
                requires_feature_store=bool(inferred_securities),
                requires_theorem_lab=True,
                retrieval_hints=self._build_retrieval_hints(topics, q, exact_mode=False),
                theorem_tasks=theorem_tasks,
            )

        if exact_score > 0:
            reasons.append("Prompt asks for an exact statement/representation/definition without a stronger market-estimation signal.")
            return self._decision(
                route="exact_statement",
                confidence=self._cap_conf(0.87),
                reasons=reasons,
                problem_kind="exact_statement",
                topics=topics,
                securities=inferred_securities,
                requires_book_memory=True,
                retrieval_hints=self._build_retrieval_hints(topics, q, exact_mode=True),
                theorem_tasks=["quote strongest exact excerpt before any paraphrase"],
            )

        if live_score > 0:
            reasons.append("Prompt asks for live/current market state.")
            market_tasks.extend(self._build_live_snapshot_tasks(q, inferred_securities))
            return self._decision(
                route="market_live_snapshot",
                confidence=self._cap_conf(0.82),
                reasons=reasons,
                problem_kind="market_live_snapshot",
                topics=topics,
                securities=inferred_securities,
                requires_live_bloomberg=True,
                market_tasks=market_tasks,
            )

        if market_feature_score > 0 and inferred_securities:
            reasons.append("Prompt is empirical/historical and can be answered from the local feature warehouse.")
            market_tasks.extend(
                [
                    "load historical features from bloomberg_daily_features",
                    "compute summary / diagnostics for requested security set",
                ]
            )
            return self._decision(
                route="market_features",
                confidence=self._cap_conf(0.80),
                reasons=reasons,
                problem_kind="market_features",
                topics=topics,
                securities=inferred_securities,
                requires_feature_store=True,
                market_tasks=market_tasks,
            )

        reasons.append("Defaulting to book-evidence lane.")
        return self._decision(
            route="book_evidence",
            confidence=0.72,
            reasons=reasons,
            problem_kind=problem_kind,
            topics=topics,
            securities=inferred_securities,
            requires_book_memory=True,
            retrieval_hints=self._build_retrieval_hints(topics, q, exact_mode=False),
        )

    def build_execution_plan(
        self,
        query: str,
        *,
        securities: Sequence[str] | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        decision = self.route(query, securities=securities, context=context)
        plan: Dict[str, Any] = {
            "route": decision.route,
            "confidence": decision.confidence,
            "problem_kind": decision.problem_kind,
            "topics": list(decision.topics),
            "securities": list(decision.securities),
            "requires": {
                "book_memory": decision.requires_book_memory,
                "feature_store": decision.requires_feature_store,
                "live_bloomberg": decision.requires_live_bloomberg,
                "theorem_lab": decision.requires_theorem_lab,
                "formal_export": decision.requires_formal_export,
            },
            "steps": [],
            "reasons": list(decision.reasons),
            "retrieval_hints": dict(decision.retrieval_hints),
            "market_tasks": list(decision.market_tasks),
            "theorem_tasks": list(decision.theorem_tasks),
            "calibration_tasks": list(decision.calibration_tasks),
        }

        steps: List[str] = []
        if decision.requires_book_memory:
            steps.append("retrieve top evidence chunks from BookMemory using route-specific retrieval hints")
        if decision.route == "exact_statement":
            steps.append("return exact excerpt(s) with page/chunk citations before any paraphrase")
        if decision.requires_feature_store:
            steps.append("load local feature summaries from bloomberg_daily_features / bloomberg_research_memory")
        if decision.requires_live_bloomberg:
            steps.append("query Bloomberg through PhysicalMarketGateway for fresh market state")
        if decision.route in {"theorem_lab", "theorem_bridge"}:
            steps.append("construct theorem packet and run verification/falsification")
        if decision.route == "market_calibration":
            steps.append("construct calibration packet, fit estimator, then attach exact theory support")
        if decision.requires_formal_export:
            steps.append("export selected theorem artifact to Lean")
        plan["steps"] = steps
        return plan

    @staticmethod
    def _normalize(text: str) -> str:
        return " ".join(str(text).strip().split())

    @staticmethod
    def _merge_unique(a: Iterable[str], b: Iterable[str]) -> List[str]:
        out: List[str] = []
        seen: set[str] = set()
        for item in list(a) + list(b):
            key = str(item).strip()
            if not key:
                continue
            if key.lower() in seen:
                continue
            seen.add(key.lower())
            out.append(key)
        return out

    def _decision(self, **kwargs: Any) -> RouteDecision:
        return RouteDecision(**kwargs)

    @staticmethod
    def _cap_conf(x: float) -> float:
        return max(0.0, min(0.99, round(float(x), 3)))

    @staticmethod
    def _score_markers(q: str, markers: Sequence[str]) -> int:
        return sum(1 for marker in markers if marker in q)

    def _infer_topics(self, q: str) -> List[str]:
        topics: List[str] = []
        for topic, markers in self._TOPIC_RULES:
            if any(marker in q for marker in markers):
                topics.append(topic)
        return topics

    def _infer_problem_kind(self, q: str, topics: Sequence[str]) -> str:
        if any(marker in q for marker in self._THEOREM_MARKERS):
            return "theorem"
        if any(marker in q for marker in self._BRIDGE_MARKERS):
            return "bridge"
        if any(marker in q for marker in self._EXACT_MARKERS):
            return "exact_statement"
        if any(marker in q for marker in self._CALIBRATION_MARKERS):
            return "market_calibration"
        if "options_surface" in topics:
            return "options_surface"
        if "optimal_execution" in topics:
            return "control"
        if "stochastic_calculus" in topics or "rough_volatility" in topics:
            return "theory"
        return "general"

    def _extract_securities(self, text: str) -> List[str]:
        out: List[str] = []
        for m in _TICKER_RE.finditer(text):
            ticker, kind = m.groups()
            out.append(f"{ticker} {kind}")

        aliases = {
            "spx": "SPX Index",
            "spy": "SPY US Equity",
            "aapl": "AAPL US Equity",
            "qqq": "QQQ US Equity",
            "vix": "VIX Index",
            "tsla": "TSLA US Equity",
            "es": "ES1 Index",
            "ndx": "NDX Index",
        }
        tokens = [tok.lower() for tok in _TOKEN_RE.findall(text)]
        for tok in tokens:
            if tok in aliases:
                out.append(aliases[tok])
        return self._merge_unique([], out)

    def _build_retrieval_hints(self, topics: Sequence[str], q: str, *, exact_mode: bool) -> Dict[str, Any]:
        preferred_books: List[str] = []
        for topic in topics:
            preferred_books.extend(self._BOOK_HINTS.get(topic, ()))

        quoted_phrases = re.findall(r'"([^"]+)"', q)
        required_terms = [tok.lower() for tok in _TOKEN_RE.findall(q) if len(tok) > 2][:28]
        exact_terms = []
        if exact_mode:
            exact_terms.extend(quoted_phrases)
            exact_terms.extend([
                tok for tok in required_terms
                if tok in {
                    "covariance", "representation", "integral", "kernel", "bridge", "modification",
                    "indistinguishability", "volterra", "fractional", "ornstein", "uhlenbeck", "skew",
                    "surface", "calibration", "theorem", "condition", "hjb", "boundary", "trajectory",
                    "almgren-chriss", "bates", "jump", "intensity", "ou", "kappa", "mle"
                }
            ])

        return {
            "preferred_books": self._merge_unique([], preferred_books),
            "required_terms": self._merge_unique([], required_terms),
            "exact_terms": self._merge_unique([], exact_terms),
            "quoted_phrases": quoted_phrases,
        }

    def _build_live_snapshot_tasks(self, q: str, securities: Sequence[str]) -> List[str]:
        tasks: List[str] = []
        if securities:
            tasks.append(f"fetch live snapshot/reference fields for {', '.join(securities)}")
        if "level ii" in q or "order book" in q or "limit order book" in q:
            tasks.append("request live order-book / depth data if available through Bloomberg entitlements")
        if "tick" in q or "intraday" in q:
            tasks.append("request intraday bars or tick-level time series")
        if "spread" in q:
            tasks.append("construct live spread series from retrieved instruments")
        if "surface" in q or "implied vol" in q or "skew" in q:
            tasks.append("request current options/implied-volatility surface data")
        return tasks or ["fetch live Bloomberg snapshot for requested object(s)"]

    def _build_calibration_market_tasks(self, q: str, securities: Sequence[str]) -> List[str]:
        tasks: List[str] = []
        if securities:
            tasks.append(f"identify calibration underlyings: {', '.join(securities)}")
        if "tick" in q or "intraday" in q or "last 60 minutes" in q:
            tasks.append("pull intraday/tick data for the requested horizon")
        tasks.extend(
            [
                "collect empirical series needed for estimation",
                "normalize the market data into an estimation table",
            ]
        )
        if "options" in q or "surface" in q or "skew" in q:
            tasks.extend(
                [
                    "pull options chain / surface inputs from Bloomberg",
                    "collect maturities, strikes/deltas, implied volatilities, and spot/reference fields",
                    "normalize the surface into a calibration table",
                ]
            )
        return tasks

    @staticmethod
    def _build_calibration_tasks(q: str) -> List[str]:
        tasks = []
        if "maximum likelihood" in q or "mle" in q or "mean-reversion speed" in q or "kappa" in q:
            tasks.append("estimate parameters via maximum likelihood from empirical series")
        if "jump intensity" in q or "lambda_j" in q:
            tasks.append("estimate jump intensity and jump-size parameters from spike diagnostics")
        if "skew" in q or "surface" in q:
            tasks.extend(
                [
                    "fit skew/smile statistics across maturities",
                    "run log-log scaling regression on skew vs maturity",
                    "estimate implied Hurst-style exponent from the fitted slope",
                ]
            )
        if not tasks:
            tasks.append("fit empirical calibration/statistical estimator from live market data")
        return tasks
