# Universe Research Manifest: spy_volatility_universe

- Securities: SPY US Equity, SPX Index, VIX Index, VIX3M Index, VVIX Index, SKEW Index, ES1 Index
- Benchmark: SPY US Equity
- Created at: 2026-03-27T23:02:01+00:00

## Templates
- spy_roughness_scaling: Propose a theorem linking rough-volatility roughness to realized variance scaling for {primary}.
- spy_execution_under_vol_state: Pull the live Bloomberg snapshot for {primary} and formulate the precise Almgren-Chriss liquidating trajectory for 10^5 shares over T=1 hour, conditioning on the current volatility state.
- pair_ou_spread: Retrieve the {primary} and {secondary} spread over the last 60 minutes and compute the maximum likelihood estimation for the OU mean-reversion speed kappa.
- spot_vol_linkage_theorem: Propose a theorem describing the empirical and theoretical linkage between {primary} and {secondary}, emphasizing volatility transmission, roughness, and regime dependence.
- universe_state_summary: Summarize the current Bloomberg empirical memory, roughness signatures, term-structure state, and tail-risk state for {universe_name}.

## Results
### spy_volatility_universe_spy_us_equity_spy_roughness_scaling
- OK: True
- Scope: SPY US Equity
```json
{
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
}
```
- JSON: artifacts\universe_research_runs\spy_volatility_universe_spy_us_equity_spy_roughness_scaling.json
- Markdown: artifacts\universe_research_runs\spy_volatility_universe_spy_us_equity_spy_roughness_scaling.md

### spy_volatility_universe_spx_index_spy_roughness_scaling
- OK: False
- Scope: SPX Index
```json
{
  "task_name": "spy_volatility_universe_spx_index_spy_roughness_scaling",
  "securities": [
    "SPX Index"
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
    "entry_id": "thm_edcb119573d44012",
    "artifact_hash": "e7f929f2313d4f2c4ec69f1f9938815ce9497f03388e0341170c1c9dacbcbb39",
    "status": "unverified_hypothesis",
    "title": "Rough-variance scaling identification theorem"
  }
}
```
Warnings:
- SPX Index: no rows in bloomberg_daily_history.
- SPX Index: no rows in bloomberg_daily_features.
- SPX Index: no rows in bloomberg_research_memory.
- JSON: artifacts\universe_research_runs\spy_volatility_universe_spx_index_spy_roughness_scaling.json
- Markdown: artifacts\universe_research_runs\spy_volatility_universe_spx_index_spy_roughness_scaling.md

### spy_volatility_universe_vix_index_spy_roughness_scaling
- OK: False
- Scope: VIX Index
```json
{
  "task_name": "spy_volatility_universe_vix_index_spy_roughness_scaling",
  "securities": [
    "VIX Index"
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
    "entry_id": "thm_f02eb1ee14c04238",
    "artifact_hash": "4795619efe1241d92d10c4f2932a4dccd6dc5ac74fb8a595d5a88347e7b0667e",
    "status": "unverified_hypothesis",
    "title": "Rough-variance scaling identification theorem"
  }
}
```
Warnings:
- VIX Index: no rows in bloomberg_daily_history.
- VIX Index: no rows in bloomberg_daily_features.
- VIX Index: no rows in bloomberg_research_memory.
- JSON: artifacts\universe_research_runs\spy_volatility_universe_vix_index_spy_roughness_scaling.json
- Markdown: artifacts\universe_research_runs\spy_volatility_universe_vix_index_spy_roughness_scaling.md

### spy_volatility_universe_vix3m_index_spy_roughness_scaling
- OK: False
- Scope: VIX3M Index
```json
{
  "task_name": "spy_volatility_universe_vix3m_index_spy_roughness_scaling",
  "securities": [
    "VIX3M Index"
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
    "entry_id": "thm_e818056ac7c74ce7",
    "artifact_hash": "ad462f735e7fe95154c44adfb0fb9428c93e0e8e577b0ef640a58bc9fb8d8ae4",
    "status": "unverified_hypothesis",
    "title": "Rough-variance scaling identification theorem"
  }
}
```
Warnings:
- VIX3M Index: no rows in bloomberg_daily_history.
- VIX3M Index: no rows in bloomberg_daily_features.
- VIX3M Index: no rows in bloomberg_research_memory.
- JSON: artifacts\universe_research_runs\spy_volatility_universe_vix3m_index_spy_roughness_scaling.json
- Markdown: artifacts\universe_research_runs\spy_volatility_universe_vix3m_index_spy_roughness_scaling.md

### spy_volatility_universe_vvix_index_spy_roughness_scaling
- OK: False
- Scope: VVIX Index
```json
{
  "task_name": "spy_volatility_universe_vvix_index_spy_roughness_scaling",
  "securities": [
    "VVIX Index"
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
    "entry_id": "thm_b4bdbb0eceee4565",
    "artifact_hash": "5be2a87d5d9711264395a3675185bae6d1117ede3a43342a7014cbf74667e26c",
    "status": "unverified_hypothesis",
    "title": "Rough-variance scaling identification theorem"
  }
}
```
Warnings:
- VVIX Index: no rows in bloomberg_daily_history.
- VVIX Index: no rows in bloomberg_daily_features.
- VVIX Index: no rows in bloomberg_research_memory.
- JSON: artifacts\universe_research_runs\spy_volatility_universe_vvix_index_spy_roughness_scaling.json
- Markdown: artifacts\universe_research_runs\spy_volatility_universe_vvix_index_spy_roughness_scaling.md

### spy_volatility_universe_skew_index_spy_roughness_scaling
- OK: False
- Scope: SKEW Index
```json
{
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
}
```
Warnings:
- SKEW Index: no rows in bloomberg_daily_history.
- SKEW Index: no rows in bloomberg_daily_features.
- SKEW Index: no rows in bloomberg_research_memory.
- JSON: artifacts\universe_research_runs\spy_volatility_universe_skew_index_spy_roughness_scaling.json
- Markdown: artifacts\universe_research_runs\spy_volatility_universe_skew_index_spy_roughness_scaling.md
