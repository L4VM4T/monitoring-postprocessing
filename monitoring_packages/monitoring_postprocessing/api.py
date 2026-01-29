# Funciones de alto nivel 
# api.py
from .io_utils import load_qubit_csvs
from .processing import process_qubit
from .plotting import plot_qubit_postprocessing

def run_qubit_postprocessing(qpu_name, qubit_name, dataset_root="datasets", max_values=None, bins=20):
    """
    Flujo completo de postprocessing de un qubit:
    1. Carga los CSVs de la carpeta correspondiente.
    2. Filtra y calcula estadísticas + ΔF.
    3. Plotea postprocessing y histograma de T1.
    
    Parameters:
    -----------
    qpu_name : str
        Nombre del QPU
    qubit_name : str
        Nombre del qubit
    dataset_root : str
        Carpeta raíz de los datasets
    max_values : dict, optional
        Diccionario con máximos permitidos por métrica
    bins : int
        Número de bins para el histograma
    """
    # 1️⃣ Carga CSVs
    csv_dfs = load_qubit_csvs(qpu_name=qpu_name, qubit_name=qubit_name, dataset_root=dataset_root)
    if not csv_dfs:
        raise FileNotFoundError(f"No CSVs found for qubit {qubit_name} in QPU {qpu_name}")

    # 2️⃣ Itera sobre cada CSV
    for csv_name, df in csv_dfs:
        df_filtered, freq_delta_df, stats_data = process_qubit(df, max_values=max_values)
        
        print(f"Processed {csv_name}")
        print("Stats data:", stats_data)
        
        # 3️⃣ Plotting
        plot_qubit_postprocessing(df_filtered, freq_delta_df, stats_data, qubit_name=qubit_name, bins=bins)

