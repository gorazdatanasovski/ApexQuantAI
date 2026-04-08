# Options Surface Repair: SPX Index

- Created at: 2026-03-28T01:50:40+00:00
- Attempts: 9

## Best attempt
```json
{
  "attempt_name": "SPX Index|type=ALL|max=1500",
  "underlying": "SPX Index",
  "option_type": null,
  "max_contracts": 1500,
  "ok": true,
  "n_chain_rows": 8000,
  "n_snapshot_rows": 1500,
  "n_surface_rows": 1500,
  "n_expiries": 1,
  "option_types_found": [
    "C",
    "P"
  ],
  "diagnostics": {
    "spot": 6368.85,
    "chain_frame_columns": [
      "security",
      "Security Description"
    ],
    "chain_candidates": 1500,
    "rows_chain": 8000,
    "rows_chain_meta": 1500,
    "rows_raw": 1500,
    "rows_surface": 1500,
    "valuation_date": "2026-03-28",
    "expiry_min": "2026-04-17",
    "expiry_max": "2026-04-17",
    "option_types": [
      "C",
      "P"
    ],
    "chain_debug": {
      "OPT_TICKERS": {
        "rows": 0,
        "columns": []
      },
      "OPT_CHAIN": {
        "rows": 8000,
        "columns": [
          "security",
          "Security Description"
        ]
      }
    },
    "chain_preview": [
      {
        "security": "SPX Index",
        "Security Description": "SPXW US 04/17/26 C1400 Index"
      },
      {
        "security": "SPX Index",
        "Security Description": "SPXW US 04/17/26 C1600 Index"
      },
      {
        "security": "SPX Index",
        "Security Description": "SPXW US 04/17/26 C1800 Index"
      },
      {
        "security": "SPX Index",
        "Security Description": "SPXW US 04/17/26 C2000 Index"
      },
      {
        "security": "SPX Index",
        "Security Description": "SPXW US 04/17/26 C2200 Index"
      },
      {
        "security": "SPX Index",
        "Security Description": "SPXW US 04/17/26 C2400 Index"
      },
      {
        "security": "SPX Index",
        "Security Description": "SPXW US 04/17/26 C2600 Index"
      },
      {
        "security": "SPX Index",
        "Security Description": "SPXW US 04/17/26 C2800 Index"
      },
      {
        "security": "SPX Index",
        "Security Description": "SPXW US 04/17/26 C3000 Index"
      },
      {
        "security": "SPX Index",
        "Security Description": "SPXW US 04/17/26 C3200 Index"
      }
    ],
    "raw_preview": [
      {
        "security": "SPXW US 04/17/26 C5000 Index",
        "sequence_number": 40,
        "errors": null,
        "OPT_EXPIRE_DT": "2026-04-17",
        "OPT_STRIKE_PX": 5000.0,
        "OPT_PUT_CALL": "Call",
        "IVOL_MID": 55.42003,
        "IVOL_BID": 47.74522,
        "IVOL_ASK": 60.71939,
        "PX_MID": 1373.05,
        "PX_BID": 1367.2,
        "PX_ASK": 1378.9,
        "PX_LAST": 1392.48,
        "VOLUME": 49.0,
        "OPEN_INT": 159
      },
      {
        "security": "SPXW US 04/17/26 C5025 Index",
        "sequence_number": 41,
        "errors": null,
        "OPT_EXPIRE_DT": "2026-04-17",
        "OPT_STRIKE_PX": 5025.0,
        "OPT_PUT_CALL": "Call",
        "IVOL_MID": 54.80883,
        "IVOL_BID": 47.51649,
        "IVOL_ASK": 59.94938,
        "PX_MID": 1348.45,
        "PX_BID": 1342.6,
        "PX_ASK": 1354.3,
        "PX_LAST": NaN,
        "VOLUME": 0.0,
        "OPEN_INT": 0
      },
      {
        "security": "SPXW US 04/17/26 C5050 Index",
        "sequence_number": 42,
        "errors": null,
        "OPT_EXPIRE_DT": "2026-04-17",
        "OPT_STRIKE_PX": 5050.0,
        "OPT_PUT_CALL": "Call",
        "IVOL_MID": 54.18231,
        "IVOL_BID": 47.00103,
        "IVOL_ASK": 59.09687,
        "PX_MID": 1323.85,
        "PX_BID": 1318.1,
        "PX_ASK": 1329.6,
        "PX_LAST": NaN,
        "VOLUME": 0.0,
        "OPEN_INT": 0
      },
      {
        "security": "SPXW US 04/17/26 C5075 Index",
        "sequence_number": 43,
        "errors": null,
        "OPT_EXPIRE_DT": "2026-04-17",
        "OPT_STRIKE_PX": 5075.0,
        "OPT_PUT_CALL": "Call",
        "IVOL_MID": 53.05969,
        "IVOL_BID": 46.69258,
        "IVOL_ASK": 57.74715,
        "PX_MID": 1298.75,
        "PX_BID": 1293.5,
        "PX_ASK": 1304.0,
        "PX_LAST": NaN,
        "VOLUME": 0.0,
        "OPEN_INT": 0
      },
      {
        "security": "SPXW US 04/17/26 C5100 Index",
        "sequence_number": 44,
        "errors": null,
        "OPT_EXPIRE_DT": "2026-04-17",
        "OPT_STRIKE_PX": 5100.0,
        "OPT_PUT_CALL": "Call",
        "IVOL_MID": 52.84183,
        "IVOL_BID": 46.34342,
        "IVOL_ASK": 57.44812,
        "PX_MID": 1274.6,
        "PX_BID": 1268.9,
        "PX_ASK": 1280.3,
        "PX_LAST": 1615.85,
        "VOLUME": 1.0,
        "OPEN_INT": 1
      },
      {
        "security": "SPXW US 04/17/26 C5125 Index",
        "sequence_number": 45,
        "errors": null,
        "OPT_EXPIRE_DT": "2026-04-17",
        "OPT_STRIKE_PX": 5125.0,
        "OPT_PUT_CALL": "Call",
        "IVOL_MID": 52.17126,
        "IVOL_BID": 45.95139,
        "IVOL_ASK": 56.65665,
        "PX_MID": 1250.0,
        "PX_BID": 1244.3,
        "PX_ASK": 1255.7,
        "PX_LAST": NaN,
        "VOLUME": 0.0,
        "OPEN_INT": 0
      },
      {
        "security": "SPXW US 04/17/26 C5150 Index",
        "sequence_number": 46,
        "errors": null,
        "OPT_EXPIRE_DT": "2026-04-17",
        "OPT_STRIKE_PX": 5150.0,
        "OPT_PUT_CALL": "Call",
        "IVOL_MID": 51.54174,
        "IVOL_BID": 45.66991,
        "IVOL_ASK": 55.85739,
        "PX_MID": 1225.45,
        "PX_BID": 1219.8,
        "PX_ASK": 1231.1,
        "PX_LAST": 1244.68,
        "VOLUME": 3.0,
        "OPEN_INT": 6
      },
      {
        "security": "SPXW US 04/17/26 C5175 Index",
        "sequence_number": 47,
        "errors": null,
        "OPT_EXPIRE_DT": "2026-04-17",
        "OPT_STRIKE_PX": 5175.0,
        "OPT_PUT_CALL": "Call",
        "IVOL_MID": 50.47952,
        "IVOL_BID": 45.2076,
        "IVOL_ASK": 54.91929,
        "PX_MID": 1200.4,
        "PX_BID": 1195.2,
        "PX_ASK": 1205.6,
        "PX_LAST": NaN,
        "VOLUME": 0.0,
        "OPEN_INT": 0
      },
      {
        "security": "SPXW US 04/17/26 C5200 Index",
        "sequence_number": 48,
        "errors": null,
        "OPT_EXPIRE_DT": "2026-04-17",
        "OPT_STRIKE_PX": 5200.0,
        "OPT_PUT_CALL": "Call",
        "IVOL_MID": 50.19542,
        "IVOL_BID": 44.84205,
        "IVOL_ASK": 54.23737,
        "PX_MID": 1176.3,
        "PX_BID": 1170.7,
        "PX_ASK": 1181.9,
        "PX_LAST": 1388.93,
        "VOLUME": 1.0,
        "OPEN_INT": 66
      },
      {
        "security": "SPXW US 04/17/26 C5220 Index",
        "sequence_number": 49,
        "errors": null,
        "OPT_EXPIRE_DT": "2026-04-17",
        "OPT_STRIKE_PX": 5220.0,
        "OPT_PUT_CALL": "Call",
        "IVOL_MID": 49.3318,
        "IVOL_BID": 44.1153,
        "IVOL_ASK": 53.44222,
        "PX_MID": 1156.25,
        "PX_BID": 1150.5,
        "PX_ASK": 1162.0,
        "PX_LAST": NaN,
        "VOLUME": 0.0,
        "OPEN_INT": 0
      }
    ],
    "surface_nulls": {
      "valuation_date": 0,
      "underlying": 0,
      "option_ticker": 0,
      "expiry": 0,
      "tau_years": 0,
      "option_type": 0,
      "strike": 0,
      "spot": 0,
      "implied_vol": 77,
      "mid_price": 0,
      "volume": 0,
      "open_interest": 0
    }
  },
  "calibration": {
    "security": "SPX Index",
    "valuation_date": "2026-03-28",
    "slices": [
      {
        "expiry": "2026-04-17",
        "tau_years": 0.0547945205479452,
        "n_points": 612,
        "atm_iv": 0.2743693183837236,
        "skew": -0.9843119659280163,
        "intercept": 0.2743693183837236,
        "r_squared": 0.9917850629201106,
        "method": "iv_vs_log_moneyness"
      }
    ],
    "scaling_fit": null,
    "diagnostics": {
      "rows_in": 1500,
      "rows_used": 1423,
      "atm_log_moneyness_band": 0.08,
      "min_points_per_slice": 5
    },
    "surface_preview": {
      "rows": [
        {
          "expiry": "2026-04-17 00:00:00",
          "strike": 200.0,
          "implied_vol": 4.191854,
          "tau_years": 0.0547945205479452,
          "log_moneyness": -3.4608568319680306
        },
        {
          "expiry": "2026-04-17 00:00:00",
          "strike": 400.0,
          "implied_vol": 3.316625,
          "tau_years": 0.0547945205479452,
          "log_moneyness": -2.7677096514080852
        },
        {
          "expiry": "2026-04-17 00:00:00",
          "strike": 600.0,
          "implied_vol": 2.819096,
          "tau_years": 0.0547945205479452,
          "log_moneyness": -2.362244543299921
        },
        {
          "expiry": "2026-04-17 00:00:00",
          "strike": 800.0,
          "implied_vol": 2.813158,
          "tau_years": 0.0547945205479452,
          "log_moneyness": -2.07456247084814
        },
        {
          "expiry": "2026-04-17 00:00:00",
          "strike": 1000.0,
          "implied_vol": 2.509075,
          "tau_years": 0.0547945205479452,
          "log_moneyness": -1.8514189195339303
        },
        {
          "expiry": "2026-04-17 00:00:00",
          "strike": 1200.0,
          "implied_vol": 2.2911859999999997,
          "tau_years": 0.0547945205479452,
          "log_moneyness": -1.6690973627399757
        },
        {
          "expiry": "2026-04-17 00:00:00",
          "strike": 1400.0,
          "implied_vol": 1.806497,
          "tau_years": 0.0547945205479452,
          "log_moneyness": -1.5149466829127174
        },
        {
          "expiry": "2026-04-17 00:00:00",
          "strike": 1400.0,
          "implied_vol": 2.111095,
          "tau_years": 0.0547945205479452,
          "log_moneyness": -1.5149466829127174
        },
        {
          "expiry": "2026-04-17 00:00:00",
          "strike": 1400.0,
          "implied_vol": 2.037009,
          "tau_years": 0.0547945205479452,
          "log_moneyness": -1.5149466829127174
        },
        {
          "expiry": "2026-04-17 00:00:00",
          "strike": 1600.0,
          "implied_vol": 1.901651,
          "tau_years": 0.0547945205479452,
          "log_moneyness": -1.3814152902881947
        }
      ]
    }
  },
  "error_type": null,
  "error": null
}
```

## Attempts
### SPX Index|type=P|max=300
- OK: False
- Surface rows: 0
- Expiries: 0
- Option types found: []

### SPX Index|type=P|max=800
- OK: True
- Surface rows: 340
- Expiries: 1
- Option types found: ['P']

### SPX Index|type=P|max=1500
- OK: True
- Surface rows: 537
- Expiries: 1
- Option types found: ['P']

### SPX Index|type=C|max=300
- OK: True
- Surface rows: 300
- Expiries: 1
- Option types found: ['C']

### SPX Index|type=C|max=800
- OK: True
- Surface rows: 460
- Expiries: 1
- Option types found: ['C']

### SPX Index|type=C|max=1500
- OK: True
- Surface rows: 963
- Expiries: 1
- Option types found: ['C']

### SPX Index|type=ALL|max=300
- OK: True
- Surface rows: 300
- Expiries: 1
- Option types found: ['C']

### SPX Index|type=ALL|max=800
- OK: True
- Surface rows: 800
- Expiries: 1
- Option types found: ['C', 'P']

### SPX Index|type=ALL|max=1500
- OK: True
- Surface rows: 1500
- Expiries: 1
- Option types found: ['C', 'P']
