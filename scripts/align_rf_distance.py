
from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling

ROOT = Path(__file__).resolve().parent.parent

INPUT = ROOT / "data" / "RF_Distancia_Rio_Original.tif"
REFERENCE = ROOT / "outputs" / "RF_Training_10m.tif"
OUTPUT = ROOT / "outputs" / "RF_Distancia_Rio_10m.tif"

with rasterio.open(INPUT) as src, rasterio.open(REFERENCE) as ref:

    distance = np.full(
        ref.shape,
        -9999.0,
        dtype=np.float32
    )

    reproject(
        source=rasterio.band(src, 1),
        destination=distance,
        src_transform=src.transform,
        src_crs=src.crs,
        src_nodata=src.nodata,
        dst_transform=ref.transform,
        dst_crs=ref.crs,
        dst_nodata=-9999.0,
        resampling=Resampling.bilinear
    )

    profile = ref.profile.copy()
    profile.update(
        dtype="float32",
        count=1,
        nodata=-9999.0,
        compress="lzw"
    )

    with rasterio.open(OUTPUT, "w", **profile) as dst:
        dst.write(distance, 1)

    valid = (distance != -9999.0) & np.isfinite(distance)

    print("\nDISTANCIA AL RÍO ALINEADA")
    print("-" * 45)
    print("Archivo:", OUTPUT)
    print("CRS:", ref.crs)
    print("Dimensiones:", ref.shape)
    print("Resolución:", ref.res)
    print("Píxeles válidos:", np.count_nonzero(valid))

    if np.any(valid):
        print("Distancia mínima:", float(distance[valid].min()))
        print("Distancia máxima:", float(distance[valid].max()))
