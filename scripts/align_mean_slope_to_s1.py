
from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "outputs"

SLOPE_FILE = OUTPUT_DIR / "Slope_AOI_05m_degrees.tif"
REFERENCE_FILE = OUTPUT_DIR / "S1_VH_change_Post_minus_Pre.tif"
OUTPUT_FILE = OUTPUT_DIR / "Slope_mean_S1grid.tif"

with rasterio.open(SLOPE_FILE) as slope_src, \
     rasterio.open(REFERENCE_FILE) as ref_src:

    if slope_src.nodata is None:
        raise ValueError(
            "La pendiente original no tiene NoData declarado. "
            "Debemos revisar sus valores antes de continuar."
        )

    if slope_src.crs is None:
        raise ValueError(
            "La pendiente original no tiene CRS."
        )

    mean_slope = np.full(
        (ref_src.height, ref_src.width),
        -9999.0,
        dtype=np.float32
    )

    reproject(
        source=rasterio.band(slope_src, 1),
        destination=mean_slope,
        src_transform=slope_src.transform,
        src_crs=slope_src.crs,
        src_nodata=slope_src.nodata,
        dst_transform=ref_src.transform,
        dst_crs=ref_src.crs,
        dst_nodata=-9999.0,
        resampling=Resampling.average
    )

    profile = ref_src.profile.copy()
    profile.update(
        dtype="float32",
        count=1,
        nodata=-9999.0,
        compress="lzw"
    )

    with rasterio.open(OUTPUT_FILE, "w", **profile) as dst:
        dst.write(mean_slope, 1)

    valid = (
        (mean_slope != -9999.0)
        & np.isfinite(mean_slope)
    )

    print("PENDIENTE MEDIA ALINEADA CON SENTINEL-1")
    print("-" * 55)
    print("Archivo:", OUTPUT_FILE)
    print("Píxeles válidos:", np.count_nonzero(valid))
    print("Píxeles NoData:", np.count_nonzero(~valid))

    if np.any(valid):
        print("Pendiente mínima:", mean_slope[valid].min())
        print("Pendiente media:", mean_slope[valid].mean())
        print("Pendiente máxima:", mean_slope[valid].max())
        print(
            "Píxeles con pendiente media <= 5°:",
            np.count_nonzero(valid & (mean_slope <= 5))
        )
