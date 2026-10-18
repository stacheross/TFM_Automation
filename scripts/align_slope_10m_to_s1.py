
from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"

SLOPE_FILE = OUT / "Slope_AOI_10m_Aligned.tif"
SAR_FILE = OUT / "S1_VH_change_Post_minus_Pre.tif"
OUTPUT_FILE = OUT / "Slope_AOI_10m_S1grid.tif"

NODATA = -9999.0

with rasterio.open(SLOPE_FILE) as slope, rasterio.open(SAR_FILE) as sar:

    if slope.crs is None or sar.crs is None:
        raise ValueError("Alguno de los rásteres no tiene CRS.")

    # Crear la matriz con las dimensiones exactas de Sentinel-1
    aligned = np.full(
        (sar.height, sar.width),
        NODATA,
        dtype=np.float32
    )

    # Reproyectar mediante vecino más próximo
    reproject(
        source=rasterio.band(slope, 1),
        destination=aligned,
        src_transform=slope.transform,
        src_crs=slope.crs,
        src_nodata=slope.nodata,
        dst_transform=sar.transform,
        dst_crs=sar.crs,
        dst_nodata=NODATA,
        resampling=Resampling.nearest
    )

    # Conservar solamente los píxeles válidos de Sentinel-1
    sar_data = sar.read(1, masked=True)
    sar_valid = (
        ~np.ma.getmaskarray(sar_data)
        & np.isfinite(sar_data.data)
    )

    slope_valid = (
        np.isfinite(aligned)
        & (aligned != NODATA)
    )

    valid = sar_valid & slope_valid
    aligned[~valid] = NODATA

    profile = sar.profile.copy()
    profile.update(
        driver="GTiff",
        dtype="float32",
        count=1,
        nodata=NODATA,
        compress="lzw"
    )

    with rasterio.open(OUTPUT_FILE, "w", **profile) as dst:
        dst.write(aligned, 1)

    print("PENDIENTE DE 10 M ALINEADA CON SENTINEL-1")
    print("-" * 55)
    print("Archivo:", OUTPUT_FILE)
    print("CRS:", sar.crs)
    print("Dimensiones:", aligned.shape)
    print("Misma cuadrícula:", True)
    print("Píxeles válidos:", np.count_nonzero(valid))

    if np.any(valid):
        print("Pendiente mínima:", aligned[valid].min())
        print("Pendiente máxima:", aligned[valid].max())
        print(
            "Píxeles con pendiente <= 5°:",
            np.count_nonzero(valid & (aligned <= 5))
        )
