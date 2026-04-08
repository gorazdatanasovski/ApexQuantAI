# Pair-Linkage Theorem Run: SPY US Equity / VVIX Index

- Created at: 2026-03-28T01:42:51+00:00
- Family matched: True

## Attempts
### Attempt 1
- Selected title: Evidence-anchored structural conjecture
- Prompt: Propose a pair-linkage theorem for SPY US Equity and VVIX Index. The theorem must be genuinely about the interaction between the two objects, not a reused single-name rough-variance theorem. Focus on spot-volatility coupling, variance scaling transmission, regime dependence, term-structure state, tail-risk state, cross-object linkage. State: (1) the pair-level object, (2) the predicted relationship or monotonicity, (3) empirical Bloomberg feature signatures, (4) failure conditions, and (5) symbolic structure that can be checked directly.

## Accepted result
```json
{
  "mode_used": "theorem",
  "response": "Research artifact: Evidence-anchored structural conjecture\nStatus: speculative_candidate\nScore: 0.452\n\nStatement:\nConjecture: the objects propose, pair-linkage, theorem admit a common structural representation in the general_quant family, and the dominant terms in that representation are exactly those that remain stable across the top retrieved excerpts and the empirical feature panel.\n\nFused research memory:\n- [bloomberg_memory] SPY US Equity empirical research memory (SPY US Equity) | score=0.745\n  This note summarizes the local Bloomberg-derived empirical state for SPY US Equity. # Bloomberg Research Memory: SPY US Equity It is intended to support theorem generation, empirical falsification, calibration design, and hypothesis ranking inside QuantAI. Compare OU-style speeds across windows for stability or regime breaks. - Volatility regime classification: **compressed_volatility** - Volatility regime: compressed_volatility Test whether roughness estimates co-move with realized-volatility r\n- [bloomberg_memory] VVIX Index empirical research memory (VVIX Index) | score=0.731\n  This note summarizes the local Bloomberg-derived empirical state for VVIX Index. It is intended to support theorem generation, empirical falsification, calibration design, and hypothesis ranking inside QuantAI. Compare OU-style speeds across windows for stability or regime breaks. - Volatility regime classification: **compressed_volatility** # Bloomberg Research Memory: VVIX Index - Volatility regime: compressed_volatility Test whether roughness estimates co-move with realized-volatility regimes\n- [bloomberg_memory] Global Bloomberg learning snapshot (GLOBAL) | score=0.579\n  QuantAI currently has a working Bloomberg historical warehouse and a working empirical feature layer. BQL is environment-dependent and currently unavailable unless the local environment includes Bloomberg's BQL object model. - Securities represented: AAPL US Equity, SPY US Equity Options-surface extraction is partially wired but still requires stronger contract selection and normalization when the requested put/call subset is not represented in the sampled chain. Route market-state questions to \n- [registry] Evidence-anchored structural conjecture | score=0.540\n  Statement: Conjecture: the objects propose, pair-linkage, theorem admit a common structural representation in the general_quant family, and the dominant terms in that representation are exactly those that remain stable across the top retrieved excerpts and the empirical feature panel. Failure conditions: Retrieved evidence remains too dispersed across unrelated mathematical families.; No exact excerpt currently pins down every constant or normalization.; Add explicit symbolic tasks with lhs/rhs \n- [book] Rough Volatility.pdf | page 69 | chunk 1 | score=0.494\n  (2.19) By comparing the model VVIX term structure (2.18) with the market VVIX term structure (2.19), we can in principle fix the model parameters H and \u03b7 (2.18) VIX variance swaps may also be estimated directly from market prices of options on VIX using the log-strip in the usual way as VVIX2t,T(T \u2212t) = \u22122Eh log p \u03b6(T) \u2212log p \u03b6(t) Ft i . The rBergomi model and VIX options 47 where 1 D2H Z h i2 f H(\u03b8) = (1 + \u03b8 \u2212x)H+ 21 \u2212(1 \u2212x)H+ 12 dx. (2.17) \u03b82 0 It is straightforward to show that f H(\u03b8) \u21921 as \u03b8\n- [book] Rough Volatility.pdf | page 77 | chunk 2 | score=0.493\n  However, we do not see agreement between the rBergomi model and the term structure of VIX volatility (VVIX). 2.10 Appendix 2.10.1 Volatility, variance, and VIX Here we briefly recall some different notions of variance and volatility that are used throughout the chapter We computed terms of Bergomi\u2013Guyon expansion up to second order in volatility of volatility, but the expan- sion parameter \u03bb = \u03b7 \u03c4H \u22482 required to fit SPX option prices is too big for this asymptotic expansion to be valid.\n\nAssumptions:\n- Empirical scope anchored to SPY US Equity.\n\nNext actions:\n- Add explicit symbolic tasks with lhs/rhs identities or qualitative constraints.\n- Refine the candidate so the implied empirical signature is sharper and testable.\n- Collect stronger exact excerpts from the book-memory layer.\n- Add a formal symbolic derivation or export the candidate to Lean for proof work.\n\nTheorem registry:\n- action: existing\n- entry_id: thm_f7911393c8574ced\n- status: speculative_candidate",
  "sources": [
    {
      "score": 1.1317457313406958,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 179,
      "chunk_no": 1,
      "text": "8.2. At-the-money short-time skew 161 Theorem 8.6. If Assumption 8.5 holds and limT\u21930 sups,r,u\u2208[0,T] E (vsvr \u2212v2u)2 = 0, and there exists v\u20320 \u2208F0 such that 1 Z T Z T lim E0[Dsvr]drds =: v\u20320, T\u21930 T \u03b4+2 0 s then \u2202k\u03c3imp(k, T) \u03f1v\u20320 = lim . (8.12) v0 T\u21930 T \u03b4 k=X0 Remark 8.2.1. The lim sup assumption in the theorem may not always be straightforward to check. However, it is implied by the condition that the spot volatility (vt)t\u22650 converges to v0 = \u03c30 > 0 uniformly in time and in L4. It is clear that it holds for both the rough Stein\u2013Stein and the rough Bergomi models. Example 8.7. In the rough Stein\u2013Stein model (8.6) equipped with the Riemann\u2013Liouville ker- \u221a 2 for s < r, and therefore the first bound in Assumption 8.5nel (8.4), dsvr = 2H\u03c3\u20320(r \u2212s)H\u22121 holds with \u03b4 = H \u221212 and C = 2H(\u03c3\u20320)2, and the second one holds trivially as the second deriv- ative is null. It is straightforward to compute the limit in Theorem 8.6 (it is, in fact, independent of T) as \u221a 1 Z T Z T 2H\u03c3\u20320 E0[Dsvr]drds = v\u20320 := 3 T H+ 23 0 s (H + 12)(H + 2)",
      "dense_score": 0.69749915599823,
      "lexical_score": 0.2465753424657534
    },
    {
      "score": 1.128652545066729,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 224,
      "chunk_no": 1,
      "text": "206 Chapter 10. Regularity structure for rough volatility Theorem 10.4 will be proved as Corollary 10.28. Remark 10.0.4. We showed in [40, Corollary 11]\u2014but see related results by Al\u00f2s, Le\u00f3n, and Vives [11] and Fukasawa [151, 153]\u2014that in the previously considered simple rough volatility models, now writing \u03c3(.) instead of f(.), the implied volatility skew behaves, in the short-time 1 2 3limit, as \u223c\u03f1 \u03c3\u2032(0)\u03c3(0) \u27e8K1, 1\u27e9tH\u22121 1 )(H+ 2 , where \u27e8K1, 1\u27e9in our setting computes to cH := (H+(2H)2 2 ). (The blow-up tH\u221212 as t \u21920 is a desired feature, in agreement with steep skews seen in the market.) from which one obtains a skewTo first order, Zt \u2248z + u(z) R 0t K(s, t)dWs = z + u(z) bW =: \u03c3( bW), formula in the nonsimple rough volatility case of the form f \u2032(z) 2 . \u03f1u(z) cHtH\u22121 f(z) Following the approach of [40], Theorem 10.4 allows for not only rigorous justification of these formula, but also for the computation of higher-order smile features, though this is not pursued in this chapter",
      "dense_score": 0.6883785724639893,
      "lexical_score": 0.273972602739726
    },
    {
      "score": 1.1074101995768613,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 230,
      "chunk_no": 1,
      "text": "212 Chapter 10. Regularity structure for rough volatility From W we now construct the fBm bW in the Riemann\u2013Liouville sense with Hurst index 1 H \u2208(0, 2] as \u221a Z t := \u02d9W \u22c6K(t) = 2H |t \u2212r|H\u221212 dWr, bWt 0 \u221a 2 denotes the Volterra kernel. We also write K(s, t) := K(t \u2212s).where K(t) = 2H 1t>0 tH\u22121 To give meaning to the product terms \u039eI(\u039e)k we follow the ideas from rough paths and define an \u201citerated integral\u201d for s, t \u2208R, s \u2264t, as Z t Wm s,t := ( bWr \u2212bWs)m dWr. (10.28) s Wm(s, t) satisfies the following modification of Chen\u2019s relation. Lemma 10.6. Wm as defined in (10.28) satisfies m m Wm s,t = Wms,u + X u,t (10.29) ( bWu \u2212bWs)lWm\u2212l l l=0 for s, u, t \u2208R, s \u2264u \u2264t. Proof. This is a direct consequence of the binomial theorem. We extend the domain of Wm to all of R2 by imposing Chen\u2019s relation for all s, u, t \u2208R, i.e., for t, s \u2208R, t \u2264s, we set m m Wm s,t := \u2212 X t,s . (10.30) (bWt \u2212bWs)lWm\u2212l l l=0 We are now in position to define a model (\u03a0, \u0393) that gives rigorous meaning to the interpre- tation we gave above for \u039e, I(\u039e), \u039eI(\u039e), . . .",
      "dense_score": 0.6761773228645325,
      "lexical_score": 0.2328767123287671
    },
    {
      "score": 1.0744253842471398,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 96,
      "chunk_no": 1,
      "text": "74 Chapter 3. No-arbitrage implies power-law market impact and rough volatility Finally, Z +\u221e Z t PTt = 1 + \u03c8T(v)dv dNa,Tv \u2212\u03bba,Tv dv \u2212dNb,Tv + \u03bbb,Tv dv 0 0 Z +\u221e = 1 + \u03c8T(v)dv (Ma,Tt \u2212Mb,Tt ). 0 Lemma 3.8 leads to T 1 \u2212aT Z +\u221e Pt = 1 + \u03c8T(v)dv (Ma,TtT \u2212Mb,TtT ). T\u00b5T 0 Step 3 We temporarily drop the superscripts a and b. Indeed, the results are valid for both buy and sell order flows. Consider the sequences 1 \u2212aT 1 \u2212aT Z tT r T\u00b5T XTt = NTtT, \u039bTt = \u03bbTs ds, ZTt = XTt \u2212\u039bTt (3.13) T\u00b5T T\u00b5T 0 1 \u2212aT defined for t \u2208[0, 1]. The following result is borrowed from [215]. Proposition 3.9. The sequence (\u039bT, XT, ZT) is tight. Furthermore, for any limit point (\u039b, X, Z) of (\u039bT, XT, ZT), Z is a continuous martingale, [Z, Z] = X, and \u039b = X. In addition, we have the following proposition which extends Theorem 3.1 in [215]. Proposition 3.10",
      "dense_score": 0.6852473020553589,
      "lexical_score": 0.1780821917808219
    },
    {
      "score": 0.9840083741488521,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 139,
      "chunk_no": 2,
      "text": ". A natural choice of the two would be the underlying asset and the weighted variance swap (with a fixed maturity). As a hedging instrument, the replication portfolio for the weighted variance swap is more convenient than the weighted variance swap itself because it is a local martingale. Let Z t Z S 0 dK Z \u221e dK UTt := (h\u2032(S 0) \u2212h\u2032(S u))dS u + 2 Pt(K, T) + 2 Ct(K, T) 0 0 f(K)2 S 0 f(K)2 be the time t value of the replication portfolio with maturity T initiated at time 0. We have then Z T UTt = EQ Vuudu Ft 0 Z T Z u = EQ Vu0 + Vus g(u \u2212s)dWs du Ft 0 0 Z T Z t Z T = Vu0du + dWs Vus g(u \u2212s)du. 0 0 s Therefore, dUTt = DgUTt dWt, (6.6) where Z T Z T \u2202Uut DgUTt = Vut g(u \u2212t)du = g(u \u2212t)du. t t \u2202u Proposition 6.3. For any F \u2208L2(F\u03c4, Q), \u03c4 \u2208(t, T), there exists an adapted process (HS , HU) such that Z \u03c4 Z \u03c4 F = EQ[F|Ft] + HSv dS v + HUv dUTv . t t Proof. By the martingale representation theorem, there exists (H1, H2) such that Z \u03c4 Z \u03c4 F = EQ[F|Ft] + H1vdWv + H2vdWv. t t",
      "dense_score": 0.6827754974365234,
      "lexical_score": 0.2328767123287671
    },
    {
      "score": 0.9770551411746299,
      "file_name": "Continuous-Time Asset Pricing Theory, A Martingale-Based, Jarrow.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Continuous-Time Asset Pricing Theory, A Martingale-Based, Jarrow.pdf",
      "page_no": 55,
      "chunk_no": 1,
      "text": "32 2 The Fundamental Theorems from the set of trading strategies before due to the modi\ufb01ed integrability conditions needed to guarantee that the relevant integrals exist. This section presents the new notation and the evolutions for the mma and the risky assets under this change of numeraire. Let Bt = BtBt = 1 for all t \u22650, this represents the normalized value of the money market account (mma). Let St = (S1(t), . . . , Sn(t))\u2032 \u2265 0 represent the risky asset prices when normalized by the value of the mma, i.e. Si(t) = Si(t)Bt . Then, dBt = 0 and (2.5) Bt dSt dSt = \u2212rtdt. (2.6) St St Proof Using the integration by parts formula Theorem 3 in Chap. 1, one obtains (dropping the t\u2019s) d BS = BdS1 + Sd B1 = dSS BS \u2212SB dBB . The \ufb01rst equality uses d S, B1 = 0, since B is continuous and of \ufb01nite variation (use Lemmas 2 and 7 in Chap. 1). Substitution yields dS = dSS S \u2212S dBB . Algebra completes the proof. Recall that L (S) is the set of predictable processes integrable with respect to S and O is the set of optional processes",
      "dense_score": 0.6878770589828491,
      "lexical_score": 0.1780821917808219
    },
    {
      "score": 0.9640145320761693,
      "file_name": "Continuous-Time Asset Pricing Theory, A Martingale-Based, Jarrow.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Continuous-Time Asset Pricing Theory, A Martingale-Based, Jarrow.pdf",
      "page_no": 92,
      "chunk_no": 1,
      "text": "2.8 Finite Dimension Brownian Motion Market 69 Theorem 20 gives suf\ufb01cient conditions for the market to satisfy NFLVR. Condi- tion (1) is that the volatility matrix must be of full rank for all t. This omits risky assets that randomly change from risky to locally riskless (\ufb01nite variation) across time. Condition (2) removes redundant assets from the market (see Theorem 10). Finally, condition (3) is a necessary integrability condition for \u03b8t. For subsequent use we note that conditions (1) and (2) are true if and only if rank (\u03c3t) = n for all t a.s. P. Given Theorem 20, we can now characterize the set of local martingale measures Ml. Theorem 21 (Characterization of Ml) Assume that (1) rank (\u03c3t) = n for all t a.s. P and T \u2032 \u2032 \u22121 2(2) 0 ...\u03c3t \u03c3t\u03c3t (bt \u2212rt1) ... dy < \u221e. Then, = e\u2212 0T (\u03b8t+\u03bdt)\u00b7dWt\u221212 0T \u2225\u03b8t+\u03bdt\u22252dt > 0, Ml = {Q\u03bd : dQ\u03bddP dQ\u03bd E dP = 1, \u03bd \u2208K(\u03c3)} \u0338= \u2205 where \u2032 \u2032 \u22121 \u03b8t = \u03c3t \u03c3t\u03c3t (bt \u2212rt1) . Proof By Theorems 19 and 20, the market satis\ufb01es NFLVR and by the First Fundamental Theorem 13 of asset pricing Ml \u0338= \u2205",
      "dense_score": 0.6897679567337036,
      "lexical_score": 0.2465753424657534
    },
    {
      "score": 0.9596070319659089,
      "file_name": "Continuous-Time Asset Pricing Theory, A Martingale-Based, Jarrow.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Continuous-Time Asset Pricing Theory, A Martingale-Based, Jarrow.pdf",
      "page_no": 126,
      "chunk_no": 1,
      "text": "4.8 Diversi\ufb01cation 103 Theorem 39 (The Beta Model) Assume that all the quantities in expression (4.27) are squared integrable with respect to P. Then, cov [RH(t), RX(t) |Ft ] E [RX(t) |Ft ] \u2212r0(t) = (E [RH(t) |Ft ] \u2212r0(t)) var [RH(t) |Ft ] (4.27) where E [RH(t) |Ft ] \u2212r0(t) < 0. Proof To simplify the notation we write E[\u00b7] = E[\u00b7 |Ft ] and we drop the t arguments in RH(t), RX(t), r0(t). . Using expression (4.24) for RH we have 1 + RH = Ht+\u0394Ht . Or, E [1 + RH] = 1 + r0 \u2212cov Ht+\u0394Ht , Ht+\u0394Ht (1 + r0) This proves E [RH] \u2212r0 < 0. Next, E [RH] = r0 \u2212var Ht+\u0394Ht (1 + r0). E[RH ]\u2212r0 = \u2212(1 + r0). Using expression (4.24) for RX gives Ht+\u0394 var Ht . Or, E[RX] = r0 \u2212(1 + r0)cov RX, Ht+\u0394Ht E[RX] = r0(t) + E[RHHt+\u0394]\u2212r0 cov [RX, RH]. This completes the proof. var Ht If the state price density is traded, then because E [RH(t) |Ft ] \u2212r0(t) < 0, it can be considered as a risk factor. Furthermore, as shown in expression (4.27), the standard beta model implies that only this single risk factor\u2019s return, RH(t), is suf\ufb01cient to determine any primary securities expected return, i.e",
      "dense_score": 0.6763193607330322,
      "lexical_score": 0.2876712328767123
    },
    {
      "score": 0.9551778736506422,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 234,
      "chunk_no": 1,
      "text": "216 Chapter 10. Regularity structure for rough volatility Lemma 10.11. The pair (\u03a0\u03b5, \u0393\u03b5) as defined above is a model on (T , A). Proof. The identity \u03a0t = \u0393ts\u03a0s is straightforward to check. The bounds (10.32) and (10.33) on \u0393st and on \u03a0sI(\u039e)m follow from the regularity of bW\u03b5 as proved in Lemma 10.10. The blow-up of \u03a0s\u039eI(\u039e)m(\u03c6\u03bbs), however, is even better than we need, since by the choice of \u03b4\u03b5 we have | \u02d9W\u03b5| \u2264C\u03b5 on compact sets, for some random constant C\u03b5. The definition of this model is justified by the fact that application of the reconstruction operator (as in Lemma 10.20) yields integrals of the form Z t r ) dW\u03b5r . (10.36) f(r, bW\u03b5 0 As we pointed out in the introduction, there is no hope that integrals of this type will converge as \u03b5 \u21930 if H < 2.1 This can be cured by working with a renormalized model ( \u02c6\u03a0\u03b5, \u0393\u03b5) instead",
      "dense_score": 0.6779175996780396,
      "lexical_score": 0.2602739726027397
    },
    {
      "score": 0.951724769579221,
      "file_name": "Methods of Mathematical Finanance, Karatzas, Shreve.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Methods of Mathematical Finanance, Karatzas, Shreve.pdf",
      "page_no": 29,
      "chunk_no": 2,
      "text": ". (4.2i) 0 T T E exp \u2212 \u03b8\u2032(s) dW(s) \u22121 \u2225\u03b8(s)\u22252 ds = 1. (4.2ii) 0 2 0 Then the market M is viable. The idea behind Theorem 4.2 is the following. Suppose that for all (t, \u03c9) in some subset of [0, T]\u00d7\u2126with positive product measure, one can \ufb01nd \u03c0(t) such that \u03c0\u2032(t)\u03c3(t) = 0 but \u03c0\u2032(t)[b(t)+\u03b4(t)\u2212r(t)1\u02dc] \u0338= 0. It is clear from (3.4)that this portfolio holds a combination of stocks that entails no risk but has a nonzero mean rate of return and hence exposes an arbitrage opportunity. Thus, for a viable market, every vector in the kernel K(\u03c3\u2032(t)) of \u03c3\u2032(t) should be orthogonal to b(t) + \u03b4(t) \u2212r(t)1\u02dc. But from linear algebra we know thatthe orthogonal complement of the kernel of \u03c3\u2032(t) is the range of \u03c3(t). Except for the issue of progressive measurability, Theorem 4.2 is just the assertion that b(t) + \u03b4(t) \u2212r(t)1\u02dc is in the range of \u03c3(t). The following lemmas makethis argument rigorous by addressing the relevant measurability issues; the reader may wish to skip these on \ufb01rst reading and proceed directly to Corollary 4.8. Notation 4.3: Let L(RD; RN) denote the space of N \u00d7 D matrices",
      "dense_score": 0.6774781942367554,
      "lexical_score": 0.2465753424657534
    }
  ],
  "used_context": [
    {
      "score": 1.1317457313406958,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 179,
      "chunk_no": 1,
      "text": "8.2. At-the-money short-time skew 161 Theorem 8.6. If Assumption 8
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