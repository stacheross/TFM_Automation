
from pathlib import Path
import numpy as np
import rasterio
from scipy.ndimage import label

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"

INPUT_FILE = OUT / "Flood_VH_minus_3dB_Slope10m_le_5deg.tif"
OUTPUT_FILE = OUT / "Flood_VH_minus_3dB_Slope10m_Min25.tif"

MIN_PIXELS = 25
NODATA = 255

# Conectividad de 8 vecinos
structure = np.ones((3, 3), dtype=np.uint8)

with rasterio.open(INPUT_FILE) as src:
    data = src.read(1)

    candidates = data == 1

    regions, total_regions = label(
        candidates,
        structure=structure
    )

    region_sizes = np.bincount(regions.ravel())

    keep = np.zeros(len(region_sizes), dtype=bool)
    keep[region_sizes >= MIN_PIXELS] = True
    keep[0] = False

    retained = candidates & keep[regions]

    result = np.full(data.shape, NODATA, dtype=np.uint8)
    result[data == 0] = 0
    result[retained] = 1
    result[candidates & ~retained] = 0

    profile = src.profile.copy()
    profile.update(
        dtype="uint8",
        nodata=NODATA,
        compress="lzw"
    )

    with rasterio.open(OUTPUT_FILE, "w", **profile) as dst:
        dst.write(result, 1)

    print("SAR — PENDIENTE 10 M + MIN25")
    print("-" * 55)
    print("Archivo:", OUTPUT_FILE)
    print("Regiones iniciales:", total_regions)
    print("Píxeles candidatos iniciales:", np.count_nonzero(candidates))
    print("Píxeles conservados:", np.count_nonzero(retained))
    print("Píxeles eliminados:", np.count_nonzero(candidates & ~retained))
    print(
        "Regiones conservadas:",
        np.count_nonzero(region_sizes[1:] >= MIN_PIXELS)
    )
