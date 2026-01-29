import pandas as pd
from pathlib import Path

input_dir = Path("/mnt/nas_monitoring/QPU-147")
output_dir = input_dir  # guardamos los CSVs en la misma carpeta

for file in input_dir.glob("*.xls*"):  # captura .xls y .xlsx
    try:
        # Leer como CSV directamente
        df = pd.read_csv(file)
        # Guardar como CSV con extensión correcta
        csv_file = output_dir / (file.stem + ".csv")
        df.to_csv(csv_file, index=False)
        print(f"Converted {file.name} -> {csv_file.name}")
    except Exception as e:
        print(f"Error converting {file.name}: {e}")
