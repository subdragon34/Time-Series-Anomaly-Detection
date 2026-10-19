# Completed Assignment Tables

## Part A - Time-Series Exploration

- `Time` is converted to a Pandas datetime index.
- Temperature changes only slightly around -8 C and shows no abrupt jump.
- Wind changes gradually around 4-5 m/s.
- Humidity generally decreases from 62% to the mid-50s.
- PM2.5 rises gradually from 28 to 47, then jumps to 95, 110, and 118 before returning to 45.
- Likely anomaly interval before applying an algorithm: **12:50-13:00**.
- No reliable seasonality can be inferred from a 65-minute series.

## Part B - Moving Average and Exponential Smoothing

Difference is defined as `Observed PM2.5 - Smoothed value`.

| Time | PM2.5 | 3-point MA | Smoothed value | Difference |
|---|---:|---:|---:|---:|
| 12:10 | 31 | 29.667 | 29.320 | 1.680 |
| 12:15 | 29 | 30.000 | 29.224 | -0.224 |
| 12:20 | 32 | 30.667 | 30.057 | 1.943 |
| 12:25 | 35 | 32.000 | 31.540 | 3.460 |
| 12:30 | 38 | 35.000 | 33.478 | 4.522 |
| 12:35 | 41 | 38.000 | 35.734 | 5.266 |
| 12:40 | 44 | 41.000 | 38.214 | 5.786 |
| 12:45 | 47 | 44.000 | 40.850 | 6.150 |
| 12:50 | 95 | 62.000 | 57.095 | 37.905 |
| 12:55 | 110 | 84.000 | 72.966 | 37.034 |
| 13:00 | 118 | 107.667 | 86.477 | 31.523 |

## Part C - Statistical Anomaly Detection

Method choice: six readings sampled every five minutes, including the current reading. Sample standard deviation (ddof=1) is used. The rule is:

`abs(x - rolling_mean) > 2 * rolling_std`

| Time | Observed PM2.5 | Rolling mean | Rolling std | Threshold | Anomaly? |
|---|---:|---:|---:|---:|---|
| 12:35 | 41 | 34.333 | 4.546 | 9.092 | No |
| 12:40 | 44 | 36.500 | 5.612 | 11.225 | No |
| 12:45 | 47 | 39.500 | 5.612 | 11.225 | No |
| 12:50 | 95 | 50.000 | 22.450 | 44.900 | Yes |
| 12:55 | 110 | 62.500 | 31.488 | 62.976 | No |
| 13:00 | 118 | 75.833 | 35.695 | 71.391 | No |

### Intermediate decision at 12:50

- Observed PM2.5 = 95
- Rolling mean = 50.000
- Rolling std = 22.450
- Threshold = 44.900
- Absolute difference = 45.000
- Since `45.000 > 44.900`, 12:50 is flagged as an anomaly.

## Part D - Compare Detection Methods

| Method | Detected points | False positives observed | Advantages | Limitations |
|---|---|---:|---|---|
| Rolling threshold | 12:50 | Not verifiable without ground-truth labels | Uses recent local behavior and reacts at the first large jump | The threshold adapts upward after the spike and does not flag 12:55 or 13:00 |
| Global z-score | 13:00 | Not verifiable without ground-truth labels | Very simple and easy to standardize | Uses whole-series mean/std, so it is not directly suitable for a true live stream without an online baseline |

5. **More interpretable:** Rolling threshold for a live dashboard because the recent mean, standard deviation, and threshold can be shown directly.

6. **Faster reaction:** Rolling threshold. It flags 12:50, while the global z-score flags 13:00.

7. **Live monitoring suitability:** The rolling method is suitable as a simple live rule, but a longer stream should use a stable historical or adaptive baseline. The global z-score would need to be converted to an online or rolling baseline for real-time use.

## Part E - Operational Recommendation

The smart-campus dashboard should display current PM2.5, recent PM2.5 trend, rolling mean, rolling threshold, and anomaly status. An alert should trigger when `abs(PM2.5 - rolling_mean) > 2 * rolling_std`. The dashboard should show a visible warning and notify the responsible campus operations staff.

## Individual experiment

The rolling multiplier was compared at 2.0 and 1.5.

- `2.0` detects: 12:50
- `1.5` detects more points, including earlier gradual increases, so it is more sensitive and produces less selective alerts.

For this short stream, `2.0` is kept because it flags the first sharp PM2.5 jump with fewer early alerts. This does not establish an optimal threshold for real data.

**Interpretation note:** 12:50-13:00 is a visually identified candidate anomaly interval, not a verified labeled dataset. False-positive counts therefore cannot be established from the supplied data. The rolling threshold includes the current PM2.5 value, which inflates the standard deviation after a spike. This helps explain missed later high readings.
