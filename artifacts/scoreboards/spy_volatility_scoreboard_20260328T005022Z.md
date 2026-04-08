# SPY Volatility Scoreboard

- Created at: 2026-03-28T00:50:22+00:00
- Securities: SPY US Equity, SPX Index, VIX Index, VIX3M Index, VVIX Index, SKEW Index, ES1 Index

## Coverage
```json
{
  "db_exists": true,
  "securities": {
    "SPY US Equity": {
      "history_rows": 41730,
      "feature_rows": 8346,
      "memory_rows": 1
    },
    "SPX Index": {
      "history_rows": 123455,
      "feature_rows": 24691,
      "memory_rows": 1
    },
    "VIX Index": {
      "history_rows": 45760,
      "feature_rows": 9152,
      "memory_rows": 1
    },
    "VIX3M Index": {
      "history_rows": 30465,
      "feature_rows": 6093,
      "memory_rows": 1
    },
    "VVIX Index": {
      "history_rows": 24920,
      "feature_rows": 4984,
      "memory_rows": 1
    },
    "SKEW Index": {
      "history_rows": 45560,
      "feature_rows": 9112,
      "memory_rows": 1
    },
    "ES1 Index": {
      "history_rows": 36230,
      "feature_rows": 7246,
      "memory_rows": 1
    }
  }
}
```

## Coverage gaps
- None

