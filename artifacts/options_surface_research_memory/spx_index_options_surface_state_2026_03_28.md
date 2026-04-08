# Bloomberg Research Memory: SPX Index Options Surface

- Valuation date: 2026-03-28
- Surface rows: 1500
- Rows with IV: 1423
- Calls: 963
- Puts: 537
- Expiries: 1

## Primary current interpretations
- Short-dated ATM skew is strongly negative, consistent with pronounced downside equity skew.
- OTM put wing carries richer implied volatility than the OTM call wing.
- Term-structure slope is currently unavailable or under-identified from stored calibration slices.

## Calibration state
- ATM IV: 0.2743693183837236
- ATM skew: -0.9843119659280163
- Method: iv_vs_log_moneyness
- Calibration rows: 1

## QuantAI usage
- Use this note when the query concerns SPX skew, smile, short-dated surface state, or implied-volatility structure.
- This note is suitable for theorem generation, calibration support, and empirical falsification.