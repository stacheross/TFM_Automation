
from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"

original_path = OUT / "Flood_Final_Reviewed_Original.tif"
final_path = OUT / "Flood_Final_Candidate_Reconstructed.tif"
min25_path = OUT / "Flood_3dB_NoLayoverShadow_Slope5_Min25_Reconstructed.tif"
lowvh_path = OUT / "NewWater_PostMaria_LowVH18_Reconstructed.tif"

output_path = OUT / "Flood_Extra_Pixels_By_Source.tif"

with rasterio.open(original_path) as original, \
     rasterio.open(final_path) as final, \
     rasterio.open(min25_path) as min25_src, \
     rasterio.open(lowvh_path) as lowvh_src:

    for src in [min25_src, lowvh_src]:
        if (
            src.shape != final.shape
            or src.crs != final.crs
            or src.transform != final.transform
        ):
            raise ValueError("Las cuadrículas no coinciden.")

    original_aligned = np.full(
        final.shape, 255, dtype=np.uint8
    )

    reproject(
        source=original.read(1),
        destination=original_aligned,
        src_transform=original.transform,
        src_crs="EPSG:6566",
        src_nodata=None,
        dst_transform=final.transform,
        dst_crs=final.crs,
        dst_nodata=255,
        resampling=Resampling.nearest
    )

    final_data = final.read(1)
    min25 = min25_src.read(1) == 1
    lowvh = lowvh_src.read(1) == 1

    extra = (final_data == 1) & (original_aligned != 1)

    diagnostic = np.zeros(final.shape, dtype=np.uint8)

    diagnostic[extra & min25 & ~lowvh] = 1
    diagnostic[extra & lowvh & ~min25] = 2
    diagnostic[extra & min25 & lowvh] = 3

    # NoData fuera del área válida de la reconstrucción
    if final.nodata is not None:
        diagnostic[final_data == final.nodata] = 255

    profile = final.profile.copy()
    profile.update(
        dtype="uint8",
        count=1,
        nodata=255,
        compress="lzw"
    )

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(diagnostic, 1)

    print("Ráster creado:", output_path)
    print("Solo Min25:", np.count_nonzero(diagnostic == 1))
    print("Solo LowVH18:", np.count_nonzero(diagnostic == 2))
    print("Ambos:", np.count_nonzero(diagnostic == 3))
    print("Total:", np.count_nonzero(
        (diagnostic >= 1) & (diagnostic <= 3)
    ))
