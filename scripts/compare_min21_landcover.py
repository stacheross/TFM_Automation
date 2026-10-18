
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

# 2. Clases NOAA 2010
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

# 3. Abrir los tres rásteres
with rasterio.open(original_path) as orig_src, \
     rasterio.open(min21_path) as min_src, \
     rasterio.open(landcover_path) as lc_src:

    for src in [min_src, lc_src]:
        if (
            src.crs != orig_src.crs
            or src.transform != orig_src.transform
            or src.shape != orig_src.shape
        ):
            raise ValueError(
                "Los rásteres no comparten la misma cuadrícula."
            )

    original = orig_src.read(1) == 1
    min21 = min_src.read(1) == 1
    landcover = lc_src.read(1)

    # 4. Comprobaciones
    if np.any(min21 & ~original):
        raise ValueError(
            "Min21 contiene detecciones ausentes del original."
        )

    total_original = np.count_nonzero(original)
    total_min21 = np.count_nonzero(min21)

    print("COMPARACIÓN DE COBERTURAS: ORIGINAL VS MIN21")
    print("-" * 75)

    print("SAR original:", total_original)
    print("SAR Min21:", total_min21)

    results = []

    # 5. Comparar cada clase
    for code, name in classes.items():

        original_count = np.count_nonzero(
            original & (landcover == code)
        )

        retained_count = np.count_nonzero(
            min21 & (landcover == code)
        )

        removed_count = original_count - retained_count

        retention_rate = (
            100 * retained_count / original_count
            if original_count > 0 else 0
        )

        original_share = (
            100 * original_count / total_original
            if total_original > 0 else 0
        )

        min21_share = (
            100 * retained_count / total_min21
            if total_min21 > 0 else 0
        )

        results.append({
            "Codigo": code,
            "Cobertura": name,
            "Pixeles_original": original_count,
            "Pixeles_Min21": retained_count,
            "Pixeles_eliminados": removed_count,
            "Conservacion_pct": round(retention_rate, 2),
            "Participacion_original_pct": round(
                original_share, 2
            ),
            "Participacion_Min21_pct": round(
                min21_share, 2
            )
        })

        print(
            f"{code:2d} | {name:35s} | "
            f"Original: {original_count:6,d} | "
            f"Min21: {retained_count:6,d} | "
            f"Conservado: {retention_rate:6.2f}% | "
            f"Peso Min21: {min21_share:6.2f}%"
        )

    # 6. Resumen por grupos
    groups = {
        "Agua abierta": [21],
        "Humedales palustres": [13, 14, 15],
        "Humedales estuarinos": [16, 17, 18],
        "Orillas no consolidadas": [19],
        "Otras coberturas": [2, 5, 6, 7, 8, 11, 12, 20]
    }

    print("\nRESUMEN POR GRUPOS")
    print("-" * 75)

    for name, codes in groups.items():

        orig_count = np.count_nonzero(
            original & np.isin(landcover, codes)
        )

        min_count = np.count_nonzero(
            min21 & np.isin(landcover, codes)
        )

        retention = (
            100 * min_count / orig_count
            if orig_count > 0 else 0
        )

        print(
            f"{name:25s} | "
            f"Original: {orig_count:6,d} | "
            f"Min21: {min_count:6,d} | "
            f"Conservado: {retention:6.2f}%"
        )

    # 7. Comprobar totales
    classified_original = sum(
        r["Pixeles_original"] for r in results
    )

    classified_min21 = sum(
        r["Pixeles_Min21"] for r in results
    )

    print("\nCOMPROBACIÓN")
    print("-" * 75)

    print(
        "Original sin clasificación:",
        total_original - classified_original
    )

    print(
        "Min21 sin clasificación:",
        total_min21 - classified_min21
    )

    # 8. Guardar CSV
    csv_path = (
        OUTPUT_DIR / "SAR_Original_vs_Min21_landcover.csv"
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
