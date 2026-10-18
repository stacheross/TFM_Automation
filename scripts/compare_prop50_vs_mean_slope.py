
from pathlib import Path
import numpy as np
import rasterio

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "outputs"

PROP50_FILE = OUTPUT_DIR / "Flood_SAR_Min21_Final.tif"
MEAN_FILE = OUTPUT_DIR / "Flood_VH_minus_3dB_MeanSlope5_Min21.tif"
OUTPUT_FILE = OUTPUT_DIR / "SAR_Prop50_vs_MeanSlope5_Comparison.tif"

with rasterio.open(PROP50_FILE) as a, \
     rasterio.open(MEAN_FILE) as b:

    if (
        a.crs != b.crs
        or a.transform != b.transform
        or a.shape != b.shape
    ):
        raise ValueError("Los rásteres no están alineados.")

    prop50 = a.read(1)
    mean = b.read(1)

    valid = np.isin(prop50, [0, 1]) & np.isin(mean, [0, 1])

    result = np.full(a.shape, 255, dtype=np.uint8)
    result[valid] = 0

    # 1 = Detectado en ambos
    result[valid & (prop50 == 1) & (mean == 1)] = 1

    # 2 = Solo Prop50
    result[valid & (prop50 == 1) & (mean == 0)] = 2

    # 3 = Solo pendiente media
    result[valid & (prop50 == 0) & (mean == 1)] = 3

    profile = a.profile.copy()
    profile.update(
        dtype="uint8",
        count=1,
        nodata=255,
        compress="lzw"
    )

    with rasterio.open(OUTPUT_FILE, "w", **profile) as dst:
        dst.write(result, 1)

    print("COMPARACIÓN ESPACIAL SAR")
    print("-" * 55)
    print("Coinciden en ambos:", np.count_nonzero(result == 1))
    print("Solo Prop50:", np.count_nonzero(result == 2))
    print("Solo pendiente media:", np.count_nonzero(result == 3))
    print("Archivo:", OUTPUT_FILE)
