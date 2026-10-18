from pathlib import Path

import numpy as np
import rasterio


# 1. Localizar el proyecto
PROJECT_DIR = Path(__file__).resolve().parent.parent

OUTPUTS = PROJECT_DIR / "outputs"


# 2. Archivos de entrada
FILE_2 = OUTPUTS / "Flood_VH_minus_2dB_Slope_le_5deg_Prop50.tif"
FILE_3 = OUTPUTS / "Flood_VH_minus_3dB_Slope_le_5deg_Prop50.tif"
FILE_4 = OUTPUTS / "Flood_VH_minus_4dB_Slope_le_5deg_Prop50.tif"

OUTPUT_FILE = OUTPUTS / "VH_sensitivity_Slope5_Prop50.tif"


# 3. Leer los tres escenarios
with rasterio.open(FILE_2) as src2, \
     rasterio.open(FILE_3) as src3, \
     rasterio.open(FILE_4) as src4:

    # Comprobar alineación espacial
    if not (
        src2.crs == src3.crs == src4.crs
        and src2.transform == src3.transform == src4.transform
        and src2.shape == src3.shape == src4.shape
    ):
        raise ValueError("Los rásteres no están alineados.")

    data2 = src2.read(1)
    data3 = src3.read(1)
    data4 = src4.read(1)

    profile = src2.profile.copy()


# 4. Identificar píxeles válidos
valid = (
    (data2 != 255)
    & (data3 != 255)
    & (data4 != 255)
)


# 5. Crear ráster de sensibilidad
result = np.full(
    data2.shape,
    255,
    dtype=np.uint8
)

result[valid] = 0

# Solo aparece con -2 dB
result[
    valid
    & (data2 == 1)
    & (data3 == 0)
] = 1

# Aparece con -3 dB, pero desaparece con -4 dB
result[
    valid
    & (data3 == 1)
    & (data4 == 0)
] = 2

# Permanece incluso con -4 dB
result[
    valid
    & (data4 == 1)
] = 3


# 6. Comprobar coherencia entre escenarios
if np.any(valid & (data3 == 1) & (data2 != 1)):
    raise ValueError("El escenario -3 no está contenido en -2.")

if np.any(valid & (data4 == 1) & (data3 != 1)):
    raise ValueError("El escenario -4 no está contenido en -3.")


# 7. Guardar GeoTIFF
profile.update(
    driver="GTiff",
    dtype="uint8",
    nodata=255,
    count=1,
    compress="lzw"
)

with rasterio.open(OUTPUT_FILE, "w", **profile) as dst:
    dst.write(result, 1)


# 8. Mostrar estadísticas
print("Mapa creado:")
print(OUTPUT_FILE)

print("\nDistribución de categorías:")

for category in [0, 1, 2, 3, 255]:
    count = np.count_nonzero(result == category)

    print(
        f"Categoría {category}: "
        f"{count:,} píxeles"
    )