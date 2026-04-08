# Bloomberg Research Memory: SKEW Index

## As of
- Date: 2026-03-27

## Market state
- Last price: 139
- Last daily return: -0.0352699
- Current drawdown: -0.240935
- Volatility regime: compressed_volatility
- Roughness signature: near_brownian
- Mean-reversion signature: moderate_mean_reversion

## Realized volatility panel
- Realized vol 5: 0.048137
- Realized vol 21: 0.137097
- Realized vol 63: 0.207153

## Roughness / Hurst-style panel
- Hurst variance scaling 5: NA
- Hurst variance scaling 21: 0.60064
- Hurst variance scaling 63: 0.509079

## OU / mean-reversion panel
- OU speed 5: NA
- OU speed 21: 0.229229
- OU speed 63: 0.301356

## Jump / discontinuity panel
- Jump share 5: 0.112659
- Jump share 21: 0.221788
- Jump share 63: 0.239059

## Volatility clustering panel
- Abs-return ACF 5: 0.280755
- Abs-return ACF 21: -0.0818515
- Abs-return ACF 63: -0.12375

## Return autocorrelation panel
- Return autocorr 5: -0.697333
- Return autocorr 21: -0.07666
- Return autocorr 63: -0.0390767

## Volume anomaly panel
- Volume z-score 5: NA
- Volume z-score 21: NA
- Volume z-score 63: NA

## Historical coverage
- Rows: 45560
- Start: 1990-01-02
- End: 2026-03-27

## Research interpretation
This note summarizes the local Bloomberg-derived empirical state for SKEW Index. It is intended to support theorem generation, empirical falsification, calibration design, and hypothesis ranking inside QuantAI.

Primary current interpretations:
- Volatility regime classification: **compressed_volatility**
- Roughness classification: **near_brownian**
- Mean-reversion classification: **moderate_mean_reversion**

## Research prompts QuantAI can pursue
1. Test whether roughness estimates co-move with realized-volatility regimes.
2. Test whether jump share rises in high-volatility drawdown states.
3. Compare OU-style speeds across windows for stability or regime breaks.
4. Examine whether absolute-return persistence supports rough-vol style memory.

## Snapshot linkage
- Feature table present: yes
- Options snapshot attempted: yes
