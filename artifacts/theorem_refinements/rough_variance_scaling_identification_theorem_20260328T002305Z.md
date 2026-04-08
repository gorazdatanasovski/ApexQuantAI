# Refinement: Rough-variance scaling identification theorem

- Securities: SPY US Equity, VIX3M Index
- Family: rough_variance_scaling
- Rationale: Strongest current theorem family; now needs symbolic checkability, tighter assumptions, and clearer observables.
- Query: Refine the rough-variance scaling theorem for SPY US Equity. Replace generic conjectural phrasing with a sharper theorem candidate. Tighten the assumptions on the Volterra kernel singularity and roughness exponent. State the observable realized-variance proxy precisely, connect it to the Bloomberg feature panel, list explicit empirical signatures and failure conditions, and produce a theorem whose symbolic structure can be checked by explicit algebraic identities or nonnegativity constraints. Make the theorem specific to SPY US Equity, not a generic placeholder.

## Result
```json
{
  "mode_used": "theorem",
  "response": "Research artifact: Rough-variance scaling identification theorem\nStatus: research_conjecture\nScore: 0.696\n\nStatement:\nConjecture: Assume the latent log-volatility process X admits a Volterra representation X_t = X_0 + \u222b_0^t K(t,s) dW_s with local kernel singularity K(t,s) ~ c (t-s)^{H-1/2} for H in (0,1/2). Then, as \u0394 \u2193 0, the increment variance satisfies E[(X_{t+\u0394}-X_t)^2] = C_X \u0394^{2H} + o(\u0394^{2H}), and any realized-variance proxy constructed from sufficiently fine observations for SPY US Equity inherits the same scaling exponent after lower-order noise correction: E[RV_\u0394] = a_0 + a_1 \u0394^{2H} + o(\u0394^{2H}).\n\nFused research memory:\n- [bloomberg_memory] SPY US Equity empirical research memory (SPY US Equity) | score=0.824\n  This note summarizes the local Bloomberg-derived empirical state for SPY US Equity. It is intended to support theorem generation, empirical falsification, calibration design, and hypothesis ranking inside QuantAI. # Bloomberg Research Memory: SPY US Equity Test whether roughness estimates co-move with realized-volatility regimes. Compare OU-style speeds across windows for stability or regime breaks. - Roughness classification: **rough_or_antipersistent** Examine whether absolute-return persisten\n- [bloomberg_memory] VIX3M Index empirical research memory (VIX3M Index) | score=0.745\n  This note summarizes the local Bloomberg-derived empirical state for VIX3M Index. It is intended to support theorem generation, empirical falsification, calibration design, and hypothesis ranking inside QuantAI. Test whether roughness estimates co-move with realized-volatility regimes. Compare OU-style speeds across windows for stability or regime breaks. - Roughness classification: **rough_or_antipersistent** Examine whether absolute-return persistence supports rough-vol style memory. - Roughne\n- [bloomberg_memory] Global Bloomberg learning snapshot (GLOBAL) | score=0.592\n  QuantAI currently has a working Bloomberg historical warehouse and a working empirical feature layer. Route market-state questions to this Bloomberg memory before invoking theorem synthesis. - Securities represented: AAPL US Equity, SPY US Equity BQL is environment-dependent and currently unavailable unless the local environment includes Bloomberg's BQL object model. Options-surface extraction is partially wired but still requires stronger contract selection and normalization when the requested \n- [book] Rough Volatility.pdf | page 236 | chunk 1 | score=0.502\n  Regularity structure for rough volatility Comparing the expressions in Lemmas 10.13 and 10.12, we see that morally we have to subtract Z t s )m\u22121 dt m \u03c6(t) K \u03b5(t, t)(bW\u03b5 \u2212bW\u03b5 from the model, which will give us a new model \u02c6\u03a0\u03b5. If we interpret K \u03b5 as an approximation to the Volterra kernel, we see that the expression C \u03b5(t) := K \u03b5(t, t), t \u22650, will correspond to something like \u201c0H\u221212 = \u221e\u201d in the limit \u03b5 \u21930. Of course we have to be careful that this step preserves \u201cChen\u2019s relation\u201d \u02c6\u03a0\u03b5s\u0393st = \u02c6\u03a0\u03b5t \n- [book] Rough Volatility.pdf | page 177 | chunk 2 | score=0.502\n  While its instantaneous stochastic varianceploys the kernel eKH(t, s) = (t \u2212s)H\u22121 Vt \u2261v2t of It\u00f4-Volterra dynamics \u221a Vt = V0 + eKH \u2217 \u03bb(\u03b8 \u2212V) + \u03bd V \u02d9W (t) does not quite fit into the above framework, it can be approximated as 2 Vt \u2248V0 + \u03bd p V0 eKH \u2217\u02d9W \u2248 \u03c30 + \u03c3\u20320 bWt , where we expanded to first order in \u2248tH and so construct an approximate rough Stein\u2013Stein \u221a bWt 1model with \u03c30 = \u221aV0 and 2\u03c3\u20320 2H = \u03bd/\u0393(H + 2). But one can also regard \u03c3\u20320 as a vol-of-vol parameter, which the rough Heston scale effec\n- [book] Rough Volatility.pdf | page 247 | chunk 1 | score=0.500\n  That is, the symbols required to describe Z are {1, I(\u039e)}, and if one adds the symbols required to describe the right-hand side, one ends up with the level-2 model space spanned by {\u039e, \u039eI(\u039e), 1, I(\u039e)} which is exactly the model space for the \u201csimple\u201d rough pricing regularity structure, (10.26) in case M = 1 It follows from general theory [191, Theorem 4.16] that if Z \u2208D\u03b30, then so is U(Z), the composition with a smooth function, and by [191, Theorem 2 \u2212\u03ba. For both reconstruction4.7] the product \n\nAssumptions:\n- H > 0 and H < 1/2.\n- The volatility driver admits a Volterra representation with local singularity exponent H-1/2.\n- The observed realized-variance proxy is asymptotically consistent up to lower-order noise distortion.\n- Empirical scope anchored to SPY US Equity.\n\nNext actions:\n- Add explicit symbolic tasks with lhs/rhs identities or qualitative constraints.\n- Collect stronger exact excerpts from the book-memory layer.\n- Add a formal symbolic derivation or export the candidate to Lean for proof work.\n\nTheorem registry:\n- action: existing\n- entry_id: thm_a83eb68e529643ae\n- status: research_conjecture",
  "sources": [
    {
      "score": 1.6496344787733896,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 176,
      "chunk_no": 1,
      "text": "158 Chapter 8. Asymptotics p 1 \u2212\u03f12 and Z t eWt := \u03f1 Wt + \u03f1Wt and bWt := (K \u2217\u02d9W)(t) = K(t, s)dWs, (8.3) 0 with (prototypical) kernel K = KH, with H \u2208(0, 12], given by \u221a KH(t, s) = 2H(t \u2212s)H\u221212 for t > 0, (8.4) with prefactor chosen such that bW1 has unit variance. Let us further agree that K(t, s) = 0 for s \u2264t; such kernels are said to be of Volterra type. Note that eW is a standard Brownian motion, correlated with W (with correlation \u03f1), whereas bW is a Riemann\u2013Liouville fractional Brownian motion (fBm) with Hurst index H. Prototypical rough volatility dynamics are given by \uf8f1 dS t \uf8f1 \u221a \u22121 \uf8f2 dXt = \uf8f4\uf8f2 S t = vtd eWt, or, equivalently, 2Vtdt + Vt deWt, (8.5) \uf8f4\uf8f3 vt = \u03c3 bWt, t , \uf8f3 Vt = \u03c32 bWt, t , with the rough stochastic volatility (resp., variance) process v (resp., V) given as an explicit function of the fBm via some continuous \u201cvolatility function\u201d \u03c3 = \u03c3(x, t)",
      "dense_score": 0.6782059073448181,
      "lexical_score": 0.3246753246753247
    },
    {
      "score": 1.6349202244622365,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 106,
      "chunk_no": 2,
      "text": ". This model, introduced in [129], takes the form38 dS t \u221a = VtdBt, S t u (4.4) 1 1 Z n Vu = Vt + \u03bb \u03b8t(s) \u2212Vs ds + \u03bd pVsdWs o, 1 2 \u2212H \u0393(H t (u \u2212s) + 12) for u \u2265t, where H \u2208(0, 1/2) is the Hurst exponent, \u0393 is the Gamma function, and the parameters \u03bb, \u03bd, \u03f1 have the same meaning as in the Heston model. The mean reversion level parameter \u03b8t(\u00b7) is now an Ft-measurable function which makes the model time consistent; see [131]. Setting the Hurst parameter to 1/2, we retrieve the classical Heston model (4.1). We recognize in (4.4) the power-law kernel of the Mandelbrot\u2013Van Ness representation of the fractional Brownian motion (fBm); hence the name \u201crough Heston.\u201d This model enjoys the nice statistical properties of rough volatility models. In addition, as will be seen in Section 4.2.3, it provides remarkable fits of the volatility surface while remaining almost as tractable as the classical Heston model, as explained in Section 4.2",
      "dense_score": 0.6863487958908081,
      "lexical_score": 0.22077922077922077
    },
    {
      "score": 1.6135956825528825,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 230,
      "chunk_no": 1,
      "text": "212 Chapter 10. Regularity structure for rough volatility From W we now construct the fBm bW in the Riemann\u2013Liouville sense with Hurst index 1 H \u2208(0, 2] as \u221a Z t := \u02d9W \u22c6K(t) = 2H |t \u2212r|H\u221212 dWr, bWt 0 \u221a 2 denotes the Volterra kernel. We also write K(s, t) := K(t \u2212s).where K(t) = 2H 1t>0 tH\u22121 To give meaning to the product terms \u039eI(\u039e)k we follow the ideas from rough paths and define an \u201citerated integral\u201d for s, t \u2208R, s \u2264t, as Z t Wm s,t := ( bWr \u2212bWs)m dWr. (10.28) s Wm(s, t) satisfies the following modification of Chen\u2019s relation. Lemma 10.6. Wm as defined in (10.28) satisfies m m Wm s,t = Wms,u + X u,t (10.29) ( bWu \u2212bWs)lWm\u2212l l l=0 for s, u, t \u2208R, s \u2264u \u2264t. Proof. This is a direct consequence of the binomial theorem. We extend the domain of Wm to all of R2 by imposing Chen\u2019s relation for all s, u, t \u2208R, i.e., for t, s \u2208R, t \u2264s, we set m m Wm s,t := \u2212 X t,s . (10.30) (bWt \u2212bWs)lWm\u2212l l l=0 We are now in position to define a model (\u03a0, \u0393) that gives rigorous meaning to the interpre- tation we gave above for \u039e, I(\u039e), \u039eI(\u039e), . . .",
      "dense_score": 0.7107385396957397,
      "lexical_score": 0.2857142857142857
    },
    {
      "score": 1.5981283405848912,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 53,
      "chunk_no": 1,
      "text": "Chapter 2 Pricing under rough volatility24 Christian Bayer, Peter K. Friz, Jim Gatheral 2.1 Introduction From an analysis of the time series of realized variance using recent high frequency data, Gatheral, Jaisson, and Rosenbaum [166] showed that the logarithm of realized variance behaves essentially as a fractional Brownian motion (fBm) with Hurst exponent H of order 0.1, at any reasonable time scale. The following stationary rough fractional stochastic volatility (RFSV) model was proposed: dS t = \u00b5tdt + VtdZt, S t Vt = exp{Xt}, t \u2208[0, T], (2.1) where \u00b5t is a suitable drift term, Zt is a standard Brownian motion, Xt is a fractional Ornstein\u2013 Uhlenbeck process (fOU process for short) satisfying dXt = \u03bddWHt \u2212\u03b1(Xt \u2212m)dt, where m \u2208R, and \u03bd and \u03b1 are positive parameters (see [92]), with Z and WH correlated in general",
      "dense_score": 0.6824140548706055,
      "lexical_score": 0.2077922077922078
    },
    {
      "score": 1.5962752648762293,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 245,
      "chunk_no": 2,
      "text": ". Although the rate function here is not given in a very useful form, it is possible to expand it in small y and thus compute (explicitly in terms of the model parameters) higher-order moderate deviations. In [40] this was related to implied volatility skew expansions. 10.4 Rough Volterra dynamics for volatility 10.4.1 Motivation from market microstructure Rosenbaum and coworkers, [126, 129, 131] show that stylized facts of modern market micro- structure naturally give rise to fractional dynamics and leverage effects. Specifically, they con- struct a sequence of Hawkes processes, suitably rescaled in time and space, that converges in law to a rough volatility model of rough Heston form \u221a dS t/S t = VtdBt \u2261\u221av \u03f1dWt + \u00af\u03f1dWt , (10.52) Z t a \u2212bVs Z t c \u221aVs Vt = V0 + 1 ds + 1 dWs. 0 (t \u2212s) 2 \u2212H 0 (t \u2212s) 2 \u2212H (As earlier, W, W are independent Brownian motions.) Similar to the case of the classical Heston model, the square-root provides both pain (with regard to any methods that rely on sufficient",
      "dense_score": 0.6819895505905151,
      "lexical_score": 0.24675324675324675
    },
    {
      "score": 1.5577060631343296,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 236,
      "chunk_no": 1,
      "text": "218 Chapter 10. Regularity structure for rough volatility Comparing the expressions in Lemmas 10.13 and 10.12, we see that morally we have to subtract Z t s )m\u22121 dt m \u03c6(t) K \u03b5(t, t)(bW\u03b5 \u2212bW\u03b5 from the model, which will give us a new model \u02c6\u03a0\u03b5. Of course we have to be careful that this step preserves \u201cChen\u2019s relation\u201d \u02c6\u03a0\u03b5s\u0393st = \u02c6\u03a0\u03b5t ; see Theorem 10.15. If we interpret K \u03b5 as an approximation to the Volterra kernel, we see that the expression C \u03b5(t) := K \u03b5(t, t), t \u22650, will correspond to something like \u201c0H\u221212 = \u221e\u201d in the limit \u03b5 \u21930. We indeed have the following upper bound. Lemma 10.14. For all s, t \u2208R we have |K \u03b5(s, t)| \u2272\u03b5H\u221212 . 2 \u2272\u03b5H\u221212 .Proof. |K \u03b5(s, t)| \u2272\u03b5\u22122 R B(t,c\u03b5) dx R B(x,c\u03b5) du |s \u2212u|H\u22121 Our hope is now that the new model \u02c6\u03a0\u03b5 converges to \u03a0 in a suitable sense",
      "dense_score": 0.721991777420044,
      "lexical_score": 0.2987012987012987
    },
    {
      "score": 1.5568274096080235,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 15,
      "chunk_no": 3,
      "text": ". The rough volatility model can be seen as an extension of the MRW with an extra parameter allowing one to tune at will the roughness of volatility. More precisely, it postulates that the log- volatility is a fractional Brownian motion with Hurst exponent H less than 1/2 (i.e., \u201crougher\u201d that the Brownian motion) while the MRW model formally corresponds to H \u21920. Indeed, empirical data reveal that volatility is slightly less rough than what the MRW posits, at least for stock indices. Calibration suggests H \u22480.1 for the S&P500, whereas very recent (2022) work by Wu, Bacry, and Muzy suggests that single stock returns are better adjusted with H = 0. The next episode of this long saga came in 2009 when Zumbach noticed a subtle, yet crucial, aspect of empirical financial time series: they are not statistically invariant upon time reversal. Past and future are not equivalent, whereas most models up to that date, including the MRW, did not distinguish past from future",
      "dense_score": 0.6811131238937378,
      "lexical_score": 0.2987012987012987
    },
    {
      "score": 1.549680997303554,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 135,
      "chunk_no": 2,
      "text": ". One of the only potential challenges that remain to be addressed in practice is an (apparent) difficulty in hedging derivatives in rough models. Hedging in rough volatility models can seem intricate since the dynamics of rough volatility models involve a fractional Brownian motion (fBm). In this chapter we demonstrate how this apparent challenge can be overcome in different modeling scenarios exhibiting different levels of generality, which allow us to derive (often explicit) hedg- ing strategies. For building a hedging portfolio, one essentially needs to compute conditional expectations of the form Ct = E[ f(S T)|Ft], (6.1) where f is a deterministic payoff function, and determine the associated martingale represen- tations. Classical theory tells us that the option payoff can be replicated at time t for a price PT\u2212t f(S t), where (Pt)t\u22650 is the semigroup on Cb(R2) generated by the infinitesimal generator A associated with the instantaneous covariance of S and with the (local) martingale problem char- acterizing the law of the process S",
      "dense_score": 0.6768238544464111,
      "lexical_score": 0.2857142857142857
    },
    {
      "score": 1.5495315647125245,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 229,
      "chunk_no": 1,
      "text": "10.2. The rough pricing regularity structure 211 Remark 10.2.1. It is useful here and in the sequel to consider as a sanity check the special case H = 12 in which we recover the \u201clevel-2\u201d rough path structure as introduced in [147, Chapter 13]. More specifically, if we take a H\u00f6lder exponent \u03b1 := 21 \u2212\u03ba < 12, we may choose M = 1. Then condition (10.25) is precisely the familiar condition \u03b1 > 1/3. The interpretation for the symbols in S is as follows: \u039e should be understood as an abstract representation of the white noise \u03be belonging to the Brownian motion W, i.e., \u03be = \u02d9W where the derivative is taken in the distributional sense. Note that since we set Wx = 0 for x \u22640, we have \u02d9W(\u03c6) = 0 for \u03c6 \u2208C\u221ec ((\u2212\u221e, 0)). The symbol I(. . .) has the intuitive meaning of \u201cintegration against the Volterra kernel,\u201d so that I(\u039e) represents the integration of the white noise against the Volterra kernel, i.e., \u221a Z t 2H |t \u2212r|H\u221212 dWr, 0 which is nothing but the fBm bWt. Symbols like \u039eI(\u039e)m = \u039e \u00b7 I(\u039e) \u00b7 . . . \u00b7 I(\u039e) or I(\u039e)m = I(\u039e) \u00b7 . . . \u00b7 I(\u039e) should be read as products between the objects above",
      "dense_score": 0.6895315647125244,
      "lexical_score": 0.2727272727272727
    },
    {
      "score": 1.549408619744437,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 247,
      "chunk_no": 1,
      "text": "10.4. Rough Volterra dynamics for volatility 229 since |I(\u039e)2| = |I(\u039eI(\u039e))| = 2H \u22122\u03ba. It follows from general theory [191, Theorem 4.16] that if Z \u2208D\u03b30, then so is U(Z), the composition with a smooth function, and by [191, Theorem 2 \u2212\u03ba. For both reconstruction4.7] the product with \u039e \u2208D\u221e\u221212 \u2212\u03ba is a modeled distribution in D\u03b3\u22121 and convolution with singular kernels, one needs modeled distributions with positive degree \u03b3 \u22121 2 \u2212\u03ba > 0. Given H \u2208(0, 2]1 we can then determine which symbols (up to which degree) are required in the expansion. As earlier, fix an integer M \u2265max m \u2208N|m \u00b7 (H \u2212\u03ba) \u22121 \u2212\u03ba \u22640 2 (so that (M + 1).(H \u2212\u03ba) \u221212 \u2212\u03ba > 0) and see that Z \u2208D(M+1).(H\u2212\u03ba)0 will do. When H > 1/4, and by choosing \u03ba > 0 small enough, we see that M = 1 will do. That is, the symbols required to describe Z are {1, I(\u039e)}, and if one adds the symbols required to describe the right-hand side, one ends up with the level-2 model space spanned by {\u039e, \u039eI(\u039e), 1, I(\u039e)} which is exactly the model space for the \u201csimple\u201d rough pricing regularity structure, (10.26) in case M = 1",
      "dense_score": 0.7136943340301514,
      "lexical_score": 0.2987012987012987
    }
  ],
  "used_context": [
    {
      "score": 1.6496344787733896,
      "file_name": "Rough Volatility.pdf",
      "file_path": "C:\\Users\\gorazd.atanasovski\\Desktop\\ApexQuantAI\\books_vault\\Rough Volatility.pdf",
      "page_no": 176,
      "chunk_no": 1,
      "text": "158 Chapter 8. Asymptotics p 1 \u2212\u03f12 and Z t eWt := \u03f1 Wt + \u03f1Wt and bWt := (K \u2217\u02d9W)(t) = K(t, s)dWs, (8.3) 0 with (prototypical) kernel K = KH, with H \u2208(0, 12], g
```

