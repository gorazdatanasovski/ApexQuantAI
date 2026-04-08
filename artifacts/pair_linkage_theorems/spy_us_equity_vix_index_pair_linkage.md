# Pair-Linkage Theorem Run: SPY US Equity / VIX Index

- Created at: 2026-03-28T01:41:58+00:00
- Family matched: True

## Attempts
### Attempt 1
- Selected title: Evidence-anchored structural conjecture
- Prompt: Propose a pair-linkage theorem for SPY US Equity and VIX Index. The theorem must be genuinely about the interaction between the two objects, not a reused single-name rough-variance theorem. Focus on spot-volatility coupling, variance scaling transmission, regime dependence, term-structure state, tail-risk state, cross-object linkage. State: (1) the pair-level object, (2) the predicted relationship or monotonicity, (3) empirical Bloomberg feature signatures, (4) failure conditions, and (5) symbolic structure that can be checked directly.

## Accepted result
```json
{
  "mode_used": "theorem",
  "response": "Research artifact: Evidence-anchored structural conjecture\nStatus: speculative_candidate\nScore: 0.452\n\nStatement:\nConjecture: the objects propose, pair-linkage, theorem admit a common structural representation in the general_quant family, and the dominant terms in that representation are exactly those that remain stable across the top retrieved excerpts and the empirical feature panel.\n\nFused research memory:\n- [bloomberg_memory] SPY US Equity empirical research memory (SPY US Equity) | score=0.745\n  This note summarizes the local Bloomberg-derived empirical state for SPY US Equity. # Bloomberg Research Memory: SPY US Equity It is intended to support theorem generation, empirical falsification, calibration design, and hypothesis ranking inside QuantAI. Compare OU-style speeds across windows for stability or regime breaks. - Volatility regime classification: **compressed_volatility** - Volatility regime: compressed_volatility Test whether roughness estimates co-move with realized-volatility r\n- [bloomberg_memory] VIX Index empirical research memory (VIX Index) | score=0.731\n  This note summarizes the local Bloomberg-derived empirical state for VIX Index. It is intended to support theorem generation, empirical falsification, calibration design, and hypothesis ranking inside QuantAI. Compare OU-style speeds across windows for stability or regime breaks. - Volatility regime classification: **compressed_volatility** # Bloomberg Research Memory: VIX Index - Volatility regime: compressed_volatility Test whether roughness estimates co-move with realized-volatility regimes. \n- [bloomberg_memory] Global Bloomberg learning snapshot (GLOBAL) | score=0.579\n  QuantAI currently has a working Bloomberg historical warehouse and a working empirical feature layer. BQL is environment-dependent and currently unavailable unless the local environment includes Bloomberg's BQL object model. - Securities represented: AAPL US Equity, SPY US Equity Options-surface extraction is partially wired but still requires stronger contract selection and normalization when the requested put/call subset is not represented in the sampled chain. Route market-state questions to \n- [registry] Evidence-anchored structural conjecture | score=0.540\n  Statement: Conjecture: the objects propose, pair-linkage, theorem admit a common structural representation in the general_quant family, and the dominant terms in that representation are exactly those that remain stable across the top retrieved excerpts and the empirical feature panel. Failure conditions: Retrieved evidence remains too dispersed across unrelated mathematical families.; No exact excerpt currently pins down every constant or normalization.; Add explicit symbolic tasks with lhs/rhs \n- [book] NONLINEAR OPTION PRICING, GUYON .pdf | page 356 | chunk 1 | score=0.491\n  For instance, the resulting correlation may have a weird skew (dependence on the asset values), or its skew may be far from the one historically observed, or it may generate prices of other options that are far from market quotes. This family is parameterized by two functions a and b that depend on time and on the values of all the underlying assets, and may depend as well on any set of path-dependent variables. Instead of assuming that the basket variance or the correlation (or equivalently \u03bb) \n- [book] Rough Volatility.pdf | page 69 | chunk 1 | score=0.490\n  (2.18) VIX variance swaps may also be estimated directly from market prices of options on VIX using the log-strip in the usual way as VVIX2t,T(T \u2212t) = \u22122Eh log p \u03b6(T) \u2212log p \u03b6(t) Ft i . (2.19) By comparing the model VVIX term structure (2.18) with the market VVIX term structure (2.19), we can in principle fix the model parameters H and \u03b7 The rBergomi model and VIX options 47 where 1 D2H Z h i2 f H(\u03b8) = (1 + \u03b8 \u2212x)H+ 21 \u2212(1 \u2212x)H+ 12 dx. The VIX variance swaps (VVIX2) are then given by H \u2206 VVIX2t,T\n\nAssumptions:\n- Empirical scope anchored to SPY US Equity.\n\nNext actions:\n- Add explicit symbolic tasks with lhs/rhs identities or qualitative constraints.\n- Refine the candidate so the implied empirical signature is sharper and testable.\n- Collect stronger exact excerpts from the book-memory layer.\n- Add a formal symbolic derivation or export the candidate to Lean for proof work.\n\nTheorem registry:\n- action: existing\n- entry_id: thm_30652b337b1c470a\n- status: speculative_candidate",
  "sources": [
    {
      "score": 1.1175827736723913,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 179,
      "chunk_no": 1,
      "text": "8.2. At-the-money short-time skew 161 Theorem 8.6. If Assumption 8.5 holds and limT\u21930 sups,r,u\u2208[0,T] E (vsvr \u2212v2u)2 = 0, and there exists v\u20320 \u2208F0 such that 1 Z T Z T lim E0[Dsvr]drds =: v\u20320, T\u21930 T \u03b4+2 0 s then \u2202k\u03c3imp(k, T) \u03f1v\u20320 = lim . (8.12) v0 T\u21930 T \u03b4 k=X0 Remark 8.2.1. The lim sup assumption in the theorem may not always be straightforward to check. However, it is implied by the condition that the spot volatility (vt)t\u22650 converges to v0 = \u03c30 > 0 uniformly in time and in L4. It is clear that it holds for both the rough Stein\u2013Stein and the rough Bergomi models. Example 8.7. In the rough Stein\u2013Stein model (8.6) equipped with the Riemann\u2013Liouville ker- \u221a 2 for s < r, and therefore the first bound in Assumption 8.5nel (8.4), dsvr = 2H\u03c3\u20320(r \u2212s)H\u22121 holds with \u03b4 = H \u221212 and C = 2H(\u03c3\u20320)2, and the second one holds trivially as the second deriv- ative is null. It is straightforward to compute the limit in Theorem 8.6 (it is, in fact, independent of T) as \u221a 1 Z T Z T 2H\u03c3\u20320 E0[Dsvr]drds = v\u20320 := 3 T H+ 23 0 s (H + 12)(H + 2)",
      "dense_score": 0.6833361983299255,
      "lexical_score": 0.2465753424657534
    },
    {
      "score": 1.1173295699080377,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 224,
      "chunk_no": 1,
      "text": "206 Chapter 10. Regularity structure for rough volatility Theorem 10.4 will be proved as Corollary 10.28. Remark 10.0.4. We showed in [40, Corollary 11]\u2014but see related results by Al\u00f2s, Le\u00f3n, and Vives [11] and Fukasawa [151, 153]\u2014that in the previously considered simple rough volatility models, now writing \u03c3(.) instead of f(.), the implied volatility skew behaves, in the short-time 1 2 3limit, as \u223c\u03f1 \u03c3\u2032(0)\u03c3(0) \u27e8K1, 1\u27e9tH\u22121 1 )(H+ 2 , where \u27e8K1, 1\u27e9in our setting computes to cH := (H+(2H)2 2 ). (The blow-up tH\u221212 as t \u21920 is a desired feature, in agreement with steep skews seen in the market.) from which one obtains a skewTo first order, Zt \u2248z + u(z) R 0t K(s, t)dWs = z + u(z) bW =: \u03c3( bW), formula in the nonsimple rough volatility case of the form f \u2032(z) 2 . \u03f1u(z) cHtH\u22121 f(z) Following the approach of [40], Theorem 10.4 allows for not only rigorous justification of these formula, but also for the computation of higher-order smile features, though this is not pursued in this chapter",
      "dense_score": 0.6770555973052979,
      "lexical_score": 0.273972602739726
    },
    {
      "score": 1.1021274995150632,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 230,
      "chunk_no": 1,
      "text": "212 Chapter 10. Regularity structure for rough volatility From W we now construct the fBm bW in the Riemann\u2013Liouville sense with Hurst index 1 H \u2208(0, 2] as \u221a Z t := \u02d9W \u22c6K(t) = 2H |t \u2212r|H\u221212 dWr, bWt 0 \u221a 2 denotes the Volterra kernel. We also write K(s, t) := K(t \u2212s).where K(t) = 2H 1t>0 tH\u22121 To give meaning to the product terms \u039eI(\u039e)k we follow the ideas from rough paths and define an \u201citerated integral\u201d for s, t \u2208R, s \u2264t, as Z t Wm s,t := ( bWr \u2212bWs)m dWr. (10.28) s Wm(s, t) satisfies the following modification of Chen\u2019s relation. Lemma 10.6. Wm as defined in (10.28) satisfies m m Wm s,t = Wms,u + X u,t (10.29) ( bWu \u2212bWs)lWm\u2212l l l=0 for s, u, t \u2208R, s \u2264u \u2264t. Proof. This is a direct consequence of the binomial theorem. We extend the domain of Wm to all of R2 by imposing Chen\u2019s relation for all s, u, t \u2208R, i.e., for t, s \u2208R, t \u2264s, we set m m Wm s,t := \u2212 X t,s . (10.30) (bWt \u2212bWs)lWm\u2212l l l=0 We are now in position to define a model (\u03a0, \u0393) that gives rigorous meaning to the interpre- tation we gave above for \u039e, I(\u039e), \u039eI(\u039e), . . .",
      "dense_score": 0.6708946228027344,
      "lexical_score": 0.2328767123287671
    },
    {
      "score": 1.0718781201480188,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 96,
      "chunk_no": 1,
      "text": "74 Chapter 3. No-arbitrage implies power-law market impact and rough volatility Finally, Z +\u221e Z t PTt = 1 + \u03c8T(v)dv dNa,Tv \u2212\u03bba,Tv dv \u2212dNb,Tv + \u03bbb,Tv dv 0 0 Z +\u221e = 1 + \u03c8T(v)dv (Ma,Tt \u2212Mb,Tt ). 0 Lemma 3.8 leads to T 1 \u2212aT Z +\u221e Pt = 1 + \u03c8T(v)dv (Ma,TtT \u2212Mb,TtT ). T\u00b5T 0 Step 3 We temporarily drop the superscripts a and b. Indeed, the results are valid for both buy and sell order flows. Consider the sequences 1 \u2212aT 1 \u2212aT Z tT r T\u00b5T XTt = NTtT, \u039bTt = \u03bbTs ds, ZTt = XTt \u2212\u039bTt (3.13) T\u00b5T T\u00b5T 0 1 \u2212aT defined for t \u2208[0, 1]. The following result is borrowed from [215]. Proposition 3.9. The sequence (\u039bT, XT, ZT) is tight. Furthermore, for any limit point (\u039b, X, Z) of (\u039bT, XT, ZT), Z is a continuous martingale, [Z, Z] = X, and \u039b = X. In addition, we have the following proposition which extends Theorem 3.1 in [215]. Proposition 3.10",
      "dense_score": 0.6827000379562378,
      "lexical_score": 0.1780821917808219
    },
    {
      "score": 1.0382081679122088,
      "file_name": "Continuous-Time Asset Pricing Theory, A Martingale-Based, Jarrow.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Continuous-Time Asset Pricing Theory, A Martingale-Based, Jarrow.pdf",
      "page_no": 24,
      "chunk_no": 1,
      "text": "Part I Arbitrage Pricing Theory Overview The key results of \ufb01nance that are successfully used in practice are based on the three fundamental theorems of asset pricing. Part 1 presents these three theorems. The applications of these three theorems are also discussed, including equivalent local martingale measures (state price densities), systematic risk, multiple-factor beta models, derivatives pricing, derivatives hedging, and asset price bubbles. All of these implications are based on the existence of an equivalent local martingale measure. The three fundamental theorems of asset pricing relate to the existence of an equivalent local martingale measure, its uniqueness, and its extensions. Roughly speaking, the \ufb01rst fundamental theorem of asset pricing equates no arbitrage with the existence of an equivalent local martingale measure. The second fundamental theorem relates market completeness to the uniqueness of the equivalent local martingale measure",
      "dense_score": 0.6699889898300171,
      "lexical_score": 0.2191780821917808
    },
    {
      "score": 0.9757187985720699,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 139,
      "chunk_no": 2,
      "text": ". A natural choice of the two would be the underlying asset and the weighted variance swap (with a fixed maturity). As a hedging instrument, the replication portfolio for the weighted variance swap is more convenient than the weighted variance swap itself because it is a local martingale. Let Z t Z S 0 dK Z \u221e dK UTt := (h\u2032(S 0) \u2212h\u2032(S u))dS u + 2 Pt(K, T) + 2 Ct(K, T) 0 0 f(K)2 S 0 f(K)2 be the time t value of the replication portfolio with maturity T initiated at time 0. We have then Z T UTt = EQ Vuudu Ft 0 Z T Z u = EQ Vu0 + Vus g(u \u2212s)dWs du Ft 0 0 Z T Z t Z T = Vu0du + dWs Vus g(u \u2212s)du. 0 0 s Therefore, dUTt = DgUTt dWt, (6.6) where Z T Z T \u2202Uut DgUTt = Vut g(u \u2212t)du = g(u \u2212t)du. t t \u2202u Proposition 6.3. For any F \u2208L2(F\u03c4, Q), \u03c4 \u2208(t, T), there exists an adapted process (HS , HU) such that Z \u03c4 Z \u03c4 F = EQ[F|Ft] + HSv dS v + HUv dUTv . t t Proof. By the martingale representation theorem, there exists (H1, H2) such that Z \u03c4 Z \u03c4 F = EQ[F|Ft] + H1vdWv + H2vdWv. t t",
      "dense_score": 0.6744859218597412,
      "lexical_score": 0.2328767123287671
    },
    {
      "score": 0.9748655049441611,
      "file_name": "Continuous-Time Asset Pricing Theory, A Martingale-Based, Jarrow.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Continuous-Time Asset Pricing Theory, A Martingale-Based, Jarrow.pdf",
      "page_no": 55,
      "chunk_no": 1,
      "text": "32 2 The Fundamental Theorems from the set of trading strategies before due to the modi\ufb01ed integrability conditions needed to guarantee that the relevant integrals exist. This section presents the new notation and the evolutions for the mma and the risky assets under this change of numeraire. Let Bt = BtBt = 1 for all t \u22650, this represents the normalized value of the money market account (mma). Let St = (S1(t), . . . , Sn(t))\u2032 \u2265 0 represent the risky asset prices when normalized by the value of the mma, i.e. Si(t) = Si(t)Bt . Then, dBt = 0 and (2.5) Bt dSt dSt = \u2212rtdt. (2.6) St St Proof Using the integration by parts formula Theorem 3 in Chap. 1, one obtains (dropping the t\u2019s) d BS = BdS1 + Sd B1 = dSS BS \u2212SB dBB . The \ufb01rst equality uses d S, B1 = 0, since B is continuous and of \ufb01nite variation (use Lemmas 2 and 7 in Chap. 1). Substitution yields dS = dSS S \u2212S dBB . Algebra completes the proof. Recall that L (S) is the set of predictable processes integrable with respect to S and O is the set of optional processes",
      "dense_score": 0.6856874227523804,
      "lexical_score": 0.1780821917808219
    },
    {
      "score": 0.9582623262274754,
      "file_name": "Continuous-Time Asset Pricing Theory, A Martingale-Based, Jarrow.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Continuous-Time Asset Pricing Theory, A Martingale-Based, Jarrow.pdf",
      "page_no": 92,
      "chunk_no": 1,
      "text": "2.8 Finite Dimension Brownian Motion Market 69 Theorem 20 gives suf\ufb01cient conditions for the market to satisfy NFLVR. Condi- tion (1) is that the volatility matrix must be of full rank for all t. This omits risky assets that randomly change from risky to locally riskless (\ufb01nite variation) across time. Condition (2) removes redundant assets from the market (see Theorem 10). Finally, condition (3) is a necessary integrability condition for \u03b8t. For subsequent use we note that conditions (1) and (2) are true if and only if rank (\u03c3t) = n for all t a.s. P. Given Theorem 20, we can now characterize the set of local martingale measures Ml. Theorem 21 (Characterization of Ml) Assume that (1) rank (\u03c3t) = n for all t a.s. P and T \u2032 \u2032 \u22121 2(2) 0 ...\u03c3t \u03c3t\u03c3t (bt \u2212rt1) ... dy < \u221e. Then, = e\u2212 0T (\u03b8t+\u03bdt)\u00b7dWt\u221212 0T \u2225\u03b8t+\u03bdt\u22252dt > 0, Ml = {Q\u03bd : dQ\u03bddP dQ\u03bd E dP = 1, \u03bd \u2208K(\u03c3)} \u0338= \u2205 where \u2032 \u2032 \u22121 \u03b8t = \u03c3t \u03c3t\u03c3t (bt \u2212rt1) . Proof By Theorems 19 and 20, the market satis\ufb01es NFLVR and by the First Fundamental Theorem 13 of asset pricing Ml \u0338= \u2205",
      "dense_score": 0.6840157508850098,
      "lexical_score": 0.2465753424657534
    },
    {
      "score": 0.955918044129463,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 143,
      "chunk_no": 1,
      "text": "6.3. Hedging VIX options: Empirical analysis 123 and follows the dynamics dFTt = \u03b3 p FTt dWt. We are hedging a VIX option with payoff (VIXT \u2212K)+, with a forward variance swap. The price of the VIX option is given by Z \u221e EQ[(VIXT \u2212K)+|Ft] = ( \u221az \u2212K)pT\u2212t FTt , z dz, K2 where pT(x, \u00b7) is the density of the CIR process at time T with starting value x. The parameter \u03b3 may be estimated by observing that \u27e8VIX\u27e9t = \u03b324 t. 6.3.3 Rough fractional stochastic volatility Assume now that the VIX index is given by VIXt = CeXt, where C > 0 is a constant and X is a centered Gaussian process under the risk-neutral probability. For all s \u22650, let F s0 := \u03c3(Xr, r \u2264s), and Fs := \u2229s<tF t0 . The interest rate is taken to be zero. Fix a time horizon T, and let Zt(T) := EQ[XT|Ft], so that (Zt(T))t\u22650 is a Gaussian martingale and thus a process with independent increments, completely characterized by the function cT(t) := EQh Zt(T)2i = EQh EQ[XT|Ft]2i . If we assume in addition that cT(\u00b7) is continuous, then (Zt(T))t\u22650 is almost surely continuous",
      "dense_score": 0.6786577701568604,
      "lexical_score": 0.2602739726027397
    },
    {
      "score": 0.9513597193156202,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 234,
      "chunk_no": 1,
      "text": "216 Chapter 10. Regularity structure for rough volatility Lemma 10.11. The pair (\u03a0\u03b5, \u0393\u03b5) as defined above is a model on (T , A). Proof. The identity \u03a0t = \u0393ts\u03a0s is straightforward to check. The bounds (10.32) and (10.33) on \u0393st and on \u03a0sI(\u039e)m follow from the regularity of bW\u03b5 as proved in Lemma 10.10. The blow-up of \u03a0s\u039eI(\u039e)m(\u03c6\u03bbs), however, is even better than we need, since by the choice of \u03b4\u03b5 we have | \u02d9W\u03b5| \u2264C\u03b5 on compact sets, for some random constant C\u03b5. The definition of this model is justified by the fact that application of the reconstruction operator (as in Lemma 10.20) yields integrals of the form Z t r ) dW\u03b5r . (10.36) f(r, bW\u03b5 0 As we pointed out in the introduction, there is no hope that integrals of this type will converge as \u03b5 \u21930 if H < 2.1 This can be cured by working with a renormalized model ( \u02c6\u03a0\u03b5, \u0393\u03b5) instead",
      "dense_score": 0.6740994453430176,
      "lexical_score": 0.2602739726027397
    }
  ],
  "used_context": [
    {
      "score": 1.1175827736723913,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 179,
      "chunk_no": 1,
      "text": "8.2. At-the-money short-time skew 161 Theorem 8.6. If Assumption 8.5 holds and limT\u21930 sups,r,u\u2208[0,T] E (vsvr \u2212v2u)2 = 0, and there exists v\u20320 \u2208F0 such that 1 Z T Z T lim E0[Dsvr]drds =: v\u20320, T\u21930 T \u03b4+2 0 s then \u2202k\u03c3imp(k, T) \u03f1v\u20320 = lim . (8.12) v0 T\u21930 T \u03b4 k=X0 Remark 8.2.1. The lim sup assumption in the theorem may not always be straightforward to check. However, it is implied by the condition that the spot volatility (vt)t\u22
```