## Top theorems
### Rough-variance scaling identification theorem
- Score: 0.8750
- Status: symbolically_verified_candidate
- Symbolic pass rate: 1.0000
```json
{
  "entry_id": "thm_a83eb68e529643ae",
  "title": "Rough-variance scaling identification theorem",
  "status": "symbolically_verified_candidate",
  "native_score": 0.695599158569593,
  "updated_at": "2026-03-28T00:40:49+00:00",
  "securities": [
    "SPY US Equity",
    "VIX3M Index"
  ],
  "statement_head": "Conjecture: Assume the latent log-volatility process X admits a Volterra representation X_t = X_0 + \u222b_0^t K(t,s) dW_s with local kernel singularity K(t,s) ~ c (t-s)^{H-1/2} for H in (0,1/2). Then, as \u0394 \u2193 0, the increment variance satisfies E[(X_{t+\u0394}-X_t)^2] = C_X \u0394^{2H} + o(\u0394^{2H}), and any realized-variance proxy constructed from sufficiently fine observations for SPY US Equity inherits the same scaling exponent after lower-order noise correction: E[RV_\u0394] = a_0 + a_1 \u0394^{2H} + o(\u0394^{2H}).",
  "metadata": {
    "query": "Refine the SPY-volatility linkage theorem for SPY US Equity and VIX3M Index. Replace generic structural language with a sharper theorem candidate about spot-volatility coupling, roughness transmission, regime dependence, or term-structure state. State the core object, the sign or monotonicity prediction if supported, the empirical Bloomberg feature signature, and explicit failure conditions. Avoid generic 'common structural representation' language.",
    "lab_status": null,
    "lab_score": null,
    "selected_status": "research_conjecture",
    "selected_score": 0.695599158569593,
    "promotion_engine": {
      "last_promotion_scan_at": "2026-03-28T00:40:49+00:00",
      "symbolic_pass_rate": 1.0,
      "symbolic_tasks": 5,
      "symbolic_ok": 5,
      "symbolic_fail": 0,
      "source_file": "artifacts\\theorem_refinements\\rough_variance_scaling_identification_theorem_20260328T003323Z.json",
      "rationale": "Theorem passed all symbolic tasks in the latest refinement run and should be promoted above purely empirical candidates."
    }
  },
  "symbolic_pass_rate": 1.0,
  "symbolic_tasks": 5
}
```
### Rough-variance scaling identification theorem
- Score: 0.4294
- Status: speculative_candidate
- Symbolic pass rate: 0.0000
```json
{
  "entry_id": "thm_dea68dae778b423d",
  "title": "Rough-variance scaling identification theorem",
  "status": "speculative_candidate",
  "native_score": 0.5016696213563169,
  "updated_at": "2026-03-27T23:01:04+00:00",
  "securities": [
    "SPY US Equity"
  ],
  "statement_head": "Conjecture: Assume the latent log-volatility process X admits a Volterra representation X_t = X_0 + \u222b_0^t K(t,s) dW_s with local kernel singularity K(t,s) ~ c (t-s)^{H-1/2} for H in (0,1/2). Then, as \u0394 \u2193 0, the increment variance satisfies E[(X_{t+\u0394}-X_t)^2] = C_X \u0394^{2H} + o(\u0394^{2H}), and any realized-variance proxy constructed from sufficiently fine observations for SPY US Equity inherits the same scaling exponent after lower-order noise correction: E[RV_\u0394] = a_0 + a_1 \u0394^{2H} + o(\u0394^{2H}).",
  "metadata": {
    "query": "Propose a theorem linking rough-volatility roughness to realized variance scaling for SPY US Equity.",
    "lab_status": null,
    "lab_score": null,
    "selected_status": "speculative_candidate",
    "selected_score": 0.5016696213563169
  },
  "symbolic_pass_rate": 0.0,
  "symbolic_tasks": 0
}
```
### Rough-variance scaling identification theorem
- Score: 0.4294
- Status: speculative_candidate
- Symbolic pass rate: 0.0000
```json
{
  "entry_id": "thm_90499b839a094ab4",
  "title": "Rough-variance scaling identification theorem",
  "status": "speculative_candidate",
  "native_score": 0.5016696213563169,
  "updated_at": "2026-03-27T18:50:24+00:00",
  "securities": [
    "SPY US Equity"
  ],
  "statement_head": "Conjecture: Assume the latent log-volatility process X admits a Volterra representation X_t = X_0 + \u222b_0^t K(t,s) dW_s with local kernel singularity K(t,s) ~ c (t-s)^{H-1/2} for H in (0,1/2). Then, as \u0394 \u2193 0, the increment variance satisfies E[(X_{t+\u0394}-X_t)^2] = C_X \u0394^{2H} + o(\u0394^{2H}), and any realized-variance proxy constructed from sufficiently fine observations for SPY US Equity inherits the same scaling exponent after lower-order noise correction: E[RV_\u0394] = a_0 + a_1 \u0394^{2H} + o(\u0394^{2H}).",
  "metadata": {
    "query": "Propose a theorem linking rough-volatility roughness to realized variance scaling for SPY.",
    "lab_status": null,
    "lab_score": null,
    "selected_status": "speculative_candidate",
    "selected_score": 0.5016696213563169
  },
  "symbolic_pass_rate": 0.0,
  "symbolic_tasks": 0
}
```
### Evidence-anchored structural conjecture
- Score: 0.4166
- Status: speculative_candidate
- Symbolic pass rate: 0.0000
```json
{
  "entry_id": "thm_91145bf65d5d4f7f",
  "title": "Evidence-anchored structural conjecture",
  "status": "speculative_candidate",
  "native_score": 0.44364050249892173,
  "updated_at": "2026-03-27T23:05:41+00:00",
  "securities": [
    "SPY US Equity",
    "VIX3M Index"
  ],
  "statement_head": "Conjecture: the objects propose, theorem, linking admit a common structural representation in the general_quant family, and the dominant terms in that representation are exactly those that remain stable across the top retrieved excerpts and the empirical feature panel.",
  "metadata": {
    "query": "Propose a theorem linking SPY US Equity and VIX3M Index through spot-volatility coupling, realized variance scaling, and regime transitions.",
    "lab_status": null,
    "lab_score": null,
    "selected_status": "speculative_candidate",
    "selected_score": 0.44364050249892173
  },
  "symbolic_pass_rate": 0.0,
  "symbolic_tasks": 0
}
```
### Evidence-anchored structural conjecture
- Score: 0.4166
- Status: speculative_candidate
- Symbolic pass rate: 0.0000
```json
{
  "entry_id": "thm_70b866f563ec43d4",
  "title": "Evidence-anchored structural conjecture",
  "status": "speculative_candidate",
  "native_score": 0.44364050249892173,
  "updated_at": "2026-03-27T23:04:23+00:00",
  "securities": [
    "SPY US Equity",
    "VIX Index"
  ],
  "statement_head": "Conjecture: the objects propose, theorem, linking admit a common structural representation in the general_quant family, and the dominant terms in that representation are exactly those that remain stable across the top retrieved excerpts and the empirical feature panel.",
  "metadata": {
    "query": "Propose a theorem linking SPY US Equity and VIX Index through spot-volatility coupling, realized variance scaling, and regime transitions.",
    "lab_status": null,
    "lab_score": null,
    "selected_status": "speculative_candidate",
    "selected_score": 0.44364050249892173
  },
  "symbolic_pass_rate": 0.0,
  "symbolic_tasks": 0
}
```
### Evidence-anchored structural conjecture
- Score: 0.4166
- Status: speculative_candidate
- Symbolic pass rate: 0.0000
```json
{
  "entry_id": "thm_04146b78e2eb455e",
  "title": "Evidence-anchored structural conjecture",
  "status": "speculative_candidate",
  "native_score": 0.44364050249892173,
  "updated_at": "2026-03-27T23:02:59+00:00",
  "securities": [
    "SPY US Equity",
    "SPX Index"
  ],
  "statement_head": "Conjecture: the objects propose, theorem, linking admit a common structural representation in the general_quant family, and the dominant terms in that representation are exactly those that remain stable across the top retrieved excerpts and the empirical feature panel.",
  "metadata": {
    "query": "Propose a theorem linking SPY US Equity and SPX Index through spot-volatility coupling, realized variance scaling, and regime transitions.",
    "lab_status": null,
    "lab_score": null,
    "selected_status": "speculative_candidate",
    "selected_score": 0.44364050249892173
  },
  "symbolic_pass_rate": 0.0,
  "symbolic_tasks": 0
}
```
### Evidence-anchored structural conjecture
- Score: 0.4166
- Status: speculative_candidate
- Symbolic pass rate: 0.0000
```json
{
  "entry_id": "thm_dc1dc81df5c14018",
  "title": "Evidence-anchored structural conjecture",
  "status": "speculative_candidate",
  "native_score": 0.44364050249892173,
  "updated_at": "2026-03-27T21:46:39+00:00",
  "securities": [
    "SPY US Equity",
    "QQQ US Equity"
  ],
  "statement_head": "Conjecture: the objects retrieve, spy, qqq admit a common structural representation in the general_quant family, and the dominant terms in that representation are exactly those that remain stable across the top retrieved excerpts and the empirical feature panel.",
  "metadata": {
    "query": "Retrieve the SPY and QQQ spread over the last 60 minutes and compute the maximum likelihood estimation for the OU mean-reversion speed kappa.",
    "lab_status": null,
    "lab_score": null,
    "selected_status": "speculative_candidate",
    "selected_score": 0.44364050249892173
  },
  "symbolic_pass_rate": 0.0,
  "symbolic_tasks": 0
}
```
### Rough-variance scaling identification theorem
- Score: 0.3850
- Status: research_conjecture
- Symbolic pass rate: 0.0000
```json
{
  "entry_id": "thm_5152791914164fbf",
  "title": "Rough-variance scaling identification theorem",
  "status": "research_conjecture",
  "native_score": 0.695599158569593,
  "updated_at": "2026-03-27T23:56:39+00:00",
  "securities": [
    "SPY US Equity",
    "QQQ US Equity"
  ],
  "statement_head": "Conjecture: Assume the latent log-volatility process X admits a Volterra representation X_t = X_0 + \u222b_0^t K(t,s) dW_s with local kernel singularity K(t,s) ~ c (t-s)^{H-1/2} for H in (0,1/2). Then, as \u0394 \u2193 0, the increment variance satisfies E[(X_{t+\u0394}-X_t)^2] = C_X \u0394^{2H} + o(\u0394^{2H}), and any realized-variance proxy constructed from sufficiently fine observations for SPY US Equity inherits the same scaling exponent after lower-order noise correction: E[RV_\u0394] = a_0 + a_1 \u0394^{2H} + o(\u0394^{2H}).",
  "metadata": {
    "query": "Refine the SPY-volatility linkage theorem for SPY US Equity and QQQ US Equity. Replace generic structural language with a sharper theorem candidate about spot-volatility coupling, roughness transmission, regime dependence, or term-structure state. State the core object, the sign or monotonicity prediction if supported, the empirical Bloomberg feature signature, and explicit failure conditions. Avoid generic 'common structural representation' language.",
    "lab_status": null,
    "lab_score": null,
    "selected_status": "research_conjecture",
    "selected_score": 0.695599158569593
  },
  "symbolic_pass_rate": 0.0,
  "symbolic_tasks": 0
}
```
### Rough-variance scaling identification theorem
- Score: 0.3850
- Status: research_conjecture
- Symbolic pass rate: 0.0000
```json
{
  "entry_id": "thm_cb97efb64d7f43e4",
  "title": "Rough-variance scaling identification theorem",
  "status": "research_conjecture",
  "native_score": 0.695599158569593,
  "updated_at": "2026-03-27T23:54:30+00:00",
  "securities": [
    "SPY US Equity",
    "SPX Index"
  ],
  "statement_head": "Conjecture: Assume the latent log-volatility process X admits a Volterra representation X_t = X_0 + \u222b_0^t K(t,s) dW_s with local kernel singularity K(t,s) ~ c (t-s)^{H-1/2} for H in (0,1/2). Then, as \u0394 \u2193 0, the increment variance satisfies E[(X_{t+\u0394}-X_t)^2] = C_X \u0394^{2H} + o(\u0394^{2H}), and any realized-variance proxy constructed from sufficiently fine observations for SPY US Equity inherits the same scaling exponent after lower-order noise correction: E[RV_\u0394] = a_0 + a_1 \u0394^{2H} + o(\u0394^{2H}).",
  "metadata": {
    "query": "Refine the SPY-volatility linkage theorem for SPY US Equity and SPX Index. Replace generic structural language with a sharper theorem candidate about spot-volatility coupling, roughness transmission, regime dependence, or term-structure state. State the core object, the sign or monotonicity prediction if supported, the empirical Bloomberg feature signature, and explicit failure conditions. Avoid generic 'common structural representation' language.",
    "lab_status": null,
    "lab_score": null,
    "selected_status": "research_conjecture",
    "selected_score": 0.695599158569593
  },
  "symbolic_pass_rate": 0.0,
  "symbolic_tasks": 0
}
```
### Rough-variance scaling identification theorem
- Score: 0.3850
- Status: research_conjecture
- Symbolic pass rate: 0.0000
```json
{
  "entry_id": "thm_396990ccdc8c4941",
  "title": "Rough-variance scaling identification theorem",
  "status": "research_conjecture",
  "native_score": 0.695599158569593,
  "updated_at": "2026-03-27T23:52:35+00:00",
  "securities": [
    "SPY US Equity",
    "VIX Index"
  ],
  "statement_head": "Conjecture: Assume the latent log-volatility process X admits a Volterra representation X_t = X_0 + \u222b_0^t K(t,s) dW_s with local kernel singularity K(t,s) ~ c (t-s)^{H-1/2} for H in (0,1/2). Then, as \u0394 \u2193 0, the increment variance satisfies E[(X_{t+\u0394}-X_t)^2] = C_X \u0394^{2H} + o(\u0394^{2H}), and any realized-variance proxy constructed from sufficiently fine observations for SPY US Equity inherits the same scaling exponent after lower-order noise correction: E[RV_\u0394] = a_0 + a_1 \u0394^{2H} + o(\u0394^{2H}).",
  "metadata": {
    "query": "Refine the SPY-volatility linkage theorem for SPY US Equity and VIX Index. Replace generic structural language with a sharper theorem candidate about spot-volatility coupling, roughness transmission, regime dependence, or term-structure state. State the core object, the sign or monotonicity prediction if supported, the empirical Bloomberg feature signature, and explicit failure conditions. Avoid generic 'common structural representation' language.",
    "lab_status": null,
    "lab_score": null,
    "selected_status": "research_conjecture",
    "selected_score": 0.695599158569593
  },
  "symbolic_pass_rate": 0.0,
  "symbolic_tasks": 0
}
```

