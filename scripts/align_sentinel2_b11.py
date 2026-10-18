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

B11_FILE = (
    PROJECT_DIR
    / "data"
    / "sentinel2"
    / "extracted"
    / "T19QFA_20171020T150709_B11_20m.jp2"
)

OUTPUT_FILE = (
    PROJECT_DIR
    / "outputs"
    / "S2_B11_10m_aligned_to_B03.tif"
)


# 3. Abrir B03 como referencia
with rasterio.open(B03_FILE) as b03_src:

    reference_profile = b03_src.profile.copy()

    reference_crs = b03_src.crs
    reference_transform = b03_src.transform
    reference_width = b03_src.width
    reference_height = b03_src.height


# 4. Abrir B11
with rasterio.open(B11_FILE) as b11_src:

    # Crear matriz de destino
    b11_aligned = np.zeros(
        (
            reference_height,
            reference_width
        ),
        dtype=np.float32
    )

    # Remuestrear B11 a la cuadrícula de B03
    reproject(
        source=rasterio.band(b11_src, 1),
        destination=b11_aligned,

        src_transform=b11_src.transform,
        src_crs=b11_src.crs,

        dst_transform=reference_transform,
        dst_crs=reference_crs,

        resampling=Resampling.bilinear
    )


# 5. Preparar metadatos
reference_profile.update(
    driver="GTiff",
    dtype="float32",
    count=1,
    compress="lzw"
)


# 6. Guardar B11 alineada
with rasterio.open(
    OUTPUT_FILE,
    "w",
    **reference_profile
) as dst:

    dst.write(
        b11_aligned,
        1
    )


print("B11 alineada correctamente:")
print(OUTPUT_FILE)

print("\nCuadrícula de salida:")
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