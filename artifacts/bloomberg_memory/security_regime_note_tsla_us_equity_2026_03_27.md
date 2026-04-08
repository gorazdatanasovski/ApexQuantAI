# Bloomberg Research Memory: TSLA US Equity

## As of
- Date: 2026-03-27

## Market state
- Last price: 361.83
- Last daily return: -0.028015
- Current drawdown: -0.261391
- Volatility regime: compressed_volatility
- Roughness signature: rough_or_antipersistent
- Mean-reversion signature: weak_mean_reversion

## Realized volatility panel
- Realized vol 5: 0.0582598
- Realized vol 21: 0.101005
- Realized vol 63: 0.177474

## Roughness / Hurst-style panel
- Hurst variance scaling 5: NA
- Hurst variance scaling 21: 0.297641
- Hurst variance scaling 63: 0.356958

## OU / mean-reversion panel
- OU speed 5: -0.18822
- OU speed 21: 0.131166
- OU speed 63: 0.077921

## Jump / discontinuity panel
- Jump share 5: 0
- Jump share 21: 0
- Jump share 63: 0

## Volatility clustering panel
- Abs-return ACF 5: -0.130293
- Abs-return ACF 21: 0.0771187
- Abs-return ACF 63: 0.0137618

## Return autocorrelation panel
- Return autocorr 5: 0.564458
- Return autocorr 21: -0.0734288
- Return autocorr 63: -0.0839452

## Volume anomaly panel
- Volume z-score 5: 0.05349
- Volume z-score 21: 0.140625
- Volume z-score 63: 0.0697684

## Historical coverage
- Rows: 19810
- Start: 2010-06-28
- End: 2026-03-27

## Research interpretation
This note summarizes the local Bloomberg-derived empirical state for TSLA US Equity. It is intended to support theorem generation, empirical falsification, calibration design, and hypothesis ranking inside QuantAI.

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
