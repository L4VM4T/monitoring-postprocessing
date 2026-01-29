import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import matplotlib.dates as mdates
import numpy as np

# Path configuration and CSV files
DATASET_DIR = Path("/home/lauramartinez/my_envs/monitoring/datasets_QPU149")  # Cambia según QPU
DATASET_DIR.mkdir(parents=True, exist_ok=True)

# List of CSV files to read
csv_file_names = [
    "20251118_coherence_monitoring_log_q3.csv",
    "20251123_coherence_monitoring_log_q3.csv",
    "20251125_coherence_monitoring_log_q3.csv"
]

csv_paths = [DATASET_DIR / name for name in csv_file_names]
print("Looking for CSV files in:", DATASET_DIR)
for f in csv_paths:
    print(f"{f.name}: exists? {f.exists()}")

qubit = "Q3"

if not csv_paths:
    raise FileNotFoundError(f"No CSV files found in: {DATASET_DIR}")

# Read CSVs and store dataframes
dfs = []
for f in csv_paths:
    try:
        df = pd.read_csv(f, dtype={'Timestamp': str})
        df = df[(df["T1"] > 0) & (df["T2*"] > 0) & (df["T2E"] > 0)]  
        dfs.append(df)
        print(f"✅ File read: {f.name}")
    except Exception as e:
        print(f"⚠️ Error reading {f.name}: {e}")

if not dfs:
    raise ValueError("No valid data after filtering.")

coherence_metrics = ["T1", "T2*", "T2E"] 
frequency_metric = "Qubit Frequency" 
metrics_to_plot = coherence_metrics + [frequency_metric] 
colors = {"T1": "blue", "T2*": "orange", "T2E": "green", "Qubit Frequency": "red"}
unit_conversion = {"T1": 1e6, "T2*": 1e6, "T2E": 1e6, "Qubit Frequency": 1e-9}
y_labels = {"T1": "Coherence Times ($\\mu$s)", "Qubit Frequency": "Frequency (GHz)"}
MAX_VALUES = {"T1": None, "T2*": 100, "T2E": None, "Qubit Frequency": None} 

for i, f in enumerate(csv_paths): 
    df = dfs[i].copy() 
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df = df.sort_values("Timestamp").reset_index(drop=True) 


    datos_incoherentes = []
    mask = pd.Series(True, index=df.index)
    for t in metrics_to_plot:
        if MAX_VALUES[t] is not None:
            t_values = df[t] * unit_conversion[t] 
            mask &= (t_values <= MAX_VALUES[t]) 

    df_filtered = df[mask] 
    datos_incoherentes = df[~mask]
    

    print(f"\n✅ CSV: {f.name}")
    print(f"Rows kept after filtering: {len(df_filtered)}")
    print(f"Rows removed due to thresholds: {len(datos_incoherentes)}")

    # --- 1. Create figure ---
    fig, (ax_t1t2, ax_freq, ax_box) = plt.subplots(
        3, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [4, 3, 1]}, constrained_layout=True
    )

    # --- 2a. Coherence metrics ---
    stats_data = {}
    for t in coherence_metrics:
        values_us = df_filtered[t] * unit_conversion[t]
        mean_val = values_us.mean()
        std_val = values_us.std()
        stats_data[t] = {'mean': mean_val, 'std': std_val, 'min': values_us.min(), 'max': values_us.max()}

        ax_t1t2.scatter(df_filtered["Timestamp"], values_us, s=25, color=colors[t], label=t)
        ax_t1t2.axhspan(mean_val - std_val, mean_val + std_val, color=colors[t], alpha=0.15) # Banda - Visualiza la dispersión mostrando donde se concentran la mayoría de medidas
                                                                                             # (puntos) - Esto ayuda a ver si un punto es una anomalía o está dentro de lo normal

    ax_t1t2.set_title(f"Coherence & Frequency Monitoring - {f.name} - Qubit {qubit}")
    ax_t1t2.set_ylabel(y_labels["T1"])
    ax_t1t2.grid(True, alpha=0.3)
    ax_t1t2.legend(fontsize=9, loc="upper right")
    plt.setp(ax_t1t2.get_xticklabels(), visible=False)

    # --- 2b. Frequency metrics (reference per session) ---
    values_ghz = df_filtered[frequency_metric] * unit_conversion[frequency_metric] # Conversión de las frecuencias a GHz
    
    session_mean_freq_ghz = values_ghz.mean()  # OBS - referencia de esta sesión - Calculo de la frecuencia media de la sesión actual
    values_khz = (values_ghz - session_mean_freq_ghz) * 1e6 # Diferencia de frecuencia - Conversión de GHz a kHz
    
    
    stats_data[frequency_metric] = {
    'mean_ghz': values_ghz.mean(),
    'std_ghz': values_ghz.std(),
    'min_ghz': values_ghz.min(),
    'max_ghz': values_ghz.max(),

    'mean_khz':  values_khz.mean(),
    'std_khz': values_khz.std(),
    'min_khz': values_khz.min(),
    'max_khz': values_khz.max()
    }

    
    ax_freq.scatter(df_filtered["Timestamp"], values_khz, s=25, color=colors[frequency_metric],
                    label=f"{frequency_metric} (session mean ref)")
    ax_freq.axhspan(stats_data[frequency_metric]['mean_khz'] - stats_data[frequency_metric]['std_khz'], stats_data[frequency_metric]['mean_khz'] + stats_data[frequency_metric]['std_khz'],     # Banda horizontal
                    color=colors[frequency_metric], alpha=0.15)

    ax_freq.xaxis.set_major_locator(mdates.MinuteLocator(interval=15)) # Modificar si las horas se plotean muy juntas
    ax_freq.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
    plt.setp(ax_freq.get_xticklabels(), rotation=45, ha='right')
    ax_freq.set_xlabel("Date & Time")
    ax_freq.set_ylabel("ΔF [kHz]")
    ax_freq.grid(True, alpha=0.3)
    ax_freq.legend(fontsize=9, loc="upper right")

    # --- 3. Statistics box ---
    stats_text = ""
    for t in metrics_to_plot:
        data_stat = stats_data[t]
        if t in coherence_metrics:
            unit = "$\\mu$s"
            stats_text += (f"std={data_stat['std']:.3f} {unit},"
                           f"{t} $\\rightarrow$ mean={data_stat['mean']:.3f} {unit}, "
                           f"min={data_stat['min']:.3f} {unit}, max={data_stat['max']:.3f} {unit}\n")
        else:
            stats_text += (f"{t} $\\rightarrow$ mean={data_stat['mean_ghz']:.6f} GHz, "
                           f"min={data_stat['min_ghz']:.6f} GHz, max={data_stat['max_ghz']:.6f} GHz, "
                           f"std={data_stat['std_khz']:.3f} kHz\n")

    ax_box.axis("off")
    ax_box.text(0.5, 0.5, stats_text.strip(),
                ha='center', va='center', fontsize=10, family='monospace',
                bbox=dict(facecolor='whitesmoke', edgecolor='gray', boxstyle='round,pad=0.6'))

    plt.show()