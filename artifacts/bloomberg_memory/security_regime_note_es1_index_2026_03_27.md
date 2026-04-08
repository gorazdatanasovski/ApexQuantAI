# Bloomberg Research Memory: ES1 Index

## As of
- Date: 2026-03-27

## Market state
- Last price: 6412.25
- Last daily return: -0.0174307
- Current drawdown: -0.0861184
- Volatility regime: compressed_volatility
- Roughness signature: rough_or_antipersistent
- Mean-reversion signature: weak_mean_reversion

## Realized volatility panel
- Realized vol 5: 0.0263856
- Realized vol 21: 0.041838
- Realized vol 63: 0.0627932

## Roughness / Hurst-style panel
- Hurst variance scaling 5: NA
- Hurst variance scaling 21: 0
- Hurst variance scaling 63: 0.318991

## OU / mean-reversion panel
- OU speed 5: -0.343047
- OU speed 21: 0.0164434
- OU speed 63: -0.0117339

## Jump / discontinuity panel
- Jump share 5: 0
- Jump share 21: 0.0163082
- Jump share 63: 0.0458597

## Volatility clustering panel
- Abs-return ACF 5: 0.562971
- Abs-return ACF 21: 0.0289351
- Abs-return ACF 63: 0.113029

## Return autocorrelation panel
- Return autocorr 5: 0.203634
- Return autocorr 21: -0.102695
- Return autocorr 63: -0.103816

## Volume anomaly panel
- Volume z-score 5: -0.303283
- Volume z-score 21: 0.257928
- Volume z-score 63: 0.56713

## Historical coverage
- Rows: 36230
- Start: 1997-09-09
- End: 2026-03-27

## Research interpretation
This note summarizes the local Bloomberg-derived empirical state for ES1 Index. It is intended to support theorem generation, empirical falsification, calibration design, and hypothesis ranking inside QuantAI.

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
