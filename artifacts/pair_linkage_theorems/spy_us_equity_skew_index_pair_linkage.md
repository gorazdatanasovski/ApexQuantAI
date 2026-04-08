# Pair-Linkage Theorem Run: SPY US Equity / SKEW Index

- Created at: 2026-03-28T01:37:46+00:00
- Family matched: True

## Attempts
### Attempt 1
- Selected title: Evidence-anchored structural conjecture
- Prompt: Propose a pair-linkage theorem for SPY US Equity and SKEW Index. The theorem must be genuinely about the interaction between the two objects, not a reused single-name rough-variance theorem. Focus on spot-volatility coupling, variance scaling transmission, regime dependence, term-structure state, tail-risk state, cross-object linkage. State: (1) the pair-level object, (2) the predicted relationship or monotonicity, (3) empirical Bloomberg feature signatures, (4) failure conditions, and (5) symbolic structure that can be checked directly.

## Accepted result
```json
{
  "mode_used": "theorem",
  "response": "Research artifact: Evidence-anchored structural conjecture\nStatus: speculative_candidate\nScore: 0.452\n\nStatement:\nConjecture: the objects propose, pair-linkage, theorem admit a common structural representation in the general_quant family, and the dominant terms in that representation are exactly those that remain stable across the top retrieved excerpts and the empirical feature panel.\n\nFused research memory:\n- [bloomberg_memory] SPY US Equity empirical research memory (SPY US Equity) | score=0.745\n  This note summarizes the local Bloomberg-derived empirical state for SPY US Equity. # Bloomberg Research Memory: SPY US Equity It is intended to support theorem generation, empirical falsification, calibration design, and hypothesis ranking inside QuantAI. Compare OU-style speeds across windows for stability or regime breaks. - Volatility regime classification: **compressed_volatility** - Volatility regime: compressed_volatility Test whether roughness estimates co-move with realized-volatility r\n- [bloomberg_memory] SKEW Index empirical research memory (SKEW Index) | score=0.731\n  This note summarizes the local Bloomberg-derived empirical state for SKEW Index. It is intended to support theorem generation, empirical falsification, calibration design, and hypothesis ranking inside QuantAI. Compare OU-style speeds across windows for stability or regime breaks. - Volatility regime classification: **compressed_volatility** # Bloomberg Research Memory: SKEW Index - Volatility regime: compressed_volatility Test whether roughness estimates co-move with realized-volatility regimes\n- [bloomberg_memory] Global Bloomberg learning snapshot (GLOBAL) | score=0.579\n  QuantAI currently has a working Bloomberg historical warehouse and a working empirical feature layer. BQL is environment-dependent and currently unavailable unless the local environment includes Bloomberg's BQL object model. - Securities represented: AAPL US Equity, SPY US Equity Options-surface extraction is partially wired but still requires stronger contract selection and normalization when the requested put/call subset is not represented in the sampled chain. Route market-state questions to \n- [registry] Evidence-anchored structural conjecture | score=0.540\n  Statement: Conjecture: the objects propose, pair-linkage, theorem admit a common structural representation in the general_quant family, and the dominant terms in that representation are exactly those that remain stable across the top retrieved excerpts and the empirical feature panel. Failure conditions: Retrieved evidence remains too dispersed across unrelated mathematical families.; No exact excerpt currently pins down every constant or normalization.; Add explicit symbolic tasks with lhs/rhs \n- [book] NONLINEAR OPTION PRICING, GUYON .pdf | page 356 | chunk 1 | score=0.497\n  For instance, the resulting correlation may have a weird skew (dependence on the asset values), or its skew may be far from the one historically observed, or it may generate prices of other options that are far from market quotes. This family is parameterized by two functions a and b that depend on time and on the values of all the underlying assets, and may depend as well on any set of path-dependent variables. Instead of assuming that the basket variance or the correlation (or equivalently \u03bb) \n- [book] NONLINEAR OPTION PRICING, GUYON .pdf | page 361 | chunk 2 | score=0.495\n  In this chapter, we are interested in the following important practical question: How do we build an almost (if not strictly) admissible correlation \u03c1(t, S1, S2) having desirable properties, such as matching a view on some correlation skew, reproducing historical features, calibrating to other option prices, etc.? This result is not com- pletely trivial, as one needs to show that EQf\u03c1t can be replaced by EQf\u03c1 . For instance, in the situation of Figure 12.6, one may want to modify the low-strike \n\nAssumptions:\n- Empirical scope anchored to SPY US Equity.\n\nNext actions:\n- Add explicit symbolic tasks with lhs/rhs identities or qualitative constraints.\n- Refine the candidate so the implied empirical signature is sharper and testable.\n- Collect stronger exact excerpts from the book-memory layer.\n- Add a formal symbolic derivation or export the candidate to Lean for proof work.\n\nTheorem registry:\n- action: existing\n- entry_id: thm_6e575618e2274dd9\n- status: speculative_candidate",
  "sources": [
    {
      "score": 1.1437250414286575,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 179,
      "chunk_no": 1,
      "text": "8.2. At-the-money short-time skew 161 Theorem 8.6. If Assumption 8.5 holds and limT\u21930 sups,r,u\u2208[0,T] E (vsvr \u2212v2u)2 = 0, and there exists v\u20320 \u2208F0 such that 1 Z T Z T lim E0[Dsvr]drds =: v\u20320, T\u21930 T \u03b4+2 0 s then \u2202k\u03c3imp(k, T) \u03f1v\u20320 = lim . (8.12) v0 T\u21930 T \u03b4 k=X0 Remark 8.2.1. The lim sup assumption in the theorem may not always be straightforward to check. However, it is implied by the condition that the spot volatility (vt)t\u22650 converges to v0 = \u03c30 > 0 uniformly in time and in L4. It is clear that it holds for both the rough Stein\u2013Stein and the rough Bergomi models. Example 8.7. In the rough Stein\u2013Stein model (8.6) equipped with the Riemann\u2013Liouville ker- \u221a 2 for s < r, and therefore the first bound in Assumption 8.5nel (8.4), dsvr = 2H\u03c3\u20320(r \u2212s)H\u22121 holds with \u03b4 = H \u221212 and C = 2H(\u03c3\u20320)2, and the second one holds trivially as the second deriv- ative is null. It is straightforward to compute the limit in Theorem 8.6 (it is, in fact, independent of T) as \u221a 1 Z T Z T 2H\u03c3\u20320 E0[Dsvr]drds = v\u20320 := 3 T H+ 23 0 s (H + 12)(H + 2)",
      "dense_score": 0.7064647674560547,
      "lexical_score": 0.2602739726027397
    },
    {
      "score": 1.142493665838895,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 224,
      "chunk_no": 1,
      "text": "206 Chapter 10. Regularity structure for rough volatility Theorem 10.4 will be proved as Corollary 10.28. Remark 10.0.4. We showed in [40, Corollary 11]\u2014but see related results by Al\u00f2s, Le\u00f3n, and Vives [11] and Fukasawa [151, 153]\u2014that in the previously considered simple rough volatility models, now writing \u03c3(.) instead of f(.), the implied volatility skew behaves, in the short-time 1 2 3limit, as \u223c\u03f1 \u03c3\u2032(0)\u03c3(0) \u27e8K1, 1\u27e9tH\u22121 1 )(H+ 2 , where \u27e8K1, 1\u27e9in our setting computes to cH := (H+(2H)2 2 ). (The blow-up tH\u221212 as t \u21920 is a desired feature, in agreement with steep skews seen in the market.) from which one obtains a skewTo first order, Zt \u2248z + u(z) R 0t K(s, t)dWs = z + u(z) bW =: \u03c3( bW), formula in the nonsimple rough volatility case of the form f \u2032(z) 2 . \u03f1u(z) cHtH\u22121 f(z) Following the approach of [40], Theorem 10.4 allows for not only rigorous justification of these formula, but also for the computation of higher-order smile features, though this is not pursued in this chapter",
      "dense_score": 0.6992059946060181,
      "lexical_score": 0.2876712328767123
    },
    {
      "score": 1.1299665331187314,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 221,
      "chunk_no": 1,
      "text": "10.0.3. Description of main results 203 Theorem 10.2. With C \u03b5 = C \u03b5(t) as in Theorem 10.1, define the renormalized integral approxi- mation Z T Z T I\u02dc \u03b5 := I\u02dcf\u03b5 (T) := f( t )dW\u03b5t \u2212 bW\u03b5 C \u03b5(t) f \u2032( bW\u03b5t )dt, (10.14) 0 0 and also the approximate total variance \u03b5 \u03b5 Z T t )dt. V := V f (T) := f 2( bW\u03b5 0 Then the price of a European call option, under the pricing model (10.1), (10.3), struck at K with time T to maturity, is given by E[(S T \u2212K)+] = lim E \u03a8( I\u02dc \u03b5, V \u03b5) , \u03b5\u21920 where \u03a8(I , V ) := CBS S 0 exp \u03f1I \u2212\u03f12 V , K, \u00af\u03f12V . (10.15) 2 Similar results hold for more general (\u201cnonsimple\u201d) rough volatility models. Let us discuss right away how to reduce the statements of Theorems 10.1 and 10.2 to the actual convergence statements that will occupy us in Section 10.2. First, note that Z t Z t 2 S t = S 0 exp f bWs dBs \u221212 f bWs ds . (10.16) 0 0 \u03b5The approximations W\u03b5, W \u03b5, and B\u03b5 := \u03f1W\u03b5 + \u00af\u03f1W converge uniformly to the obvious limits, so that it suffices to understand the convergence of the stochastic integral. Note that bW is heavily correlated with W but independent of W",
      "dense_score": 0.6687336564064026,
      "lexical_score": 0.2328767123287671
    },
    {
      "score": 1.0948253590113497,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 177,
      "chunk_no": 3,
      "text": ". But one can also regard \u03c3\u20320 as a vol-of-vol parameter, which the rough Heston scale effectively prescribes to be divergent as H \u21930. Structure of this article In Section 8.2.1 we briefly review the pioneering work of Al\u00f2s, Le\u00f3n, and Vives [11] (see also [10]) that provides a direct route to at-the-money (ATM), short-dated implied volatility skew asymptotics \u2202 2 \u00d7 (const). \u03c3imp(k, t) \u223ctH\u22121 \u2202k k=0 Section 8.3 considers the central limit theorem (CLT) regime, with nonzero log-strike kt = xt\u03b3 for \u03b3 = 12, which naturally leads to the asymptotic formula for the discrete skew \u03c3imp(kt, t) \u2212\u03c3imp k\u2032t, t SBS := \u223ctH\u221212 \u00d7 (const)x,x\u2032 kt \u2212k\u2032t",
      "dense_score": 0.6815376877784729,
      "lexical_score": 0.2876712328767123
    },
    {
      "score": 1.0664801696555255,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 189,
      "chunk_no": 2,
      "text": ". (Note that martingality of the price process exp{X}, shown in [162] for the rough Bergomi model, already entails existence of a first moment; negative correlation, \u03f1 < 0, is conjectured to yield existence of (some) higher moments, as is the case in classical lognormal volatility models (e.g., \u221aVt = \u03c30 exp(\u03b7Wt)). Remark 8.4.1. Note that kt = xt 21 \u2212H tends to zero as t tends to zero. The Caravenna\u2013Corbetta formula [83, (2.41)], an extension of Benaim and Friz [46], gives k2t x2 \u03c32BS(kt, t) \u223c \u223c = \u03a32(x) (8.26) kt 2\u039b(x) 2t log C(kt,t) where we used the precise log-asymptotic equivalence of (8.25), in agreement with expected (8.24). Remark 8.4.2. Both option price and implied volatility asymptotics derived here are consistent with those in the rough Heston model as in Theorem 4.4 in Chapter 4. In Theorem 8.11 we gave a CLT based expansion of \u03c3imp(x \u221at, t); formally subtracting the expansion for distinct x, x\u2032 led us to the skew formula (8.17)",
      "dense_score": 0.6682609915733337,
      "lexical_score": 0.2191780821917808
    },
    {
      "score": 1.0626895277140893,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 96,
      "chunk_no": 1,
      "text": "74 Chapter 3. No-arbitrage implies power-law market impact and rough volatility Finally, Z +\u221e Z t PTt = 1 + \u03c8T(v)dv dNa,Tv \u2212\u03bba,Tv dv \u2212dNb,Tv + \u03bbb,Tv dv 0 0 Z +\u221e = 1 + \u03c8T(v)dv (Ma,Tt \u2212Mb,Tt ). 0 Lemma 3.8 leads to T 1 \u2212aT Z +\u221e Pt = 1 + \u03c8T(v)dv (Ma,TtT \u2212Mb,TtT ). T\u00b5T 0 Step 3 We temporarily drop the superscripts a and b. Indeed, the results are valid for both buy and sell order flows. Consider the sequences 1 \u2212aT 1 \u2212aT Z tT r T\u00b5T XTt = NTtT, \u039bTt = \u03bbTs ds, ZTt = XTt \u2212\u039bTt (3.13) T\u00b5T T\u00b5T 0 1 \u2212aT defined for t \u2208[0, 1]. The following result is borrowed from [215]. Proposition 3.9. The sequence (\u039bT, XT, ZT) is tight. Furthermore, for any limit point (\u039b, X, Z) of (\u039bT, XT, ZT), Z is a continuous martingale, [Z, Z] = X, and \u039b = X. In addition, we have the following proposition which extends Theorem 3.1 in [215]. Proposition 3.10",
      "dense_score": 0.6735114455223083,
      "lexical_score": 0.1780821917808219
    },
    {
      "score": 1.0432976893202899,
      "file_name": "Continuous-Time Asset Pricing Theory, A Martingale-Based, Jarrow.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Continuous-Time Asset Pricing Theory, A Martingale-Based, Jarrow.pdf",
      "page_no": 24,
      "chunk_no": 1,
      "text": "Part I Arbitrage Pricing Theory Overview The key results of \ufb01nance that are successfully used in practice are based on the three fundamental theorems of asset pricing. Part 1 presents these three theorems. The applications of these three theorems are also discussed, including equivalent local martingale measures (state price densities), systematic risk, multiple-factor beta models, derivatives pricing, derivatives hedging, and asset price bubbles. All of these implications are based on the existence of an equivalent local martingale measure. The three fundamental theorems of asset pricing relate to the existence of an equivalent local martingale measure, its uniqueness, and its extensions. Roughly speaking, the \ufb01rst fundamental theorem of asset pricing equates no arbitrage with the existence of an equivalent local martingale measure. The second fundamental theorem relates market completeness to the uniqueness of the equivalent local martingale measure",
      "dense_score": 0.6750785112380981,
      "lexical_score": 0.2191780821917808
    },
    {
      "score": 1.0092968339789403,
      "file_name": "Stochastic Calculus for Finance, Shreve.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Stochastic Calculus for Finance, Shreve.pdf",
      "page_no": 298,
      "chunk_no": 2,
      "text": ". We show by example how the Discounted Feynman-Kac Theorem can be used to find prices and hedges, even for path\u00ad dependent options. The option we choose for this example is an Asian option.A more detailed discussion of this option is presented in Section 7.5. The payoff we consider is V(T) \u0888 S(u) du - (\u0101 [ Kfwhere S(u) is a geometric Brownian motion, the expiration time T is fixed and positive, and K is a positive strike pric \u0889 In terms of the Brownian mo\u00ad tion W(u) under the risk-neutral measure IP', we may write the stochastic differential equation for S ( u) as dS(u) = rS(u) du + aS(u) dW(u). (6.6.5) Because the payoff depends on the whole path of the stock price via its integral, at each time t prior to expiration it is not enough to know just the stock price in order to determine the value of the option. We must also know the integral of the stock price, Y(t) = S(u) du, 1t",
      "dense_score": 0.6750502586364746,
      "lexical_score": 0.2465753424657534
    },
    {
      "score": 0.970668980324105,
      "file_name": "Continuous-Time Asset Pricing Theory, A Martingale-Based, Jarrow.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Continuous-Time Asset Pricing Theory, A Martingale-Based, Jarrow.pdf",
      "page_no": 55,
      "chunk_no": 1,
      "text": "32 2 The Fundamental Theorems from the set of trading strategies before due to the modi\ufb01ed integrability conditions needed to guarantee that the relevant integrals exist. This section presents the new notation and the evolutions for the mma and the risky assets under this change of numeraire. Let Bt = BtBt = 1 for all t \u22650, this represents the normalized value of the money market account (mma). Let St = (S1(t), . . . , Sn(t))\u2032 \u2265 0 represent the risky asset prices when normalized by the value of the mma, i.e. Si(t) = Si(t)Bt . Then, dBt = 0 and (2.5) Bt dSt dSt = \u2212rtdt. (2.6) St St Proof Using the integration by parts formula Theorem 3 in Chap. 1, one obtains (dropping the t\u2019s) d BS = BdS1 + Sd B1 = dSS BS \u2212SB dBB . The \ufb01rst equality uses d S, B1 = 0, since B is continuous and of \ufb01nite variation (use Lemmas 2 and 7 in Chap. 1). Substitution yields dS = dSS S \u2212S dBB . Algebra completes the proof. Recall that L (S) is the set of predictable processes integrable with respect to S and O is the set of optional processes",
      "dense_score": 0.6814908981323242,
      "lexical_score": 0.1780821917808219
    },
    {
      "score": 0.95977649401312,
      "file_name": "NONLINEAR OPTION PRICING, GUYON .pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\NONLINEAR OPTION PRICING, GUYON .pdf",
      "page_no": 361,
      "chunk_no": 2,
      "text": ". For instance, in the situation of Figure 12.6, one may want to modify the low-strike extrapolations of \u03c31 and \u03c32. In this chapter, we are interested in the following important practical question: How do we build an almost (if not strictly) admissible correlation \u03c1(t, S1, S2) having desirable properties, such as matching a view on some correlation skew, reproducing historical features, calibrating to other option prices, etc.? REMARK 12.1 We may have started with a general stochastic pro- cess (\u03c1t) for the correlation, which possibly depends on extra sources of ran- domness. In this situation, the calibration condition (12.3) still holds with \u03c1(t, S1t , S2t ) \u2261EQf\u03c1t \u03c1t S1t , S2t = EQ\u03c1t \u03c1t S1t , S2t . This result is not com- pletely trivial, as one needs to show that EQf\u03c1t can be replaced by EQf\u03c1 . This follows from Gy\u00a8ongy\u2019s theorem; see Section 12.8.2 for a simple derivation",
      "dense_score": 0.7155299186706543,
      "lexical_score": 0.2465753424657534
    }
  ],
  "used_context": [
    {
      "score": 1.1437250414286575,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 179,
      "chunk_no": 1,
      "text": "8.2. At-the-money short-time skew 161 Theorem 8.6. If Assumption 8.5 holds and limT\u21930 sups,r,u\u2208[0,T] E (vsvr \u2212v2u)2 = 0, and there exists v\u20320 \u2208F0 such that 1 Z T Z T lim E0[Dsvr]drds =: v\u20320, T\u21930 T \u03b4+2 0 s then \u2202k\u03c3imp(k, T) \u03f1v\u20320 = lim . (8.12) v0 T\u21930 T \u03b4 k=X0 Remark 8.2.1. The lim sup assumption in the theorem may not always be straightforward to check. However, it is implied by the condition that the spot volatility (vt)t\u22650 converges to v0 = \u03c30 > 0 uniformly in time and in L4. It is clear that it holds for both the rough Stein\u2013Stein and the rough Bergomi models. Example 8.7. In the rough Stein\u2013Stein model (8.6) equipped with the Riemann\u2013Liouville ker- \u221a 2 for s < r, and therefore the first bound in Assumption 8.5nel (8.4), dsvr = 2H\u03c3\u20320(r \u2212s)H\u22121 holds with \u03b4 = H \u221212 and C = 2H(\u03c3\u20320)2, and the second one holds trivially as the second deriv- ative is null. It is straightforward to compute the limit in Theorem 8.6 (it is, in fact, independent of T) as \u221a 1 Z T Z T 2H\u03c3\u20320 E0[Dsvr]drds = v\u20320 := 3 T H+ 23 0 s (H + 12)(H + 2)",
      "dense_score": 0.7064647674560547,
      "lexical_score": 0.26027
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