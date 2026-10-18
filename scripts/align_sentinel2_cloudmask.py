from pathlib import Path

import numpy as np
import rasterio

from rasterio.warp import reproject, Resampling


# 1. Localizar el proyecto
PROJECT_DIR = Path(__file__).resolve().parent.parent


# 2. Definir archivos
B03_FILE = (
    PROJECT_DIR
    / "data"
    / "sentinel2"
    / "extracted"
    / "T19QFA_20171020T150709_B03_10m.jp2"
)

CLOUDMASK_FILE = (
    PROJECT_DIR
    / "outputs"
    / "S2_cloudmask_20m.tif"
)

OUTPUT_FILE = (
    PROJECT_DIR
    / "outputs"
    / "S2_cloudmask_10m_aligned_to_B03.tif"
)


# 3. Abrir B03 como referencia
with rasterio.open(B03_FILE) as b03_src:

    reference_profile = b03_src.profile.copy()

    reference_crs = b03_src.crs
    reference_transform = b03_src.transform
    reference_width = b03_src.width
    reference_height = b03_src.height


# 4. Abrir máscara de nubes
with rasterio.open(CLOUDMASK_FILE) as mask_src:

    # Crear matriz de destino llena inicialmente de NoData
    cloudmask_10m = np.full(
        (
            reference_height,
            reference_width
        ),
        255,
        dtype=np.uint8
    )

    # Llevar la máscara a la cuadrícula de B03
    reproject(
        source=rasterio.band(mask_src, 1),
        destination=cloudmask_10m,

        src_transform=mask_src.transform,
        src_crs=mask_src.crs,

        src_nodata=255,

        dst_transform=reference_transform,
        dst_crs=reference_crs,
        dst_nodata=255,

        resampling=Resampling.nearest
    )


# 5. Preparar metadatos de salida
reference_profile.update(
    driver="GTiff",
    dtype="uint8",
    count=1,
    nodata=255,
    compress="lzw"
)


# 6. Guardar resultado
with rasterio.open(
    OUTPUT_FILE,
    "w",
    **reference_profile
) as dst:

    dst.write(
        cloudmask_10m,
        1
    )


# 7. Mostrar estadísticas
print("Máscara alineada correctamente:")
print(OUTPUT_FILE)

print("\nCuadrícula:")
print(
    "Dimensiones:",
    reference_width,
    "x",
    reference_height
)

print(
    "CRS:",
    reference_crs
)

print(
    "Resolución:",
    reference_transform.a,
    "x",
    abs(reference_transform.e)
)

print("\nValores:")
print(
    "Válidos:",
    np.count_nonzero(cloudmask_10m == 1)
)

print(
    "Nubes/sombras:",
    np.count_nonzero(cloudmask_10m == 0)
)

print(
    "NoData:",
    np.count_nonzero(cloudmask_10m == 255)
)