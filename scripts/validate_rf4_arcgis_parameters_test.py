
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

POINTS = ROOT / "data" / "RF4_Puntos_Validacion_Original.shp"
RASTER = ROOT / "data" / "RF4_Todas_Variables_Original.tif"
MODEL = ROOT / "outputs" / "RF4_ArcGIS_Parameters_Test.joblib"
OUTPUT = ROOT / "outputs" / "RF4_ArcGIS_Parameters_Validation.csv"

FEATURES = [
    "VH_Pre",
    "VH_Post",
    "VH_Change",
    "Elevacion",
    "Pendiente",
    "Distancia_Rio",
    "Cobertura_Suelo"
]

rf = joblib.load(MODEL)
points = gpd.read_file(POINTS)

# Extraer los valores originales en los puntos de validacion
with rasterio.open(RASTER) as src:
    points = points.to_crs("EPSG:6566")

    coordinates = [
        (geom.x, geom.y)
        for geom in points.geometry
    ]

    values = np.asarray(list(src.sample(coordinates)))

reference = points["GrndTruth"].to_numpy(dtype=int)

# Excluir el fondo común de las tres bandas SAR
valid = (
    np.all(np.isfinite(values), axis=1)
    & ~np.all(values[:, :3] == 0, axis=1)
)

print("\nVALIDACION RF4 - PARAMETROS ARCGIS")
print("-" * 50)
print("Puntos totales:", len(points))
print("Puntos validos:", int(valid.sum()))
print("Puntos sin datos:", int((~valid).sum()))

if not valid.all():
    raise ValueError(
        "Existen puntos sin datos validos en RF4."
    )

# Clasificar los puntos
X = pd.DataFrame(values, columns=FEATURES)
predictions = rf.predict(X)

# Calcular matriz de confusion
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

# Guardar comparacion con RF4 original
results = pd.DataFrame({
    "GrndTruth": reference,
    "RF4_ArcGIS_Original": points["Classified"].to_numpy(dtype=int),
    "RF4_Parameters_Test": predictions
})

results.to_csv(OUTPUT, index=False)

print("\nArchivo generado:", OUTPUT)
