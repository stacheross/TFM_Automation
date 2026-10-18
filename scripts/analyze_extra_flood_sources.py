
from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"

ORIGINAL = OUT / "Flood_Final_Reviewed_Original.tif"
FINAL = OUT / "Flood_Final_Candidate_Reconstructed.tif"
MIN25 = OUT / "Flood_3dB_NoLayoverShadow_Slope5_Min25_Reconstructed.tif"
LOWVH18 = OUT / "NewWater_PostMaria_LowVH18_Reconstructed.tif"

with rasterio.open(FINAL) as final, \
     rasterio.open(ORIGINAL) as original, \
     rasterio.open(MIN25) as min25_src, \
     rasterio.open(LOWVH18) as lowvh_src:

    # Comprobar la alineación de los rásteres reconstruidos
    for src in [min25_src, lowvh_src]:
        if (
            src.crs != final.crs
            or src.transform != final.transform
            or src.shape != final.shape
        ):
            raise ValueError("Las cuadrículas reconstruidas no coinciden.")

    final_data = final.read(1)
    min25 = min25_src.read(1) == 1
    lowvh18 = lowvh_src.read(1) == 1

    # Alinear únicamente el original a la reconstrucción
    original_aligned = np.zeros(final.shape, dtype=np.uint8)

    reproject(
        source=original.read(1),
        destination=original_aligned,
        src_transform=original.transform,
        src_crs="EPSG:6566",
        src_nodata=None,
        dst_transform=final.transform,
        dst_crs=final.crs,
        dst_nodata=255,
        resampling=Resampling.nearest,
    )

    # Píxeles adicionales en la reconstrucción
    extra = (final_data == 1) & (original_aligned != 1)

    only_min25 = extra & min25 & ~lowvh18
    only_lowvh18 = extra & lowvh18 & ~min25
    both = extra & min25 & lowvh18
    neither = extra & ~min25 & ~lowvh18

    print("PROCEDENCIA DE PÍXELES ADICIONALES")
    print("-" * 48)
    print("Total adicionales:", np.count_nonzero(extra))
    print("Solo Min25:", np.count_nonzero(only_min25))
    print("Solo LowVH18:", np.count_nonzero(only_lowvh18))
    print("Ambos criterios:", np.count_nonzero(both))
    print("Ninguno:", np.count_nonzero(neither))
