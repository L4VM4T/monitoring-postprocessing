from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm

def plot_histograms_gaussian(
    qpu_name: str,
    qubit_name: str,
    dataset_root: str = "datasets",
    max_values: dict = None,
    bins: int = 20,
    show_plot: bool = True
):
    """
    Genera histogramas de las métricas de coherencia y frecuencia de un qubit,
    ajustando una curva gaussiana y mostrando estadísticas básicas.

    Args:
        qpu_name (str): Nombre del QPU (ej. "QPU149").
        qubit_name (str): Nombre del qubit (ej. "Q3").
        dataset_root (str): Carpeta donde se encuentran los datasets.
        max_values (dict, optional): Diccionario con máximos para filtrar outliers.
                                     Ej: {"T1": None, "T2*": 100, "T2E": None, "Qubit Frequency": None}
        bins (int, optional): Número de barras para los histogramas.
        show_plot (bool, optional): Si True, muestra los gráficos.

    Returns:
        dict: Estadísticas por métrica {'T1': {'mean':..., 'std':..., 'min':..., 'max':...}, ...}
    """
    if max_values is None:
        max_values = {"T1": None, "T2*": 100, "T2E": None, "Qubit Frequency": None}

    dataset_dir = Path(dataset_root) / f"datasets_{qpu_name}"
    if not dataset_dir.exists():
        raise FileNotFoundError(f"Dataset directory does not exist: {dataset_dir}")

    csv_files = sorted(dataset_dir.glob(f"*_{qubit_name}.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found for {qubit_name} in {dataset_dir}")

    dfs = []
    for f in csv_files:
        df = pd.read_csv(f, dtype={"Timestamp": str})
        # Filtra valores inválidos
        df = df[(df["T1"] > 0) & (df["T2*"] > 0) & (df["T2E"] > 0)]
        dfs.append(df)

    df_all = pd.concat(dfs, ignore_index=True)

    metrics = ["T1", "T2*", "T2E", "Qubit Frequency"]
    unit_conv = {"T1": 1e6, "T2*": 1e6, "T2E": 1e6, "Qubit Frequency": 1e-9}

    # Aplica filtros de máximos
    for metric, max_val in max_values.items():
        if max_val is not None:
            df_all = df_all[df_all[metric] * unit_conv[metric] <= max_val]

    stats = {}

    for metric in metrics:
        values = df_all[metric] * unit_conv[metric]

        mu, sigma = norm.fit(values)

        stats[metric] = {
            "mean": values.mean(),
            "std": values.std(),
            "min": values.min(),
            "max": values.max(),
            "fit_mu": mu,
            "fit_sigma": sigma
        }

        if show_plot:
            plt.figure(figsize=(8, 4))
            plt.hist(values, bins=bins, density=True, alpha=0.6, color='skyblue', edgecolor='black')
            x = np.linspace(values.min(), values.max(), 100)
            plt.plot(x, norm.pdf(x, mu, sigma), 'r--', linewidth=2, label=f'Gaussian fit\nμ={mu:.2f}, σ={sigma:.2f}')
            plt.title(f"{metric} histogram - Qubit {qubit_name}")
            plt.xlabel(f"{metric} ({'µs' if metric != 'Qubit Frequency' else 'GHz'})")
            plt.ylabel("Probability Density")
            plt.grid(alpha=0.3)
            plt.legend()
            plt.text(
                0.95, 0.8,
                f"Mean: {values.mean():.2f}\nStd: {values.std():.2f}\nMin: {values.min():.2f}\nMax: {values.max():.2f}",
                ha="right", va="top", transform=plt.gca().transAxes,
                bbox=dict(facecolor="white", alpha=0.8, edgecolor="gray")
            )
            plt.show()

    return stats

# Example usage:
"""
stats = plot_histograms_gaussian(
    qpu_name="QPU149",
    qubit_name="q3",
    dataset_root="../monitoring_packages/datasets",
    max_values={"T1": None, "T2*": 100, "T2E": None, "Qubit Frequency": None},
    bins=20,
    show_plot=True
)
"""