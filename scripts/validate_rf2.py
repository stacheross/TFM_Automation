
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio

from sklearn.metrics import (
    confusion_matrix,
    accuracy_score,
    cohen_kappa_score
)

ROOT = Path(__file__).resolve().parent.parent

POINTS = ROOT / "data" / "RF1_Puntos_Validacion_Original.shp"
RASTER = ROOT / "outputs" / "RF2_Classification_10m.tif"
OUTPUT = ROOT / "outputs" / "RF2_Validation_Comparison.csv"

points = gpd.read_file(POINTS)

with rasterio.open(RASTER) as src:
    points = points.to_crs(src.crs)

    coordinates = [
        (geometry.x, geometry.y)
        for geometry in points.geometry
    ]

    predictions = np.array([
        value[0] for value in src.sample(coordinates)
    ])

reference = points["GrndTruth"].to_numpy(dtype=int)

valid = np.isin(predictions, [1, 2])

print("\nVALIDACIÓN RF2 RECONSTRUIDO")
print("-" * 50)

print("Puntos totales:", len(points))
print("Puntos válidos:", np.count_nonzero(valid))
print("Puntos sin predicción:", np.count_nonzero(~valid))

if valid.any():
    matrix = confusion_matrix(
        reference[valid],
        predictions[valid],
        labels=[1, 2]
    )

    print("\nMatriz de confusión RF2:")
    print(matrix)

    print(
        "Exactitud:",
        round(accuracy_score(reference[valid], predictions[valid]), 4)
    )

    print(
        "Kappa:",
        round(cohen_kappa_score(reference[valid], predictions[valid]), 4)
    )

    print("Falsos positivos:", int(matrix[0, 1]))
    print("Falsos negativos:", int(matrix[1, 0]))

results = pd.DataFrame({
    "GrndTruth": reference,
    "RF2_Reconstruido": predictions
})

results.to_csv(OUTPUT, index=False)

print("\nArchivo:", OUTPUT)
