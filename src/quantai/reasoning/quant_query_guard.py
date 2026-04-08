from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Sequence


_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
_PROFANITY = {
    "fuck",
    "fucking",
    "shit",
    "bitch",
    "damn",
    "wtf",
    "bruh",
}
_HATE_CONTEXT = {
    "hate",
    "speech",
    "hitler",
    "nazi",
    "racist",
    "racism",
}
_SMALLTALK = {
    "good",
    "job",
    "hello",
    "hi",
    "hey",
    "yo",
    "thanks",
    "thank",
    "cool",
    "nice",
    "great",
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
    "heston",
    "bergomi",
    "rough",
    "volatility",
    "affine",
    "variance",
    "pde",
    "pdes",
    "bsde",
    "bsdes",
    "forward",
    "theorem",
    "lemma",
    "proposition",
    "derivation",
    "derive",
    "proof",
    "replicating",
    "hedging",
    "feynman",
    "kac",
    "generator",
    "diffusion",
    "markov",
    "stochastic",
}
_VALID_SHORT_SINGLETONS = {
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
    "brownian",
    "black",
    "scholes",
    "hurst",
    "fractional",
    "ornstein",
    "uhlenbeck",
    "pde",
    "sde",
}
_CANONICAL_MAP = {
    "ricatti": "riccati",
    "blackscholes": "black scholes",
    "black-scholes": "black scholes",
    "volterra equations": "volterra equation",
    "volterra processes": "volterra process",
    "pdes": "pde",
    "sdes": "sde",
}


@dataclass(frozen=True)
class QueryGuardDecision:
    reject: bool
    reason: str
    message: str

    def as_dict(self) -> Dict[str, str | bool]:
        return {
            "reject": self.reject,
            "reason": self.reason,
            "message": self.message,
        }


class QuantQueryGuard:
    """
    Guards QuantAI from wasting retrieval / synthesis budget on
    profanity-only, hate-only, gibberish, or generic small-talk prompts.

    The guard is intentionally permissive when a valid quant/math concept
    is present, even if the user writes informally around it.
    """

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return [tok.lower() for tok in _TOKEN_RE.findall(text) if len(tok) > 1]

    @classmethod
    def _normalize(cls, query: str) -> str:
        q = " ".join(str(query).strip().split()).strip('"').lower()
        return _CANONICAL_MAP.get(q, q)

    @classmethod
    def assess(cls, query: str, securities: Sequence[str] | None = None) -> QueryGuardDecision:
        q = cls._normalize(query)
        tokens = cls._tokenize(q)
        securities = [str(x).lower() for x in (securities or []) if str(x).strip()]

        if not tokens:
            return QueryGuardDecision(
                reject=True,
                reason="empty",
                message="No valid mathematical or finance concept was detected in the query.",
            )

        domain_hits = sum(tok in _DOMAIN_TOKENS for tok in tokens)
        profanity_hits = sum(tok in _PROFANITY for tok in tokens)
        hate_hits = sum(tok in _HATE_CONTEXT for tok in tokens)
        smalltalk_hits = sum(tok in _SMALLTALK for tok in tokens)

        # If the query clearly references a security or domain concept, allow it.
        if domain_hits > 0:
            return QueryGuardDecision(reject=False, reason="domain", message="ok")

        if any(sec.split()[0] in q for sec in securities if sec):
            return QueryGuardDecision(reject=False, reason="security", message="ok")

        if profanity_hits > 0 and hate_hits > 0:
            return QueryGuardDecision(
                reject=True,
                reason="abusive_non_domain",
                message="No valid quant / math / finance concept was detected in the query.",
            )

        if len(tokens) <= 3 and smalltalk_hits > 0:
            return QueryGuardDecision(
                reject=True,
                reason="smalltalk",
                message="Ask a quant, stochastic-process, derivatives, or market-structure question.",
            )

        if len(tokens) == 1:
            token = tokens[0]
            if token in _SMALLTALK or token in _PROFANITY or token in _HATE_CONTEXT:
                return QueryGuardDecision(
                    reject=True,
                    reason="non_domain_singleton",
                    message="No valid quant / math / finance concept was detected in the query.",
                )
            vowel_count = sum(ch in "aeiou" for ch in token)
            if len(token) >= 8 and vowel_count <= 1 and token not in _VALID_SHORT_SINGLETONS:
                return QueryGuardDecision(
                    reject=True,
                    reason="gibberish",
                    message="No valid quant / math / finance concept was detected in the query.",
                )

        if profanity_hits > 0 and domain_hits == 0:
            return QueryGuardDecision(
                reject=True,
                reason="profanity_non_domain",
                message="Ask a mathematical, stochastic-process, derivatives, or market-structure question.",
            )

        return QueryGuardDecision(reject=False, reason="allow", message="ok")