## Top runs
### refresh_spy_volatility_universe_spy_us_equity_spx_index_spy_vix_linkage
- Score: 0.9000
```json
{
  "task_name": "refresh_spy_volatility_universe_spy_us_equity_spx_index_spy_vix_linkage",
  "securities": [
    "SPY US Equity",
    "SPX Index"
  ],
  "core_query": "Propose a theorem linking SPY US Equity and SPX Index through spot-volatility coupling, realized variance scaling, and regime transitions.",
  "summary": {
    "task_name": "refresh_spy_volatility_universe_spy_us_equity_spx_index_spy_vix_linkage",
    "securities": [
      "SPY US Equity",
      "SPX Index"
    ],
    "coverage_ok": true,
    "evidence_ok": true,
    "theorem_ok": true,
    "market_memory_ok": true,
    "market_calibration_ok": true,
    "market_live_snapshot_ok": false,
    "selected_theorem_title": "Evidence-anchored structural conjecture",
    "theorem_registry": {
      "action": "existing",
      "entry_id": "thm_04146b78e2eb455e",
      "artifact_hash": "1e4d587632ce67e7f9c4b15486c8399b82fbbcff38828be41d9505a925a9913f",
      "status": "speculative_candidate",
      "title": "Evidence-anchored structural conjecture"
    }
  },
  "warnings": [],
  "path": "artifacts\\universe_research_runs\\refresh_spy_volatility_universe_spy_us_equity_spx_index_spy_vix_linkage.json",
  "requested_summary_flags": [
    "evidence_ok",
    "theorem_ok",
    "market_memory_ok",
    "market_calibration_ok"
  ],
  "task": {
    "name": "refresh_spy_volatility_universe_spy_us_equity_spx_index_spy_vix_linkage",
    "core_query": "Propose a theorem linking SPY US Equity and SPX Index through spot-volatility coupling, realized variance scaling, and regime transitions.",
    "securities": [
      "SPY US Equity",
      "SPX Index"
    ],
    "benchmark_security": "SPY US Equity",
    "include_evidence": true,
    "include_theorem": true,
    "include_market_memory": true,
    "include_market_calibration": true,
    "include_market_live_snapshot": false,
    "include_formal_export": false,
    "acceptance_score": 0.82
  }
}
```
### refresh_spy_volatility_universe_spy_us_equity_vix3m_index_spy_vix_linkage
- Score: 0.9000
```json
{
  "task_name": "refresh_spy_volatility_universe_spy_us_equity_vix3m_index_spy_vix_linkage",
  "securities": [
    "SPY US Equity",
    "VIX3M Index"
  ],
  "core_query": "Propose a theorem linking SPY US Equity and VIX3M Index through spot-volatility coupling, realized variance scaling, and regime transitions.",
  "summary": {
    "task_name": "refresh_spy_volatility_universe_spy_us_equity_vix3m_index_spy_vix_linkage",
    "securities": [
      "SPY US Equity",
      "VIX3M Index"
    ],
    "coverage_ok": true,
    "evidence_ok": true,
    "theorem_ok": true,
    "market_memory_ok": true,
    "market_calibration_ok": true,
    "market_live_snapshot_ok": false,
    "selected_theorem_title": "Evidence-anchored structural conjecture",
    "theorem_registry": {
      "action": "existing",
      "entry_id": "thm_91145bf65d5d4f7f",
      "artifact_hash": "de9a223c8aab0ac055d518e65d5e5e4c6d5c21a3cc0daeb40f6f249ef687c12e",
      "status": "speculative_candidate",
      "title": "Evidence-anchored structural conjecture"
    }
  },
  "warnings": [],
  "path": "artifacts\\universe_research_runs\\refresh_spy_volatility_universe_spy_us_equity_vix3m_index_spy_vix_linkage.json",
  "requested_summary_flags": [
    "evidence_ok",
    "theorem_ok",
    "market_memory_ok",
    "market_calibration_ok"
  ],
  "task": {
    "name": "refresh_spy_volatility_universe_spy_us_equity_vix3m_index_spy_vix_linkage",
    "core_query": "Propose a theorem linking SPY US Equity and VIX3M Index through spot-volatility coupling, realized variance scaling, and regime transitions.",
    "securities": [
      "SPY US Equity",
      "VIX3M Index"
    ],
    "benchmark_security": "SPY US Equity",
    "include_evidence": true,
    "include_theorem": true,
    "include_market_memory": true,
    "include_market_calibration": true,
    "include_market_live_snapshot": false,
    "include_formal_export": false,
    "acceptance_score": 0.82
  }
}
```
### refresh_spy_volatility_universe_spy_us_equity_vix_index_spy_vix_linkage
- Score: 0.9000
```json
{
  "task_name": "refresh_spy_volatility_universe_spy_us_equity_vix_index_spy_vix_linkage",
  "securities": [
    "SPY US Equity",
    "VIX Index"
  ],
  "core_query": "Propose a theorem linking SPY US Equity and VIX Index through spot-volatility coupling, realized variance scaling, and regime transitions.",
  "summary": {
    "task_name": "refresh_spy_volatility_universe_spy_us_equity_vix_index_spy_vix_linkage",
    "securities": [
      "SPY US Equity",
      "VIX Index"
    ],
    "coverage_ok": true,
    "evidence_ok": true,
    "theorem_ok": true,
    "market_memory_ok": true,
    "market_calibration_ok": true,
    "market_live_snapshot_ok": false,
    "selected_theorem_title": "Evidence-anchored structural conjecture",
    "theorem_registry": {
      "action": "existing",
      "entry_id": "thm_70b866f563ec43d4",
      "artifact_hash": "fd3f6d986bb71ccc004bcbd72664a31bf69f2635522c7212030d5e6dd7b51b3a",
      "status": "speculative_candidate",
      "title": "Evidence-anchored structural conjecture"
    }
  },
  "warnings": [],
  "path": "artifacts\\universe_research_runs\\refresh_spy_volatility_universe_spy_us_equity_vix_index_spy_vix_linkage.json",
  "requested_summary_flags": [
    "evidence_ok",
    "theorem_ok",
    "market_memory_ok",
    "market_calibration_ok"
  ],
  "task": {
    "name": "refresh_spy_volatility_universe_spy_us_equity_vix_index_spy_vix_linkage",
    "core_query": "Propose a theorem linking SPY US Equity and VIX Index through spot-volatility coupling, realized variance scaling, and regime transitions.",
    "securities": [
      "SPY US Equity",
      "VIX Index"
    ],
    "benchmark_security": "SPY US Equity",
    "include_evidence": true,
    "include_theorem": true,
    "include_market_memory": true,
    "include_market_calibration": true,
    "include_market_live_snapshot": false,
    "include_formal_export": false,
    "acceptance_score": 0.82
  }
}
```
### refresh_spy_volatility_universe_skew_index_spy_roughness_scaling
- Score: 0.7500
```json
{
  "task_name": "refresh_spy_volatility_universe_skew_index_spy_roughness_scaling",
  "securities": [
    "SKEW Index"
  ],
  "core_query": "Propose a theorem linking rough-volatility roughness to realized variance scaling for SKEW Index.",
  "summary": {
    "task_name": "refresh_spy_volatility_universe_skew_index_spy_roughness_scaling",
    "securities": [
      "SKEW Index"
    ],
    "coverage_ok": true,
    "evidence_ok": true,
    "theorem_ok": true,
    "market_memory_ok": true,
    "market_calibration_ok": false,
    "market_live_snapshot_ok": false,
    "selected_theorem_title": "Rough-variance scaling identification theorem",
    "theorem_registry": {
      "action": "existing",
      "entry_id": "thm_47fcbcb7cf68433a",
      "artifact_hash": "350c3cb580e30954e4c6f745fd28574f9d79c12cf6387d40007af17072ba46a6",
      "status": "unverified_hypothesis",
      "title": "Rough-variance scaling identification theorem"
    }
  },
  "warnings": [],
  "path": "artifacts\\universe_research_runs\\refresh_spy_volatility_universe_skew_index_spy_roughness_scaling.json",
  "requested_summary_flags": [
    "evidence_ok",
    "theorem_ok",
    "market_memory_ok"
  ],
  "task": {
    "name": "refresh_spy_volatility_universe_skew_index_spy_roughness_scaling",
    "core_query": "Propose a theorem linking rough-volatility roughness to realized variance scaling for SKEW Index.",
    "securities": [
      "SKEW Index"
    ],
    "benchmark_security": "SPY US Equity",
    "include_evidence": true,
    "include_theorem": true,
    "include_market_memory": true,
    "include_market_calibration": false,
    "include_market_live_snapshot": false,
    "include_formal_export": false,
    "acceptance_score": 0.82
  }
}
```
### refresh_spy_volatility_universe_spx_index_spy_roughness_scaling
- Score: 0.7500
```json
{
  "task_name": "refresh_spy_volatility_universe_spx_index_spy_roughness_scaling",
  "securities": [
    "SPX Index"
  ],
  "core_query": "Propose a theorem linking rough-volatility roughness to realized variance scaling for SPX Index.",
  "summary": {
    "task_name": "refresh_spy_volatility_universe_spx_index_spy_roughness_scaling",
    "securities": [
      "SPX Index"
    ],
    "coverage_ok": true,
    "evidence_ok": true,
    "theorem_ok": true,
    "market_memory_ok": true,
    "market_calibration_ok": false,
    "market_live_snapshot_ok": false,
    "selected_theorem_title": "Rough-variance scaling identification theorem",
    "theorem_registry": {
      "action": "existing",
      "entry_id": "thm_edcb119573d44012",
      "artifact_hash": "e7f929f2313d4f2c4ec69f1f9938815ce9497f03388e0341170c1c9dacbcbb39",
      "status": "unverified_hypothesis",
      "title": "Rough-variance scaling identification theorem"
    }
  },
  "warnings": [],
  "path": "artifacts\\universe_research_runs\\refresh_spy_volatility_universe_spx_index_spy_roughness_scaling.json",
  "requested_summary_flags": [
    "evidence_ok",
    "theorem_ok",
    "market_memory_ok"
  ],
  "task": {
    "name": "refresh_spy_volatility_universe_spx_index_spy_roughness_scaling",
    "core_query": "Propose a theorem linking rough-volatility roughness to realized variance scaling for SPX Index.",
    "securities": [
      "SPX Index"
    ],
    "benchmark_security": "SPY US Equity",
    "include_evidence": true,
    "include_theorem": true,
    "include_market_memory": true,
    "include_market_calibration": false,
    "include_market_live_snapshot": false,
    "include_formal_export": false,
    "acceptance_score": 0.82
  }
}
```
### spy_volatility_universe_spy_us_equity_spy_roughness_scaling
- Score: 0.7500
```json
{
  "task_name": "spy_volatility_universe_spy_us_equity_spy_roughness_scaling",
  "securities": [
    "SPY US Equity"
  ],
  "core_query": "Propose a theorem linking rough-volatility roughness to realized variance scaling for SPY US Equity.",
  "summary": {
    "task_name": "spy_volatility_universe_spy_us_equity_spy_roughness_scaling",
    "securities": [
      "SPY US Equity"
    ],
    "coverage_ok": true,
    "evidence_ok": true,
    "theorem_ok": true,
    "market_memory_ok": true,
    "market_calibration_ok": false,
    "market_live_snapshot_ok": false,
    "selected_theorem_title": "Rough-variance scaling identification theorem",
    "theorem_registry": {
      "action": "inserted",
      "entry_id": "thm_dea68dae778b423d",
      "artifact_hash": "14b0cb4f1415b71a2f6ff53b3b09f10d3aa0af1003d6dd65d319ad36f3625f80",
      "status": "speculative_candidate",
      "title": "Rough-variance scaling identification theorem"
    }
  },
  "warnings": [],
  "path": "artifacts\\universe_research_runs\\spy_volatility_universe_spy_us_equity_spy_roughness_scaling.json",
  "requested_summary_flags": [
    "evidence_ok",
    "theorem_ok",
    "market_memory_ok"
  ],
  "task": {
    "name": "spy_volatility_universe_spy_us_equity_spy_roughness_scaling",
    "core_query": "Propose a theorem linking rough-volatility roughness to realized variance scaling for SPY US Equity.",
    "securities": [
      "SPY US Equity"
    ],
    "benchmark_security": "SPY US Equity",
    "include_evidence": true,
    "include_theorem": true,
    "include_market_memory": true,
    "include_market_calibration": false,
    "include_market_live_snapshot": false,
    "include_formal_export": false,
    "acceptance_score": 0.8
  }
}
```
### spy_volatility_universe_spy_us_equity_spx_index_spy_vix_linkage
- Score: 0.5600
```json
{
  "task_name": "spy_volatility_universe_spy_us_equity_spx_index_spy_vix_linkage",
  "securities": [
    "SPY US Equity",
    "SPX Index"
  ],
  "core_query": "Propose a theorem linking SPY US Equity and SPX Index through spot-volatility coupling, realized variance scaling, and regime transitions.",
  "summary": {
    "task_name": "spy_volatility_universe_spy_us_equity_spx_index_spy_vix_linkage",
    "securities": [
      "SPY US Equity",
      "SPX Index"
    ],
    "coverage_ok": false,
    "evidence_ok": true,
    "theorem_ok": true,
    "market_memory_ok": true,
    "market_calibration_ok": true,
    "market_live_snapshot_ok": false,
    "selected_theorem_title": "Evidence-anchored structural conjecture",
    "theorem_registry": {
      "action": "inserted",
      "entry_id": "thm_04146b78e2eb455e",
      "artifact_hash": "1e4d587632ce67e7f9c4b15486c8399b82fbbcff38828be41d9505a925a9913f",
      "status": "speculative_candidate",
      "title": "Evidence-anchored structural conjecture"
    }
  },
  "warnings": [
    "SPX Index: no rows in bloomberg_daily_history.",
    "SPX Index: no rows in bloomberg_daily_features.",
    "SPX Index: no rows in bloomberg_research_memory."
  ],
  "path": "artifacts\\universe_research_runs\\spy_volatility_universe_spy_us_equity_spx_index_spy_vix_linkage.json",
  "requested_summary_flags": [
    "evidence_ok",
    "theorem_ok",
    "market_memory_ok",
    "market_calibration_ok"
  ],
  "task": {
    "name": "spy_volatility_universe_spy_us_equity_spx_index_spy_vix_linkage",
    "core_query": "Propose a theorem linking SPY US Equity and SPX Index through spot-volatility coupling, realized variance scaling, and regime transitions.",
    "securities": [
      "SPY US Equity",
      "SPX Index"
    ],
    "benchmark_security": "SPY US Equity",
    "include_evidence": true,
    "include_theorem": true,
    "include_market_memory": true,
    "include_market_calibration": true,
    "include_market_live_snapshot": false,
    "include_formal_export": false,
    "acceptance_score": 0.83
  }
}
```
### spy_volatility_universe_spy_us_equity_vix3m_index_spy_vix_linkage
- Score: 0.5600
```json
{
  "task_name": "spy_volatility_universe_spy_us_equity_vix3m_index_spy_vix_linkage",
  "securities": [
    "SPY US Equity",
    "VIX3M Index"
  ],
  "core_query": "Propose a theorem linking SPY US Equity and VIX3M Index through spot-volatility coupling, realized variance scaling, and regime transitions.",
  "summary": {
    "task_name": "spy_volatility_universe_spy_us_equity_vix3m_index_spy_vix_linkage",
    "securities": [
      "SPY US Equity",
      "VIX3M Index"
    ],
    "coverage_ok": false,
    "evidence_ok": true,
    "theorem_ok": true,
    "market_memory_ok": true,
    "market_calibration_ok": true,
    "market_live_snapshot_ok": false,
    "selected_theorem_title": "Evidence-anchored structural conjecture",
    "theorem_registry": {
      "action": "inserted",
      "entry_id": "thm_91145bf65d5d4f7f",
      "artifact_hash": "de9a223c8aab0ac055d518e65d5e5e4c6d5c21a3cc0daeb40f6f249ef687c12e",
      "status": "speculative_candidate",
      "title": "Evidence-anchored structural conjecture"
    }
  },
  "warnings": [
    "VIX3M Index: no rows in bloomberg_daily_history.",
    "VIX3M Index: no rows in bloomberg_daily_features.",
    "VIX3M Index: no rows in bloomberg_research_memory."
  ],
  "path": "artifacts\\universe_research_runs\\spy_volatility_universe_spy_us_equity_vix3m_index_spy_vix_linkage.json",
  "requested_summary_flags": [
    "evidence_ok",
    "theorem_ok",
    "market_memory_ok",
    "market_calibration_ok"
  ],
  "task": {
    "name": "spy_volatility_universe_spy_us_equity_vix3m_index_spy_vix_linkage",
    "core_query": "Propose a theorem linking SPY US Equity and VIX3M Index through spot-volatility coupling, realized variance scaling, and regime transitions.",
    "securities": [
      "SPY US Equity",
      "VIX3M Index"
    ],
    "benchmark_security": "SPY US Equity",
    "include_evidence": true,
    "include_theorem": true,
    "include_market_memory": true,
    "include_market_calibration": true,
    "include_market_live_snapshot": false,
    "include_formal_export": false,
    "acceptance_score": 0.83
  }
}
```
### spy_volatility_universe_spy_us_equity_vix_index_spy_vix_linkage
- Score: 0.5600
```json
{
  "task_name": "spy_volatility_universe_spy_us_equity_vix_index_spy_vix_linkage",
  "securities": [
    "SPY US Equity",
    "VIX Index"
  ],
  "core_query": "Propose a theorem linking SPY US Equity and VIX Index through spot-volatility coupling, realized variance scaling, and regime transitions.",
  "summary": {
    "task_name": "spy_volatility_universe_spy_us_equity_vix_index_spy_vix_linkage",
    "securities": [
      "SPY US Equity",
      "VIX Index"
    ],
    "coverage_ok": false,
    "evidence_ok": true,
    "theorem_ok": true,
    "market_memory_ok": true,
    "market_calibration_ok": true,
    "market_live_snapshot_ok": false,
    "selected_theorem_title": "Evidence-anchored structural conjecture",
    "theorem_registry": {
      "action": "inserted",
      "entry_id": "thm_70b866f563ec43d4",
      "artifact_hash": "fd3f6d986bb71ccc004bcbd72664a31bf69f2635522c7212030d5e6dd7b51b3a",
      "status": "speculative_candidate",
      "title": "Evidence-anchored structural conjecture"
    }
  },
  "warnings": [
    "VIX Index: no rows in bloomberg_daily_history.",
    "VIX Index: no rows in bloomberg_daily_features.",
    "VIX Index: no rows in bloomberg_research_memory."
  ],
  "path": "artifacts\\universe_research_runs\\spy_volatility_universe_spy_us_equity_vix_index_spy_vix_linkage.json",
  "requested_summary_flags": [
    "evidence_ok",
    "theorem_ok",
    "market_memory_ok",
    "market_calibration_ok"
  ],
  "task": {
    "name": "spy_volatility_universe_spy_us_equity_vix_index_spy_vix_linkage",
    "core_query": "Propose a theorem linking SPY US Equity and VIX Index through spot-volatility coupling, realized variance scaling, and regime transitions.",
    "securities": [
      "SPY US Equity",
      "VIX Index"
    ],
    "benchmark_security": "SPY US Equity",
    "include_evidence": true,
    "include_theorem": true,
    "include_market_memory": true,
    "include_market_calibration": true,
    "include_market_live_snapshot": false,
    "include_formal_export": false,
    "acceptance_score": 0.83
  }
}
```
### spy_volatility_universe_skew_index_spy_roughness_scaling
- Score: 0.4100
```json
{
  "task_name": "spy_volatility_universe_skew_index_spy_roughness_scaling",
  "securities": [
    "SKEW Index"
  ],
  "core_query": "Propose a theorem linking rough-volatility roughness to realized variance scaling for SKEW Index.",
  "summary": {
    "task_name": "spy_volatility_universe_skew_index_spy_roughness_scaling",
    "securities": [
      "SKEW Index"
    ],
    "coverage_ok": false,
    "evidence_ok": true,
    "theorem_ok": true,
    "market_memory_ok": true,
    "market_calibration_ok": false,
    "market_live_snapshot_ok": false,
    "selected_theorem_title": "Rough-variance scaling identification theorem",
    "theorem_registry": {
      "action": "inserted",
      "entry_id": "thm_47fcbcb7cf68433a",
      "artifact_hash": "350c3cb580e30954e4c6f745fd28574f9d79c12cf6387d40007af17072ba46a6",
      "status": "unverified_hypothesis",
      "title": "Rough-variance scaling identification theorem"
    }
  },
  "warnings": [
    "SKEW Index: no rows in bloomberg_daily_history.",
    "SKEW Index: no rows in bloomberg_daily_features.",
    "SKEW Index: no rows in bloomberg_research_memory."
  ],
  "path": "artifacts\\universe_research_runs\\spy_volatility_universe_skew_index_spy_roughness_scaling.json",
  "requested_summary_flags": [
    "evidence_ok",
    "theorem_ok",
    "market_memory_ok"
  ],
  "task": {
    "name": "spy_volatility_universe_skew_index_spy_roughness_scaling",
    "core_query": "Propose a theorem linking rough-volatility roughness to realized variance scaling for SKEW Index.",
    "securities": [
      "SKEW Index"
    ],
    "benchmark_security": "SPY US Equity",
    "include_evidence": true,
    "include_theorem": true,
    "include_market_memory": true,
    "include_market_calibration": false,
    "include_market_live_snapshot": false,
    "include_formal_export": false,
    "acceptance_score": 0.8
  }
}
```

