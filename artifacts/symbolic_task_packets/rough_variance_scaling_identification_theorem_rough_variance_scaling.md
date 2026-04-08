# Symbolic Task Packet: Rough-variance scaling identification theorem

- Family: rough_variance_scaling
- Securities: SPY US Equity, VIX3M Index

## Assumptions
- H > 0 and H < 1/2.
- The volatility driver admits a Volterra representation with local singularity exponent H-1/2.
- The observed realized-variance proxy is asymptotically consistent up to lower-order noise distortion.
- Empirical scope anchored to SPY US Equity.
- Delta > 0
- 0 < H < 1/2
- C_X >= 0
- a1 >= 0
- Higher-order remainder is lower order than Delta^(2H)

## Tasks
### variance_scaling_factorization
- Kind: verify_identity
- Rationale: Checks algebraic coherence of the scaling-law form used in the theorem candidate.
```json
{
  "lhs": "C_X*Delta**(2*H) + a0 + a1*Delta**(2*H)",
  "rhs": "a0 + (C_X + a1)*Delta**(2*H)"
}
```
### variance_term_nonnegative
- Kind: verify_nonnegative
- Rationale: Under positive coefficient and positive scale assumptions, the scaling contribution should remain nonnegative.
```json
{
  "expression": "a1*Delta**(2*H)"
}
```
### increment_variance_nonnegative
- Kind: verify_nonnegative
- Rationale: Variance contribution must remain nonnegative under the roughness scaling ansatz.
```json
{
  "expression": "C_X*Delta**(2*H)"
}
```
### scaling_at_origin_consistency
- Kind: verify_derivative_zero
- Rationale: Checks a simple origin-consistency proxy for higher-order remainder terms in the small-scale expansion.
```json
{
  "expression": "Delta**(2*H + 1)",
  "variable": "Delta",
  "point": 0
}
```
### exponent_additivity
- Kind: verify_identity
- Rationale: Provides a reusable exponent-composition identity for scaling arguments.
```json
{
  "lhs": "Delta**(2*H) * Delta**(2*K)",
  "rhs": "Delta**(2*(H + K))"
}
```

## Notes
- These tasks do not prove the full theorem.
- They turn the current scaling-law candidate into executable symbolic consistency checks.
- The next layer should connect these tasks to verification_engine and theorem_refinement_engine.