# Assignment 3 - Real-Time Time Series Analysis and Anomaly Detection

## Astana Weather and Urban Comfort Monitoring

This project processes the supplied synthetic Astana weather stream and focuses on PM2.5 time-series behavior, smoothing, anomaly detection, method comparison, and an operational dashboard recommendation.

## Files

- `main.py` - complete analysis workflow
- `astana_weather_data.csv` - supplied input data
- `processed_weather_data.csv` - calculated moving averages, smoothing, anomaly fields, and z-scores
- `completed_tables.md` - completed assignment tables and answers
- `plots/` - time-series, smoothing, and anomaly plots
- `evidence/` - execution output, intermediate tables, and sensitivity experiment
- `Assignment3_Technical_Report_Amankos_Danial_BDA_2405.pdf` - technical report

## Install

```bash
python -m pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Main choices

- PM2.5 moving average uses 3 observations.
- Exponential smoothing uses alpha = 0.3.
- The rolling anomaly detector uses a 6-observation window.
- The anomaly rule is `abs(x - rolling_mean) > 2 * rolling_std`.
- The comparison method is a global z-score with `abs(z) > 2`.
- A 6-observation window uses six successive readings taken 5 minutes apart. The latest observation is included in its mean and standard deviation.

## Expected main result

The visually suspicious PM2.5 interval is 12:50-13:00. The rolling rule flags the initial jump at 12:50. The global z-score flags 13:00.
