
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
import joblib

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ROOT / "outputs"

MODEL = OUTPUTS / "RF2_Model.joblib"
REFERENCE = OUTPUTS / "DEM_AOI_10m_Bilinear.tif"
OUTPUT = OUTPUTS / "RF2_Classification_10m.tif"

FILES = {
    "VH_Pre": OUTPUTS / "RF_VH_Pre_10m.tif",
    "VH_Post": OUTPUTS / "RF_VH_Post_10m.tif",
    "VH_Change": OUTPUTS / "RF_VH_Change_10m.tif"
}

rf = joblib.load(MODEL)

with rasterio.open(REFERENCE) as ref:
    profile = ref.profile.copy()
    dem = ref.read(1, masked=True)

    valid = (
        ~np.ma.getmaskarray(dem)
        & np.isfinite(dem.data)
    )

    arrays = {}

    for name, path in FILES.items():
        with rasterio.open(path) as src:
            if (
                src.crs != ref.crs
                or src.transform != ref.transform
                or src.shape != ref.shape
            ):
                raise ValueError(f"Ráster no alineado: {name}")

            data = src.read(1, masked=True)
            arrays[name] = data.data

            valid &= (
                ~np.ma.getmaskarray(data)
                & np.isfinite(data.data)
            )

    classification = np.zeros(ref.shape, dtype=np.uint8)

    X = pd.DataFrame({
        name: array[valid]
        for name, array in arrays.items()
    })

    classification[valid] = rf.predict(X).astype(np.uint8)

    profile.update(
        dtype="uint8",
        count=1,
        nodata=0,
        compress="lzw"
    )

    with rasterio.open(OUTPUT, "w", **profile) as dst:
        dst.write(classification, 1)

print("\nCLASIFICACIÓN RANDOM FOREST 2")
print("-" * 45)
print("Archivo:", OUTPUT)

for value, label in [(1, "No inundado"), (2, "Inundado")]:
    pixels = np.count_nonzero(classification == value)
    area_km2 = pixels * 100 / 1_000_000

    print(f"{label}: {pixels} píxeles")
    print(f"  Superficie: {area_km2:.4f} km²")

print("Sin datos:", np.count_nonzero(classification == 0))
