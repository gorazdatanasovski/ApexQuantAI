from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence
import re

try:
    from quantai.reasoning.feature_store import MarketFeatureStore
except Exception:  # pragma: no cover
    MarketFeatureStore = None  # type: ignore


@dataclass(frozen=True)
class ConjectureEvidence:
    source_type: str
    source_name: str
    support_score: float | None = None
    excerpt: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ConjectureCandidate:
    title: str
    statement: str
    assumptions: list[str]
    variables: dict[str, str]
    motivation: str
    empirical_tests: list[Any]
    symbolic_tasks: list[Any]
    failure_conditions: list[str]
    confidence: float
    tags: list[str] = field(default_factory=list)
    evidence: list[ConjectureEvidence] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evidence"] = [e.as_dict() for e in self.evidence]
        return payload


@dataclass(frozen=True)
class ConjecturePacket:
    query: str
    problem_kind: str
    topics: list[str]
    candidates: list[ConjectureCandidate]
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "problem_kind": self.problem_kind,
            "topics": list(self.topics),
            "candidates": [c.as_dict() for c in self.candidates],
            "metadata": dict(self.metadata),
        }


class ConjectureEngine:
    _TOPIC_PATTERNS: dict[str, tuple[str, ...]] = {
        "rough_volatility": (
            "rough volatility", "rfsv", "rough bergomi", "volterra", "fractional brownian",
            "hurst", "fractional volatility", "fou", "fractional ornstein", "roughness",
        ),
        "stochastic_calculus": (
            "ito", "itô", "stieltjes", "young integral", "skorohod", "malliavin", "covariance",
            "kernel", "semimartingale", "quadratic variation", "indistinguish", "modification",
        ),
        "optimal_execution": (
            "hjb", "optimal execution", "temporary impact", "permanent impact", "inventory",
            "liquidation", "cartea", "almgren",
        ),
        "microstructure": (
            "microstructure", "order flow", "limit order", "queue", "impact", "trade imbalance",
        ),
        "term_structure": (
            "term structure", "yield curve", "forward rate", "short rate", "affine",
        ),
    }

    _KIND_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
        ("exact_statement", ("state", "formulate", "write down", "exact", "representation", "covariance")),
        ("definition", ("what is", "define", "meaning of", "interpret")),
        ("derivation", ("derive", "show", "prove", "obtain", "deduce")),
        ("comparison", ("compare", "relation between", "difference between", "versus", "vs", "connect")),
        ("hypothesis", ("conjecture", "hypothesis", "propose", "invent", "new theorem")),
    ]

    _STOPWORDS = {
        "the", "and", "for", "with", "from", "into", "then", "that", "this", "have", "does",
        "how", "what", "when", "where", "your", "their", "like", "they", "them", "onto", "about",
        "should", "would", "there", "under", "using", "through", "same", "exist", "find", "deal",
    }

    def __init__(self, feature_store: MarketFeatureStore | None = None):
        self.feature_store = feature_store

    def build_packet(
        self,
        query: str,
        text_hits: Sequence[Any] | None = None,
        securities: Sequence[str] | None = None,
        empirical_summary: Mapping[str, Any] | None = None,
        max_candidates: int = 3,
    ) -> ConjecturePacket:
        query_clean = self._clean_text(query)
        problem_kind = self._classify_problem_kind(query_clean)
        topics = self._infer_topics(query_clean)
        evidences = self._normalize_text_evidence(text_hits or [])
        market_context = self._build_market_context(securities=securities or [], empirical_summary=empirical_summary)
        candidates = self._propose_candidates(query_clean, problem_kind, topics, evidences, market_context)
        ranked = sorted(candidates, key=lambda c: c.confidence, reverse=True)[: max(1, max_candidates)]
        return ConjecturePacket(
            query=query_clean,
            problem_kind=problem_kind,
            topics=topics,
            candidates=ranked,
            metadata={
                "n_text_evidence": len(evidences),
                "securities": list(securities or []),
                "market_context_keys": sorted(market_context.keys()),
            },
        )

    @staticmethod
    def _clean_text(text: str) -> str:
        return " ".join(str(text).strip().split())

    def _classify_problem_kind(self, query: str) -> str:
        q = query.lower()
        for label, patterns in self._KIND_PATTERNS:
            if any(p in q for p in patterns):
                return label
        return "research"

    def _infer_topics(self, query: str) -> list[str]:
        q = query.lower()
        out: list[str] = []
        for topic, patterns in self._TOPIC_PATTERNS.items():
            if any(p in q for p in patterns):
                out.append(topic)
        if not out:
            out.append("general_quant")
        return out

    def _normalize_text_evidence(self, text_hits: Sequence[Any]) -> list[ConjectureEvidence]:
        out: list[ConjectureEvidence] = []
        for hit in text_hits:
            if hasattr(hit, "file_name"):
                out.append(
                    ConjectureEvidence(
                        source_type="book",
                        source_name=str(getattr(hit, "file_name", "unknown")),
                        support_score=self._coerce_float(getattr(hit, "score", None)),
                        excerpt=self._clean_text(str(getattr(hit, "text", "")))[:1600] or None,
                        metadata={"page_no": getattr(hit, "page_no", None), "chunk_no": getattr(hit, "chunk_no", None)},
                    )
                )
            elif isinstance(hit, Mapping):
                out.append(
                    ConjectureEvidence(
                        source_type=str(hit.get("source_type", "book")),
                        source_name=str(hit.get("source_name") or hit.get("file_name") or "unknown"),
                        support_score=self._coerce_float(hit.get("support_score", hit.get("score"))),
                        excerpt=self._clean_text(str(hit.get("excerpt") or hit.get("text") or ""))[:1600] or None,
                        metadata=dict(hit.get("metadata") or {}),
                    )
                )
        return out

    @staticmethod
    def _coerce_float(value: Any) -> float | None:
        try:
            return None if value is None else float(value)
        except Exception:
            return None

    def _build_market_context(self, securities: Sequence[str], empirical_summary: Mapping[str, Any] | None) -> dict[str, Any]:
        context: dict[str, Any] = {}
        if empirical_summary:
            context.update(dict(empirical_summary))
        if securities and self.feature_store is not None:
            stats: dict[str, Any] = {}
            for sec in securities:
                try:
                    stats[sec] = self.feature_store.summarize_security(sec)
                except Exception as exc:
                    stats[sec] = {"error": str(exc)}
            context["securities"] = stats
        return context

    def _propose_candidates(self, query: str, problem_kind: str, topics: Sequence[str], evidences: Sequence[ConjectureEvidence], market_context: Mapping[str, Any]) -> list[ConjectureCandidate]:
        topic_set = set(topics)
        out: list[ConjectureCandidate] = []
        q = query.lower()
        if "rough_volatility" in topic_set:
            out.append(self._rough_variance_scaling_candidate(evidences, market_context))
            if any(k in q for k in ["fou", "fractional ornstein", "indistinguish", "modification", "stieltjes", "ito", "itô"]):
                out.append(self._volterra_modification_bridge_candidate(evidences, market_context))
        if "stochastic_calculus" in topic_set and not any(c.title.startswith("Volterra") for c in out):
            out.append(self._integral_consistency_candidate(evidences, market_context))
        if "optimal_execution" in topic_set:
            out.append(self._execution_candidate(evidences))
        if not out:
            out.append(self._generic_structural_candidate(query, evidences, market_context, topics))
        if problem_kind in {"exact_statement", "definition"}:
            out = [self._tighten_statement(c) for c in out]
        return [self._attach_evidence(c, evidences, query) for c in out]

    def _rough_variance_scaling_candidate(self, evidences: Sequence[ConjectureEvidence], market_context: Mapping[str, Any]) -> ConjectureCandidate:
        sec = self._first_security(market_context)
        sec_clause = f" for {sec}" if sec else ""
        support = self._support_score(evidences, ("rough", "volterra", "hurst", "variance", "rfsv"))
        return ConjectureCandidate(
            title="Rough-variance scaling identification theorem",
            statement=(
                "Assume the latent log-volatility process X admits a Volterra representation "
                "X_t = X_0 + ∫_0^t K(t,s) dW_s with local kernel singularity K(t,s) ~ c (t-s)^{H-1/2} for H in (0,1/2). "
                "Then, as Δ ↓ 0, the increment variance satisfies E[(X_{t+Δ}-X_t)^2] = C_X Δ^{2H} + o(Δ^{2H}), and any realized-variance "
                f"proxy constructed from sufficiently fine observations{sec_clause} inherits the same scaling exponent after lower-order noise correction: "
                "E[RV_Δ] = a_0 + a_1 Δ^{2H} + o(Δ^{2H})."
            ),
            assumptions=[
                "H > 0 and H < 1/2.",
                "The volatility driver admits a Volterra representation with local singularity exponent H-1/2.",
                "The observed realized-variance proxy is asymptotically consistent up to lower-order noise distortion.",
                *([f"Empirical scope anchored to {sec}."] if sec else []),
            ],
            variables={
                "H": "roughness exponent",
                "Delta": "observation scale Δ",
                "K": "Volterra kernel",
                "X": "latent log-volatility state",
                "RV_Delta": "realized-variance proxy at scale Δ",
                "C_X": "latent scaling constant",
                "a_0": "noise/intercept term",
                "a_1": "leading realized-variance scaling coefficient",
            },
            motivation="Connect latent rough-volatility regularity to an empirically estimable variance-scaling slope.",
            empirical_tests=[
                {"kind": "hurst_persistence", "name": "roughness_from_variance_scaling"},
                {"kind": "vol_clustering", "name": "volatility_clustering_consistency"},
                {"kind": "range_vol_link", "name": "range_variance_alignment"},
            ],
            symbolic_tasks=[
                {"kind": "positivity", "name": "variance_constant_nonnegative", "expr": "C_X"},
                {"kind": "positivity", "name": "realized_variance_nonnegative", "expr": "a_1*Delta**(2*H)"},
            ],
            failure_conditions=[
                "Estimated scaling slope is unstable across windows or frequencies.",
                "Jump-share dominates the short-horizon variance proxy.",
                "No persistent roughness signal appears in the Bloomberg feature panel.",
            ],
            confidence=min(0.93, 0.60 + support),
            tags=["rough_volatility", "variance_scaling", "rfsv", "empirical_identification"],
        )

    def _volterra_modification_bridge_candidate(self, evidences: Sequence[ConjectureEvidence], market_context: Mapping[str, Any]) -> ConjectureCandidate:
        sec = self._first_security(market_context)
        support = self._support_score(evidences, ("stieltjes", "ito", "modification", "indistinguish", "fou", "rfsv"))
        return ConjectureCandidate(
            title="Volterra modification-invariance bridge",
            statement=(
                "Conjecture: Let X and X_tilde be indistinguishable modifications of a Gaussian Volterra state, and let deterministic kernels preserve the common path-regularity regime required by the integral in use. "
                "Then any admissible representation Y_t = ∫_0^t G(t,s) dX_s is modification-invariant up to indistinguishability on the common domain of definition. "
                "When G combines exponential damping with a rough singular factor, the resulting state interpolates between a fractional Ornstein–Uhlenbeck representation and the log-volatility backbone used in RFSV-type models."
            ),
            assumptions=[
                "X and X_tilde are indistinguishable versions of the same underlying Gaussian Volterra state.",
                "The chosen integral notion is well defined under the joint regularity of integrand and integrator.",
                "Kernel G preserves the regularity class required for the target process.",
                *([f"Empirical scope anchored to {sec}."] if sec else []),
            ],
            variables={
                "X": "latent Gaussian Volterra driver",
                "X_tilde": "indistinguishable modification of X",
                "G": "transfer kernel",
                "Y": "transformed state",
                "H": "roughness exponent",
                "lambda_": "OU-style damping parameter",
                "CovXY": "generic covariance term",
            },
            motivation="Connect Itô / Stieltjes / Volterra viewpoints through a common modification-invariant state representation.",
            empirical_tests=[
                {"kind": "mean_reversion", "name": "ou_style_reversion_signal"},
                {"kind": "hurst_persistence", "name": "rough_persistence_under_transformation"},
            ],
            symbolic_tasks=[
                {"kind": "positivity", "name": "damping_positive", "expr": "lambda_"},
                {"kind": "identity", "name": "covariance_symmetry", "lhs": "CovXY", "rhs": "CovXY"},
            ],
            failure_conditions=[
                "Integral notions require incompatible regularity classes on the same path space.",
                "Empirical features suggest no stable coexistence of roughness and mean reversion.",
                "The retrieved evidence does not support a common Volterra state representation.",
            ],
            confidence=min(0.90, 0.53 + support),
            tags=["volterra", "modification", "indistinguishability", "fou", "rfsv"],
        )

    def _integral_consistency_candidate(self, evidences: Sequence[ConjectureEvidence], market_context: Mapping[str, Any]) -> ConjectureCandidate:
        support = self._support_score(evidences, ("ito", "stieltjes", "skorohod", "malliavin", "kernel"))
        return ConjectureCandidate(
            title="Integral-consistency transfer principle",
            statement=(
                "Whenever a stochastic integral, a pathwise integral, and a Volterra-kernel representation are all well defined on a shared regularity class, "
                "their induced state equations coincide up to the correction term generated by the quadratic-variation or anticipative component absent from the pathwise formulation."
            ),
            assumptions=[
                "All compared integral notions are well defined on a common filtered path space.",
                "The correction term is explicitly representable by quadratic variation or Malliavin divergence.",
            ],
            variables={"X": "integrator", "f": "integrand", "Q": "correction term"},
            motivation="Turn narrative relationships among Itô, Stieltjes/Young, and anticipative integrals into a single comparison principle.",
            empirical_tests=[{"kind": "vol_clustering", "name": "volatility_proxy_stability"}],
            symbolic_tasks=[{"kind": "positivity", "name": "quadratic_variation_nonnegative", "expr": "Q**2"}],
            failure_conditions=[
                "No shared regularity regime exists for the compared integral notions.",
                "The correction term cannot be represented by an explicit adapted/anticipative decomposition.",
            ],
            confidence=min(0.88, 0.48 + support),
            tags=["stochastic_calculus", "ito", "stieltjes", "malliavin"],
        )

    def _execution_candidate(self, evidences: Sequence[ConjectureEvidence]) -> ConjectureCandidate:
        support = self._support_score(evidences, ("execution", "impact", "hjb", "inventory"))
        return ConjectureCandidate(
            title="Impact-curvature execution principle",
            statement=(
                "If temporary impact is convex in trading rate while permanent impact enters linearly in inventory, then the value-function curvature in inventory dominates the near-terminal control law and induces a monotone increase in optimal urgency as residual horizon shrinks."
            ),
            assumptions=[
                "Temporary impact is convex in trading speed.",
                "Permanent impact is affine in inventory or execution flow.",
                "The value function is twice differentiable in inventory.",
            ],
            variables={"v": "trading rate", "q": "inventory", "V": "value function"},
            motivation="Give the execution engine a reusable structural theorem template instead of isolated HJB snippets.",
            empirical_tests=[{"kind": "range_vol_link", "name": "impact_proxy_range_link"}],
            symbolic_tasks=[],
            failure_conditions=["Estimated impact is not convex in speed."],
            confidence=min(0.86, 0.46 + support),
            tags=["optimal_execution", "impact", "inventory"],
        )

    def _generic_structural_candidate(self, query: str, evidences: Sequence[ConjectureEvidence], market_context: Mapping[str, Any], topics: Sequence[str]) -> ConjectureCandidate:
        keywords = self._top_query_keywords(query, k=6)
        sec = self._first_security(market_context)
        topic_label = ", ".join(topics[:3]) if topics else "quantitative structure"
        return ConjectureCandidate(
            title="Evidence-anchored structural conjecture",
            statement=(
                f"Conjecture: the objects {', '.join(keywords[:3]) or 'identified in the query'} admit a common structural representation in the {topic_label} family, "
                "and the dominant terms in that representation are exactly those that remain stable across the top retrieved excerpts and the empirical feature panel."
            ),
            assumptions=[*([f"Empirical scope anchored to {sec}."] if sec else [])],
            variables={k: "query-driven variable" for k in keywords[:4]},
            motivation="Avoid vacuous fallback statements by tying the candidate to the actual query vocabulary.",
            empirical_tests=[{"kind": "vol_clustering", "name": "default_volatility_persistence"}],
            symbolic_tasks=[],
            failure_conditions=["Retrieved evidence remains too dispersed across unrelated mathematical families."],
            confidence=min(0.78, 0.40 + self._support_score(evidences, tuple(keywords[:4]))),
            tags=["generic", *topics[:3]],
        )

    def _tighten_statement(self, c: ConjectureCandidate) -> ConjectureCandidate:
        statement = c.statement if c.statement.lower().startswith(("assume", "conjecture", "let", "if")) else "Conjecture: " + c.statement
        failure_conditions = list(c.failure_conditions)
        if "No exact excerpt currently pins down every constant or normalization." not in failure_conditions:
            failure_conditions.append("No exact excerpt currently pins down every constant or normalization.")
        return ConjectureCandidate(
            title=c.title,
            statement=statement,
            assumptions=list(c.assumptions),
            variables=dict(c.variables),
            motivation=c.motivation,
            empirical_tests=list(c.empirical_tests),
            symbolic_tasks=list(c.symbolic_tasks),
            failure_conditions=failure_conditions,
            confidence=min(0.95, c.confidence + 0.02),
            tags=list(c.tags),
            evidence=list(c.evidence),
        )

    def _attach_evidence(self, candidate: ConjectureCandidate, evidences: Sequence[ConjectureEvidence], query: str) -> ConjectureCandidate:
        if not evidences:
            return candidate
        q_terms = set(self._top_query_keywords(query, k=12))
        scored: list[tuple[float, ConjectureEvidence]] = []
        for e in evidences:
            text = (e.excerpt or "").lower()
            overlap = sum(1 for t in q_terms if t in text)
            score = (e.support_score or 0.0) + 0.03 * overlap
            scored.append((score, e))
        selected = [e for _, e in sorted(scored, key=lambda x: x[0], reverse=True)[:4]]
        return ConjectureCandidate(
            title=candidate.title,
            statement=candidate.statement,
            assumptions=list(candidate.assumptions),
            variables=dict(candidate.variables),
            motivation=candidate.motivation,
            empirical_tests=list(candidate.empirical_tests),
            symbolic_tasks=list(candidate.symbolic_tasks),
            failure_conditions=list(candidate.failure_conditions),
            confidence=min(0.97, candidate.confidence + 0.02 * len(selected)),
            tags=list(candidate.tags),
            evidence=selected,
        )

    def _support_score(self, evidences: Sequence[ConjectureEvidence], favored_terms: Sequence[str]) -> float:
        if not evidences:
            return 0.08
        total = 0.0
        for e in evidences[:8]:
            text = (e.excerpt or "").lower()
            overlap = sum(1 for t in favored_terms if t and t.lower() in text)
            total += (e.support_score or 0.0) * 0.6 + min(0.2, 0.03 * overlap)
        return max(0.08, min(0.35, total / max(1, min(len(evidences), 8))))

    def _first_security(self, market_context: Mapping[str, Any]) -> str | None:
        secs = market_context.get("securities") if isinstance(market_context, Mapping) else None
        if isinstance(secs, Mapping) and secs:
            return next(iter(secs.keys()))
        return None

    def _top_query_keywords(self, query: str, k: int = 6) -> list[str]:
        words = re.findall(r"[A-Za-z][A-Za-z0-9_\-]*", query.lower())
        seen: list[str] = []
        for w in words:
            if len(w) <= 2 or w in self._STOPWORDS:
                continue
            if w not in seen:
                seen.append(w)
        return seen[:k]
