
from pathlib import Path
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"

PROP50_FILE = OUT / "Flood_SAR_Min21_Final.tif"
SLOPE10M_FILE = OUT / "Flood_VH_minus_3dB_Slope10m_Min25.tif"

OUTPUT_FILE = OUT / "SAR_Prop50_vs_Slope10m_Comparison.tif"

NODATA = 255

with rasterio.open(PROP50_FILE) as a, \
     rasterio.open(SLOPE10M_FILE) as b:

    if (
        a.crs != b.crs
        or a.transform != b.transform
        or a.shape != b.shape
    ):
        raise ValueError("Los rásteres no están alineados.")

    prop50 = a.read(1)
    slope10m = b.read(1)

    valid = (
        (a.read_masks(1) > 0)
        & (b.read_masks(1) > 0)
    )

    flood_a = valid & (prop50 == 1)
    flood_b = valid & (slope10m == 1)

    result = np.full(a.shape, NODATA, dtype=np.uint8)

    result[valid] = 0
    result[flood_a & flood_b] = 1
    result[flood_a & ~flood_b] = 2
    result[~flood_a & flood_b] = 3

    profile = a.profile.copy()
    profile.update(
        dtype="uint8",
        nodata=NODATA,
        compress="lzw"
    )

    with rasterio.open(OUTPUT_FILE, "w", **profile) as dst:
        dst.write(result, 1)

    print("COMPARACIÓN ESPACIAL SAR")
    print("-" * 55)
    print("Coinciden en ambos:", np.count_nonzero(result == 1))
    print("Solo Prop50:", np.count_nonzero(result == 2))
    print("Solo pendiente 10 m:", np.count_nonzero(result == 3))
    print("Archivo:", OUTPUT_FILE)
