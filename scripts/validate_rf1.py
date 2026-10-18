
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from sklearn.metrics import confusion_matrix, accuracy_score, cohen_kappa_score

ROOT = Path(__file__).resolve().parent.parent

POINTS = ROOT / "data" / "RF1_Puntos_Validacion_Original.shp"
RASTER = ROOT / "outputs" / "RF1_Classification_10m.tif"

points = gpd.read_file(POINTS)

with rasterio.open(RASTER) as src:
    points = points.to_crs(src.crs)

    coordinates = [
        (geom.x, geom.y)
        for geom in points.geometry
    ]

    predictions = np.array(
        [value[0] for value in src.sample(coordinates)]
    )

    rows_cols = [
        src.index(x, y)
        for x, y in coordinates
    ]

    with rasterio.open(
        ROOT / "outputs" / "RF_Training_10m.tif"
    ) as training_src:
        training = training_src.read(1)

    overlaps = 0
    for row, col in rows_cols:
        if 0 <= row < training.shape[0] and 0 <= col < training.shape[1]:
            overlaps += int(training[row, col] in [1, 2])

reference = points["GrndTruth"].to_numpy(dtype=int)
original = points["Classified"].to_numpy(dtype=int)

valid = np.isin(predictions, [1, 2])

print("\nVALIDACION RF1 RECONSTRUIDO")
print("-" * 50)
print("Puntos totales:", len(points))
print("Puntos con prediccion valida:", valid.sum())
print("Puntos sin prediccion:", (~valid).sum())
print("Puntos en celdas de entrenamiento:", overlaps)

print("\nRF1 ORIGINAL")
print(confusion_matrix(reference, original, labels=[1, 2]))
print("Exactitud:", round(accuracy_score(reference, original), 4))
print("Kappa:", round(cohen_kappa_score(reference, original), 4))

if valid.any():
    print("\nRF1 RECONSTRUIDO")
    print(confusion_matrix(
        reference[valid],
        predictions[valid],
        labels=[1, 2]
    ))
    print(
        "Exactitud:",
        round(accuracy_score(reference[valid], predictions[valid]), 4)
    )
    print(
        "Kappa:",
        round(cohen_kappa_score(reference[valid], predictions[valid]), 4)
    )

results = pd.DataFrame({
    "GrndTruth": reference,
    "RF1_Original": original,
    "RF1_Reconstruido": predictions
})

output = ROOT / "outputs" / "RF1_Validation_Comparison.csv"
results.to_csv(output, index=False)

print("\nComparacion guardada:", output)
