from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from scipy.stats import norm

def run_postprocessing_with_histogram(qpu_name: str, qubit_name: str,
                                      dataset_root: str = "datasets",
                                      max_values: dict = None,
                                      xaxis_interval: int = 15,
                                      bins: int = 20):
    """
    Procesa CSV de un qubit mostrando:
    - Monitoring postprocessing (T1, T2*, T2E, frecuencia)
    - Histograma con ajuste gaussiano
    usando los mismos datos filtrados.
    """
    DATASET_DIR = Path(dataset_root) / f"datasets_{qpu_name}"
    if not DATASET_DIR.exists():
        raise FileNotFoundError(f"Dataset directory does not exist: {DATASET_DIR}")

    csv_files = sorted(DATASET_DIR.glob(f"*_{qubit_name}.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found for {qubit_name} in {DATASET_DIR}")

    print(f"Found {len(csv_files)} CSV(s) for qubit {qubit_name}")

    if max_values is None:
        max_values = {"T1": None, "T2*": 100, "T2E": None, "Qubit Frequency": None}

    unit_conversion = {"T1": 1e6, "T2*": 1e6, "T2E": 1e6, "Qubit Frequency": 1e-9}

    # Itera cada CSV
    for csv_file in csv_files:
        df = pd.read_csv(csv_file, dtype={"Timestamp": str})
        df = df[(df["T1"] > 0) & (df["T2*"] > 0) & (df["T2E"] > 0)]

        # Filtrado de máximos
        for metric, max_val in max_values.items():
            if max_val is not None:
                df = df[df[metric] * unit_conversion[metric] <= max_val]

        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        df = df.sort_values("Timestamp").reset_index(drop=True)

        # --- Configuración de subplots: arriba postprocessing, abajo histograma ---
        fig, axes = plt.subplots(2, 1, figsize=(14,10), gridspec_kw={"height_ratios":[3,2]}, constrained_layout=True)
        ax_post, ax_hist = axes

        # --- Postprocessing plot ---
        colors = {"T1":"blue","T2*":"orange","T2E":"green","Qubit Frequency":"red"}
        coherence_metrics = ["T1","T2*","T2E"]
        frequency_metric = "Qubit Frequency"

        stats_data = {}
        # Coherence metrics
        for t in coherence_metrics:
            values = df[t]*unit_conversion[t]
            stats_data[t] = {"mean": values.mean(), "std": values.std()}
            ax_post.scatter(df["Timestamp"], values, s=25, color=colors[t], label=t)
            ax_post.axhspan(values.mean()-values.std(), values.mean()+values.std(), color=colors[t], alpha=0.15)

        # Frequency
        values_freq = df[frequency_metric]*unit_conversion[frequency_metric]
        session_mean = values_freq.mean()
        values_freq_khz = (values_freq - session_mean)*1e6
        stats_data[frequency_metric] = {"mean": values_freq_khz.mean(), "std": values_freq_khz.std()}
        ax_post.scatter(df["Timestamp"], values_freq_khz, s=25, color=colors[frequency_metric], label=f"{frequency_metric} (ΔF)")
        ax_post.axhspan(stats_data[frequency_metric]["mean"]-stats_data[frequency_metric]["std"],
                        stats_data[frequency_metric]["mean"]+stats_data[frequency_metric]["std"],
                        color=colors[frequency_metric], alpha=0.15)

        ax_post.set_title(f"Monitoring Postprocessing - {csv_file.name} - Qubit {qubit_name}")
        ax_post.set_ylabel("Coherence ($μs$) / ΔF (kHz)")
        ax_post.grid(True, alpha=0.3)
        ax_post.legend()

        # --- Histograma ---
        # Para simplicidad, solo T1 aquí (puedes repetir para otras métricas)
        metric = "T1"
        values_hist = df[metric]*unit_conversion[metric]
        mu, sigma = norm.fit(values_hist)
        ax_hist.hist(values_hist, bins=bins, density=True, alpha=0.6, color='skyblue', edgecolor='black')
        x = np.linspace(values_hist.min(), values_hist.max(), 100)
        ax_hist.plot(x, norm.pdf(x, mu, sigma), 'r--', linewidth=2)
        ax_hist.set_title(f"Histogram {metric} - Gaussian fit")
        ax_hist.set_xlabel(f"{metric} (μs)")
        ax_hist.set_ylabel("Probability Density")
        ax_hist.grid(alpha=0.3)
        ax_hist.text(0.95,0.8,f"Mean={mu:.2f}\nStd={sigma:.2f}", transform=ax_hist.transAxes,
                     ha="right", va="top", bbox=dict(facecolor="white", alpha=0.8, edgecolor="gray"))

        plt.show()
