from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling


# 1. Localizar la carpeta principal del proyecto
PROJECT_DIR = Path(__file__).resolve().parent.parent


# 2. Sentinel-1 que servirá como cuadrícula de referencia
S1_REFERENCE = (
    PROJECT_DIR
    / "outputs"
    / "S1_20170916_VH_dB.tif"
)


# 3. Umbrales de pendiente que ya hemos creado
THRESHOLDS = [6, 7]


# 4. Valor NoData para los nuevos rásteres
NODATA_VALUE = -9999.0


# 5. Abrir Sentinel-1 como referencia
with rasterio.open(S1_REFERENCE) as s1_ref:

    print("Cuadrícula de referencia Sentinel-1:")
    print("CRS:", s1_ref.crs)
    print("Resolución:", s1_ref.res)
    print(
        "Dimensiones:",
        s1_ref.width,
        "x",
        s1_ref.height
    )

    # 6. Procesar cada criterio de pendiente
    for threshold in THRESHOLDS:

        SLOPE_MASK = (
            PROJECT_DIR
            / "outputs"
            / f"Slope_threshold_le_{threshold}deg.tif"
        )

        OUTPUT_FILE = (
            PROJECT_DIR
            / "outputs"
            / f"Slope_proportion_le_{threshold}deg_S1grid.tif"
        )

        print(
            f"\nProcesando pendiente <= {threshold}°..."
        )

        with rasterio.open(SLOPE_MASK) as slope_src:

            # Crear la matriz de destino con la forma exacta de S1
            proportion = np.full(
                (s1_ref.height, s1_ref.width),
                NODATA_VALUE,
                dtype=np.float32
            )

            # 7. Reproyectar y calcular la proporción
            reproject(
                source=rasterio.band(slope_src, 1),
                destination=proportion,

                src_transform=slope_src.transform,
                src_crs=slope_src.crs,
                src_nodata=255,

                dst_transform=s1_ref.transform,
                dst_crs=s1_ref.crs,
                dst_nodata=NODATA_VALUE,

                resampling=Resampling.average
            )

            # 8. Preparar el perfil de salida
            profile = s1_ref.profile.copy()

            profile.update(
                dtype="float32",
                count=1,
                nodata=NODATA_VALUE,
                compress="lzw"
            )

            # 9. Guardar el resultado
            with rasterio.open(
                OUTPUT_FILE,
                "w",
                **profile
            ) as dst:

                dst.write(proportion, 1)

            # 10. Comprobar los valores válidos
            valid = proportion[
                proportion != NODATA_VALUE
            ]

            print(
                "Mínimo:",
                float(valid.min())
            )

            print(
                "Máximo:",
                float(valid.max())
            )

            print(
                "Media:",
                float(valid.mean())
            )

            print(
                "Archivo:",
                OUTPUT_FILE.name
            )


print(
    "\nProporciones de pendiente creadas correctamente."
)