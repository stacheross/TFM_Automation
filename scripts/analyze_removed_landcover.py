
from pathlib import Path
import csv
import numpy as np
import rasterio

# 1. Rutas
PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "outputs"

original_path = (
    OUTPUT_DIR / "SAR_components_Original_8neighbors.tif"
)

min21_path = (
    OUTPUT_DIR / "SAR_components_Min21_8neighbors.tif"
)

landcover_path = (
    OUTPUT_DIR / "NOAA_LandCover_2010_S1grid.tif"
)

# 2. Categorías NOAA
classes = {
    2: "Impervious Surface",
    5: "Open Space Developed",
    6: "Cultivated Land",
    7: "Pasture/Hay",
    8: "Grassland",
    11: "Mixed Forest",
    12: "Scrub Shrub",
    13: "Palustrine Forested Wetland",
    14: "Palustrine Scrub Shrub Wetland",
    15: "Palustrine Emergent Wetland",
    16: "Estuarine Forested Wetland",
    17: "Estuarine Scrub Shrub Wetland",
    18: "Estuarine Emergent Wetland",
    19: "Unconsolidated Shore",
    20: "Bare Land",
    21: "Open Water"
}

# 3. Abrir los rásteres
with rasterio.open(original_path) as orig_src, \
     rasterio.open(min21_path) as min_src, \
     rasterio.open(landcover_path) as lc_src:

    for other in [min_src, lc_src]:
        if (
            orig_src.crs != other.crs
            or orig_src.transform != other.transform
            or orig_src.shape != other.shape
        ):
            raise ValueError(
                "Los rásteres no comparten la misma cuadrícula."
            )

    original = orig_src.read(1)
    min21 = min_src.read(1)
    landcover = lc_src.read(1)

    # 4. Identificar los píxeles eliminados
    removed = (original == 1) & (min21 != 1)
    retained = min21 == 1

    if np.any(retained & (original != 1)):
        raise ValueError(
            "Min21 contiene píxeles ausentes del original."
        )

    total_removed = np.count_nonzero(removed)

    print("ANÁLISIS DE PÍXELES ELIMINADOS POR MIN21")
    print("-" * 70)

    print("Píxeles originales:",
          np.count_nonzero(original == 1))

    print("Píxeles conservados:",
          np.count_nonzero(retained))

    print("Píxeles eliminados:", total_removed)

    # 5. Distribución por cobertura
    results = []

    print("\nCOBERTURAS DE LOS PÍXELES ELIMINADOS")
    print("-" * 70)

    for code, name in classes.items():

        removed_count = np.count_nonzero(
            removed & (landcover == code)
        )

        original_count = np.count_nonzero(
            (original == 1) & (landcover == code)
        )

        percentage_of_removed = (
            100 * removed_count / total_removed
            if total_removed > 0 else 0
        )

        removal_rate = (
            100 * removed_count / original_count
            if original_count > 0 else 0
        )

        results.append({
            "Codigo": code,
            "Cobertura": name,
            "SAR_original": original_count,
            "Pixeles_eliminados": removed_count,
            "Porcentaje_de_eliminados": round(
                percentage_of_removed, 2
            ),
            "Porcentaje_eliminado_de_clase": round(
                removal_rate, 2
            )
        })

        print(
            f"{code:2d} | {name:35s} | "
            f"{removed_count:5,d} | "
            f"{percentage_of_removed:6.2f}% | "
            f"{removal_rate:6.2f}%"
        )

    # 6. Agrupar categorías
    groups = {
        "Agua abierta": [21],
        "Humedales palustres": [13, 14, 15],
        "Humedales estuarinos": [16, 17, 18],
        "Orillas no consolidadas": [19],
        "Otras coberturas": [2, 5, 6, 7, 8, 11, 12, 20]
    }

    print("\nRESUMEN POR GRUPOS")
    print("-" * 70)

    for name, codes in groups.items():

        count = np.count_nonzero(
            removed & np.isin(landcover, codes)
        )

        percentage = (
            100 * count / total_removed
            if total_removed > 0 else 0
        )

        print(
            f"{name:25s}: "
            f"{count:5,d} ({percentage:.2f}%)"
        )

    # 7. Comprobar que todos los píxeles
    # eliminados tienen cobertura NOAA
    classified_removed = np.count_nonzero(
        removed & np.isin(landcover, list(classes.keys()))
    )

    print("\nCOMPROBACIÓN")
    print("-" * 70)
    print("Total eliminado:", total_removed)
    print("Total clasificado:", classified_removed)
    print(
        "Sin clasificación:",
        total_removed - classified_removed
    )

    # 8. Guardar tabla CSV
    csv_path = (
        OUTPUT_DIR / "SAR_Min21_removed_landcover.csv"
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
