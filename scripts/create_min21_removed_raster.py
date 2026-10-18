
from pathlib import Path
import numpy as np
import rasterio

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "outputs"

original_path = (
    OUTPUT_DIR / "SAR_components_Original_8neighbors.tif"
)

min21_path = (
    OUTPUT_DIR / "SAR_components_Min21_8neighbors.tif"
)

output_path = (
    OUTPUT_DIR / "SAR_Removed_by_Min21.tif"
)

with rasterio.open(original_path) as original_src, \
     rasterio.open(min21_path) as min21_src:

    if (
        original_src.crs != min21_src.crs
        or original_src.transform != min21_src.transform
        or original_src.shape != min21_src.shape
    ):
        raise ValueError(
            "Los rásteres no comparten la misma cuadrícula."
        )

    original = original_src.read(1)
    min21 = min21_src.read(1)

    # Identificar las detecciones eliminadas
    removed = (original == 1) & (min21 != 1)

    # Crear ráster: 1 = eliminado, 255 = NoData
    result = np.full(
        original.shape,
        255,
        dtype=np.uint8
    )

    result[removed] = 1

    profile = original_src.profile.copy()
    profile.update(
        dtype="uint8",
        nodata=255,
        compress="lzw"
    )

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(result, 1)

    print("RÁSTER DE DETECCIONES ELIMINADAS")
    print("-" * 55)
    print("Píxeles eliminados:", np.count_nonzero(removed))
    print("Archivo:", output_path)
