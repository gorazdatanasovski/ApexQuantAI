# Bloomberg Research Memory: VIX Index

## As of
- Date: 2026-03-27

## Market state
- Last price: 31.05
- Last daily return: 0.123597
- Current drawdown: -0.624501
- Volatility regime: compressed_volatility
- Roughness signature: rough_or_antipersistent
- Mean-reversion signature: moderate_mean_reversion

## Realized volatility panel
- Realized vol 5: 0.164305
- Realized vol 21: 0.452305
- Realized vol 63: 0.661377

## Roughness / Hurst-style panel
- Hurst variance scaling 5: NA
- Hurst variance scaling 21: 0.136763
- Hurst variance scaling 63: 0.383335

## OU / mean-reversion panel
- OU speed 5: 0.132412
- OU speed 21: 0.722804
- OU speed 63: 0.0645617

## Jump / discontinuity panel
- Jump share 5: 0
- Jump share 21: 0
- Jump share 63: 0

## Volatility clustering panel
- Abs-return ACF 5: 0.947384
- Abs-return ACF 21: 0.0188679
- Abs-return ACF 63: 0.139566

## Return autocorrelation panel
- Return autocorr 5: 0.0874207
- Return autocorr 21: -0.177539
- Return autocorr 63: -0.150386

## Volume anomaly panel
- Volume z-score 5: NA
- Volume z-score 21: NA
- Volume z-score 63: NA

## Historical coverage
- Rows: 45760
- Start: 1990-01-02
- End: 2026-03-27

## Research interpretation
This note summarizes the local Bloomberg-derived empirical state for VIX Index. It is intended to support theorem generation, empirical falsification, calibration design, and hypothesis ranking inside QuantAI.

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
