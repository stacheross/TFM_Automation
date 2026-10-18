from pathlib import Path

import numpy as np
import rasterio


# 1. Localizar proyecto
PROJECT_DIR = Path(__file__).resolve().parent.parent


# 2. Archivos
MNDWI_FILE = (
    PROJECT_DIR
    / "outputs"
    / "MNDWI_20171020_S1grid.tif"
)

FLOOD_5_FILE = (
    PROJECT_DIR
    / "outputs"
    / "Flood_VH_minus_3dB_Slope_le_5deg_Prop50.tif"
)

ADDED_6_FILE = (
    PROJECT_DIR
    / "outputs"
    / "Added_pixels_Slope5_to_6.tif"
)


NODATA_MNDWI = -9999.0


# 3. Leer rásteres
with rasterio.open(MNDWI_FILE) as src:
    mndwi = src.read(1)

with rasterio.open(FLOOD_5_FILE) as src:
    flood5 = src.read(1)

with rasterio.open(ADDED_6_FILE) as src:
    added6 = src.read(1)


# 4. Comprobar dimensiones
if not (
    mndwi.shape
    == flood5.shape
    == added6.shape
):
    raise ValueError(
        "Los rásteres no tienen las mismas dimensiones."
    )


# 5. Seleccionar píxeles con MNDWI válido
valid_mndwi = (
    (mndwi != NODATA_MNDWI)
    & np.isfinite(mndwi)
)


# 6. Crear los dos grupos
group_5 = (
    (flood5 == 1)
    & valid_mndwi
)

group_added_6 = (
    (added6 == 1)
    & valid_mndwi
)


values_5 = mndwi[group_5]
values_added_6 = mndwi[group_added_6]


# 7. Función para mostrar estadísticas
def describe_group(name, values):

    print("\n" + "=" * 55)
    print(name)
    print("=" * 55)

    print(
        "Píxeles con MNDWI válido:",
        f"{values.size:,}"
    )

    if values.size == 0:
        return

    print(
        "Mínimo:",
        float(values.min())
    )

    print(
        "Máximo:",
        float(values.max())
    )

    print(
        "Media:",
        float(values.mean())
    )

    print(
        "Mediana:",
        float(np.median(values))
    )

    print("\nPercentiles:")

    for percentile in [
        5,
        25,
        50,
        75,
        95
    ]:

        value = np.percentile(
            values,
            percentile
        )

        print(
            f"P{percentile:02d}:",
            float(value)
        )


# 8. Mostrar resultados
describe_group(
    "GRUPO A - Escenario pendiente <= 5 grados",
    values_5
)

describe_group(
    "GRUPO B - Pixeles adicionales de 5 a 6 grados",
    values_added_6
)


# 9. Comparación directa
if (
    values_5.size > 0
    and values_added_6.size > 0
):

    difference = (
        values_added_6.mean()
        - values_5.mean()
    )

    print("\n" + "=" * 55)
    print("COMPARACIÓN")
    print("=" * 55)

    print(
        "Diferencia de medias "
        "(adicionales 6° - escenario 5°):",
        float(difference)
    )