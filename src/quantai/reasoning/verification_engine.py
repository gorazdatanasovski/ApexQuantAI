from __future__ import annotations

import math
import sqlite3
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

import numpy as np
import pandas as pd
import sympy as sp


@dataclass
class VerificationCheck:
    name: str
    kind: str
    passed: bool
    score: float
    summary: str
    details: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VerificationReport:
    candidate_title: str
    verdict: str
    overall_score: float
    symbolic_checks: List[VerificationCheck] = field(default_factory=list)
    empirical_checks: List[VerificationCheck] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommended_refinements: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "candidate_title": self.candidate_title,
            "verdict": self.verdict,
            "overall_score": self.overall_score,
            "symbolic_checks": [c.as_dict() for c in self.symbolic_checks],
            "empirical_checks": [c.as_dict() for c in self.empirical_checks],
            "warnings": list(self.warnings),
            "recommended_refinements": list(self.recommended_refinements),
        }


class VerificationEngine:
    """
    Empirical + symbolic verification layer for QuantAI theorem candidates.

    Design goals:
    - accept flexible candidate dictionaries from the conjecture engine
    - perform explicit symbolic checks with SymPy when expressions are supplied
    - perform empirical falsification tests against the local Bloomberg feature store
    - return structured pass/fail diagnostics instead of a single opaque score
    """

    def __init__(self, db_path: str | Path = "data/market_history.sqlite"):
        self.db_path = Path(db_path)
        self._conn: Optional[sqlite3.Connection] = None
        self._feature_columns_cache: Optional[set[str]] = None

    # -----------------------------
    # connection helpers
    # -----------------------------
    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            if not self.db_path.exists():
                raise FileNotFoundError(f"Feature store database not found: {self.db_path}")
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
            self._feature_columns_cache = None

    def __enter__(self) -> "VerificationEngine":
        _ = self.conn
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    # -----------------------------
    # public API
    # -----------------------------
    def verify_candidate(
        self,
        candidate: Mapping[str, Any],
        *,
        security: Optional[str] = None,
        benchmark_security: Optional[str] = None,
        min_symbolic_score: float = 0.65,
        min_empirical_score: float = 0.55,
    ) -> VerificationReport:
        title = str(
            candidate.get("title")
            or candidate.get("theorem_statement")
            or candidate.get("statement")
            or "Untitled candidate"
        )

        symbolic_checks = self._run_symbolic_checks(candidate)
        empirical_checks = self._run_empirical_checks(
            candidate,
            security=security or self._infer_security(candidate),
            benchmark_security=benchmark_security,
        )

        warnings: List[str] = []
        refinements: List[str] = []

        symbolic_score = self._aggregate_score(symbolic_checks)
        empirical_score = self._aggregate_score(empirical_checks)

        if not symbolic_checks:
            warnings.append("No symbolic checks were supplied; symbolic validity remains untested.")
            refinements.append("Add explicit symbolic tasks with lhs/rhs identities or qualitative constraints.")
        elif symbolic_score < min_symbolic_score:
            refinements.append("Strengthen or revise the symbolic assumptions before trusting the conjecture.")

        if not empirical_checks:
            warnings.append("No empirical checks were supplied; empirical falsification remains incomplete.")
            refinements.append("Add explicit empirical tests tied to a security, basket, or factor panel.")
        elif empirical_score < min_empirical_score:
            refinements.append("Refine the candidate so the implied empirical signature is sharper and testable.")

        overall = self._weighted_overall(symbolic_score, empirical_score, bool(symbolic_checks), bool(empirical_checks))
        verdict = self._choose_verdict(overall, symbolic_score, empirical_score, min_symbolic_score, min_empirical_score)

        for check in symbolic_checks + empirical_checks:
            if not check.passed:
                refinements.append(f"Resolve failed {check.kind} check: {check.name}.")

        refinements = self._dedupe_preserve_order(refinements)
        warnings = self._dedupe_preserve_order(warnings)

        return VerificationReport(
            candidate_title=title,
            verdict=verdict,
            overall_score=overall,
            symbolic_checks=symbolic_checks,
            empirical_checks=empirical_checks,
            warnings=warnings,
            recommended_refinements=refinements,
        )

    def verify_candidates(
        self,
        candidates: Sequence[Mapping[str, Any]],
        *,
        security: Optional[str] = None,
        benchmark_security: Optional[str] = None,
    ) -> List[VerificationReport]:
        return [
            self.verify_candidate(c, security=security, benchmark_security=benchmark_security)
            for c in candidates
        ]

    # -----------------------------
    # symbolic verification
    # -----------------------------
    def _run_symbolic_checks(self, candidate: Mapping[str, Any]) -> List[VerificationCheck]:
        variables = candidate.get("variables") or {}
        assumptions = candidate.get("assumptions") or []
        tasks = candidate.get("symbolic_tasks") or []
        if isinstance(tasks, Mapping):
            tasks = [tasks]
        if isinstance(tasks, str):
            tasks = [{"kind": "qualitative", "name": tasks, "description": tasks}]

        checks: List[VerificationCheck] = []
        symbols = self._build_symbol_table(variables, assumptions)

        for i, raw_task in enumerate(tasks, start=1):
            if isinstance(raw_task, str):
                raw_task = {"kind": "qualitative", "name": raw_task, "description": raw_task}
            task = dict(raw_task)
            kind = str(task.get("kind", "identity")).lower()
            name = str(task.get("name") or f"symbolic_task_{i}")

            try:
                if kind in {"identity", "equality", "equation"}:
                    checks.append(self._check_symbolic_identity(name, task, symbols))
                elif kind in {"positivity", "nonnegativity"}:
                    checks.append(self._check_symbolic_positivity(name, task, symbols))
                elif kind in {"derivative_zero", "stationary_point"}:
                    checks.append(self._check_derivative_zero(name, task, symbols))
                elif kind in {"monotone", "monotonicity"}:
                    checks.append(self._check_monotonicity(name, task, symbols))
                else:
                    checks.append(
                        VerificationCheck(
                            name=name,
                            kind="symbolic",
                            passed=False,
                            score=0.0,
                            summary=f"Unsupported symbolic task kind: {kind}",
                            details={"task": task},
                        )
                    )
            except Exception as exc:
                checks.append(
                    VerificationCheck(
                        name=name,
                        kind="symbolic",
                        passed=False,
                        score=0.0,
                        summary=f"Symbolic check failed with exception: {exc}",
                        details={"task": task},
                    )
                )

        return checks

    def _check_symbolic_identity(self, name: str, task: Mapping[str, Any], symbols: Dict[str, Any]) -> VerificationCheck:
        lhs = sp.sympify(str(task.get("lhs", "0")), locals=symbols)
        rhs = sp.sympify(str(task.get("rhs", "0")), locals=symbols)
        diff = sp.simplify(lhs - rhs)

        if diff == 0:
            return VerificationCheck(
                name=name,
                kind="symbolic",
                passed=True,
                score=1.0,
                summary="Symbolic identity simplified exactly to zero.",
                details={"lhs": str(lhs), "rhs": str(rhs), "difference": "0"},
            )

        max_abs = self._numeric_probe(diff, symbols)
        passed = max_abs is not None and max_abs < float(task.get("tolerance", 1e-8))
        score = 0.85 if passed else 0.0
        return VerificationCheck(
            name=name,
            kind="symbolic",
            passed=passed,
            score=score,
            summary=(
                "Identity did not simplify symbolically but passed numeric probing."
                if passed
                else "Identity failed symbolic and numeric validation."
            ),
            details={
                "lhs": str(lhs),
                "rhs": str(rhs),
                "difference": str(diff),
                "numeric_probe_max_abs": max_abs,
            },
        )

    def _check_symbolic_positivity(self, name: str, task: Mapping[str, Any], symbols: Dict[str, Any]) -> VerificationCheck:
        expr = sp.sympify(str(task.get("expr", task.get("expression", "0"))), locals=symbols)
        simplified = sp.simplify(expr)
        is_nonnegative = simplified.is_nonnegative
        is_positive = simplified.is_positive
        passed = bool(is_nonnegative or is_positive)
        score = 1.0 if passed else 0.0
        return VerificationCheck(
            name=name,
            kind="symbolic",
            passed=passed,
            score=score,
            summary=(
                "Expression is nonnegative under the supplied assumptions."
                if passed
                else "Could not prove nonnegativity under the supplied assumptions."
            ),
            details={"expression": str(expr), "simplified": str(simplified)},
        )

    def _check_derivative_zero(self, name: str, task: Mapping[str, Any], symbols: Dict[str, Any]) -> VerificationCheck:
        expr = sp.sympify(str(task.get("expr", "0")), locals=symbols)
        var_name = str(task.get("var", task.get("variable", "x")))
        var = symbols.get(var_name, sp.Symbol(var_name, real=True))
        point = sp.sympify(str(task.get("point", "0")), locals=symbols)
        deriv = sp.diff(expr, var)
        val = sp.simplify(deriv.subs(var, point))
        passed = val == 0
        return VerificationCheck(
            name=name,
            kind="symbolic",
            passed=passed,
            score=1.0 if passed else 0.0,
            summary=(
                f"First derivative vanishes at {point}." if passed else f"First derivative does not vanish at {point}."
            ),
            details={"expression": str(expr), "derivative": str(deriv), "value_at_point": str(val)},
        )

    def _check_monotonicity(self, name: str, task: Mapping[str, Any], symbols: Dict[str, Any]) -> VerificationCheck:
        expr = sp.sympify(str(task.get("expr", "0")), locals=symbols)
        var_name = str(task.get("var", task.get("variable", "x")))
        direction = str(task.get("direction", "increasing")).lower()
        var = symbols.get(var_name, sp.Symbol(var_name, real=True))
        deriv = sp.simplify(sp.diff(expr, var))
        sign_flag = deriv.is_nonnegative if direction == "increasing" else deriv.is_nonpositive
        passed = bool(sign_flag)
        return VerificationCheck(
            name=name,
            kind="symbolic",
            passed=passed,
            score=1.0 if passed else 0.0,
            summary=(
                f"Expression is provably {direction}." if passed else f"Could not prove {direction} monotonicity."
            ),
            details={"expression": str(expr), "derivative": str(deriv), "direction": direction},
        )

    def _build_symbol_table(self, variables: Mapping[str, Any], assumptions: Sequence[Any]) -> Dict[str, Any]:
        positivity_names = set()
        real_names = set()
        for raw in assumptions:
            text = str(raw).lower()
            for name in variables.keys():
                lname = str(name).lower()
                if lname in text:
                    if any(token in text for token in ["> 0", ">= 0", "positive", "nonnegative"]):
                        positivity_names.add(str(name))
                    if "real" in text:
                        real_names.add(str(name))

        symbols: Dict[str, Any] = {"pi": sp.pi, "E": sp.E, "exp": sp.exp, "log": sp.log, "sqrt": sp.sqrt}
        for name in variables.keys():
            symbols[str(name)] = sp.Symbol(
                str(name),
                real=(str(name) in real_names) or (str(name) in positivity_names),
                positive=str(name) in positivity_names,
            )
        return symbols

    def _numeric_probe(self, expr: sp.Expr, symbols: Mapping[str, Any]) -> Optional[float]:
        free = sorted(expr.free_symbols, key=lambda s: s.name)
        if not free:
            try:
                return float(abs(complex(expr.evalf())))
            except Exception:
                return None

        probes: Dict[sp.Symbol, float] = {}
        for idx, sym in enumerate(free, start=1):
            probes[sym] = 0.25 + 0.5 * idx
            if getattr(sym, "is_positive", False):
                probes[sym] = 1.0 + idx

        try:
            val = expr.evalf(subs=probes)
            return float(abs(complex(val)))
        except Exception:
            return None

    # -----------------------------
    # empirical verification
    # -----------------------------
    def _run_empirical_checks(
        self,
        candidate: Mapping[str, Any],
        *,
        security: Optional[str],
        benchmark_security: Optional[str],
    ) -> List[VerificationCheck]:
        tasks = candidate.get("empirical_tests") or []
        if isinstance(tasks, Mapping):
            tasks = [tasks]
        if isinstance(tasks, str):
            tasks = [{"kind": tasks, "name": tasks}]

        if not tasks or not security:
            return []

        df = self._load_feature_frame(security)
        bench_df = self._load_feature_frame(benchmark_security) if benchmark_security else None
        checks: List[VerificationCheck] = []

        for i, raw_task in enumerate(tasks, start=1):
            if isinstance(raw_task, str):
                raw_task = {"kind": raw_task, "name": raw_task}
            task = dict(raw_task)
            kind = self._normalize_empirical_kind(str(task.get("kind") or task.get("name") or ""))
            name = str(task.get("name") or f"empirical_task_{i}")

            try:
                if kind == "vol_clustering":
                    checks.append(self._check_vol_clustering(name, df))
                elif kind == "leverage_effect":
                    checks.append(self._check_leverage_effect(name, df))
                elif kind == "mean_reversion":
                    checks.append(self._check_mean_reversion(name, df))
                elif kind == "hurst_persistence":
                    checks.append(self._check_hurst_persistence(name, df))
                elif kind == "jump_share":
                    checks.append(self._check_jump_share(name, df))
                elif kind == "benchmark_relative_corr":
                    checks.append(self._check_benchmark_relative_corr(name, df, bench_df))
                elif kind == "range_vol_link":
                    checks.append(self._check_range_vol_link(name, df))
                else:
                    checks.append(
                        VerificationCheck(
                            name=name,
                            kind="empirical",
                            passed=False,
                            score=0.0,
                            summary=f"Unsupported empirical test kind: {kind}",
                            details={"task": task},
                        )
                    )
            except Exception as exc:
                checks.append(
                    VerificationCheck(
                        name=name,
                        kind="empirical",
                        passed=False,
                        score=0.0,
                        summary=f"Empirical check failed with exception: {exc}",
                        details={"task": task},
                    )
                )

        return checks

    def _normalize_empirical_kind(self, text: str) -> str:
        t = text.strip().lower().replace("-", "_").replace(" ", "_")
        if any(k in t for k in ["cluster", "vol_persist", "volatility_persistence"]):
            return "vol_clustering"
        if any(k in t for k in ["leverage", "return_vol", "negative_return_vol"]):
            return "leverage_effect"
        if any(k in t for k in ["mean_reversion", "ou", "reversion"]):
            return "mean_reversion"
        if any(k in t for k in ["hurst", "self_similar", "persistence"]):
            return "hurst_persistence"
        if any(k in t for k in ["jump", "bipower"]):
            return "jump_share"
        if any(k in t for k in ["benchmark", "relative_corr", "cross_asset"]):
            return "benchmark_relative_corr"
        if any(k in t for k in ["range", "high_low", "parkinson"]):
            return "range_vol_link"
        return t

    def _check_vol_clustering(self, name: str, df: pd.DataFrame) -> VerificationCheck:
        ret_col = self._first_existing(df, ["log_return", "return", "ret"])
        vol = df[ret_col].abs().dropna()
        ac1 = float(vol.autocorr(lag=1)) if len(vol) > 10 else float("nan")
        ac5 = float(vol.autocorr(lag=5)) if len(vol) > 20 else float("nan")
        score = np.nanmean([max(ac1, 0.0), max(ac5, 0.0)])
        passed = bool(np.isfinite(score) and score > 0.05)
        return VerificationCheck(
            name=name,
            kind="empirical",
            passed=passed,
            score=float(max(min(score, 1.0), 0.0)) if np.isfinite(score) else 0.0,
            summary=(
                "Absolute returns exhibit persistence consistent with volatility clustering."
                if passed
                else "Absolute-return persistence is weak for the tested sample."
            ),
            details={"abs_return_autocorr_lag1": ac1, "abs_return_autocorr_lag5": ac5},
        )

    def _check_leverage_effect(self, name: str, df: pd.DataFrame) -> VerificationCheck:
        ret_col = self._first_existing(df, ["log_return", "return", "ret"])
        vol_col = self._first_existing(
            df,
            [
                "realized_var_21",
                "rv_21",
                "realized_vol_21",
                "rv_63",
                "realized_var_63",
            ],
        )
        x = df[ret_col]
        y = df[vol_col].shift(-1)
        valid = pd.concat([x, y], axis=1).dropna()
        if len(valid) < 20:
            return VerificationCheck(name, "empirical", False, 0.0, "Insufficient data for leverage-effect test.")
        corr = float(valid.iloc[:, 0].corr(valid.iloc[:, 1]))
        passed = corr < 0
        score = min(abs(corr), 1.0)
        return VerificationCheck(
            name=name,
            kind="empirical",
            passed=passed,
            score=score,
            summary=(
                "Negative return/forward-volatility relation is present."
                if passed
                else "Leverage effect is absent or reversed in the sample."
            ),
            details={"corr_return_future_vol": corr, "vol_column": vol_col},
        )

    def _check_mean_reversion(self, name: str, df: pd.DataFrame) -> VerificationCheck:
        beta_col = self._first_existing(df, ["ou_beta_21", "ou_beta_63", "ou_beta_5"])
        kappa_col = self._first_existing(df, ["ou_kappa_21", "ou_kappa_63", "ou_kappa_5"])
        if beta_col is None and kappa_col is None:
            ret_col = self._first_existing(df, ["log_return", "return", "ret"])
            series = df[ret_col].dropna()
            if len(series) < 30:
                return VerificationCheck(name, "empirical", False, 0.0, "Insufficient data for mean-reversion test.")
            x = series.shift(1)
            y = series
            valid = pd.concat([x, y], axis=1).dropna()
            beta = float(np.polyfit(valid.iloc[:, 0], valid.iloc[:, 1], 1)[0])
            passed = beta < 1.0
            score = float(max(0.0, min(1.0, 1.0 - max(beta - 1.0, 0.0))))
            return VerificationCheck(
                name=name,
                kind="empirical",
                passed=passed,
                score=score,
                summary=(
                    "Discrete AR(1)-style slope is below one, consistent with mean reversion."
                    if passed
                    else "Estimated slope is too persistent for mean reversion."
                ),
                details={"estimated_beta": beta},
            )

        metric_series = df[beta_col] if beta_col else df[kappa_col]
        metric = float(metric_series.dropna().median()) if metric_series.notna().any() else float("nan")
        passed = bool(np.isfinite(metric) and ((metric < 1.0) if beta_col else (metric > 0.0)))
        score = 1.0 if passed else 0.0
        return VerificationCheck(
            name=name,
            kind="empirical",
            passed=passed,
            score=score,
            summary=(
                "OU-style calibration indicates mean reversion."
                if passed
                else "OU-style calibration does not support mean reversion."
            ),
            details={"beta_col": beta_col, "kappa_col": kappa_col, "median_metric": metric},
        )

    def _check_hurst_persistence(self, name: str, df: pd.DataFrame) -> VerificationCheck:
        h_col = self._first_existing(df, ["hurst_varscale_63", "hurst_varscale_21", "hurst_varscale_5"])
        if h_col is None:
            return VerificationCheck(name, "empirical", False, 0.0, "No Hurst-style feature column is available.")
        h = float(df[h_col].dropna().median()) if df[h_col].notna().any() else float("nan")
        passed = bool(np.isfinite(h) and 0.0 < h < 1.0)
        score = 1.0 - min(abs(h - 0.5), 0.5) * 2.0 if np.isfinite(h) else 0.0
        return VerificationCheck(
            name=name,
            kind="empirical",
            passed=passed,
            score=float(max(min(score, 1.0), 0.0)),
            summary=(
                "Hurst-style estimate is finite and lies in the admissible range (0,1)."
                if passed
                else "Hurst-style estimate is missing or outside the admissible range."
            ),
            details={"hurst_estimate": h, "column": h_col},
        )

    def _check_jump_share(self, name: str, df: pd.DataFrame) -> VerificationCheck:
        jump_col = self._first_existing(df, ["jump_var_21", "jump_var_63", "jump_var_5"])
        rv_col = self._first_existing(df, ["realized_var_21", "rv_21", "realized_var_63", "rv_63"])
        if jump_col is None or rv_col is None:
            return VerificationCheck(name, "empirical", False, 0.0, "Jump-share features are unavailable.")
        valid = df[[jump_col, rv_col]].dropna()
        if valid.empty:
            return VerificationCheck(name, "empirical", False, 0.0, "Jump-share features contain no valid rows.")
        share = (valid[jump_col] / valid[rv_col].replace(0.0, np.nan)).replace([np.inf, -np.inf], np.nan).dropna()
        if share.empty:
            return VerificationCheck(name, "empirical", False, 0.0, "Jump-share ratio is undefined in the sample.")
        median_share = float(share.median())
        passed = 0.0 <= median_share <= 1.0
        score = 1.0 if passed else 0.0
        return VerificationCheck(
            name=name,
            kind="empirical",
            passed=passed,
            score=score,
            summary=(
                "Jump-share ratio lies in the admissible range [0,1]."
                if passed
                else "Jump-share ratio falls outside the admissible range."
            ),
            details={"median_jump_share": median_share, "jump_column": jump_col, "rv_column": rv_col},
        )

    def _check_benchmark_relative_corr(
        self,
        name: str,
        df: pd.DataFrame,
        bench_df: Optional[pd.DataFrame],
    ) -> VerificationCheck:
        if bench_df is None:
            return VerificationCheck(name, "empirical", False, 0.0, "Benchmark security was not supplied.")
        ret_col = self._first_existing(df, ["log_return", "return", "ret"])
        bench_ret_col = self._first_existing(bench_df, ["log_return", "return", "ret"])
        merged = pd.merge(
            df[["date", ret_col]].rename(columns={ret_col: "x"}),
            bench_df[["date", bench_ret_col]].rename(columns={bench_ret_col: "y"}),
            on="date",
            how="inner",
        ).dropna()
        if len(merged) < 20:
            return VerificationCheck(name, "empirical", False, 0.0, "Insufficient overlap with benchmark series.")
        corr = float(merged["x"].corr(merged["y"]))
        passed = np.isfinite(corr)
        score = float(abs(corr)) if np.isfinite(corr) else 0.0
        return VerificationCheck(
            name=name,
            kind="empirical",
            passed=passed,
            score=min(score, 1.0),
            summary="Benchmark-relative correlation estimated successfully." if passed else "Could not estimate benchmark-relative correlation.",
            details={"return_correlation": corr},
        )

    def _check_range_vol_link(self, name: str, df: pd.DataFrame) -> VerificationCheck:
        range_col = self._first_existing(df, ["log_hl_range", "hl_range", "parkinson_var"])
        rv_col = self._first_existing(df, ["realized_var_21", "rv_21", "realized_vol_21", "rv_63"])
        if range_col is None or rv_col is None:
            return VerificationCheck(name, "empirical", False, 0.0, "Range/volatility features are unavailable.")
        valid = df[[range_col, rv_col]].dropna()
        if len(valid) < 20:
            return VerificationCheck(name, "empirical", False, 0.0, "Insufficient range/volatility observations.")
        corr = float(valid[range_col].corr(valid[rv_col]))
        passed = corr > 0
        score = min(abs(corr), 1.0)
        return VerificationCheck(
            name=name,
            kind="empirical",
            passed=passed,
            score=score,
            summary=(
                "High-low range is positively related to realized volatility."
                if passed
                else "Range/volatility link is weak or has the wrong sign."
            ),
            details={"corr_range_vol": corr, "range_column": range_col, "rv_column": rv_col},
        )

    # -----------------------------
    # data helpers
    # -----------------------------
    def _infer_security(self, candidate: Mapping[str, Any]) -> Optional[str]:
        for key in ["security", "ticker", "instrument"]:
            if candidate.get(key):
                return str(candidate[key])
        tests = candidate.get("empirical_tests") or []
        if isinstance(tests, Mapping):
            tests = [tests]
        for test in tests:
            if isinstance(test, Mapping):
                for key in ["security", "ticker", "instrument"]:
                    if test.get(key):
                        return str(test[key])
        return None

    def _load_feature_frame(self, security: Optional[str]) -> pd.DataFrame:
        if not security:
            return pd.DataFrame()
        table = self._resolve_feature_table()
        query = f"SELECT * FROM {table} WHERE security = ? ORDER BY date"
        df = pd.read_sql_query(query, self.conn, params=[security])
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
        return df

    def _resolve_feature_table(self) -> str:
        candidates = ["bloomberg_daily_features", "daily_features", "market_features"]
        rows = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        existing = {str(r[0]) for r in rows}
        for name in candidates:
            if name in existing:
                return name
        raise RuntimeError(
            f"No feature table found. Expected one of {candidates}; existing tables are {sorted(existing)}"
        )

    def _feature_columns(self) -> set[str]:
        if self._feature_columns_cache is None:
            table = self._resolve_feature_table()
            rows = self.conn.execute(f"PRAGMA table_info({table})").fetchall()
            self._feature_columns_cache = {str(r[1]) for r in rows}
        return self._feature_columns_cache

    def _first_existing(self, df: pd.DataFrame, candidates: Sequence[str]) -> Optional[str]:
        for col in candidates:
            if col in df.columns:
                return col
        return None

    # -----------------------------
    # scoring / verdict helpers
    # -----------------------------
    def _aggregate_score(self, checks: Sequence[VerificationCheck]) -> float:
        if not checks:
            return 0.0
        return float(np.mean([float(c.score) for c in checks]))

    def _weighted_overall(self, symbolic_score: float, empirical_score: float, has_symbolic: bool, has_empirical: bool) -> float:
        if has_symbolic and has_empirical:
            return 0.55 * symbolic_score + 0.45 * empirical_score
        if has_symbolic:
            return symbolic_score
        if has_empirical:
            return empirical_score
        return 0.0

    def _choose_verdict(
        self,
        overall: float,
        symbolic_score: float,
        empirical_score: float,
        min_symbolic_score: float,
        min_empirical_score: float,
    ) -> str:
        if overall >= 0.85 and symbolic_score >= min_symbolic_score and empirical_score >= min_empirical_score:
            return "provisionally_supported"
        if overall >= 0.65:
            return "partially_supported"
        if overall >= 0.40:
            return "weak_or_incomplete"
        return "rejected_or_unverified"

    def _dedupe_preserve_order(self, items: Iterable[str]) -> List[str]:
        seen = set()
        out: List[str] = []
        for item in items:
            if item not in seen:
                seen.add(item)
                out.append(item)
        return out


__all__ = [
    "VerificationCheck",
    "VerificationEngine",
    "VerificationReport",
]
 