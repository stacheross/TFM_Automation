from pathlib import Path

import numpy as np
import rasterio

from rasterio.warp import reproject, Resampling


# 1. Localizar proyecto
PROJECT_DIR = Path(__file__).resolve().parent.parent


# 2. Archivos
MNDWI_FILE = (
    PROJECT_DIR
    / "outputs"
    / "MNDWI_20171020_cloudmasked.tif"
)

S1_REFERENCE = (
    PROJECT_DIR
    / "outputs"
    / "S1_20170916_VH_dB.tif"
)

OUTPUT_FILE = (
    PROJECT_DIR
    / "outputs"
    / "MNDWI_20171020_S1grid.tif"
)


NODATA = -9999.0


# 3. Abrir Sentinel-1 como cuadrícula de referencia
with rasterio.open(S1_REFERENCE) as s1_src:

    reference_profile = s1_src.profile.copy()

    reference_crs = s1_src.crs
    reference_transform = s1_src.transform
    reference_width = s1_src.width
    reference_height = s1_src.height


# 4. Abrir MNDWI
with rasterio.open(MNDWI_FILE) as mndwi_src:

    # Crear matriz destino
    mndwi_s1 = np.full(
        (
            reference_height,
            reference_width
        ),
        NODATA,
        dtype=np.float32
    )

    # Reproyectar y alinear
    reproject(
        source=rasterio.band(mndwi_src, 1),
        destination=mndwi_s1,

        src_transform=mndwi_src.transform,
        src_crs=mndwi_src.crs,
        src_nodata=NODATA,

        dst_transform=reference_transform,
        dst_crs=reference_crs,
        dst_nodata=NODATA,

        resampling=Resampling.bilinear
    )


# 5. Preparar metadatos
reference_profile.update(
    driver="GTiff",
    dtype="float32",
    count=1,
    nodata=NODATA,
    compress="lzw"
)


# 6. Guardar
with rasterio.open(
    OUTPUT_FILE,
    "w",
    **reference_profile
) as dst:

    dst.write(
        mndwi_s1,
        1
    )


# 7. Estadísticas básicas
valid = mndwi_s1 != NODATA

print("MNDWI alineado a Sentinel-1:")
print(OUTPUT_FILE)

print("\nCuadrícula:")
print(
    "Dimensiones:",
    reference_width,
    "x",
    reference_height
)
print("CRS:", reference_crs)
print(
    "Resolución:",
    reference_transform.a,
    "x",
    abs(reference_transform.e)
)

print("\nPíxeles MNDWI válidos:")
print(
    f"{np.count_nonzero(valid):,}"
)

if np.any(valid):
    print(
        "Mínimo:",
        float(mndwi_s1[valid].min())
    )
    print(
        "Máximo:",
        float(mndwi_s1[valid].max())
    )