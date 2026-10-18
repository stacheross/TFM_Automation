
from pathlib import Path
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"

CHANGE_FILE = OUT / "S1_VH_change_Post_minus_Pre.tif"
SLOPE_FILE = OUT / "Slope_AOI_10m_S1grid.tif"

OUTPUT_FILE = OUT / "Flood_VH_minus_3dB_Slope10m_le_5deg.tif"

NODATA = 255

with rasterio.open(CHANGE_FILE) as change, \
     rasterio.open(SLOPE_FILE) as slope:

    if (
        change.crs != slope.crs
        or change.transform != slope.transform
        or change.shape != slope.shape
    ):
        raise ValueError("Los rásteres no comparten la misma cuadrícula.")

    vh = change.read(1, masked=True)
    slope_data = slope.read(1, masked=True)

    valid = (
        ~np.ma.getmaskarray(vh)
        & ~np.ma.getmaskarray(slope_data)
        & np.isfinite(vh.data)
        & np.isfinite(slope_data.data)
    )

    flood = np.full(change.shape, NODATA, dtype=np.uint8)

    flood[valid] = 0

    candidates = (
        valid
        & (vh.data <= -3.0)
        & (slope_data.data <= 5.0)
    )

    flood[candidates] = 1

    profile = change.profile.copy()
    profile.update(
        driver="GTiff",
        dtype="uint8",
        count=1,
        nodata=NODATA,
        compress="lzw"
    )

    with rasterio.open(OUTPUT_FILE, "w", **profile) as dst:
        dst.write(flood, 1)

    print("DELIMITACIÓN SAR — PENDIENTE DE 10 M")
    print("-" * 55)
    print("Archivo:", OUTPUT_FILE)
    print("Píxeles válidos:", np.count_nonzero(valid))
    print("Píxeles candidatos a inundación:", np.count_nonzero(candidates))
    print("Píxeles no inundados:", np.count_nonzero(flood == 0))
    print("Píxeles NoData:", np.count_nonzero(flood == NODATA))
