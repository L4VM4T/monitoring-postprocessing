# plotting.py
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm

colors = {"T1": "blue", "T2*": "orange", "T2E": "green", "Qubit Frequency": "red"}

def plot_qubit_postprocessing(df_filtered, freq_delta_df, stats_data, qubit_name="", bins=20):
    """
    Genera los plots de postprocessing y el histograma con ajuste gaussiano.
    La lógica de los ejes y colores sigue exactamente el código original.

    Parameters:
    -----------
    df_filtered: pd.DataFrame
        DataFrame filtrado con las métricas originales y columna Timestamp.
    freq_delta_df : pd.DataFrame
        DataFrame de una columna con ΔF de la frecuencia.
    stats_data : dict
        Diccionario con media y std de cada métrica.
    qubit_name : str
        Nombre del qubit (para títulos).
    bins : int
        Número de bins para el histograma de T1.
    """
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={"height_ratios": [3, 2]}, constrained_layout=True)
    ax_post, ax_hist = axes

    coherence_metrics = ["T1", "T2*", "T2E"]
    frequency_metric = "Qubit Frequency"

    # --- Postprocessing plot ---
    for metric in coherence_metrics:
        values = df_filtered[metric] * 1e6  # convertir a μs
        ax_post.scatter(df_filtered["Timestamp"], values, s=25, color=colors[metric], label=metric)
        ax_post.axhspan(stats_data[metric]["mean"] - stats_data[metric]["std"],
                        stats_data[metric]["mean"] + stats_data[metric]["std"],
                        color=colors[metric], alpha=0.15)

    # Frecuencia (ΔF)
    delta_values = freq_delta_df["Freq_delta"]
    ax_post.scatter(df_filtered["Timestamp"], delta_values, s=25, color=colors[frequency_metric], label=f"{frequency_metric} (ΔF)")
    ax_post.axhspan(stats_data[frequency_metric]["mean"] - stats_data[frequency_metric]["std"],
                    stats_data[frequency_metric]["mean"] + stats_data[frequency_metric]["std"],
                    color=colors[frequency_metric], alpha=0.15)

    ax_post.set_title(f"Monitoring Postprocessing - Qubit {qubit_name}")
    ax_post.set_ylabel("Coherence ($μs$) / ΔF (kHz)")
    ax_post.grid(True, alpha=0.3)
    ax_post.legend()

    # --- Histograma T1 ---
    t1_values = df_filtered["T1"] * 1e6  # μs
    mu, sigma = norm.fit(t1_values)
    ax_hist.hist(t1_values, bins=bins, density=True, alpha=0.6, color='skyblue', edgecolor='black')
    x = np.linspace(t1_values.min(), t1_values.max(), 100)
    ax_hist.plot(x, norm.pdf(x, mu, sigma), 'r--', linewidth=2)
    ax_hist.set_title("Histogram T1 - Gaussian fit")
    ax_hist.set_xlabel("T1 (μs)")
    ax_hist.set_ylabel("Probability Density")
    ax_hist.grid(alpha=0.3)
    ax_hist.text(0.95, 0.8, f"Mean={mu:.2f}\nStd={sigma:.2f}", transform=ax_hist.transAxes,
                 ha="right", va="top", bbox=dict(facecolor="white", alpha=0.8, edgecolor="gray"))

    plt.show()

