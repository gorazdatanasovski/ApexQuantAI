# Rough-variance scaling identification theorem

**Query:** Propose a theorem linking rough-volatility roughness to realized variance scaling for SPY.
**Status:** speculative_candidate
**Score:** 0.502

## Statement
Conjecture: Assume the latent log-volatility process X admits a Volterra representation X_t = X_0 + ∫_0^t K(t,s) dW_s with local kernel singularity K(t,s) ~ c (t-s)^{H-1/2} for H in (0,1/2). Then, as Δ ↓ 0, the increment variance satisfies E[(X_{t+Δ}-X_t)^2] = C_X Δ^{2H} + o(Δ^{2H}), and any realized-variance proxy constructed from sufficiently fine observations for SPY US Equity inherits the same scaling exponent after lower-order noise correction: E[RV_Δ] = a_0 + a_1 Δ^{2H} + o(Δ^{2H}).

## Assumptions
- H > 0 and H < 1/2.
- The volatility driver admits a Volterra representation with local singularity exponent H-1/2.
- The observed realized-variance proxy is asymptotically consistent up to lower-order noise distortion.
- Empirical scope anchored to SPY US Equity.

## Variables
- **H**: roughness exponent
- **Delta**: observation scale Δ
- **K**: Volterra kernel
- **X**: latent log-volatility state
- **RV_Delta**: realized-variance proxy at scale Δ
- **C_X**: latent scaling constant
- **a_0**: noise/intercept term
- **a_1**: leading realized-variance scaling coefficient

## Empirical signature
- roughness_from_variance_scaling
- volatility_clustering_consistency
- range_variance_alignment

## Symbolic agenda
- {'kind': 'positivity', 'name': 'variance_constant_nonnegative', 'expr': 'C_X'}
- {'kind': 'positivity', 'name': 'realized_variance_nonnegative', 'expr': 'a_1*Delta**(2*H)'}

## Failure conditions
- Estimated scaling slope is unstable across windows or frequencies.
- Jump-share dominates the short-horizon variance proxy.
- No persistent roughness signal appears in the Bloomberg feature panel.
- Strengthen or revise the symbolic assumptions before trusting the conjecture.
- Resolve failed symbolic check: variance_constant_nonnegative.
- Resolve failed symbolic check: realized_variance_nonnegative.

## Next actions
- Strengthen or revise the symbolic assumptions before trusting the conjecture.
- Resolve failed symbolic check: variance_constant_nonnegative.
- Resolve failed symbolic check: realized_variance_nonnegative.
- Collect stronger exact excerpts from the book-memory layer.
- Add a formal symbolic derivation or export the candidate to Lean for proof work.

## Verification rounds
### Round 1
- Lab score: 0.502
- Verdict: rejected_or_unverified
- Verification score: 0.264
- Notes:
  - Problem kind: hypothesis
  - Verdict: rejected_or_unverified
### Round 2
- Lab score: 0.502
- Verdict: rejected_or_unverified
- Verification score: 0.264
- Notes:
  - Problem kind: hypothesis
  - Verdict: rejected_or_unverified
### Round 3
- Lab score: 0.502
- Verdict: rejected_or_unverified
- Verification score: 0.264
- Notes:
  - Problem kind: hypothesis
  - Verdict: rejected_or_unverified