
from pathlib import Path
import numpy as np
import rasterio

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "outputs"

VH_FILE = OUTPUT_DIR / "S1_VH_change_Post_minus_Pre.tif"
SLOPE_FILE = OUTPUT_DIR / "Slope_mean_S1grid.tif"

OUTPUT_FILE = (
    OUTPUT_DIR / "Flood_VH_minus_3dB_MeanSlope_le_5deg.tif"
)

with rasterio.open(VH_FILE) as vh_src, \
     rasterio.open(SLOPE_FILE) as slope_src:

    # Comprobar alineación
    if (
        vh_src.crs != slope_src.crs
        or vh_src.transform != slope_src.transform
        or vh_src.shape != slope_src.shape
    ):
        raise ValueError(
            "Los rásteres VH y pendiente no están alineados."
        )

    vh = vh_src.read(1, masked=True)
    slope = slope_src.read(1, masked=True)

    # Identificar datos válidos
    valid = (
        ~np.ma.getmaskarray(vh)
        & ~np.ma.getmaskarray(slope)
        & np.isfinite(vh.data)
        & np.isfinite(slope.data)
    )

    # Crear ráster de salida
    result = np.full(
        vh_src.shape,
        255,
        dtype=np.uint8
    )

    result[valid] = 0

    # Aplicar criterios SAR
    flood_mask = (
        valid
        & (vh.data <= -3)
        & (slope.data <= 5)
    )

    result[flood_mask] = 1

    # Guardar
    profile = vh_src.profile.copy()
    profile.update(
        dtype="uint8",
        count=1,
        nodata=255,
        compress="lzw"
    )

    with rasterio.open(OUTPUT_FILE, "w", **profile) as dst:
        dst.write(result, 1)

    print("ESCENARIO SAR SIN PROP50")
    print("-" * 55)

    print("Criterio VH: POST - PRE <= -3 dB")
    print("Criterio topográfico: pendiente media <= 5°")

    print(
        "Píxeles detectados:",
        np.count_nonzero(flood_mask)
    )

    print(
        "Píxeles válidos:",
        np.count_nonzero(valid)
    )

    print("Archivo generado:")
    print(OUTPUT_FILE)
