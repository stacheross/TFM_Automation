
from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling

PROJECT_DIR = Path(__file__).resolve().parent.parent

landcover_path = (
    PROJECT_DIR / "data" / "landcover"
    / "NOAA_LandCover_2010_Clip.tif"
)

reference_path = (
    PROJECT_DIR / "outputs"
    / "S1_20170916_VH_dB.tif"
)

output_path = (
    PROJECT_DIR / "outputs"
    / "NOAA_LandCover_2010_S1grid.tif"
)

valid_codes = [
    2, 5, 6, 7, 8, 11, 12,
    13, 14, 15, 16, 17, 18,
    19, 20, 21
]

with rasterio.open(landcover_path) as src, \
     rasterio.open(reference_path) as ref:

    source = src.read(1)

    source_clean = np.where(
        np.isin(source, valid_codes),
        source,
        255
    ).astype("uint8")

    destination = np.full(
        (ref.height, ref.width),
        255,
        dtype="uint8"
    )

    reproject(
        source=source_clean,
        destination=destination,
        src_transform=src.transform,
        src_crs=src.crs,
        src_nodata=255,
        dst_transform=ref.transform,
        dst_crs=ref.crs,
        dst_nodata=255,
        resampling=Resampling.nearest
    )

    profile = ref.profile.copy()

    profile.update(
        driver="GTiff",
        count=1,
        dtype="uint8",
        nodata=255,
        compress="lzw"
    )

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(destination, 1)

    print("Cobertura alineada:")
    print(output_path)

    print("\nCuadrícula:")
    print("CRS:", ref.crs)
    print("Dimensiones:", ref.width, "x", ref.height)

    values, counts = np.unique(
        destination,
        return_counts=True
    )

    print("\nDistribución de clases:")

    for value, count in zip(values, counts):
        print(f"Clase {value}: {count:,} píxeles")
