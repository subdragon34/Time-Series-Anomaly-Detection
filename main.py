from pathlib import Path
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "astana_weather_data.csv"
PROCESSED_FILE = BASE_DIR / "processed_weather_data.csv"
PLOTS_DIR = BASE_DIR / "plots"

ALPHA = 0.3
ROLLING_WINDOW = 6
ROLLING_MULTIPLIER = 2.0
ZSCORE_THRESHOLD = 2.0


def load_data(path=DATA_FILE):
    df = pd.read_csv(path)
    df["Time"] = pd.to_datetime(df["Time"], format="%H:%M")
    df = df.set_index("Time")
    return df


def add_smoothing(df):
    result = df.copy()

    result["PM25_MA3"] = (
        result["PM25_ug_m3"]
        .rolling(window=3, min_periods=3)
        .mean()
    )
    result["PM25_Smoothed"] = (
        result["PM25_ug_m3"]
        .ewm(alpha=ALPHA, adjust=False)
        .mean()
    )
    result["PM25_Difference"] = (
        result["PM25_ug_m3"] - result["PM25_Smoothed"]
    )

    return result


def add_rolling_anomaly(df, multiplier=ROLLING_MULTIPLIER):
    result = df.copy()

    result["Rolling_Mean"] = (
        result["PM25_ug_m3"]
        .rolling(window=ROLLING_WINDOW, min_periods=ROLLING_WINDOW)
        .mean()
    )
    result["Rolling_Std"] = (
        result["PM25_ug_m3"]
        .rolling(window=ROLLING_WINDOW, min_periods=ROLLING_WINDOW)
        .std(ddof=1)
    )
    result["Rolling_Threshold"] = multiplier * result["Rolling_Std"]
    result["Rolling_Abs_Diff"] = (
        result["PM25_ug_m3"] - result["Rolling_Mean"]
    ).abs()
    result["Rolling_Anomaly"] = (
        result["Rolling_Abs_Diff"] > result["Rolling_Threshold"]
    )

    return result


def add_zscore_method(df):
    result = df.copy()

    mean = result["PM25_ug_m3"].mean()
    std = result["PM25_ug_m3"].std(ddof=0)

    result["Z_Score"] = (result["PM25_ug_m3"] - mean) / std
    result["Z_Anomaly"] = result["Z_Score"].abs() > ZSCORE_THRESHOLD

    return result


def sensitivity_experiment(df):
    rows = []

    for multiplier in [2.0, 1.5]:
        checked = add_rolling_anomaly(df, multiplier=multiplier)
        detected = [
            time.strftime("%H:%M")
            for time in checked.index[checked["Rolling_Anomaly"]]
        ]

        rows.append({
            "multiplier": multiplier,
            "detected_points": ", ".join(detected) if detected else "None",
        })

    return pd.DataFrame(rows)


def save_processed_data(df, path=PROCESSED_FILE):
    output = df.reset_index().copy()
    output["Time"] = output["Time"].dt.strftime("%H:%M")
    output.to_csv(path, index=False)


def create_plots(df, output_dir=PLOTS_DIR):
    output_dir.mkdir(parents=True, exist_ok=True)

    series_to_plot = [
        ("Temperature_C", "Temperature over Time", "Temperature (C)", "01_temperature_timeseries.png"),
        ("Wind_mps", "Wind Speed over Time", "Wind speed (m/s)", "02_wind_timeseries.png"),
        ("PM25_ug_m3", "PM2.5 over Time", "PM2.5 (ug/m3)", "03_pm25_timeseries.png"),
        ("Humidity_%", "Humidity over Time", "Humidity (%)", "04_humidity_timeseries.png"),
    ]

    for column, title, ylabel, filename in series_to_plot:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(df.index, df[column], marker="o")
        ax.set_title(title)
        ax.set_xlabel("Time")
        ax.set_ylabel(ylabel)
        ax.tick_params(axis="x", rotation=45)
        fig.tight_layout()
        fig.savefig(output_dir / filename, dpi=180)
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(df.index, df["PM25_ug_m3"], marker="o", label="Observed PM2.5")
    ax.plot(df.index, df["PM25_MA3"], label="3-point moving average")
    ax.plot(df.index, df["PM25_Smoothed"], label="Exponential smoothing")
    ax.set_title("PM2.5 Moving Average and Exponential Smoothing")
    ax.set_xlabel("Time")
    ax.set_ylabel("PM2.5 (ug/m3)")
    ax.tick_params(axis="x", rotation=45)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "05_pm25_smoothing.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(df.index, df["PM25_ug_m3"], marker="o", label="Observed PM2.5")
    anomaly_rows = df[df["Rolling_Anomaly"]]
    ax.scatter(
        anomaly_rows.index,
        anomaly_rows["PM25_ug_m3"],
        s=70,
        label="Rolling anomaly",
    )
    ax.set_title("PM2.5 Rolling Anomaly Detection")
    ax.set_xlabel("Time")
    ax.set_ylabel("PM2.5 (ug/m3)")
    ax.tick_params(axis="x", rotation=45)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "06_anomaly_detection.png", dpi=180)
    plt.close(fig)


