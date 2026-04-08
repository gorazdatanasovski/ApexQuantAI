# Bloomberg Research Memory: SPY US Equity

## As of
- Date: 2026-03-26

## Market state
- Last price: 645.09
- Last daily return: -0.0180202
- Current drawdown: -0.0724669
- Volatility regime: compressed_volatility
- Roughness signature: rough_or_antipersistent
- Mean-reversion signature: weak_mean_reversion

## Realized volatility panel
- Realized vol 5: 0.0277618
- Realized vol 21: 0.0426373
- Realized vol 63: 0.0627613

## Roughness / Hurst-style panel
- Hurst variance scaling 5: NA
- Hurst variance scaling 21: 0
- Hurst variance scaling 63: 0.0180497

## OU / mean-reversion panel
- OU speed 5: NA
- OU speed 21: 0.0823583
- OU speed 63: 0.0219479

## Jump / discontinuity panel
- Jump share 5: 0.234451
- Jump share 21: 0.114189
- Jump share 63: 0.0863611

## Volatility clustering panel
- Abs-return ACF 5: -0.0685379
- Abs-return ACF 21: -0.291613
- Abs-return ACF 63: 0.0329935

## Return autocorrelation panel
- Return autocorr 5: -0.746464
- Return autocorr 21: -0.366119
- Return autocorr 63: -0.209893

## Volume anomaly panel
- Volume z-score 5: -0.701767
- Volume z-score 21: -0.0243653
- Volume z-score 63: 0.510649

## Historical coverage
- Rows: 41730
- Start: 1993-01-29
- End: 2026-03-26

## Research interpretation
This note summarizes the local Bloomberg-derived empirical state for SPY US Equity. It is intended to support theorem generation, empirical falsification, calibration design, and hypothesis ranking inside QuantAI.

Primary current interpretations:
- Volatility regime classification: **compressed_volatility**
- Roughness classification: **rough_or_antipersistent**
- Mean-reversion classification: **weak_mean_reversion**

## Research prompts QuantAI can pursue
1. Test whether roughness estimates co-move with realized-volatility regimes.
2. Test whether jump share rises in high-volatility drawdown states.
3. Compare OU-style speeds across windows for stability or regime breaks.
4. Examine whether absolute-return persistence supports rough-vol style memory.

## Snapshot linkage
- Feature table present: yes
- Options snapshot attempted: yes
