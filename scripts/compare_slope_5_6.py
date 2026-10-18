from pathlib import Path
import numpy as np
import rasterio


# 1. Localizar la carpeta principal
PROJECT_DIR = Path(__file__).resolve().parent.parent


# 2. Escenario con pendiente <= 5°
FLOOD_5_FILE = (
    PROJECT_DIR
    / "outputs"
    / "Flood_VH_minus_3dB_Slope_le_5deg_Prop50.tif"
)


# 3. Escenario con pendiente <= 6°
FLOOD_6_FILE = (
    PROJECT_DIR
    / "outputs"
    / "Flood_VH_minus_3dB_Slope_le_6deg_Prop50.tif"
)


# 4. Archivo que contendrá solamente
# los píxeles añadidos al pasar de 5° a 6°
OUTPUT_FILE = (
    PROJECT_DIR
    / "outputs"
    / "Added_pixels_Slope5_to_6.tif"
)


# 5. Abrir ambos escenarios
with rasterio.open(FLOOD_5_FILE) as flood5, \
     rasterio.open(FLOOD_6_FILE) as flood6:

    data5 = flood5.read(1)
    data6 = flood6.read(1)

    # 6. Comprobar que las cuadrículas coinciden
    if (
        flood5.crs != flood6.crs
        or flood5.transform != flood6.transform
        or flood5.width != flood6.width
        or flood5.height != flood6.height
    ):
        raise ValueError(
            "Los escenarios de 5° y 6° "
            "no están perfectamente alineados."
        )

    # 7. Identificar píxeles válidos
    valid = (
        (data5 != flood5.nodata)
        & (data6 != flood6.nodata)
    )

    # 8. Crear ráster de salida
    result = np.full(
        data5.shape,
        255,
        dtype=np.uint8
    )

    result[valid] = 0

    # 9. Identificar exclusivamente
    # lo que aparece con 6° pero no con 5°
    added_pixels = (
        valid
        & (data5 == 0)
        & (data6 == 1)
    )

    result[added_pixels] = 1

    # 10. Preparar propiedades del archivo
    profile = flood5.profile.copy()

    profile.update(
        dtype="uint8",
        count=1,
        nodata=255,
        compress="lzw"
    )

    # 11. Guardar resultado
    with rasterio.open(
        OUTPUT_FILE,
        "w",
        **profile
    ) as dst:

        dst.write(result, 1)


# 12. Contar los píxeles añadidos
number_added = np.count_nonzero(
    result == 1
)


print("\nComparación 5° → 6° completada.")

print(
    "Píxeles añadidos con 6°:",
    f"{number_added:,}"
)

print("\nArchivo creado:")
print(OUTPUT_FILE)