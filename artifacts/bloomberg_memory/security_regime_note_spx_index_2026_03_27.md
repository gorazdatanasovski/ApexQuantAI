# Bloomberg Research Memory: SPX Index

## As of
- Date: 2026-03-27

## Market state
- Last price: 6368.85
- Last daily return: -0.0168632
- Current drawdown: -0.0873743
- Volatility regime: compressed_volatility
- Roughness signature: rough_or_antipersistent
- Mean-reversion signature: weak_mean_reversion

## Realized volatility panel
- Realized vol 5: 0.0276706
- Realized vol 21: 0.0450225
- Realized vol 63: 0.0649778

## Roughness / Hurst-style panel
- Hurst variance scaling 5: NA
- Hurst variance scaling 21: 0.23527
- Hurst variance scaling 63: 0.297006

## OU / mean-reversion panel
- OU speed 5: -0.320931
- OU speed 21: 0.00885961
- OU speed 63: -0.017272

## Jump / discontinuity panel
- Jump share 5: 0
- Jump share 21: 0.00370177
- Jump share 63: 0.0312051

## Volatility clustering panel
- Abs-return ACF 5: 0.281503
- Abs-return ACF 21: -0.094978
- Abs-return ACF 63: 0.0985198

## Return autocorrelation panel
- Return autocorr 5: 0.242006
- Return autocorr 21: -0.210901
- Return autocorr 63: -0.140531

## Volume anomaly panel
- Volume z-score 5: -0.0423011
- Volume z-score 21: -0.281732
- Volume z-score 63: -0.196134

## Historical coverage
- Rows: 123455
- Start: 1927-12-30
- End: 2026-03-27

## Research interpretation
This note summarizes the local Bloomberg-derived empirical state for SPX Index. It is intended to support theorem generation, empirical falsification, calibration design, and hypothesis ranking inside QuantAI.

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