def main():
    df = load_data()

    print("Time-series exploration")
    print(f"Datetime index: {isinstance(df.index, pd.DatetimeIndex)}")
    print("Likely anomaly interval before algorithm: 12:50-13:00")
    print(
        "Observation: PM2.5 rises gradually, then jumps sharply from "
        "47 at 12:45 to 95 at 12:50."
    )
    print(
        "Seasonality: no reliable seasonal pattern can be inferred "
        "from this short 65-minute series."
    )

    processed = add_smoothing(df)
    processed = add_rolling_anomaly(processed)
    processed = add_zscore_method(processed)

    print("\nPart B - Moving average and exponential smoothing")
    part_b = processed.between_time("12:10", "13:00")[[
        "PM25_ug_m3", "PM25_MA3", "PM25_Smoothed", "PM25_Difference"
    ]].round(3)
    part_b.index = part_b.index.strftime("%H:%M")
    part_b.index.name = "Time"
    print(part_b.to_string())

    print("\nPart C - Rolling anomaly detection")
    part_c = processed.between_time("12:35", "13:00")[[
        "PM25_ug_m3", "Rolling_Mean", "Rolling_Std",
        "Rolling_Threshold", "Rolling_Anomaly"
    ]].round(3)
    part_c.index = part_c.index.strftime("%H:%M")
    part_c.index.name = "Time"
    print(part_c.to_string())

    row_1250 = processed.between_time("12:50", "12:50").iloc[0]
    print("\n12:50 anomaly decision")
    print(f'Observed PM2.5: {row_1250["PM25_ug_m3"]:.0f}')
    print(f'Rolling mean: {row_1250["Rolling_Mean"]:.3f}')
    print(f'Rolling std: {row_1250["Rolling_Std"]:.3f}')
    print(f'Threshold: {row_1250["Rolling_Threshold"]:.3f}')
    print(f'Absolute difference: {row_1250["Rolling_Abs_Diff"]:.3f}')
    print(f'Anomaly: {bool(row_1250["Rolling_Anomaly"])}')

    rolling_points = [
        time.strftime("%H:%M")
        for time in processed.index[processed["Rolling_Anomaly"]]
    ]
    zscore_points = [
        time.strftime("%H:%M")
        for time in processed.index[processed["Z_Anomaly"]]
    ]

    print("\nPart D - Method comparison")
    print("Rolling threshold detected:", ", ".join(rolling_points))
    print("Global z-score detected:", ", ".join(zscore_points))
    print("False positives cannot be verified without ground-truth labels.")
    print(
        "Rolling threshold reacts faster here because it flags the first "
        "large jump at 12:50, while the global z-score flags 13:00."
    )

    experiment = sensitivity_experiment(processed)
    evidence_dir = BASE_DIR / "evidence"
    evidence_dir.mkdir(exist_ok=True)
    experiment.to_csv(evidence_dir / "sensitivity_experiment.csv", index=False)
    part_b.to_csv(evidence_dir / "part_b_table.csv")
    part_c.to_csv(evidence_dir / "part_c_table.csv")

    checks = {
        "12:50": {
            "observed": float(row_1250["PM25_ug_m3"]),
            "rolling_mean": float(row_1250["Rolling_Mean"]),
            "rolling_std_sample": float(row_1250["Rolling_Std"]),
            "threshold": float(row_1250["Rolling_Threshold"]),
            "absolute_difference": float(row_1250["Rolling_Abs_Diff"]),
            "anomaly": bool(row_1250["Rolling_Anomaly"]),
        },
        "detected": {"rolling": rolling_points, "global_zscore": zscore_points},
        "parameters": {
            "moving_average_window": 3,
            "smoothing_alpha": ALPHA,
            "rolling_window": ROLLING_WINDOW,
            "rolling_std_ddof": 1,
            "rolling_multiplier": ROLLING_MULTIPLIER,
            "global_zscore_std_ddof": 0,
            "zscore_cutoff": ZSCORE_THRESHOLD,
        },
    }
    (evidence_dir / "calculation_check.json").write_text(
        json.dumps(checks, indent=2), encoding="utf-8"
    )

    print("\nSensitivity experiment")
    print(experiment.to_string(index=False))

    print("\nOperational recommendation")
    print(
        "Dashboard: current PM2.5, recent trend, rolling mean, rolling "
        "threshold, and anomaly status."
    )
    print(
        "Alert: trigger when |PM2.5 - rolling_mean| is greater than "
        "2 x rolling_std."
    )
    print(
        "Communication: show a visible dashboard warning and notify "
        "campus operations staff."
    )

    save_processed_data(processed)
    create_plots(processed)


if __name__ == "__main__":
    main()
