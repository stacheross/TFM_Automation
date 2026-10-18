
from pathlib import Path
import csv
import numpy as np
import rasterio
from scipy import ndimage
from pyproj import CRS

# 1. Rutas
PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "outputs"

input_path = (
    OUTPUT_DIR
    / "Flood_VH_minus_3dB_Slope_le_5deg_Prop50.tif"
)

# 2. Escenarios de sensibilidad
scenarios = {
    "Original": 1,
    "Min2": 2,
    "Min6": 6,
    "Min21": 21
}

# 3. Abrir el ráster SAR
with rasterio.open(input_path) as src:

    data = src.read(1)
    detected = data == 1

    # Conectividad de 8 vecinos
    structure = np.ones((3, 3), dtype=np.uint8)

    labels, number = ndimage.label(
        detected,
        structure=structure
    )

    # Tamaño de cada componente
    sizes = np.bincount(labels.ravel())

    # El identificador 0 corresponde al fondo
    sizes[0] = 0

    # Información espacial
    transform = src.transform
    crs = CRS.from_user_input(src.crs)

    if not crs.is_geographic:
        raise ValueError(
            "Se esperaba el ráster Sentinel-1 en EPSG:4326."
        )

    if transform.b != 0 or transform.d != 0:
        raise ValueError(
            "Se requiere una cuadrícula sin rotación."
        )

    geod = crs.get_geod()

    # 4. Calcular el área geodésica por fila
    # En esta cuadrícula, cada fila tiene
    # píxeles con la misma superficie.
    area_per_row = np.zeros(src.height)

    for row in range(src.height):

        x_left = transform.c
        x_right = x_left + transform.a

        y_top = transform.f + row * transform.e
        y_bottom = y_top + transform.e

        area, _ = geod.polygon_area_perimeter(
            [x_left, x_right, x_right, x_left],
            [y_top, y_top, y_bottom, y_bottom]
        )

        area_per_row[row] = abs(area)

    # 5. Preparar el perfil de salida
    profile = src.profile.copy()

    profile.update(
        driver="GTiff",
        dtype="uint8",
        count=1,
        nodata=255,
        compress="lzw"
    )

    results = []

    original_pixels = np.count_nonzero(detected)

    print("SENSIBILIDAD POR TAMAÑO DE COMPONENTES")
    print("-" * 65)

    for name, minimum_size in scenarios.items():

        # Conservar componentes que cumplan
        # el tamaño mínimo establecido
        keep = detected & (
            sizes[labels] >= minimum_size
        )

        # Mantener los NoData originales
        output = np.zeros(data.shape, dtype="uint8")

        output[src.dataset_mask() == 0] = 255
        output[keep] = 1

        filename = (
            f"SAR_components_{name}_8neighbors.tif"
        )

        output_path = OUTPUT_DIR / filename

        with rasterio.open(
            output_path, "w", **profile
        ) as dst:
            dst.write(output, 1)

        # 6. Contar píxeles
        pixels = np.count_nonzero(keep)
        removed = original_pixels - pixels

        # 7. Calcular superficie geodésica
        pixels_per_row = np.count_nonzero(
            keep,
            axis=1
        )

        area_m2 = np.sum(
            pixels_per_row * area_per_row
        )

        area_km2 = area_m2 / 1_000_000

        percentage_removed = (
            100 * removed / original_pixels
        )

        results.append({
            "Escenario": name,
            "Tamano_minimo": minimum_size,
            "Pixeles_conservados": pixels,
            "Pixeles_excluidos": removed,
            "Porcentaje_excluido": round(
                percentage_removed, 2
            ),
            "Superficie_km2": round(area_km2, 4)
        })

        print(f"\nEscenario: {name}")
        print(f"Tamaño mínimo: {minimum_size}")
        print(f"Píxeles conservados: {pixels:,}")
        print(f"Píxeles excluidos: {removed:,}")
        print(f"Porcentaje excluido: {percentage_removed:.2f}%")
        print(f"Superficie: {area_km2:.4f} km²")

    # 8. Guardar tabla CSV
    csv_path = (
        OUTPUT_DIR
        / "SAR_component_sensitivity.csv"
    )

    with open(
        csv_path,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=results[0].keys()
        )

        writer.writeheader()
        writer.writerows(results)

    print("\nTabla guardada:")
    print(csv_path)

    print("\nAnálisis completado.")
