from __future__ import annotations

import ast
from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, Optional

import sympy as sp
from sympy.parsing.sympy_parser import (
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
    parse_expr,
)

_TRANSFORMS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)


@dataclass(frozen=True)
class SymbolicResult:
    operation: str
    result: str

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VerificationResult:
    name: str
    kind: str
    passed: bool
    result: str
    details: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


class UnsafeCodeError(ValueError):
    pass


class SymbolicLogicEngine:
    """
    Assumption-aware deterministic SymPy engine.

    Superior pair-linkage upgrade:
    - keeps limit-aware origin checks
    - keeps theorem-assumption propagation
    - adds bounded-correlation nonnegativity reasoning for
      sigma_s**2 + sigma_v**2 - 2*rho*sigma_s*sigma_v under -1 <= rho <= 1
    """

    def __init__(self) -> None:
        self.base_namespace: Dict[str, Any] = self._build_base_namespace()

    def _build_base_namespace(self) -> Dict[str, Any]:
        ns: Dict[str, Any] = {
            "sp": sp,
            "sympy": sp,
        }

        ns["x"] = sp.Symbol("x", real=True)
        ns["y"] = sp.Symbol("y", real=True)
        ns["z"] = sp.Symbol("z", real=True)
        ns["t"] = sp.Symbol("t", real=True)

        ns["sigma"] = sp.Symbol("sigma", positive=True, real=True)
        ns["mu"] = sp.Symbol("mu", real=True)
        ns["kappa"] = sp.Symbol("kappa", positive=True, real=True)
        ns["theta"] = sp.Symbol("theta", real=True)
        ns["rho"] = sp.Symbol("rho", real=True)
        ns["r"] = sp.Symbol("r", real=True)
        ns["S"] = sp.Symbol("S", positive=True, real=True)

        ns["Delta"] = sp.Symbol("Delta", positive=True, real=True)
        ns["H"] = sp.Symbol("H", positive=True, real=True)
        ns["K"] = sp.Symbol("K", real=True)
        ns["C_X"] = sp.Symbol("C_X", nonnegative=True, real=True)
        ns["a0"] = sp.Symbol("a0", real=True)
        ns["a1"] = sp.Symbol("a1", nonnegative=True, real=True)

        ns["sigma_s"] = sp.Symbol("sigma_s", positive=True, real=True)
        ns["sigma_v"] = sp.Symbol("sigma_v", positive=True, real=True)
        ns["rv_hi"] = sp.Symbol("rv_hi", real=True)
        ns["rv_lo"] = sp.Symbol("rv_lo", real=True)
        ns["iv_hi"] = sp.Symbol("iv_hi", real=True)
        ns["iv_lo"] = sp.Symbol("iv_lo", real=True)

        return ns

    def _with_assumptions(self, assumptions: Optional[Iterable[str]] = None) -> Dict[str, Any]:
        ns: Dict[str, Any] = dict(self.base_namespace)
        if not assumptions:
            return ns
        parsed = self._parse_assumptions(assumptions)
        for name, sym in parsed.items():
            ns[name] = sym
        return ns

    def _expr(self, text: str, *, assumptions: Optional[Iterable[str]] = None):
        ns = self._with_assumptions(assumptions)
        return parse_expr(
            str(text),
            local_dict=ns,
            transformations=_TRANSFORMS,
            evaluate=True,
        )

    def _parse_assumptions(self, assumptions: Iterable[str]) -> Dict[str, sp.Symbol]:
        out: Dict[str, sp.Symbol] = {}

        def set_symbol(name: str, *, positive: bool = False, nonnegative: bool = False, real: bool = True) -> None:
            if nonnegative:
                out[name] = sp.Symbol(name, nonnegative=True, real=real)
            elif positive:
                out[name] = sp.Symbol(name, positive=True, real=real)
            else:
                out[name] = sp.Symbol(name, real=real)

        for raw in assumptions:
            s = " ".join(str(raw).strip().split())
            if not s:
                continue

            if s.endswith("> 0"):
                name = s[:-3].strip()
                if name.isidentifier() or "_" in name:
                    set_symbol(name, positive=True)
                continue

            if s.endswith(">= 0"):
                name = s[:-4].strip()
                if name.isidentifier() or "_" in name:
                    set_symbol(name, nonnegative=True)
                continue

            if s.startswith("0 < ") and " < 1/2" in s:
                name = s.replace("0 < ", "").replace("< 1/2", "").strip()
                if name.isidentifier() or "_" in name:
                    set_symbol(name, positive=True)
                continue

            if "<= rho <=" in s or "<= rho <" in s or "rho <=" in s:
                set_symbol("rho", real=True)
                continue

        return out

    def simplify(self, expression: str, *, assumptions: Optional[Iterable[str]] = None) -> SymbolicResult:
        return SymbolicResult("simplify", str(sp.simplify(self._expr(expression, assumptions=assumptions))))

    def expand(self, expression: str, *, assumptions: Optional[Iterable[str]] = None) -> SymbolicResult:
        return SymbolicResult("expand", str(sp.expand(self._expr(expression, assumptions=assumptions))))

    def factor(self, expression: str, *, assumptions: Optional[Iterable[str]] = None) -> SymbolicResult:
        return SymbolicResult("factor", str(sp.factor(self._expr(expression, assumptions=assumptions))))

    def differentiate(self, expression: str, variable: str, *, assumptions: Optional[Iterable[str]] = None) -> SymbolicResult:
        ns = self._with_assumptions(assumptions)
        var = ns[variable]
        return SymbolicResult("differentiate", str(sp.diff(self._expr(expression, assumptions=assumptions), var)))

    def integrate(self, expression: str, variable: str, *, assumptions: Optional[Iterable[str]] = None) -> SymbolicResult:
        ns = self._with_assumptions(assumptions)
        var = ns[variable]
        return SymbolicResult("integrate", str(sp.integrate(self._expr(expression, assumptions=assumptions), var)))

    def solve(self, expression: str, variable: str, *, assumptions: Optional[Iterable[str]] = None) -> SymbolicResult:
        ns = self._with_assumptions(assumptions)
        var = ns[variable]
        return SymbolicResult("solve", str(sp.solve(self._expr(expression, assumptions=assumptions), var)))

    def series(
        self,
        expression: str,
        variable: str,
        point: int = 0,
        order: int = 6,
        *,
        assumptions: Optional[Iterable[str]] = None,
    ) -> SymbolicResult:
        ns = self._with_assumptions(assumptions)
        var = ns[variable]
        return SymbolicResult(
            "series",
            str(sp.series(self._expr(expression, assumptions=assumptions), var, point, order)),
        )

    def evaluate_expression(self, expression_str: str, *, assumptions: Optional[Iterable[str]] = None) -> str:
        return self.simplify(expression_str, assumptions=assumptions).result

    def verify_identity(
        self,
        lhs: str,
        rhs: str,
        *,
        assumptions: Optional[Iterable[str]] = None,
    ) -> VerificationResult:
        lhs_expr = self._expr(lhs, assumptions=assumptions)
        rhs_expr = self._expr(rhs, assumptions=assumptions)
        difference = sp.simplify(lhs_expr - rhs_expr)
        passed = difference == 0
        return VerificationResult(
            name="identity",
            kind="identity",
            passed=bool(passed),
            result="proved_exactly" if passed else "not_proved",
            details={
                "lhs": str(lhs_expr),
                "rhs": str(rhs_expr),
                "difference": str(difference),
                "assumptions": list(assumptions or []),
            },
        )

    def verify_nonnegative(
        self,
        expression: str,
        *,
        assumptions: Optional[Iterable[str]] = None,
    ) -> VerificationResult:
        expr = self._expr(expression, assumptions=assumptions)
        simplified = sp.simplify(expr)

        passed = False
        reason = "not_proved"

        if simplified.is_nonnegative is True:
            passed = True
            reason = "proved"
        else:
            passed = self._heuristic_nonnegative(simplified, assumptions=list(assumptions or []))
            reason = "proved_by_assumptions" if passed else "not_proved"

        return VerificationResult(
            name="nonnegative",
            kind="nonnegative",
            passed=bool(passed),
            result=reason,
            details={
                "expression": str(expr),
                "simplified": str(simplified),
                "is_nonnegative": simplified.is_nonnegative,
                "assumptions": list(assumptions or []),
            },
        )

    def _heuristic_nonnegative(self, expr, assumptions: List[str]) -> bool:
        if expr.is_Pow and len(expr.args) == 2:
            base, exponent = expr.args
            if exponent.is_integer and exponent >= 2 and exponent % 2 == 0:
                return True

        if expr.is_Mul:
            for arg in expr.args:
                if arg.is_nonnegative is True or arg.is_positive is True:
                    continue
                return False
            return True

        if expr.is_Add:
            good = True
            any_term = False
            for arg in expr.args:
                any_term = True
                if arg.is_nonnegative is True or arg.is_positive is True:
                    continue
                good = False
                break
            if any_term and good:
                return True

        if self._bounded_correlation_quadratic_nonnegative(expr, assumptions):
            return True

        return False

    def _bounded_correlation_quadratic_nonnegative(self, expr, assumptions: List[str]) -> bool:
        normalized = " ".join(" ".join(a.split()) for a in assumptions)
        if "-1 <= rho <= 1" not in normalized and "-1<=rho<=1" not in normalized.replace(" ", ""):
            return False

        rho = self.base_namespace["rho"]
        sigma_s = self.base_namespace["sigma_s"]
        sigma_v = self.base_namespace["sigma_v"]

        target = sp.expand(sigma_s**2 + sigma_v**2 - 2 * rho * sigma_s * sigma_v)
        if sp.expand(expr - target) != 0:
            return False

        rewritten = sp.expand((sigma_s - rho * sigma_v) ** 2 + (1 - rho**2) * sigma_v**2)
        if sp.expand(target - rewritten) != 0:
            return False

        return True

    def verify_limit_zero(
        self,
        expression: str,
        *,
        variable: str,
        point: Any,
        direction: str = "+",
        assumptions: Optional[Iterable[str]] = None,
    ) -> VerificationResult:
        ns = self._with_assumptions(assumptions)
        var = ns[variable]
        expr = self._expr(expression, assumptions=assumptions)
        lim = sp.limit(expr, var, point, dir=direction)
        passed = lim == 0

        return VerificationResult(
            name="limit_zero",
            kind="limit_zero",
            passed=bool(passed),
            result="proved" if passed else "not_proved",
            details={
                "expression": str(expr),
                "variable": variable,
                "point": str(point),
                "direction": direction,
                "limit": str(lim),
                "assumptions": list(assumptions or []),
            },
        )

    def verify_derivative_zero(
        self,
        expression: str,
        *,
        variable: str,
        point: Any,
        assumptions: Optional[Iterable[str]] = None,
    ) -> VerificationResult:
        ns = self._with_assumptions(assumptions)
        var = ns[variable]
        expr = self._expr(expression, assumptions=assumptions)
        derivative = sp.diff(expr, var)

        value = sp.simplify(derivative.subs(var, point))
        passed = value == 0
        result = "proved" if passed else "not_proved"
        limit_payload = None

        if not passed:
            try:
                right_lim = sp.limit(derivative, var, point, dir="+")
                if right_lim == 0:
                    passed = True
                    result = "proved_by_limit"
                limit_payload = {"right_limit": str(right_lim)}
            except Exception as exc:
                limit_payload = {"right_limit_error": str(exc)}

        details = {
            "expression": str(expr),
            "derivative": str(derivative),
            "point": str(point),
            "value": str(value),
            "assumptions": list(assumptions or []),
        }
        if limit_payload is not None:
            details.update(limit_payload)

        return VerificationResult(
            name="derivative_zero",
            kind="derivative_zero",
            passed=bool(passed),
            result=result,
            details=details,
        )

    def execute_proof(self, python_code: str) -> str:
        tree = ast.parse(python_code, mode="exec")
        self._validate_ast(tree)

        safe_builtins = {
            "print": print,
            "range": range,
            "len": len,
            "min": min,
            "max": max,
            "sum": sum,
        }
        env: Dict[str, Any] = dict(self.base_namespace)
        env["__builtins__"] = safe_builtins

        compiled = compile(tree, filename="<symbolic-proof>", mode="exec")
        exec(compiled, env, env)
        visible = {k: v for k, v in env.items() if not k.startswith("_") and k not in {"sp", "sympy", "__builtins__"}}
        rendered = {k: str(v) for k, v in visible.items()}
        return str(rendered)

    def _validate_ast(self, tree: ast.AST) -> None:
        banned_nodes = (
            ast.Import,
            ast.ImportFrom,
            ast.With,
            ast.AsyncWith,
            ast.Try,
            ast.Raise,
            ast.Global,
            ast.Nonlocal,
            ast.Lambda,
            ast.ClassDef,
            ast.AsyncFunctionDef,
        )
        banned_names = {
            "open",
            "exec",
            "eval",
            "compile",
            "input",
            "__import__",
            "globals",
            "locals",
            "getattr",
            "setattr",
            "delattr",
            "breakpoint",
        }
        for node in ast.walk(tree):
            if isinstance(node, banned_nodes):
                raise UnsafeCodeError(f"Unsupported node: {type(node).__name__}")
            if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
                raise UnsafeCodeError("Dunder attribute access is not allowed.")
            if isinstance(node, ast.Name) and node.id in banned_names:
                raise UnsafeCodeError(f"Forbidden name: {node.id}")


__all__ = [
    "SymbolicLogicEngine",
    "SymbolicResult",
    "VerificationResult",
    "UnsafeCodeError",
]
