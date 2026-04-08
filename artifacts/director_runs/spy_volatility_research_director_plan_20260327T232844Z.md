# SPY Volatility Research Director Plan

- Created at: 2026-03-27T23:28:44+00:00

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

## Selected actions
### refresh_spy_volatility_universe_skew_index_spy_roughness_scaling
- Priority: 1
- Category: refresh_stale_lane
- Securities: SKEW Index
- Rationale: This lane was weak in the scoreboard because the original run happened before the SPY/VIX universe was fully backfilled. Coverage is now present, so rerun it.
- Query: Propose a theorem linking rough-volatility roughness to realized variance scaling for SKEW Index.

### refresh_spy_volatility_universe_spx_index_spy_roughness_scaling
- Priority: 1
- Category: refresh_stale_lane
- Securities: SPX Index
- Rationale: This lane was weak in the scoreboard because the original run happened before the SPY/VIX universe was fully backfilled. Coverage is now present, so rerun it.
- Query: Propose a theorem linking rough-volatility roughness to realized variance scaling for SPX Index.

### refresh_spy_volatility_universe_spy_us_equity_spx_index_spy_vix_linkage
- Priority: 1
- Category: refresh_stale_lane
- Securities: SPY US Equity, SPX Index
- Rationale: This lane was weak in the scoreboard because the original run happened before the SPY/VIX universe was fully backfilled. Coverage is now present, so rerun it.
- Query: Propose a theorem linking SPY US Equity and SPX Index through spot-volatility coupling, realized variance scaling, and regime transitions.

### refresh_spy_volatility_universe_spy_us_equity_vix3m_index_spy_vix_linkage
- Priority: 1
- Category: refresh_stale_lane
- Securities: SPY US Equity, VIX3M Index
- Rationale: This lane was weak in the scoreboard because the original run happened before the SPY/VIX universe was fully backfilled. Coverage is now present, so rerun it.
- Query: Propose a theorem linking SPY US Equity and VIX3M Index through spot-volatility coupling, realized variance scaling, and regime transitions.

### refresh_spy_volatility_universe_spy_us_equity_vix_index_spy_vix_linkage
- Priority: 1
- Category: refresh_stale_lane
- Securities: SPY US Equity, VIX Index
- Rationale: This lane was weak in the scoreboard because the original run happened before the SPY/VIX universe was fully backfilled. Coverage is now present, so rerun it.
- Query: Propose a theorem linking SPY US Equity and VIX Index through spot-volatility coupling, realized variance scaling, and regime transitions.

### refresh_spy_volatility_universe_vix3m_index_spy_roughness_scaling
- Priority: 1
- Category: refresh_stale_lane
- Securities: VIX3M Index
- Rationale: This lane was weak in the scoreboard because the original run happened before the SPY/VIX universe was fully backfilled. Coverage is now present, so rerun it.
- Query: Propose a theorem linking rough-volatility roughness to realized variance scaling for VIX3M Index.

### refresh_spy_volatility_universe_vix_index_spy_roughness_scaling
- Priority: 1
- Category: refresh_stale_lane
- Securities: VIX Index
- Rationale: This lane was weak in the scoreboard because the original run happened before the SPY/VIX universe was fully backfilled. Coverage is now present, so rerun it.
- Query: Propose a theorem linking rough-volatility roughness to realized variance scaling for VIX Index.

### refresh_spy_volatility_universe_vvix_index_spy_roughness_scaling
- Priority: 1
- Category: refresh_stale_lane
- Securities: VVIX Index
- Rationale: This lane was weak in the scoreboard because the original run happened before the SPY/VIX universe was fully backfilled. Coverage is now present, so rerun it.
- Query: Propose a theorem linking rough-volatility roughness to realized variance scaling for VVIX Index.
