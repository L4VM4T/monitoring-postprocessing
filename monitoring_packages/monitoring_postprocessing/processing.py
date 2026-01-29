# Cálculo de T1, T2, T2E, frecuencias, referencias
import pandas as pd

# Diccionario con conversiones de unidades
unit_conversion = {"T1": 1e6, "T2*": 1e6, "T2E": 1e6, "Qubit Frequency": 1e-9}

# Función que recibe un df (el CSV leído de un qubit) y opcionalmente un diccionario 'max_values' para establecer máximos permitidos por métrica.
# Objetivo: filtrar los datos antes de analizarlos. 
def filter_metrics(df, max_values=None):
    """
    Filtra valores negativos y por máximos.
    """
    if max_values is None:
        max_values = {"T1": None, "T2*": 100, "T2E": None, "Qubit Frequency": None}

    df = df[(df["T1"] > 0) & (df["T2*"] > 0) & (df["T2E"] > 0)]
    # Para cada métrica y su límite máximo
    for metric, max_val in max_values.items():
        if max_val is not None:
            df = df[df[metric]*unit_conversion[metric] <= max_val]
    return df

# Calcula las estadísticas de interés y calcula ΔF respecto a la media de la sesión
def compute_statistics(df):
    """
    Calcula media y std para cada métrica de coherencia y frecuencia.
    Para frecuencia devuelve ΔF respecto a la media de la sesión en kHz.
    """
    stats_data = {}
    coherence_metrics = ["T1", "T2*", "T2E"]

    # Coherence metrics
    for t in coherence_metrics:
        values = df[t] * unit_conversion[t]
        stats_data[t] = {"mean": values.mean(), "std": values.std()}

    # Frecuencia
    values_freq = df["Qubit Frequency"] * unit_conversion["Qubit Frequency"]
    session_mean = values_freq.mean()
    freq_delta = (values_freq - session_mean) * 1e6  # ΔF en kHz
    stats_data["Qubit Frequency"] = {"mean": freq_delta.mean(), "std": freq_delta.std()}

    return stats_data, freq_delta

# Flujo completo de postprocessing para un qubit: filtra datos, calcula ΔF y estadísticas
def process_qubit(df, max_values=None):
    df_filtered = filter_metrics(df, max_values)
    stats_data, freq_delta = compute_statistics(df_filtered)
    freq_delta_df = pd.DataFrame({"Freq_delta": freq_delta})
    return df_filtered, freq_delta_df, stats_data