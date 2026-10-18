
from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling

# 1. Localizar la carpeta principal del proyecto
PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "outputs"

# 2. Definir los archivos
dem_path = OUTPUT_DIR / "DEM_AOI_05m.tif"

reference_path = (
    OUTPUT_DIR / "S1_20170916_VH_dB.tif"
)

output_path = OUTPUT_DIR / "DEM_AOI_S1grid.tif"

# 3. Abrir el DEM y la referencia Sentinel-1
with rasterio.open(dem_path) as dem_src, \
     rasterio.open(reference_path) as ref:

    # Preparar la cuadrícula de salida
    destination = np.full(
        (ref.height, ref.width),
        -9999.0,
        dtype="float32"
    )

    # 4. Reproyectar y remuestrear el DEM
    reproject(
        source=rasterio.band(dem_src, 1),
        destination=destination,
        src_transform=dem_src.transform,
        src_crs=dem_src.crs,
        src_nodata=dem_src.nodata,
        dst_transform=ref.transform,
        dst_crs=ref.crs,
        dst_nodata=-9999.0,
        resampling=Resampling.average,
        init_dest_nodata=True
    )

    # 5. Preparar las propiedades del GeoTIFF
    profile = ref.profile.copy()

    profile.update(
        driver="GTiff",
        count=1,
        dtype="float32",
        nodata=-9999.0,
        compress="lzw"
    )

    # 6. Guardar el DEM alineado
    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(destination, 1)

    # 7. Comprobar los resultados
    valid = (
        np.isfinite(destination)
        & (destination != -9999.0)
    )

    print("DEM ALINEADO CON SENTINEL-1")
    print("-" * 55)

    print("Archivo:", output_path)
    print("CRS:", ref.crs)
    print("Dimensiones:", ref.width, "x", ref.height)
    print("Píxeles válidos:", np.count_nonzero(valid))
    print("Píxeles NoData:", np.count_nonzero(~valid))

    if np.any(valid):
        print(
            "Elevación mínima:",
            round(float(destination[valid].min()), 2),
            "m"
        )

        print(
            "Elevación máxima:",
            round(float(destination[valid].max()), 2),
            "m"
        )

        print(
            "Elevación media:",
            round(float(destination[valid].mean()), 2),
            "m"
        )
