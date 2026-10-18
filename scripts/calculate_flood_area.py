
from pathlib import Path
import numpy as np
import rasterio
from pyproj import CRS, Geod

# 1. Definir rutas
PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "outputs"

files = {
    "SAR sobre agua abierta 2010":
        "SAR_on_OpenWater_2010.tif",

    "SAR fuera de agua abierta 2010":
        "SAR_outside_OpenWater_2010.tif",

    "SAR total":
        "Flood_VH_minus_3dB_Slope_le_5deg_Prop50.tif"
}

# 2. Función para calcular superficies
def calculate_area(path):

    with rasterio.open(path) as src:

        data = src.read(1)

        if src.crs is None or not src.crs.is_geographic:
            raise ValueError(
                "Este cálculo requiere un ráster geográfico."
            )

        crs = CRS.from_user_input(src.crs)
        geod = crs.get_geod()

        transform = src.transform

        if transform.b != 0 or transform.d != 0:
            raise ValueError(
                "El script requiere una cuadrícula sin rotación."
            )

        selected = data == 1

        rows, cols = np.where(selected)

        if len(rows) == 0:
            return 0, 0.0

        # 3. Calcular las esquinas de cada píxel
        x_left = transform.c + cols * transform.a
        x_right = x_left + transform.a

        y_top = transform.f + rows * transform.e
        y_bottom = y_top + transform.e

        # 4. Calcular el área geodésica
        total_area_m2 = 0.0

        for left, right, top, bottom in zip(
            x_left, x_right, y_top, y_bottom
        ):

            longitudes = [
                left, right, right, left
            ]

            latitudes = [
                top, top, bottom, bottom
            ]

            area, perimeter = geod.polygon_area_perimeter(
                longitudes,
                latitudes
            )

            total_area_m2 += abs(area)

        area_km2 = total_area_m2 / 1_000_000

        return len(rows), area_km2


# 5. Procesar los tres rásteres
results = {}

print("SUPERFICIES DE DETECCIONES SAR")
print("-" * 65)

for name, filename in files.items():

    path = OUTPUT_DIR / filename

    count, area = calculate_area(path)

    results[name] = area

    print(f"\n{name}")
    print(f"Píxeles: {count:,}")
    print(f"Superficie: {area:.4f} km²")


# 6. Comprobar la suma
sum_parts = (
    results["SAR sobre agua abierta 2010"]
    + results["SAR fuera de agua abierta 2010"]
)

total = results["SAR total"]

print("\nCOMPROBACIÓN")
print("-" * 65)

print(f"Suma de las dos categorías: {sum_parts:.4f} km²")
print(f"Superficie SAR total:        {total:.4f} km²")
print(f"Diferencia:                  {abs(sum_parts-total):.8f} km²")
