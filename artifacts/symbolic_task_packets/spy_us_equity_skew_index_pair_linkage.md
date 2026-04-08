# Symbolic Task Packet: Evidence-anchored structural conjecture

- Family: spot_vol_linkage
- Securities: SPY US Equity, SKEW Index

## Assumptions
- Empirical scope anchored to SPY US Equity.
- sigma_s > 0
- sigma_v > 0
- -1 <= rho <= 1
- Regime labels correspond to empirically observed states
- Observed feature differences are mapped consistently to theorem notation

## Tasks
### covariance_symmetry
- Kind: verify_identity
- Rationale: Basic symmetry check for spot-vol covariance style terms.
```json
{
  "lhs": "rho*sigma_s*sigma_v",
  "rhs": "sigma_v*sigma_s*rho"
}
```
### quadratic_form_nonnegative
- Kind: verify_nonnegative
- Rationale: Any squared coupling residual should remain nonnegative.
```json
{
  "expression": "(sigma_s - rho*sigma_v)**2"
}
```
### variance_of_linear_combination
- Kind: verify_nonnegative
- Rationale: A variance-style quadratic form should remain nonnegative under admissible coupling assumptions.
```json
{
  "expression": "sigma_s**2 + sigma_v**2 - 2*rho*sigma_s*sigma_v"
}
```
### regime_gap_identity
- Kind: verify_identity
- Rationale: Checks algebraic coherence of regime-difference decomposition used in pair-linkage narratives.
```json
{
  "lhs": "(rv_hi - rv_lo) + (iv_hi - iv_lo)",
  "rhs": "(rv_hi + iv_hi) - (rv_lo + iv_lo)"
}
```
### zero_spread_baseline
- Kind: verify_derivative_zero
- Rationale: Provides a simple baseline zero-point regularity check for local spread/coupling expansions.
```json
{
  "expression": "x**2",
  "variable": "x",
  "point": 0
}
```

## Notes
- These are symbolic consistency checks for pair-linkage theorems.
- Packet assumptions are threaded into symbolic execution so rho bounds and positivity can actually be used.