## Weak lanes
### spy_volatility_universe_spy_us_equity_spx_index_spy_vix_linkage
- Penalty: 2.5000
```json
{
  "failed_flags": [
    "coverage_ok"
  ],
  "warnings": [
    "SPX Index: no rows in bloomberg_daily_history.",
    "SPX Index: no rows in bloomberg_daily_features.",
    "SPX Index: no rows in bloomberg_research_memory."
  ],
  "warnings_stale_coverage": true,
  "securities": [
    "SPY US Equity",
    "SPX Index"
  ],
  "path": "artifacts\\universe_research_runs\\spy_volatility_universe_spy_us_equity_spx_index_spy_vix_linkage.json",
  "requested_summary_flags": [
    "evidence_ok",
    "theorem_ok",
    "market_memory_ok",
    "market_calibration_ok"
  ]
}
```
### spy_volatility_universe_spy_us_equity_vix3m_index_spy_vix_linkage
- Penalty: 2.5000
```json
{
  "failed_flags": [
    "coverage_ok"
  ],
  "warnings": [
    "VIX3M Index: no rows in bloomberg_daily_history.",
    "VIX3M Index: no rows in bloomberg_daily_features.",
    "VIX3M Index: no rows in bloomberg_research_memory."
  ],
  "warnings_stale_coverage": true,
  "securities": [
    "SPY US Equity",
    "VIX3M Index"
  ],
  "path": "artifacts\\universe_research_runs\\spy_volatility_universe_spy_us_equity_vix3m_index_spy_vix_linkage.json",
  "requested_summary_flags": [
    "evidence_ok",
    "theorem_ok",
    "market_memory_ok",
    "market_calibration_ok"
  ]
}
```
### spy_volatility_universe_spy_us_equity_vix_index_spy_vix_linkage
- Penalty: 2.5000
```json
{
  "failed_flags": [
    "coverage_ok"
  ],
  "warnings": [
    "VIX Index: no rows in bloomberg_daily_history.",
    "VIX Index: no rows in bloomberg_daily_features.",
    "VIX Index: no rows in bloomberg_research_memory."
  ],
  "warnings_stale_coverage": true,
  "securities": [
    "SPY US Equity",
    "VIX Index"
  ],
  "path": "artifacts\\universe_research_runs\\spy_volatility_universe_spy_us_equity_vix_index_spy_vix_linkage.json",
  "requested_summary_flags": [
    "evidence_ok",
    "theorem_ok",
    "market_memory_ok",
    "market_calibration_ok"
  ]
}
```
### spy_volatility_universe_skew_index_spy_roughness_scaling
- Penalty: 2.5000
```json
{
  "failed_flags": [
    "coverage_ok"
  ],
  "warnings": [
    "SKEW Index: no rows in bloomberg_daily_history.",
    "SKEW Index: no rows in bloomberg_daily_features.",
    "SKEW Index: no rows in bloomberg_research_memory."
  ],
  "warnings_stale_coverage": true,
  "securities": [
    "SKEW Index"
  ],
  "path": "artifacts\\universe_research_runs\\spy_volatility_universe_skew_index_spy_roughness_scaling.json",
  "requested_summary_flags": [
    "evidence_ok",
    "theorem_ok",
    "market_memory_ok"
  ]
}
```
### spy_volatility_universe_spx_index_spy_roughness_scaling
- Penalty: 2.5000
```json
{
  "failed_flags": [
    "coverage_ok"
  ],
  "warnings": [
    "SPX Index: no rows in bloomberg_daily_history.",
    "SPX Index: no rows in bloomberg_daily_features.",
    "SPX Index: no rows in bloomberg_research_memory."
  ],
  "warnings_stale_coverage": true,
  "securities": [
    "SPX Index"
  ],
  "path": "artifacts\\universe_research_runs\\spy_volatility_universe_spx_index_spy_roughness_scaling.json",
  "requested_summary_flags": [
    "evidence_ok",
    "theorem_ok",
    "market_memory_ok"
  ]
}
```
### spy_volatility_universe_vix3m_index_spy_roughness_scaling
- Penalty: 2.5000
```json
{
  "failed_flags": [
    "coverage_ok"
  ],
  "warnings": [
    "VIX3M Index: no rows in bloomberg_daily_history.",
    "VIX3M Index: no rows in bloomberg_daily_features.",
    "VIX3M Index: no rows in bloomberg_research_memory."
  ],
  "warnings_stale_coverage": true,
  "securities": [
    "VIX3M Index"
  ],
  "path": "artifacts\\universe_research_runs\\spy_volatility_universe_vix3m_index_spy_roughness_scaling.json",
  "requested_summary_flags": [
    "evidence_ok",
    "theorem_ok",
    "market_memory_ok"
  ]
}
```
### spy_volatility_universe_vix_index_spy_roughness_scaling
- Penalty: 2.5000
```json
{
  "failed_flags": [
    "coverage_ok"
  ],
  "warnings": [
    "VIX Index: no rows in bloomberg_daily_history.",
    "VIX Index: no rows in bloomberg_daily_features.",
    "VIX Index: no rows in bloomberg_research_memory."
  ],
  "warnings_stale_coverage": true,
  "securities": [
    "VIX Index"
  ],
  "path": "artifacts\\universe_research_runs\\spy_volatility_universe_vix_index_spy_roughness_scaling.json",
  "requested_summary_flags": [
    "evidence_ok",
    "theorem_ok",
    "market_memory_ok"
  ]
}
```
### spy_volatility_universe_vvix_index_spy_roughness_scaling
- Penalty: 2.5000
```json
{
  "failed_flags": [
    "coverage_ok"
  ],
  "warnings": [
    "VVIX Index: no rows in bloomberg_daily_history.",
    "VVIX Index: no rows in bloomberg_daily_features.",
    "VVIX Index: no rows in bloomberg_research_memory."
  ],
  "warnings_stale_coverage": true,
  "securities": [
    "VVIX Index"
  ],
  "path": "artifacts\\universe_research_runs\\spy_volatility_universe_vvix_index_spy_roughness_scaling.json",
  "requested_summary_flags": [
    "evidence_ok",
    "theorem_ok",
    "market_memory_ok"
  ]
}
```