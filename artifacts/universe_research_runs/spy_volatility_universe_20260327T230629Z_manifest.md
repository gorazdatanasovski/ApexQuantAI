# Universe Research Manifest: spy_volatility_universe

- Securities: SPY US Equity, SPX Index, VIX Index, VIX3M Index, VVIX Index, SKEW Index, ES1 Index
- Benchmark: SPY US Equity
- Created at: 2026-03-27T23:06:29+00:00

## Templates
- spy_vix_linkage: Propose a theorem linking {primary} and {secondary} through spot-volatility coupling, realized variance scaling, and regime transitions.
- vix_vvix_linkage: Propose a theorem linking {primary} and {secondary} through implied volatility, vol-of-vol, and jump-intensity style state dependence.
- spy_vix_term_state: Summarize the empirical state of {primary}, {secondary}, and {universe_name}, with emphasis on roughness, mean reversion, skew, and term structure.

## Results
### spy_volatility_universe_spy_us_equity_spx_index_spy_vix_linkage
- OK: False
- Scope: SPY US Equity, SPX Index
```json
{
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
}
```
Warnings:
- SPX Index: no rows in bloomberg_daily_history.
- SPX Index: no rows in bloomberg_daily_features.
- SPX Index: no rows in bloomberg_research_memory.
- JSON: artifacts\universe_research_runs\spy_volatility_universe_spy_us_equity_spx_index_spy_vix_linkage.json
- Markdown: artifacts\universe_research_runs\spy_volatility_universe_spy_us_equity_spx_index_spy_vix_linkage.md

### spy_volatility_universe_spy_us_equity_vix_index_spy_vix_linkage
- OK: False
- Scope: SPY US Equity, VIX Index
```json
{
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
}
```
Warnings:
- VIX Index: no rows in bloomberg_daily_history.
- VIX Index: no rows in bloomberg_daily_features.
- VIX Index: no rows in bloomberg_research_memory.
- JSON: artifacts\universe_research_runs\spy_volatility_universe_spy_us_equity_vix_index_spy_vix_linkage.json
- Markdown: artifacts\universe_research_runs\spy_volatility_universe_spy_us_equity_vix_index_spy_vix_linkage.md

### spy_volatility_universe_spy_us_equity_vix3m_index_spy_vix_linkage
- OK: False
- Scope: SPY US Equity, VIX3M Index
```json
{
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
}
```
Warnings:
- VIX3M Index: no rows in bloomberg_daily_history.
- VIX3M Index: no rows in bloomberg_daily_features.
- VIX3M Index: no rows in bloomberg_research_memory.
- JSON: artifacts\universe_research_runs\spy_volatility_universe_spy_us_equity_vix3m_index_spy_vix_linkage.json
- Markdown: artifacts\universe_research_runs\spy_volatility_universe_spy_us_equity_vix3m_index_spy_vix_linkage.md
