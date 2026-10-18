
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ROOT / "outputs"

RF1_DATA = OUTPUTS / "RF1_Training_Data.csv"
CHANGE = OUTPUTS / "RF_VH_Change_10m.tif"
OUTPUT = OUTPUTS / "RF2_Training_Data.csv"

# Leer tabla original de RF1
training = pd.read_csv(RF1_DATA)

# Extraer cambio VH en los mismos píxeles
with rasterio.open(CHANGE) as src:
    change = src.read(1, masked=True)

    rows = training["row"].to_numpy(dtype=int)
    cols = training["col"].to_numpy(dtype=int)

    values = change.data[rows, cols]

    valid = (
        ~np.ma.getmaskarray(change)[rows, cols]
        & np.isfinite(values)
    )

    if not valid.all():
        raise ValueError(
            f"Hay {(~valid).sum()} muestras sin cambio VH válido."
        )

training["VH_Change"] = values

# Comprobar coherencia matemática
error = np.abs(
    training["VH_Change"]
    - (training["VH_Post"] - training["VH_Pre"])
)

print("\nPREPARACIÓN DE RF2")
print("-" * 45)
print("Observaciones:", len(training))
print("Error máximo cambio VH:", error.max())

# Guardar tabla
training.to_csv(OUTPUT, index=False)

print("Archivo:", OUTPUT)
print("\nDistribución de clases:")
print(training["Classvalue"].value_counts().sort_index())

print("\nPrimeras cinco observaciones:")
print(training.head().to_string(index=False))
