
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
import joblib

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ROOT / "outputs"

MODEL = OUTPUTS / "RF1_Model.joblib"
PRE = OUTPUTS / "RF_VH_Pre_10m.tif"
POST = OUTPUTS / "RF_VH_Post_10m.tif"
REFERENCE = OUTPUTS / "DEM_AOI_10m_Bilinear.tif"
OUTPUT = OUTPUTS / "RF1_Classification_10m.tif"

rf = joblib.load(MODEL)

with (
    rasterio.open(PRE) as pre_src,
    rasterio.open(POST) as post_src,
    rasterio.open(REFERENCE) as ref
):
    pre = pre_src.read(1, masked=True)
    post = post_src.read(1, masked=True)
    dem = ref.read(1, masked=True)

    valid = (
        ~np.ma.getmaskarray(pre)
        & ~np.ma.getmaskarray(post)
        & ~np.ma.getmaskarray(dem)
        & np.isfinite(pre.data)
        & np.isfinite(post.data)
    )

    # 0 = NoData; 1 = No inundado; 2 = Inundado
    classification = np.zeros(ref.shape, dtype=np.uint8)

    X = pd.DataFrame({
        "VH_Pre": pre.data[valid],
        "VH_Post": post.data[valid]
    })

    classification[valid] = rf.predict(X).astype(np.uint8)

    profile = ref.profile.copy()
    profile.update(
        dtype="uint8",
        count=1,
        nodata=0,
        compress="lzw"
    )

    with rasterio.open(OUTPUT, "w", **profile) as dst:
        dst.write(classification, 1)

print("\nCLASIFICACIÓN RANDOM FOREST 1")
print("-" * 45)
print("Archivo:", OUTPUT)

for value, label in [(1, "No inundado"), (2, "Inundado")]:
    pixels = np.count_nonzero(classification == value)
    area_km2 = pixels * 100 / 1_000_000

    print(f"{label}: {pixels} píxeles")
    print(f"  Superficie: {area_km2:.4f} km²")

print("Sin datos:", np.count_nonzero(classification == 0))
