# Pair-Linkage Theorem Run: SPY US Equity / VIX3M Index

- Created at: 2026-03-28T01:40:49+00:00
- Family matched: True

## Attempts
### Attempt 1
- Selected title: Evidence-anchored structural conjecture
- Prompt: Propose a pair-linkage theorem for SPY US Equity and VIX3M Index. The theorem must be genuinely about the interaction between the two objects, not a reused single-name rough-variance theorem. Focus on spot-volatility coupling, variance scaling transmission, regime dependence, term-structure state, tail-risk state, cross-object linkage. State: (1) the pair-level object, (2) the predicted relationship or monotonicity, (3) empirical Bloomberg feature signatures, (4) failure conditions, and (5) symbolic structure that can be checked directly.

## Accepted result
```json
{
  "mode_used": "theorem",
  "response": "Research artifact: Evidence-anchored structural conjecture\nStatus: speculative_candidate\nScore: 0.452\n\nStatement:\nConjecture: the objects propose, pair-linkage, theorem admit a common structural representation in the general_quant family, and the dominant terms in that representation are exactly those that remain stable across the top retrieved excerpts and the empirical feature panel.\n\nFused research memory:\n- [bloomberg_memory] SPY US Equity empirical research memory (SPY US Equity) | score=0.745\n  This note summarizes the local Bloomberg-derived empirical state for SPY US Equity. # Bloomberg Research Memory: SPY US Equity It is intended to support theorem generation, empirical falsification, calibration design, and hypothesis ranking inside QuantAI. Compare OU-style speeds across windows for stability or regime breaks. - Volatility regime classification: **compressed_volatility** - Volatility regime: compressed_volatility Test whether roughness estimates co-move with realized-volatility r\n- [bloomberg_memory] VIX3M Index empirical research memory (VIX3M Index) | score=0.731\n  This note summarizes the local Bloomberg-derived empirical state for VIX3M Index. It is intended to support theorem generation, empirical falsification, calibration design, and hypothesis ranking inside QuantAI. Compare OU-style speeds across windows for stability or regime breaks. - Volatility regime classification: **compressed_volatility** # Bloomberg Research Memory: VIX3M Index - Volatility regime: compressed_volatility Test whether roughness estimates co-move with realized-volatility regim\n- [bloomberg_memory] Global Bloomberg learning snapshot (GLOBAL) | score=0.579\n  QuantAI currently has a working Bloomberg historical warehouse and a working empirical feature layer. BQL is environment-dependent and currently unavailable unless the local environment includes Bloomberg's BQL object model. - Securities represented: AAPL US Equity, SPY US Equity Options-surface extraction is partially wired but still requires stronger contract selection and normalization when the requested put/call subset is not represented in the sampled chain. Route market-state questions to \n- [registry] Evidence-anchored structural conjecture | score=0.540\n  Statement: Conjecture: the objects propose, pair-linkage, theorem admit a common structural representation in the general_quant family, and the dominant terms in that representation are exactly those that remain stable across the top retrieved excerpts and the empirical feature panel. Failure conditions: Retrieved evidence remains too dispersed across unrelated mathematical families.; No exact excerpt currently pins down every constant or normalization.; Add explicit symbolic tasks with lhs/rhs \n- [book] NONLINEAR OPTION PRICING, GUYON .pdf | page 356 | chunk 1 | score=0.493\n  For instance, the resulting correlation may have a weird skew (dependence on the asset values), or its skew may be far from the one historically observed, or it may generate prices of other options that are far from market quotes. This family is parameterized by two functions a and b that depend on time and on the values of all the underlying assets, and may depend as well on any set of path-dependent variables. Instead of assuming that the basket variance or the correlation (or equivalently \u03bb) \n- [book] NONLINEAR OPTION PRICING, GUYON .pdf | page 356 | chunk 2 | score=0.491\n  Using the new family, one can now design one\u2019s favorite local correlation model in order to match a view on a correlation skew, and/or reproduce some features of historical data, and/or calibrate to other option prices, on top of reproducing the market smile of the basket, be it a stock index, a cross-FX rate, or an interest rate spread. Instead of assuming that the basket variance or the correlation (or equivalently \u03bb) is local in index, we assume that a + b\u03bb is. If for some time and asset valu\n\nAssumptions:\n- Empirical scope anchored to SPY US Equity.\n\nNext actions:\n- Add explicit symbolic tasks with lhs/rhs identities or qualitative constraints.\n- Refine the candidate so the implied empirical signature is sharper and testable.\n- Collect stronger exact excerpts from the book-memory layer.\n- Add a formal symbolic derivation or export the candidate to Lean for proof work.\n\nTheorem registry:\n- action: existing\n- entry_id: thm_b799d5af3b024d41\n- status: speculative_candidate",
  "sources": [
    {
      "score": 1.1379306077303952,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 221,
      "chunk_no": 1,
      "text": "10.0.3. Description of main results 203 Theorem 10.2. With C \u03b5 = C \u03b5(t) as in Theorem 10.1, define the renormalized integral approxi- mation Z T Z T I\u02dc \u03b5 := I\u02dcf\u03b5 (T) := f( t )dW\u03b5t \u2212 bW\u03b5 C \u03b5(t) f \u2032( bW\u03b5t )dt, (10.14) 0 0 and also the approximate total variance \u03b5 \u03b5 Z T t )dt. V := V f (T) := f 2( bW\u03b5 0 Then the price of a European call option, under the pricing model (10.1), (10.3), struck at K with time T to maturity, is given by E[(S T \u2212K)+] = lim E \u03a8( I\u02dc \u03b5, V \u03b5) , \u03b5\u21920 where \u03a8(I , V ) := CBS S 0 exp \u03f1I \u2212\u03f12 V , K, \u00af\u03f12V . (10.15) 2 Similar results hold for more general (\u201cnonsimple\u201d) rough volatility models. Let us discuss right away how to reduce the statements of Theorems 10.1 and 10.2 to the actual convergence statements that will occupy us in Section 10.2. First, note that Z t Z t 2 S t = S 0 exp f bWs dBs \u221212 f bWs ds . (10.16) 0 0 \u03b5The approximations W\u03b5, W \u03b5, and B\u03b5 := \u03f1W\u03b5 + \u00af\u03f1W converge uniformly to the obvious limits, so that it suffices to understand the convergence of the stochastic integral. Note that bW is heavily correlated with W but independent of W",
      "dense_score": 0.6766977310180664,
      "lexical_score": 0.2328767123287671
    },
    {
      "score": 1.1237107239684014,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 224,
      "chunk_no": 1,
      "text": "206 Chapter 10. Regularity structure for rough volatility Theorem 10.4 will be proved as Corollary 10.28. Remark 10.0.4. We showed in [40, Corollary 11]\u2014but see related results by Al\u00f2s, Le\u00f3n, and Vives [11] and Fukasawa [151, 153]\u2014that in the previously considered simple rough volatility models, now writing \u03c3(.) instead of f(.), the implied volatility skew behaves, in the short-time 1 2 3limit, as \u223c\u03f1 \u03c3\u2032(0)\u03c3(0) \u27e8K1, 1\u27e9tH\u22121 1 )(H+ 2 , where \u27e8K1, 1\u27e9in our setting computes to cH := (H+(2H)2 2 ). (The blow-up tH\u221212 as t \u21920 is a desired feature, in agreement with steep skews seen in the market.) from which one obtains a skewTo first order, Zt \u2248z + u(z) R 0t K(s, t)dWs = z + u(z) bW =: \u03c3( bW), formula in the nonsimple rough volatility case of the form f \u2032(z) 2 . \u03f1u(z) cHtH\u22121 f(z) Following the approach of [40], Theorem 10.4 allows for not only rigorous justification of these formula, but also for the computation of higher-order smile features, though this is not pursued in this chapter",
      "dense_score": 0.6834367513656616,
      "lexical_score": 0.273972602739726
    },
    {
      "score": 1.1214064712393774,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 179,
      "chunk_no": 1,
      "text": "8.2. At-the-money short-time skew 161 Theorem 8.6. If Assumption 8.5 holds and limT\u21930 sups,r,u\u2208[0,T] E (vsvr \u2212v2u)2 = 0, and there exists v\u20320 \u2208F0 such that 1 Z T Z T lim E0[Dsvr]drds =: v\u20320, T\u21930 T \u03b4+2 0 s then \u2202k\u03c3imp(k, T) \u03f1v\u20320 = lim . (8.12) v0 T\u21930 T \u03b4 k=X0 Remark 8.2.1. The lim sup assumption in the theorem may not always be straightforward to check. However, it is implied by the condition that the spot volatility (vt)t\u22650 converges to v0 = \u03c30 > 0 uniformly in time and in L4. It is clear that it holds for both the rough Stein\u2013Stein and the rough Bergomi models. Example 8.7. In the rough Stein\u2013Stein model (8.6) equipped with the Riemann\u2013Liouville ker- \u221a 2 for s < r, and therefore the first bound in Assumption 8.5nel (8.4), dsvr = 2H\u03c3\u20320(r \u2212s)H\u22121 holds with \u03b4 = H \u221212 and C = 2H(\u03c3\u20320)2, and the second one holds trivially as the second deriv- ative is null. It is straightforward to compute the limit in Theorem 8.6 (it is, in fact, independent of T) as \u221a 1 Z T Z T 2H\u03c3\u20320 E0[Dsvr]drds = v\u20320 := 3 T H+ 23 0 s (H + 12)(H + 2)",
      "dense_score": 0.6871598958969116,
      "lexical_score": 0.2465753424657534
    },
    {
      "score": 1.1190393291434197,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 231,
      "chunk_no": 1,
      "text": "10.2. The rough pricing regularity structure 213 Lemma 10.7. The pair (\u03a0, \u0393) as defined above defines (a.s.) a model on (T , A). Proof. The only symbol in S for which (10.31) is not straightforward is \u039eI(\u039e)m, where the statement follows by Chen\u2019s relation. The bounds (10.32) and (10.33) follow for 1 trivially and for I(\u039e)m by the H \u2212\u03ba\u2032-H\u00f6lder regularity of bW, \u03ba\u2032 \u2208(0, H). It is straightforward to check the condition (10.33) by using the rule \u0393ts\u03c4\u03c4\u2032 = \u0393ts\u03c4 \u00b7 \u0393ts\u03c4\u2032, so that we are only left with the task of bounding \u03a0s\u039eI(\u039e)m(\u03c6\u03bbs). Along the lines of the proof of [147, Theorem 3.1], it follows that |Wms,t| \u2264C|s \u2212t|mH+ 1 2 \u2212(m+1)\u03ba (where C > 0 denotes a random constant with C \u2208T p<\u221eLp), so that Z |\u03a0sI(\u039e)m\u039e(\u03c6\u03bbs)| = \u03c6\u03bbs \u2032(t)Wm(s, t) dt dt Z \u2264C \u03c6\u2032\u22121(t \u2212s))|s \u2212t|mH+ 21 \u2212(m+1)\u03ba \u03bb2 \u2264C\u03bbmH\u221212 \u2212(m+1)\u03ba = C\u03bb|I(\u039e)m\u039e|. As we will see in Section 10.2.2 this model is the toolbox from which we can build pathwise dW(r)",
      "dense_score": 0.6787653565406799,
      "lexical_score": 0.273972602739726
    },
    {
      "score": 1.1115506362261838,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 230,
      "chunk_no": 1,
      "text": "212 Chapter 10. Regularity structure for rough volatility From W we now construct the fBm bW in the Riemann\u2013Liouville sense with Hurst index 1 H \u2208(0, 2] as \u221a Z t := \u02d9W \u22c6K(t) = 2H |t \u2212r|H\u221212 dWr, bWt 0 \u221a 2 denotes the Volterra kernel. We also write K(s, t) := K(t \u2212s).where K(t) = 2H 1t>0 tH\u22121 To give meaning to the product terms \u039eI(\u039e)k we follow the ideas from rough paths and define an \u201citerated integral\u201d for s, t \u2208R, s \u2264t, as Z t Wm s,t := ( bWr \u2212bWs)m dWr. (10.28) s Wm(s, t) satisfies the following modification of Chen\u2019s relation. Lemma 10.6. Wm as defined in (10.28) satisfies m m Wm s,t = Wms,u + X u,t (10.29) ( bWu \u2212bWs)lWm\u2212l l l=0 for s, u, t \u2208R, s \u2264u \u2264t. Proof. This is a direct consequence of the binomial theorem. We extend the domain of Wm to all of R2 by imposing Chen\u2019s relation for all s, u, t \u2208R, i.e., for t, s \u2208R, t \u2264s, we set m m Wm s,t := \u2212 X t,s . (10.30) (bWt \u2212bWs)lWm\u2212l l l=0 We are now in position to define a model (\u03a0, \u0393) that gives rigorous meaning to the interpre- tation we gave above for \u039e, I(\u039e), \u039eI(\u039e), . . .",
      "dense_score": 0.680317759513855,
      "lexical_score": 0.2328767123287671
    },
    {
      "score": 1.0771521775363244,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 96,
      "chunk_no": 1,
      "text": "74 Chapter 3. No-arbitrage implies power-law market impact and rough volatility Finally, Z +\u221e Z t PTt = 1 + \u03c8T(v)dv dNa,Tv \u2212\u03bba,Tv dv \u2212dNb,Tv + \u03bbb,Tv dv 0 0 Z +\u221e = 1 + \u03c8T(v)dv (Ma,Tt \u2212Mb,Tt ). 0 Lemma 3.8 leads to T 1 \u2212aT Z +\u221e Pt = 1 + \u03c8T(v)dv (Ma,TtT \u2212Mb,TtT ). T\u00b5T 0 Step 3 We temporarily drop the superscripts a and b. Indeed, the results are valid for both buy and sell order flows. Consider the sequences 1 \u2212aT 1 \u2212aT Z tT r T\u00b5T XTt = NTtT, \u039bTt = \u03bbTs ds, ZTt = XTt \u2212\u039bTt (3.13) T\u00b5T T\u00b5T 0 1 \u2212aT defined for t \u2208[0, 1]. The following result is borrowed from [215]. Proposition 3.9. The sequence (\u039bT, XT, ZT) is tight. Furthermore, for any limit point (\u039b, X, Z) of (\u039bT, XT, ZT), Z is a continuous martingale, [Z, Z] = X, and \u039b = X. In addition, we have the following proposition which extends Theorem 3.1 in [215]. Proposition 3.10",
      "dense_score": 0.6879740953445435,
      "lexical_score": 0.1780821917808219
    },
    {
      "score": 1.0475294402854083,
      "file_name": "Continuous-Time Asset Pricing Theory, A Martingale-Based, Jarrow.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Continuous-Time Asset Pricing Theory, A Martingale-Based, Jarrow.pdf",
      "page_no": 24,
      "chunk_no": 1,
      "text": "Part I Arbitrage Pricing Theory Overview The key results of \ufb01nance that are successfully used in practice are based on the three fundamental theorems of asset pricing. Part 1 presents these three theorems. The applications of these three theorems are also discussed, including equivalent local martingale measures (state price densities), systematic risk, multiple-factor beta models, derivatives pricing, derivatives hedging, and asset price bubbles. All of these implications are based on the existence of an equivalent local martingale measure. The three fundamental theorems of asset pricing relate to the existence of an equivalent local martingale measure, its uniqueness, and its extensions. Roughly speaking, the \ufb01rst fundamental theorem of asset pricing equates no arbitrage with the existence of an equivalent local martingale measure. The second fundamental theorem relates market completeness to the uniqueness of the equivalent local martingale measure",
      "dense_score": 0.6793102622032166,
      "lexical_score": 0.2191780821917808
    },
    {
      "score": 0.9813396422503745,
      "file_name": "Continuous-Time Asset Pricing Theory, A Martingale-Based, Jarrow.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Continuous-Time Asset Pricing Theory, A Martingale-Based, Jarrow.pdf",
      "page_no": 55,
      "chunk_no": 1,
      "text": "32 2 The Fundamental Theorems from the set of trading strategies before due to the modi\ufb01ed integrability conditions needed to guarantee that the relevant integrals exist. This section presents the new notation and the evolutions for the mma and the risky assets under this change of numeraire. Let Bt = BtBt = 1 for all t \u22650, this represents the normalized value of the money market account (mma). Let St = (S1(t), . . . , Sn(t))\u2032 \u2265 0 represent the risky asset prices when normalized by the value of the mma, i.e. Si(t) = Si(t)Bt . Then, dBt = 0 and (2.5) Bt dSt dSt = \u2212rtdt. (2.6) St St Proof Using the integration by parts formula Theorem 3 in Chap. 1, one obtains (dropping the t\u2019s) d BS = BdS1 + Sd B1 = dSS BS \u2212SB dBB . The \ufb01rst equality uses d S, B1 = 0, since B is continuous and of \ufb01nite variation (use Lemmas 2 and 7 in Chap. 1). Substitution yields dS = dSS S \u2212S dBB . Algebra completes the proof. Recall that L (S) is the set of predictable processes integrable with respect to S and O is the set of optional processes",
      "dense_score": 0.6921615600585938,
      "lexical_score": 0.1780821917808219
    },
    {
      "score": 0.9808195256533687,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 139,
      "chunk_no": 2,
      "text": ". A natural choice of the two would be the underlying asset and the weighted variance swap (with a fixed maturity). As a hedging instrument, the replication portfolio for the weighted variance swap is more convenient than the weighted variance swap itself because it is a local martingale. Let Z t Z S 0 dK Z \u221e dK UTt := (h\u2032(S 0) \u2212h\u2032(S u))dS u + 2 Pt(K, T) + 2 Ct(K, T) 0 0 f(K)2 S 0 f(K)2 be the time t value of the replication portfolio with maturity T initiated at time 0. We have then Z T UTt = EQ Vuudu Ft 0 Z T Z u = EQ Vu0 + Vus g(u \u2212s)dWs du Ft 0 0 Z T Z t Z T = Vu0du + dWs Vus g(u \u2212s)du. 0 0 s Therefore, dUTt = DgUTt dWt, (6.6) where Z T Z T \u2202Uut DgUTt = Vut g(u \u2212t)du = g(u \u2212t)du. t t \u2202u Proposition 6.3. For any F \u2208L2(F\u03c4, Q), \u03c4 \u2208(t, T), there exists an adapted process (HS , HU) such that Z \u03c4 Z \u03c4 F = EQ[F|Ft] + HSv dS v + HUv dUTv . t t Proof. By the martingale representation theorem, there exists (H1, H2) such that Z \u03c4 Z \u03c4 F = EQ[F|Ft] + H1vdWv + H2vdWv. t t",
      "dense_score": 0.67958664894104,
      "lexical_score": 0.2328767123287671
    },
    {
      "score": 0.9662162680495274,
      "file_name": "Continuous-Time Asset Pricing Theory, A Martingale-Based, Jarrow.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Continuous-Time Asset Pricing Theory, A Martingale-Based, Jarrow.pdf",
      "page_no": 92,
      "chunk_no": 1,
      "text": "2.8 Finite Dimension Brownian Motion Market 69 Theorem 20 gives suf\ufb01cient conditions for the market to satisfy NFLVR. Condi- tion (1) is that the volatility matrix must be of full rank for all t. This omits risky assets that randomly change from risky to locally riskless (\ufb01nite variation) across time. Condition (2) removes redundant assets from the market (see Theorem 10). Finally, condition (3) is a necessary integrability condition for \u03b8t. For subsequent use we note that conditions (1) and (2) are true if and only if rank (\u03c3t) = n for all t a.s. P. Given Theorem 20, we can now characterize the set of local martingale measures Ml. Theorem 21 (Characterization of Ml) Assume that (1) rank (\u03c3t) = n for all t a.s. P and T \u2032 \u2032 \u22121 2(2) 0 ...\u03c3t \u03c3t\u03c3t (bt \u2212rt1) ... dy < \u221e. Then, = e\u2212 0T (\u03b8t+\u03bdt)\u00b7dWt\u221212 0T \u2225\u03b8t+\u03bdt\u22252dt > 0, Ml = {Q\u03bd : dQ\u03bddP dQ\u03bd E dP = 1, \u03bd \u2208K(\u03c3)} \u0338= \u2205 where \u2032 \u2032 \u22121 \u03b8t = \u03c3t \u03c3t\u03c3t (bt \u2212rt1) . Proof By Theorems 19 and 20, the market satis\ufb01es NFLVR and by the First Fundamental Theorem 13 of asset pricing Ml \u0338= \u2205",
      "dense_score": 0.6919696927070618,
      "lexical_score": 0.2465753424657534
    }
  ],
  "used_context": [
    {
      "score": 1.1379306077303952,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 221,
      "chunk_no": 1,
      "text": "10.0.3. Description of main results 203 Theorem 10.2. With C \u03b5 = C \u03b5(t) as in Theorem 10.1, define the renormalized integral approxi- mation Z T Z T I\u02dc \u03b
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