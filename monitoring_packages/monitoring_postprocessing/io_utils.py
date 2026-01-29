# # Lectura y validación de CSVs
# from pathlib import Path
# import pandas as pd

# def load_qubit_csvs(qpu_name: str, qubit_name: str, dataset_root: str):
#     DATASET_DIR = Path(dataset_root) 
#     if not DATASET_DIR.exists():
#         raise FileNotFoundError(f"Dataset directory does not exist: {DATASET_DIR}")

#     csv_files = sorted(DATASET_DIR.glob(f"*_{qubit_name}.csv"))
#     if not csv_files:
#         raise FileNotFoundError(f"No CSV files found for {qubit_name} in {DATASET_DIR}")

#     csv_dfs = []
#     # for csv_file in csv_files:
#     #     df = pd.read_csv(csv_file, dtype={"Timestamp": str})
#     #     df["Timestamp"] = pd.to_datetime(df["Timestamp"])
#     #     df = df.sort_values("Timestamp").reset_index(drop=True)
#     #     csv_dfs.append((csv_file.name, df))
#     for csv_file in csv_files:
#         df = pd.read_csv(csv_file, dtype={"Timestamp": str}, encoding="utf-8-sig")
#         df.columns = df.columns.str.strip()  # <--- elimina espacios al inicio/final
#         df["Timestamp"] = pd.to_datetime(df["Timestamp"])
#         df = df.sort_values("Timestamp").reset_index(drop=True)
#         csv_dfs.append((csv_file.name, df))

#     return csv_dfs


# # Lectura y validación de CSVs robusta
# from pathlib import Path
# import pandas as pd

# def load_qubit_csvs(qpu_name: str, qubit_name: str, dataset_root: str):
#     DATASET_DIR = Path(dataset_root)
#     if not DATASET_DIR.exists():
#         raise FileNotFoundError(f"Dataset directory does not exist: {DATASET_DIR}")

#     csv_files = sorted(DATASET_DIR.glob(f"*_{qubit_name}.csv"))
#     if not csv_files:
#         raise FileNotFoundError(f"No CSV files found for {qubit_name} in {DATASET_DIR}")

#     csv_dfs = []
#     for csv_file in csv_files:
#         # Leer CSV
#         df = pd.read_csv(csv_file, dtype=str)  # leer todo como string para evitar errores

#         # Limpiar nombres de columnas y valores
#         df.columns = df.columns.str.strip()
#         if "Timestamp" not in df.columns:
#             raise KeyError(f"'Timestamp' column not found in {csv_file.name}")

#         df["Timestamp"] = df["Timestamp"].str.strip()  # eliminar espacios invisibles
#         df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")  # convertir a datetime
#         df = df.dropna(subset=["Timestamp"])  # eliminar filas con timestamps inválidos

#         df = df.sort_values("Timestamp").reset_index(drop=True)
#         csv_dfs.append((csv_file.name, df))

#     return csv_dfs




from pathlib import Path
import pandas as pd

def load_qubit_csvs(qpu_name: str, qubit_name: str, dataset_root: str):
    DATASET_DIR = Path(dataset_root) / qpu_name
    if not DATASET_DIR.exists():
        raise FileNotFoundError(f"Dataset directory does not exist: {DATASET_DIR}")

    csv_files = sorted(DATASET_DIR.glob(f"*_{qubit_name}.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found for {qubit_name} in {DATASET_DIR}")

    csv_dfs = []
    for csv_file in csv_files:
        try:
            # Leer CSV como string para evitar errores
            df = pd.read_csv(csv_file, header=None, dtype=str)

            # Si todo está en una columna, separar por comas
            if df.shape[1] == 1:
                df = df[0].str.split(",", expand=True)

            # Asignar nombres de columnas
            expected_cols = ["Iteration","Timestamp","T1","T1_std","T2*","T2*_std","T2E","T2E_std", "Qubit Frequency"]
            if df.shape[1] != len(expected_cols):
                print(f"Warning: {csv_file.name} tiene {df.shape[1]} columnas, se esperaban {len(expected_cols)}. Se omite.")
                continue
            df.columns = expected_cols

            # Convertir Timestamp a datetime
            df["Timestamp"] = df["Timestamp"].astype(str).str.strip()
            df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
            df = df.dropna(subset=["Timestamp"])

            # Convertir métricas a float
            for col in ["T1","T1_std","T2*","T2*_std","T2E","T2E_std", "Qubit Frequency"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            df = df.sort_values("Timestamp").reset_index(drop=True)
            csv_dfs.append((csv_file.name, df))

        except Exception as e:
            print(f"Error leyendo {csv_file.name}: {e}")
            continue

    if not csv_dfs:
        raise FileNotFoundError(f"No CSVs válidos encontrados para {qubit_name} en {DATASET_DIR}")

    return csv_dfs


