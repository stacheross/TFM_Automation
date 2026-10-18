from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling


# 1. Localizar la carpeta principal del proyecto
PROJECT_DIR = Path(__file__).resolve().parent.parent


# 2. Definir los archivos
SLOPE_FILE = (
    PROJECT_DIR
    / "outputs"
    / "Slope_AOI_05m_degrees.tif"
)

S1_REFERENCE = (
    PROJECT_DIR
    / "outputs"
    / "S1_20170916_VH_dB.tif"
)

OUTPUT_FILE = (
    PROJECT_DIR
    / "outputs"
    / "Slope_aligned_to_S1_mean.tif"
)


# 3. Definir NoData
NODATA_VALUE = -9999.0


# 4. Abrir pendiente y Sentinel-1
with rasterio.open(SLOPE_FILE) as slope_src, \
     rasterio.open(S1_REFERENCE) as s1_ref:

    print("Pendiente original:")
    print("CRS:", slope_src.crs)
    print("Resolución:", slope_src.res)

    print("\nReferencia Sentinel-1:")
    print("CRS:", s1_ref.crs)
    print("Dimensiones:", s1_ref.width, "x", s1_ref.height)
    print("Resolución:", s1_ref.res)

    # 5. Crear una matriz con las dimensiones exactas de Sentinel-1
    destination = np.full(
        (s1_ref.height, s1_ref.width),
        NODATA_VALUE,
        dtype=np.float32
    )

    # 6. Reproyectar y agregar la pendiente
    reproject(
        source=rasterio.band(slope_src, 1),
        destination=destination,

        src_transform=slope_src.transform,
        src_crs=slope_src.crs,
        src_nodata=slope_src.nodata,

        dst_transform=s1_ref.transform,
        dst_crs=s1_ref.crs,
        dst_nodata=NODATA_VALUE,

        resampling=Resampling.average
    )

    # 7. Copiar el perfil espacial de Sentinel-1
    profile = s1_ref.profile.copy()

    profile.update(
        dtype="float32",
        count=1,
        nodata=NODATA_VALUE,
        compress="lzw"
    )

    # 8. Guardar el resultado
    with rasterio.open(
        OUTPUT_FILE,
        "w",
        **profile
    ) as dst:

        dst.write(destination, 1)


print("\nPendiente transferida a la cuadrícula Sentinel-1.")
print("Archivo creado:")
print(OUTPUT_FILE)