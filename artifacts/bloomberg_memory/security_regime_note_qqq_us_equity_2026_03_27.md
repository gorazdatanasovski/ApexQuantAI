# Bloomberg Research Memory: QQQ US Equity

## As of
- Date: 2026-03-27

## Market state
- Last price: 562.58
- Last daily return: -0.0197301
- Current drawdown: -0.11512
- Volatility regime: compressed_volatility
- Roughness signature: rough_or_antipersistent
- Mean-reversion signature: weak_mean_reversion

## Realized volatility panel
- Realized vol 5: 0.0341462
- Realized vol 21: 0.0545513
- Realized vol 63: 0.0836858

## Roughness / Hurst-style panel
- Hurst variance scaling 5: NA
- Hurst variance scaling 21: 0.397194
- Hurst variance scaling 63: 0.204204

## OU / mean-reversion panel
- OU speed 5: -0.21658
- OU speed 21: -0.0391678
- OU speed 63: 0.0165397

## Jump / discontinuity panel
- Jump share 5: 0
- Jump share 21: 0.0237717
- Jump share 63: 0

## Volatility clustering panel
- Abs-return ACF 5: 0.294207
- Abs-return ACF 21: -0.0562123
- Abs-return ACF 63: 0.0923426

## Return autocorrelation panel
- Return autocorr 5: 0.0705932
- Return autocorr 21: -0.184756
- Return autocorr 63: -0.0912744

## Volume anomaly panel
- Volume z-score 5: 0.622408
- Volume z-score 21: 0.645688
- Volume z-score 63: 1.08326

## Historical coverage
- Rows: 34025
- Start: 1999-03-10
- End: 2026-03-27

## Research interpretation
This note summarizes the local Bloomberg-derived empirical state for QQQ US Equity. It is intended to support theorem generation, empirical falsification, calibration design, and hypothesis ranking inside QuantAI.

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
