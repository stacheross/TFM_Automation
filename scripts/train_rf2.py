
from pathlib import Path
import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier

ROOT = Path(__file__).resolve().parent.parent

INPUT = ROOT / "outputs" / "RF2_Training_Data.csv"
OUTPUT = ROOT / "outputs" / "RF2_Model.joblib"

# Leer muestras de entrenamiento
training = pd.read_csv(INPUT)

# Variables predictoras de RF2
features = ["VH_Pre", "VH_Post", "VH_Change"]

X = training[features]
y = training["Classvalue"]

# Entrenar Random Forest
rf = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    n_jobs=-1
)

rf.fit(X, y)

# Guardar el modelo
joblib.dump(rf, OUTPUT)

print("\nMODELO RANDOM FOREST 2")
print("-" * 45)

print("Observaciones:", len(training))
print("Variables:", features)
print("Árboles:", rf.n_estimators)
print("Clases:", rf.classes_)
print("Modelo guardado:", OUTPUT)

print("\nImportancia de variables:")

for name, importance in zip(
    features,
    rf.feature_importances_
):
    print(f"  {name}: {importance:.4f}")