## Symbolic execution
```json
{
  "title": "Evidence-anchored structural conjecture",
  "family": "spot_vol_linkage",
  "assumptions_used": [
    "Empirical scope anchored to SPY US Equity.",
    "sigma_s > 0",
    "sigma_v > 0",
    "-1 <= rho <= 1",
    "Regime labels correspond to empirically observed states",
    "Observed feature differences are mapped consistently to theorem notation"
  ],
  "n_tasks": 5,
  "n_ok": 5,
  "n_fail": 0,
  "results": [
    {
      "task": {
        "name": "covariance_symmetry",
        "kind": "verify_identity",
        "payload": {
          "lhs": "rho*sigma_s*sigma_v",
          "rhs": "sigma_v*sigma_s*rho"
        },
        "rationale": "Basic symmetry check for spot-vol covariance style terms."
      },
      "ok": true,
      "assumptions_used": [
        "Empirical scope anchored to SPY US Equity.",
        "sigma_s > 0",
        "sigma_v > 0",
        "-1 <= rho <= 1",
        "Regime labels correspond to empirically observed states",
        "Observed feature differences are mapped consistently to theorem notation"
      ],
      "result": {
        "name": "identity",
        "kind": "identity",
        "passed": true,
        "result": "proved_exactly",
        "details": {
          "lhs": "rho*sigma_s*sigma_v",
          "rhs": "rho*sigma_s*sigma_v",
          "difference": "0",
          "assumptions": [
            "Empirical scope anchored to SPY US Equity.",
            "sigma_s > 0",
            "sigma_v > 0",
            "-1 <= rho <= 1",
            "Regime labels correspond to empirically observed states",
            "Observed feature differences are mapped consistently to theorem notation"
          ]
        }
      }
    },
    {
      "task": {
        "name": "quadratic_form_nonnegative",
        "kind": "verify_nonnegative",
        "payload": {
          "expression": "(sigma_s - rho*sigma_v)**2"
        },
        "rationale": "Any squared coupling residual should remain nonnegative."
      },
      "ok": true,
      "assumptions_used": [
        "Empirical scope anchored to SPY US Equity.",
        "sigma_s > 0",
        "sigma_v > 0",
        "-1 <= rho <= 1",
        "Regime labels correspond to empirically observed states",
        "Observed feature differences are mapped consistently to theorem notation"
      ],
      "result": {
        "name": "nonnegative",
        "kind": "nonnegative",
        "passed": true,
        "result": "proved",
        "details": {
          "expression": "(-rho*sigma_v + sigma_s)**2",
          "simplified": "(rho*sigma_v - sigma_s)**2",
          "is_nonnegative": true,
          "assumptions": [
            "Empirical scope anchored to SPY US Equity.",
            "sigma_s > 0",
            "sigma_v > 0",
            "-1 <= rho <= 1",
            "Regime labels correspond to empirically observed states",
            "Observed feature differences are mapped consistently to theorem notation"
          ]
        }
      }
    },
    {
      "task": {
        "name": "variance_of_linear_combination",
        "kind": "verify_nonnegative",
        "payload": {
          "expression": "sigma_s**2 + sigma_v**2 - 2*rho*sigma_s*sigma_v"
        },
        "rationale": "A variance-style quadratic form should remain nonnegative under admissible coupling assumptions."
      },
      "ok": true,
      "assumptions_used": [
        "Empirical scope anchored to SPY US Equity.",
        "sigma_s > 0",
        "sigma_v > 0",
        "-1 <= rho <= 1",
        "Regime labels correspond to empirically observed states",
        "Observed feature differences are mapped consistently to theorem notation"
      ],
      "result": {
        "name": "nonnegative",
        "kind": "nonnegative",
        "passed": true,
        "result": "proved_by_assumptions",
        "details": {
          "expression": "-2*rho*sigma_s*sigma_v + sigma_s**2 + sigma_v**2",
          "simplified": "-2*rho*sigma_s*sigma_v + sigma_s**2 + sigma_v**2",
          "is_nonnegative": null,
          "assumptions": [
            "Empirical scope anchored to SPY US Equity.",
            "sigma_s > 0",
            "sigma_v > 0",
            "-1 <= rho <= 1",
            "Regime labels correspond to empirically observed states",
            "Observed feature differences are mapped consistently to theorem notation"
          ]
        }
      }
    },
    {
      "task": {
        "name": "regime_gap_identity",
        "kind": "verify_identity",
        "payload": {
          "lhs": "(rv_hi - rv_lo) + (iv_hi - iv_lo)",
          "rhs": "(rv_hi + iv_hi) - (rv_lo + iv_lo)"
        },
        "rationale": "Checks algebraic coherence of regime-difference decomposition used in pair-linkage narratives."
      },
      "ok": true,
      "assumptions_used": [
        "Empirical scope anchored to SPY US Equity.",
        "sigma_s > 0",
        "sigma_v > 0",
        "-1 <= rho <= 1",
        "Regime labels correspond to empirically observed states",
        "Observed feature differences are mapped consistently to theorem notation"
      ],
      "result": {
        "name": "identity",
        "kind": "identity",
        "passed": true,
        "result": "proved_exactly",
        "details": {
          "lhs": "iv_hi - iv_lo + rv_hi - rv_lo",
          "rhs": "iv_hi - iv_lo + rv_hi - rv_lo",
          "difference": "0",
          "assumptions": [
            "Empirical scope anchored to SPY US Equity.",
            "sigma_s > 0",
            "sigma_v > 0",
            "-1 <= rho <= 1",
            "Regime labels correspond to empirically observed states",
            "Observed feature differences are mapped consistently to theorem notation"
          ]
        }
      }
    },
    {
      "task": {
        "name": "zero_spread_baseline",
        "kind": "verify_derivative_zero",
        "payload": {
          "expression": "x**2",
          "variable": "x",
          "point": 0
        },
        "rationale": "Provides a simple baseline zero-point regularity check for local spread/coupling expansions."
      },
      "ok": true,
      "assumptions_used": [
        "Empirical scope anchored to SPY US Equity.",
        "sigma_s > 0",
        "sigma_v > 0",
        "-1 <= rho <= 1",
        "Regime labels correspond to empirically observed states",
        "Observed feature differences are mapped consistently to theorem notation"
      ],
      "result": {
        "name": "derivative_zero",
        "kind": "derivative_zero",
        "passed": true,
        "result": "proved",
        "details": {
          "expression": "x**2",
          "derivative": "2*x",
          "point": "0",
          "value": "0",
          "assumptions": [
            "Empirical scope anchored to SPY US Equity.",
            "sigma_s > 0",
            "sigma_v > 0",
            "-1 <= rho <= 1",
            "Regime labels correspond to empirically observed states",
            "Observed feature differences are mapped consistently to theorem notation"
          ]
        }
      }
    }
  ]
}
```