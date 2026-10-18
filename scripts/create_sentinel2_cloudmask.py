from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio

from rasterio.mask import mask
from shapely.geometry import mapping


# 1. Localizar el proyecto
PROJECT_DIR = Path(__file__).resolve().parent.parent


# 2. Archivos de entrada y salida
SCL_FILE = (
    PROJECT_DIR
    / "data"
    / "sentinel2"
    / "extracted"
    / "T19QFA_20171020T150709_SCL_20m.jp2"
)

AOI_FILE = (
    PROJECT_DIR
    / "data"
    / "aoi"
    / "AOI_Raster_Footprint.shp"
)

OUTPUT_FILE = (
    PROJECT_DIR
    / "outputs"
    / "S2_cloudmask_20m.tif"
)


# 3. Clases que queremos excluir
CLOUD_CLASSES = [3, 8, 9, 10]


# 4. Leer el AOI
aoi = gpd.read_file(AOI_FILE)


# 5. Abrir la SCL
with rasterio.open(SCL_FILE) as src:

    # Transformar AOI al CRS de Sentinel-2
    aoi_s2 = aoi.to_crs(src.crs)

    # Unir geometrías
    aoi_geometry = aoi_s2.geometry.union_all()

    # Recortar SCL al AOI
    scl_clip, out_transform = mask(
        src,
        [mapping(aoi_geometry)],
        crop=True,
        filled=False
    )

    scl = scl_clip[0]

    # Máscara inicial:
    # 1 = válido
    # 0 = nube/sombra
    # 255 = NoData
    cloudmask = np.full(
        scl.shape,
        255,
        dtype=np.uint8
    )

    valid_aoi = ~scl.mask

    cloudmask[valid_aoi] = 1

    cloud_pixels = (
        valid_aoi
        & np.isin(
            scl.data,
            CLOUD_CLASSES
        )
    )

    cloudmask[cloud_pixels] = 0

    # Preparar metadatos de salida
    profile = src.profile.copy()

    profile.update(
        driver="GTiff",
        height=cloudmask.shape[0],
        width=cloudmask.shape[1],
        transform=out_transform,
        count=1,
        dtype="uint8",
        nodata=255,
        compress="lzw"
    )

    # Guardar GeoTIFF
    with rasterio.open(
        OUTPUT_FILE,
        "w",
        **profile
    ) as dst:

        dst.write(
            cloudmask,
            1
        )


print("Máscara creada:")
print(OUTPUT_FILE)

print(
    "Píxeles válidos:",
    np.count_nonzero(cloudmask == 1)
)

print(
    "Nubes/sombras:",
    np.count_nonzero(cloudmask == 0)
)

print(
    "NoData:",
    np.count_nonzero(cloudmask == 255)
)