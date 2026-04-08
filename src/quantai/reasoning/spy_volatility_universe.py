from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from quantai.reasoning.universe_research_scheduler import (
    JobTemplate,
    UniverseResearchScheduler,
    UniverseSpec,
)


SPY_VOLATILITY_CORE_SECURITIES: List[str] = [
    "SPY US Equity",
    "SPX Index",
    "VIX Index",
    "VIX3M Index",
    "VVIX Index",
    "SKEW Index",
    "ES1 Index",
]

SPY_VOLATILITY_EXTENDED_SECURITIES: List[str] = [
    "SPY US Equity",
    "SPX Index",
    "VIX Index",
    "VIX3M Index",
    "VVIX Index",
    "SKEW Index",
    "ES1 Index",
    "UX1 Index",
    "UX2 Index",
]


@dataclass(frozen=True)
class SpyVolatilityAgenda:
    universe: UniverseSpec
    templates: List[JobTemplate]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "universe": self.universe.as_dict(),
            "templates": [t.as_dict() for t in self.templates],
        }


def default_spy_volatility_universe(
    *,
    extended: bool = False,
) -> UniverseSpec:
    securities = list(
        SPY_VOLATILITY_EXTENDED_SECURITIES
        if extended
        else SPY_VOLATILITY_CORE_SECURITIES
    )
    return UniverseSpec(
        name="spy_volatility_universe",
        securities=securities,
        benchmark_security="SPY US Equity",
        metadata={
            "anchor_asset": "SPY US Equity",
            "index_anchor": "SPX Index",
            "implied_vol_anchor": "VIX Index",
            "term_structure_anchor": "VIX3M Index",
            "vol_of_vol_anchor": "VVIX Index",
            "tail_risk_anchor": "SKEW Index",
            "futures_anchor": "ES1 Index",
            "research_focus": [
                "rough volatility",
                "realized variance scaling",
                "spot-volatility coupling",
                "term structure state",
                "tail-risk regime shifts",
                "execution under volatility state",
            ],
        },
    )


def default_spy_volatility_templates() -> List[JobTemplate]:
    return [
        JobTemplate(
            name="spy_roughness_scaling",
            query_template=(
                "Propose a theorem linking rough-volatility roughness to realized "
                "variance scaling for {primary}."
            ),
            use_all_securities=False,
            min_securities=1,
            include_evidence=True,
            include_theorem=True,
            include_market_memory=True,
            include_market_calibration=False,
            include_market_live_snapshot=False,
            acceptance_score=0.80,
        ),
        JobTemplate(
            name="spy_execution_under_vol_state",
            query_template=(
                "Pull the live Bloomberg snapshot for {primary} and formulate the "
                "precise Almgren-Chriss liquidating trajectory for 10^5 shares over "
                "T=1 hour, conditioning on the current volatility state."
            ),
            use_all_securities=False,
            min_securities=1,
            include_evidence=True,
            include_theorem=False,
            include_market_memory=True,
            include_market_calibration=False,
            include_market_live_snapshot=True,
            acceptance_score=0.80,
        ),
        JobTemplate(
            name="pair_ou_spread",
            query_template=(
                "Retrieve the {primary} and {secondary} spread over the last 60 minutes "
                "and compute the maximum likelihood estimation for the OU mean-reversion speed kappa."
            ),
            use_all_securities=False,
            min_securities=2,
            include_evidence=True,
            include_theorem=True,
            include_market_memory=True,
            include_market_calibration=True,
            include_market_live_snapshot=False,
            acceptance_score=0.80,
        ),
        JobTemplate(
            name="spot_vol_linkage_theorem",
            query_template=(
                "Propose a theorem describing the empirical and theoretical linkage between "
                "{primary} and {secondary}, emphasizing volatility transmission, roughness, "
                "and regime dependence."
            ),
            use_all_securities=False,
            min_securities=2,
            include_evidence=True,
            include_theorem=True,
            include_market_memory=True,
            include_market_calibration=True,
            include_market_live_snapshot=False,
            acceptance_score=0.82,
        ),
        JobTemplate(
            name="universe_state_summary",
            query_template=(
                "Summarize the current Bloomberg empirical memory, roughness signatures, "
                "term-structure state, and tail-risk state for {universe_name}."
            ),
            use_all_securities=True,
            min_securities=1,
            include_evidence=False,
            include_theorem=False,
            include_market_memory=True,
            include_market_calibration=False,
            include_market_live_snapshot=False,
            acceptance_score=0.80,
        ),
    ]


