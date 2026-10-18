
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
import joblib

from sklearn.metrics import (
    confusion_matrix,
    accuracy_score,
    cohen_kappa_score
)

ROOT = Path(__file__).resolve().parent.parent

POINTS = ROOT / "data" / "RF2_Puntos_Validacion_Original.shp"
SAR = ROOT / "data" / "RF2_SAR_Cambio_Original.tif"
MODEL = ROOT / "outputs" / "RF2_OriginalSAR_Test.joblib"
OUTPUT = ROOT / "outputs" / "RF2_OriginalSAR_Test_Validation.csv"

features = ["VH_Pre", "VH_Post", "VH_Change"]

# Cargar modelo y referencias
rf = joblib.load(MODEL)
points = gpd.read_file(POINTS)

# Extraer los valores originales en los puntos de validacion
with rasterio.open(SAR) as src:
    points = points.to_crs("EPSG:6566")

    coordinates = [
        (geom.x, geom.y)
        for geom in points.geometry
    ]

    values = np.asarray(
        list(src.sample(coordinates))
    )

reference = points["GrndTruth"].to_numpy(dtype=int)

# Comprobar valores validos
valid = (
    np.all(np.isfinite(values), axis=1)
    & ~np.all(values == 0, axis=1)
)

print("\nVALIDACION RF2 CON SAR ORIGINAL")
print("-" * 50)
print("Puntos totales:", len(points))
print("Puntos validos:", int(valid.sum()))
print("Puntos sin datos:", int((~valid).sum()))

if not valid.all():
    raise ValueError(
        "Existen puntos sin datos SAR originales validos."
    )

# Clasificar los puntos
X = pd.DataFrame(values, columns=features)
predictions = rf.predict(X)

# Matriz de confusion
matrix = confusion_matrix(
    reference,
    predictions,
    labels=[1, 2]
)

print("\nMatriz de confusion:")
print(matrix)

print(
    "Exactitud:",
    round(accuracy_score(reference, predictions), 4)
)

print(
    "Kappa:",
    round(cohen_kappa_score(reference, predictions), 4)
)

print("Falsos positivos:", int(matrix[0, 1]))
print("Falsos negativos:", int(matrix[1, 0]))

# Guardar comparacion con el RF2 original
results = pd.DataFrame({
    "GrndTruth": reference,
    "RF2_ArcGIS_Original": points["Classified"].to_numpy(),
    "RF2_OriginalSAR_Test": predictions
})

results.to_csv(OUTPUT, index=False)

print("\nArchivo generado:", OUTPUT)