## Symbolic execution summary
```json
{
  "title": "Rough-variance scaling identification theorem",
  "family": "rough_variance_scaling",
  "n_tasks": 5,
  "n_ok": 4,
  "n_fail": 1,
  "results": [
    {
      "task": {
        "name": "variance_scaling_factorization",
        "kind": "verify_identity",
        "payload": {
          "lhs": "C_X*Delta**(2*H) + a0 + a1*Delta**(2*H)",
          "rhs": "a0 + (C_X + a1)*Delta**(2*H)"
        },
        "rationale": "Checks algebraic coherence of the scaling-law form used in the theorem candidate."
      },
      "ok": true,
      "result": {
        "name": "identity",
        "kind": "identity",
        "passed": true,
        "result": "proved_exactly",
        "details": {
          "lhs": "C_X*Delta**(2*H) + Delta**(2*H)*a1 + a0",
          "rhs": "Delta**(2*H)*(C_X + a1) + a0",
          "difference": "0",
          "assumptions": []
        }
      }
    },
    {
      "task": {
        "name": "variance_term_nonnegative",
        "kind": "verify_nonnegative",
        "payload": {
          "expression": "a1*Delta**(2*H)"
        },
        "rationale": "Under positive coefficient and positive scale assumptions, the scaling contribution should remain nonnegative."
      },
      "ok": true,
      "result": {
        "name": "nonnegative",
        "kind": "nonnegative",
        "passed": true,
        "result": "proved",
        "details": {
          "expression": "Delta**(2*H)*a1",
          "simplified": "Delta**(2*H)*a1",
          "is_nonnegative": true,
          "assumptions": []
        }
      }
    },
    {
      "task": {
        "name": "increment_variance_nonnegative",
        "kind": "verify_nonnegative",
        "payload": {
          "expression": "C_X*Delta**(2*H)"
        },
        "rationale": "Variance contribution must remain nonnegative under the roughness scaling ansatz."
      },
      "ok": true,
      "result": {
        "name": "nonnegative",
        "kind": "nonnegative",
        "passed": true,
        "result": "proved",
        "details": {
          "expression": "C_X*Delta**(2*H)",
          "simplified": "C_X*Delta**(2*H)",
          "is_nonnegative": true,
          "assumptions": []
        }
      }
    },
    {
      "task": {
        "name": "scaling_at_origin_consistency",
        "kind": "verify_derivative_zero",
        "payload": {
          "expression": "Delta**(2*H + 1)",
          "variable": "Delta",
          "point": 0
        },
        "rationale": "Checks a simple origin-consistency proxy for higher-order remainder terms in the small-scale expansion."
      },
      "ok": false,
      "result": {
        "name": "derivative_zero",
        "kind": "derivative_zero",
        "passed": false,
        "result": "not_proved",
        "details": {
          "expression": "Delta**(2*H + 1)",
          "derivative": "Delta**(2*H + 1)*(2*H + 1)/Delta",
          "point": "0",
          "value": "nan",
          "assumptions": []
        }
      }
    },
    {
      "task": {
        "name": "exponent_additivity",
        "kind": "verify_identity",
        "payload": {
          "lhs": "Delta**(2*H) * Delta**(2*K)",
          "rhs": "Delta**(2*(H + K))"
        },
        "rationale": "Provides a reusable exponent-composition identity for scaling arguments."
      },
      "ok": true,
      "result": {
        "name": "identity",
        "kind": "identity",
        "passed": true,
        "result": "proved_exactly",
        "details": {
          "lhs": "Delta**(2*H)*Delta**(2*K)",
          "rhs": "Delta**(2*H + 2*K)",
          "difference": "0",
          "assumptions": []
        }
      }
    }
  ]
}
```