def focused_spy_vix_templates() -> List[JobTemplate]:
    """
    Narrower agenda when you want only the highest-value SPY/VIX relationships.
    """
    return [
        JobTemplate(
            name="spy_vix_linkage",
            query_template=(
                "Propose a theorem linking {primary} and {secondary} through spot-volatility "
                "coupling, realized variance scaling, and regime transitions."
            ),
            use_all_securities=False,
            min_securities=2,
            include_evidence=True,
            include_theorem=True,
            include_market_memory=True,
            include_market_calibration=True,
            include_market_live_snapshot=False,
            acceptance_score=0.83,
        ),
        JobTemplate(
            name="vix_vvix_linkage",
            query_template=(
                "Propose a theorem linking {primary} and {secondary} through implied volatility, "
                "vol-of-vol, and jump-intensity style state dependence."
            ),
            use_all_securities=False,
            min_securities=2,
            include_evidence=True,
            include_theorem=True,
            include_market_memory=True,
            include_market_calibration=True,
            include_market_live_snapshot=False,
            acceptance_score=0.83,
        ),
        JobTemplate(
            name="spy_vix_term_state",
            query_template=(
                "Summarize the empirical state of {primary}, {secondary}, and {universe_name}, "
                "with emphasis on roughness, mean reversion, skew, and term structure."
            ),
            use_all_securities=True,
            min_securities=1,
            include_evidence=False,
            include_theorem=False,
            include_market_memory=True,
            include_market_calibration=False,
            include_market_live_snapshot=False,
            acceptance_score=0.80,
        ),
    ]


def build_spy_volatility_agenda(
    *,
    extended_universe: bool = False,
    focused: bool = False,
) -> SpyVolatilityAgenda:
    universe = default_spy_volatility_universe(extended=extended_universe)
    templates = focused_spy_vix_templates() if focused else default_spy_volatility_templates()
    return SpyVolatilityAgenda(universe=universe, templates=templates)


class SpyVolatilityUniverseRunner:
    """
    Convenience wrapper around UniverseResearchScheduler for the SPY/VIX agenda.
    """

    def __init__(
        self,
        work_dir: str | Path = "rag_ingest_state",
        market_db_path: str | Path = "data/market_history.sqlite",
        output_dir: str | Path = "artifacts/universe_research_runs",
        answer_mode: str = "auto",
    ) -> None:
        self.scheduler = UniverseResearchScheduler(
            work_dir=work_dir,
            market_db_path=market_db_path,
            output_dir=output_dir,
            answer_mode=answer_mode,
        )

    def run_default(
        self,
        *,
        extended_universe: bool = False,
        focused: bool = False,
        limit_jobs: Optional[int] = None,
    ) -> Dict[str, Any]:
        agenda = build_spy_volatility_agenda(
            extended_universe=extended_universe,
            focused=focused,
        )
        return self.scheduler.run_universe(
            agenda.universe,
            templates=agenda.templates,
            limit_jobs=limit_jobs,
        )


__all__ = [
    "SPY_VOLATILITY_CORE_SECURITIES",
    "SPY_VOLATILITY_EXTENDED_SECURITIES",
    "SpyVolatilityAgenda",
    "default_spy_volatility_universe",
    "default_spy_volatility_templates",
    "focused_spy_vix_templates",
    "build_spy_volatility_agenda",
    "SpyVolatilityUniverseRunner",
]
