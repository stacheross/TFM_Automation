
from pathlib import Path
import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier

ROOT = Path(__file__).resolve().parent.parent

INPUT = ROOT / "outputs" / "RF1_Training_Data.csv"
OUTPUT = ROOT / "outputs" / "RF1_Model.joblib"

# Leer las muestras originales de entrenamiento
training = pd.read_csv(INPUT)

# Variables predictoras
X = training[["VH_Pre", "VH_Post"]]

# Etiquetas:
# 1 = No inundado
# 2 = Inundado
y = training["Classvalue"]

# Entrenar Random Forest
rf = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    n_jobs=-1
)

rf.fit(X, y)

# Guardar el modelo entrenado
joblib.dump(rf, OUTPUT)

print("\nMODELO RANDOM FOREST 1")
print("-" * 45)

print("Observaciones:", len(training))
print("Variables:", list(X.columns))
print("Árboles:", rf.n_estimators)
print("Clases:", rf.classes_)
print("Modelo guardado:", OUTPUT)

print("\nImportancia de variables:")
for name, importance in zip(
    X.columns,
    rf.feature_importances_
):
    print(f"  {name}: {importance:.4f}")
