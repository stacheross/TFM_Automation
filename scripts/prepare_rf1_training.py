
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ROOT / "outputs"

FILES = {
    "Classvalue": OUTPUTS / "RF_Training_10m.tif",
    "VH_Pre": OUTPUTS / "RF_VH_Pre_10m.tif",
    "VH_Post": OUTPUTS / "RF_VH_Post_10m.tif",
}

arrays = {}
valid = None

for name, path in FILES.items():
    with rasterio.open(path) as src:
        data = src.read(1, masked=True)

        arrays[name] = data.data

        current_valid = (
            ~np.ma.getmaskarray(data)
            & np.isfinite(data.data)
        )

        if valid is None:
            valid = current_valid
        else:
            valid &= current_valid

# Conservar exclusivamente las muestras de entrenamiento
valid &= np.isin(arrays["Classvalue"], [1, 2])

rows, cols = np.where(valid)

training = pd.DataFrame({
    "row": rows,
    "col": cols,
    "VH_Pre": arrays["VH_Pre"][valid],
    "VH_Post": arrays["VH_Post"][valid],
    "Classvalue": arrays["Classvalue"][valid].astype(int)
})

output = OUTPUTS / "RF1_Training_Data.csv"
training.to_csv(output, index=False)

print("\nTABLA DE ENTRENAMIENTO RF1")
print("-" * 45)
print("Archivo:", output)
print("Observaciones:", len(training))

print("\nDistribución de clases:")
print(training["Classvalue"].value_counts().sort_index())

print("\nPrimeras cinco observaciones:")
print(training.head().to_string(index=False))
