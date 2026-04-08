# Bloomberg Research Memory: AAPL US Equity

## As of
- Date: 2026-03-26

## Market state
- Last price: 252.89
- Last daily return: 0.00106823
- Current drawdown: -0.116356
- Volatility regime: compressed_volatility
- Roughness signature: rough_or_antipersistent
- Mean-reversion signature: moderate_mean_reversion

## Realized volatility panel
- Realized vol 5: 0.0151082
- Realized vol 21: 0.0545906
- Realized vol 63: 0.117968

## Roughness / Hurst-style panel
- Hurst variance scaling 5: NA
- Hurst variance scaling 21: 0
- Hurst variance scaling 63: 0.385609

## OU / mean-reversion panel
- OU speed 5: 1.34488
- OU speed 21: 0.288881
- OU speed 63: 0.115237

## Jump / discontinuity panel
- Jump share 5: 0.415926
- Jump share 21: 0.192091
- Jump share 63: 0.239424

## Volatility clustering panel
- Abs-return ACF 5: -0.36667
- Abs-return ACF 21: -0.090562
- Abs-return ACF 63: -0.00686491

## Return autocorrelation panel
- Return autocorr 5: -0.779127
- Return autocorr 21: 0.0198393
- Return autocorr 63: 0.107809

## Volume anomaly panel
- Volume z-score 5: -0.344175
- Volume z-score 21: 0.0337257
- Volume z-score 63: -0.256193

## Historical coverage
- Rows: 54590
- Start: 1982-11-30
- End: 2026-03-26

## Research interpretation
This note summarizes the local Bloomberg-derived empirical state for AAPL US Equity. It is intended to support theorem generation, empirical falsification, calibration design, and hypothesis ranking inside QuantAI.

Primary current interpretations:
- Volatility regime classification: **compressed_volatility**
- Roughness classification: **rough_or_antipersistent**
- Mean-reversion classification: **moderate_mean_reversion**

## Research prompts QuantAI can pursue
1. Test whether roughness estimates co-move with realized-volatility regimes.
2. Test whether jump share rises in high-volatility drawdown states.
3. Compare OU-style speeds across windows for stability or regime breaks.
4. Examine whether absolute-return persistence supports rough-vol style memory.

## Snapshot linkage
- Feature table present: yes
- Options snapshot attempted: yes
