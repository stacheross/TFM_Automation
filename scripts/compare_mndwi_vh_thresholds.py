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

FLOOD_2_FILE = (
    PROJECT_DIR
    / "outputs"
    / "Flood_VH_minus_2dB_Slope_le_5deg_Prop50.tif"
)

FLOOD_3_FILE = (
    PROJECT_DIR
    / "outputs"
    / "Flood_VH_minus_3dB_Slope_le_5deg_Prop50.tif"
)

FLOOD_4_FILE = (
    PROJECT_DIR
    / "outputs"
    / "Flood_VH_minus_4dB_Slope_le_5deg_Prop50.tif"
)


NODATA_MNDWI = -9999.0


# 3. Función para leer un ráster
def read_raster(file_path):

    with rasterio.open(file_path) as src:
        return src.read(1)


# 4. Leer datos
mndwi = read_raster(MNDWI_FILE)

flood2 = read_raster(FLOOD_2_FILE)
flood3 = read_raster(FLOOD_3_FILE)
flood4 = read_raster(FLOOD_4_FILE)


# 5. Comprobar dimensiones
if not (
    mndwi.shape
    == flood2.shape
    == flood3.shape
    == flood4.shape
):
    raise ValueError(
        "Los rásteres no tienen las mismas dimensiones."
    )


# 6. Identificar MNDWI válido
valid_mndwi = (
    (mndwi != NODATA_MNDWI)
    & np.isfinite(mndwi)
)


# 7. Crear grupos

# Escenario completo -3 dB
group_minus3 = (
    (flood3 == 1)
    & valid_mndwi
)

# Píxeles incluidos con -2 pero NO con -3
added_by_minus2 = (
    (flood2 == 1)
    & (flood3 == 0)
    & valid_mndwi
)

# Píxeles incluidos con -3 pero eliminados con -4
lost_by_minus4 = (
    (flood3 == 1)
    & (flood4 == 0)
    & valid_mndwi
)


# 8. Extraer valores MNDWI
values_minus3 = mndwi[group_minus3]

values_added_minus2 = mndwi[added_by_minus2]

values_lost_minus4 = mndwi[lost_by_minus4]


# 9. Función de estadísticas
def describe_group(name, values):

    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)

    print(
        "Píxeles con MNDWI válido:",
        f"{values.size:,}"
    )

    if values.size == 0:
        return

    print("Mínimo:", float(values.min()))
    print("Máximo:", float(values.max()))
    print("Media:", float(values.mean()))
    print("Mediana:", float(np.median(values)))

    print("\nPercentiles:")

    for percentile in [5, 25, 50, 75, 95]:

        value = np.percentile(
            values,
            percentile
        )

        print(
            f"P{percentile:02d}:",
            float(value)
        )


# 10. Mostrar resultados
describe_group(
    "ESCENARIO BASE - VH <= -3 dB",
    values_minus3
)

describe_group(
    "PIXELES ADICIONALES AL USAR -2 dB",
    values_added_minus2
)

describe_group(
    "PIXELES QUE -4 dB ELIMINA DEL ESCENARIO -3 dB",
    values_lost_minus4
)