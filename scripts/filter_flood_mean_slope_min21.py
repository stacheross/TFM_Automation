
from pathlib import Path
import numpy as np
import rasterio
from scipy import ndimage

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "outputs"

INPUT_FILE = OUTPUT_DIR / "Flood_VH_minus_3dB_MeanSlope_le_5deg.tif"
OUTPUT_FILE = OUTPUT_DIR / "Flood_VH_minus_3dB_MeanSlope5_Min21.tif"

MIN_PIXELS = 21

with rasterio.open(INPUT_FILE) as src:
    data = src.read(1)
    profile = src.profile.copy()

    flood = data == 1

    # Conectividad de ocho vecinos
    structure = np.ones((3, 3), dtype=np.uint8)

    labels, num_components = ndimage.label(
        flood,
        structure=structure
    )

    component_sizes = np.bincount(labels.ravel())

    keep = (
        flood
        & (component_sizes[labels] >= MIN_PIXELS)
    )

    result = np.full(data.shape, 255, dtype=np.uint8)
    result[data == 0] = 0
    result[keep] = 1
    result[flood & ~keep] = 0

    profile.update(
        dtype="uint8",
        nodata=255,
        compress="lzw"
    )

    with rasterio.open(OUTPUT_FILE, "w", **profile) as dst:
        dst.write(result, 1)

    print("ESCENARIO PENDIENTE MEDIA <= 5° + MIN21")
    print("-" * 55)
    print("Componentes originales:", num_components)
    print("Píxeles antes de Min21:", np.count_nonzero(flood))
    print("Píxeles conservados:", np.count_nonzero(keep))
    print("Píxeles eliminados:", np.count_nonzero(flood & ~keep))
    print("Archivo generado:", OUTPUT_FILE)
