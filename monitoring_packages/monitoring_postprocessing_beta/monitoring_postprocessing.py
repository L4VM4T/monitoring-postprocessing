from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

def run_postprocessing(qpu_name: str, qubit_name: str,
                       dataset_root: str = "datasets",
                       max_values: dict = None,
                       xaxis_interval: int = 15):
    """
    Post-process coherence times (T1, T2*, T2E) and qubit frequency for a given qubit.

    Args:
        qpu_name (str): Name of the QPU (e.g., "QPU149")
        qubit_name (str): Name of the qubit (e.g., "Q3")
        dataset_root (str): Path to the datasets folder (default: "datasets")
        max_values (dict, optional): Dict specifying maximum values for metrics to filter outliers.
                                     Example: {"T1": None, "T2*": 100, "T2E": None, "Qubit Frequency": None}
        xaxis_interval (int, optional): Interval in minutes for frequency plot x-axis ticks (default: 15)
    """
    # --- 1. Dataset directory ---
    DATASET_DIR = Path(dataset_root) 
    if not DATASET_DIR.exists():
        raise FileNotFoundError(f"Dataset directory does not exist: {DATASET_DIR}")

    # --- 2. CSV files ---
    csv_file_names = sorted([f.name for f in DATASET_DIR.glob(f"*_{qubit_name}.csv")])
    if not csv_file_names:
        raise FileNotFoundError(f"No CSV files found for {qubit_name} in {DATASET_DIR}")

    csv_paths = [DATASET_DIR / name for name in csv_file_names]
    print("Found CSV files:", csv_file_names)

    # --- 3. Read CSVs ---
    dfs = []
    for f in csv_paths:
        try:
            df = pd.read_csv(f, dtype={"Timestamp": str})
            df = df[(df["T1"] > 0) & (df["T2*"] > 0) & (df["T2E"] > 0)]
            dfs.append(df)
            print(f"✅ File read: {f.name}")
        except Exception as e:
            print(f"⚠️ Error reading {f.name}: {e}")

    if not dfs:
        raise ValueError("No valid data after filtering.")

    # --- 4. Metrics & plotting settings ---
    coherence_metrics = ["T1", "T2*", "T2E"]
    frequency_metric = "Qubit Frequency"
    metrics_to_plot = coherence_metrics + [frequency_metric]
    colors = {"T1": "blue", "T2*": "orange", "T2E": "green", "Qubit Frequency": "red"}
    unit_conversion = {"T1": 1e6, "T2*": 1e6, "T2E": 1e6, "Qubit Frequency": 1e-9}
    y_labels = {"T1": "Coherence Times ($\\mu$s)", "Qubit Frequency": "Frequency (GHz)"}

    # Use user-provided max_values or defaults
    if max_values is None:
        max_values = {"T1": None, "T2*": 100, "T2E": None, "Qubit Frequency": None}

    # --- 5. Process & plot each CSV ---
    for i, f in enumerate(csv_paths):
        df = dfs[i].copy()
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        df = df.sort_values("Timestamp").reset_index(drop=True)

        # --- Filtering ---
        mask = pd.Series(True, index=df.index)
        for t in metrics_to_plot:
            if max_values.get(t) is not None:
                t_values = df[t] * unit_conversion[t]
                mask &= (t_values <= max_values[t])

        df_filtered = df[mask]

        # --- Plotting ---
        fig, (ax_t1t2, ax_freq, ax_box) = plt.subplots(
            3, 1, figsize=(12, 10), gridspec_kw={"height_ratios": [4, 3, 1]}, constrained_layout=True
        )

        # Coherence metrics
        stats_data = {}
        for t in coherence_metrics:
            values_us = df_filtered[t] * unit_conversion[t]
            mean_val = values_us.mean()
            std_val = values_us.std()
            stats_data[t] = {"mean": mean_val, "std": std_val, "min": values_us.min(), "max": values_us.max()}
            ax_t1t2.scatter(df_filtered["Timestamp"], values_us, s=25, color=colors[t], label=t)
            ax_t1t2.axhspan(mean_val - std_val, mean_val + std_val, color=colors[t], alpha=0.15)

        ax_t1t2.set_title(f"Coherence & Frequency Monitoring - {f.name} - Qubit {qubit_name}")
        ax_t1t2.set_ylabel(y_labels["T1"])
        ax_t1t2.grid(True, alpha=0.3)
        ax_t1t2.legend(fontsize=9, loc="upper right")
        plt.setp(ax_t1t2.get_xticklabels(), visible=False)

        # Frequency metrics
        values_ghz = df_filtered[frequency_metric] * unit_conversion[frequency_metric]
        session_mean_freq_ghz = values_ghz.mean()  # always session mean
        values_khz = (values_ghz - session_mean_freq_ghz) * 1e6

        stats_data[frequency_metric] = {
            "mean_ghz": values_ghz.mean(),
            "std_ghz": values_ghz.std(),
            "min_ghz": values_ghz.min(),
            "max_ghz": values_ghz.max(),
            "mean_khz": values_khz.mean(),
            "std_khz": values_khz.std(),
            "min_khz": values_khz.min(),
            "max_khz": values_khz.max(),
        }

        ax_freq.scatter(df_filtered["Timestamp"], values_khz, s=25, color=colors[frequency_metric],
                        label=f"{frequency_metric} (session mean ref)")
        ax_freq.axhspan(stats_data[frequency_metric]["mean_khz"] - stats_data[frequency_metric]["std_khz"],
                        stats_data[frequency_metric]["mean_khz"] + stats_data[frequency_metric]["std_khz"],
                        color=colors[frequency_metric], alpha=0.15)

        # Use user-defined x-axis interval
        ax_freq.xaxis.set_major_locator(mdates.MinuteLocator(interval=xaxis_interval))
        ax_freq.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
        plt.setp(ax_freq.get_xticklabels(), rotation=45, ha="right")
        ax_freq.set_xlabel("Date & Time")
        ax_freq.set_ylabel("ΔF [kHz]")
        ax_freq.grid(True, alpha=0.3)
        ax_freq.legend(fontsize=9, loc="upper right")

        # Statistics box
        stats_text = ""
        for t in metrics_to_plot:
            data_stat = stats_data[t]
            if t in coherence_metrics:
                unit = "$\\mu$s"
                stats_text += (f"std={data_stat['std']:.3f} {unit}, {t} → mean={data_stat['mean']:.3f} {unit}, "
                               f"min={data_stat['min']:.3f} {unit}, max={data_stat['max']:.3f} {unit}\n")
            else:
                stats_text += (f"{t} → mean={data_stat['mean_ghz']:.6f} GHz, min={data_stat['min_ghz']:.6f} GHz, "
                               f"max={data_stat['max_ghz']:.6f} GHz, std={data_stat['std_khz']:.3f} kHz\n")

        ax_box.axis("off")
        ax_box.text(0.5, 0.5, stats_text.strip(),
                    ha="center", va="center", fontsize=10, family="monospace",
                    bbox=dict(facecolor="whitesmoke", edgecolor="gray", boxstyle="round,pad=0.6"))

        plt.show()
