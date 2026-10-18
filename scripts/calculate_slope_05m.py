from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import Window


# 1. Localizar la carpeta principal del proyecto
PROJECT_DIR = Path(__file__).resolve().parent.parent


# 2. Definir archivos de entrada y salida
DEM_FILE = (
    PROJECT_DIR
    / "outputs"
    / "DEM_AOI_05m.tif"
)

SLOPE_FILE = (
    PROJECT_DIR
    / "outputs"
    / "Slope_AOI_05m_degrees.tif"
)


# 3. Definir el valor NoData de salida
NODATA_VALUE = -9999.0


# 4. Tamaño de los bloques de procesamiento
BLOCK_SIZE = 2048


# 5. Abrir el DEM
with rasterio.open(DEM_FILE) as src:

    # Obtener la resolución del DEM
    xres = abs(src.transform.a)
    yres = abs(src.transform.e)

    print("Resolución X:", xres, "m")
    print("Resolución Y:", yres, "m")

    # Copiar las propiedades espaciales del DEM
    profile = src.profile.copy()

    profile.update(
        dtype="float32",
        count=1,
        nodata=NODATA_VALUE,
        compress="lzw"
    )

    # Crear el ráster de pendiente
    with rasterio.open(
        SLOPE_FILE,
        "w",
        **profile
    ) as dst:

        # Recorrer el DEM por bloques
        for row_start in range(0, src.height, BLOCK_SIZE):

            for col_start in range(0, src.width, BLOCK_SIZE):

                # Calcular el tamaño real del bloque
                block_height = min(
                    BLOCK_SIZE,
                    src.height - row_start
                )

                block_width = min(
                    BLOCK_SIZE,
                    src.width - col_start
                )

                # Crear una ventana con un píxel adicional alrededor
                read_row_start = max(0, row_start - 1)
                read_col_start = max(0, col_start - 1)

                read_row_end = min(
                    src.height,
                    row_start + block_height + 1
                )

                read_col_end = min(
                    src.width,
                    col_start + block_width + 1
                )

                read_window = Window(
                    read_col_start,
                    read_row_start,
                    read_col_end - read_col_start,
                    read_row_end - read_row_start
                )

                # Leer el bloque ampliado
                dem = src.read(
                    1,
                    window=read_window,
                    masked=True
                )

                # Convertir temporalmente NoData a NaN
                dem_array = dem.filled(np.nan).astype(
                    np.float32
                )

                # Calcular las derivadas de elevación
                dz_dy, dz_dx = np.gradient(
                    dem_array,
                    yres,
                    xres
                )

                # Calcular la pendiente en grados
                slope = np.degrees(
                    np.arctan(
                        np.sqrt(
                            dz_dx ** 2
                            + dz_dy ** 2
                        )
                    )
                )

                # Determinar qué parte corresponde al bloque central
                top = row_start - read_row_start
                left = col_start - read_col_start

                slope_block = slope[
                    top:top + block_height,
                    left:left + block_width
                ]

                # Sustituir NaN por NoData
                slope_block = np.where(
                    np.isfinite(slope_block),
                    slope_block,
                    NODATA_VALUE
                ).astype(np.float32)

                # Definir dónde escribir este bloque
                write_window = Window(
                    col_start,
                    row_start,
                    block_width,
                    block_height
                )

                # Escribir el bloque
                dst.write(
                    slope_block,
                    1,
                    window=write_window
                )

            print(
                "Fila procesada:",
                min(row_start + BLOCK_SIZE, src.height),
                "de",
                src.height
            )


print("\nPendiente calculada correctamente.")
print("Archivo creado:")
print(SLOPE_FILE)