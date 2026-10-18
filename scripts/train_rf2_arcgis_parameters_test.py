
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
import joblib

from sklearn.ensemble import RandomForestClassifier

ROOT = Path(__file__).resolve().parent.parent

TRAINING = ROOT / "outputs" / "RF_Training_10m.tif"
ORIGINAL = ROOT / "data" / "RF2_SAR_Cambio_Original.tif"

OUTPUT = ROOT / "outputs" / "RF2_ArcGIS_Parameters_Test.joblib"

FEATURES = ["VH_Pre", "VH_Post", "VH_Change"]
SEED = 42

# Leer muestras de entrenamiento
with rasterio.open(TRAINING) as src:
    labels = src.read(1)

    rows, cols = np.where(np.isin(labels, [1, 2]))

    xs, ys = rasterio.transform.xy(
        src.transform,
        rows,
        cols,
        offset="center"
    )

    y = labels[rows, cols].astype(int)

# Extraer valores SAR originales
with rasterio.open(ORIGINAL) as src:
    values = np.asarray(
        list(src.sample(zip(xs, ys)))
    )

valid = (
    np.all(np.isfinite(values), axis=1)
    & ~np.all(values == 0, axis=1)
)

if not valid.all():
    raise ValueError("Existen muestras sin valores SAR válidos.")

X = pd.DataFrame(values, columns=FEATURES)

# Seleccionar 1.000 muestras por clase
rng = np.random.default_rng(SEED)

selected_indices = []

for classvalue in [1, 2]:
    indices = np.flatnonzero(y == classvalue)

    selected = rng.choice(
        indices,
        size=1000,
        replace=False
    )

    selected_indices.extend(selected)

selected_indices = np.array(selected_indices)

X_sample = X.iloc[selected_indices]
y_sample = y[selected_indices]

# Entrenar modelo experimental
rf = RandomForestClassifier(
    n_estimators=100,
    max_depth=30,
    random_state=SEED,
    n_jobs=-1
)

rf.fit(X_sample, y_sample)

joblib.dump(rf, OUTPUT)

print("\nRF2 - PRUEBA PARAMETROS ARCGIS")
print("-" * 50)

print("Muestras utilizadas:", len(y_sample))
print("Clase 1:", np.count_nonzero(y_sample == 1))
print("Clase 2:", np.count_nonzero(y_sample == 2))

print("Arboles:", rf.n_estimators)
print("Profundidad maxima:", rf.max_depth)

print("\nImportancia de variables:")
for name, importance in zip(
    FEATURES,
    rf.feature_importances_
):
    print(f"  {name}: {importance:.4f}")

print("\nModelo guardado:", OUTPUT)
