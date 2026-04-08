# Bloomberg Research Memory: VVIX Index

## As of
- Date: 2026-03-27

## Market state
- Last price: 133.18
- Last daily return: 0.0679583
- Current drawdown: -0.358447
- Volatility regime: compressed_volatility
- Roughness signature: rough_or_antipersistent
- Mean-reversion signature: moderate_mean_reversion

## Realized volatility panel
- Realized vol 5: 0.0936119
- Realized vol 21: 0.361372
- Realized vol 63: 0.519473

## Roughness / Hurst-style panel
- Hurst variance scaling 5: NA
- Hurst variance scaling 21: 0.160828
- Hurst variance scaling 63: 0.361688

## OU / mean-reversion panel
- OU speed 5: 0.84107
- OU speed 21: 1.44448
- OU speed 63: 0.178231

## Jump / discontinuity panel
- Jump share 5: 0
- Jump share 21: 0
- Jump share 63: 0

## Volatility clustering panel
- Abs-return ACF 5: 0.421376
- Abs-return ACF 21: 0.255603
- Abs-return ACF 63: 0.281841

## Return autocorrelation panel
- Return autocorr 5: 0.152553
- Return autocorr 21: -0.323439
- Return autocorr 63: -0.271257

## Volume anomaly panel
- Volume z-score 5: NA
- Volume z-score 21: NA
- Volume z-score 63: NA

## Historical coverage
- Rows: 24920
- Start: 2006-03-06
- End: 2026-03-27

## Research interpretation
This note summarizes the local Bloomberg-derived empirical state for VVIX Index. It is intended to support theorem generation, empirical falsification, calibration design, and hypothesis ranking inside QuantAI.

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
