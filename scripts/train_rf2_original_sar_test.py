
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
import joblib

from sklearn.ensemble import RandomForestClassifier

ROOT = Path(__file__).resolve().parent.parent

TRAINING = ROOT / "outputs" / "RF_Training_10m.tif"
ORIGINAL = ROOT / "data" / "RF2_SAR_Cambio_Original.tif"

MODEL = ROOT / "outputs" / "RF2_OriginalSAR_Test.joblib"

# Leer las muestras rasterizadas
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

# Extraer los valores SAR originales en las mismas ubicaciones
with rasterio.open(ORIGINAL) as src:
    # Ambos rásteres comparten el sistema horizontal EPSG:6566
    values = np.asarray(
        list(src.sample(zip(xs, ys)))
    )

# Comprobar que todas las muestras tienen datos válidos
valid = (
    np.all(np.isfinite(values), axis=1)
    & ~np.all(values == 0, axis=1)
)

if not valid.all():
    raise ValueError(
        f"Hay {(~valid).sum()} muestras sin datos SAR válidos."
    )

features = ["VH_Pre", "VH_Post", "VH_Change"]

X = pd.DataFrame(values, columns=features)

# Comprobar la tercera banda
error = np.abs(
    X["VH_Change"] - (X["VH_Post"] - X["VH_Pre"])
)

print("\nRF2 - PRUEBA CON SAR ORIGINAL")
print("-" * 50)
print("Observaciones:", len(X))
print("Error máximo cambio VH:", error.max())

# Entrenar con los mismos parámetros de RF2 reconstruido
rf = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    n_jobs=-1
)

rf.fit(X, y)

joblib.dump(rf, MODEL)

print("\nModelo guardado:", MODEL)
print("Árboles:", rf.n_estimators)

print("\nImportancia de variables:")
for name, importance in zip(
    features,
    rf.feature_importances_
):
    print(f"  {name}: {importance:.4f}")
