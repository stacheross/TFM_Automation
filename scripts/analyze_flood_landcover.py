
from pathlib import Path
import numpy as np
import rasterio

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "outputs"

landcover_path = OUTPUT_DIR / "NOAA_LandCover_2010_S1grid.tif"

flood_path = (
    OUTPUT_DIR
    / "Flood_VH_minus_3dB_Slope_le_5deg_Prop50.tif"
)

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

with rasterio.open(landcover_path) as lc_src, \
     rasterio.open(flood_path) as flood_src:

    if (
        lc_src.crs != flood_src.crs
        or lc_src.transform != flood_src.transform
        or lc_src.shape != flood_src.shape
    ):
        raise ValueError(
            "Los rásteres no comparten exactamente la misma cuadrícula."
        )

    landcover = lc_src.read(1)
    flood = flood_src.read(1)

    detected = flood == 1
    classified = landcover != 255

    valid_detection = detected & classified

    total_detected = np.count_nonzero(detected)
    total_classified = np.count_nonzero(valid_detection)

    print("TOTAL DE DETECCIONES SAR:", total_detected)
    print("Con cobertura NOAA:", total_classified)
    print(
        "Sin cobertura NOAA:",
        total_detected - total_classified
    )

    print("\nDETECCIONES POR CLASE NOAA")
    print("-" * 65)

    for code, name in classes.items():
        count = np.count_nonzero(
            valid_detection & (landcover == code)
        )

        percentage = (
            100 * count / total_classified
            if total_classified > 0 else 0
        )

        print(
            f"{code:2d} | {name:35s} | "
            f"{count:7,d} | {percentage:6.2f}%"
        )

    groups = {
        "Agua abierta": [21],
        "Humedales palustres": [13, 14, 15],
        "Humedales estuarinos": [16, 17, 18],
        "Orillas no consolidadas": [19],
        "Otras coberturas": [2, 5, 6, 7, 8, 11, 12, 20]
    }

    print("\nRESUMEN POR GRUPOS")
    print("-" * 65)

    for name, codes in groups.items():
        count = np.count_nonzero(
            valid_detection & np.isin(landcover, codes)
        )

        percentage = (
            100 * count / total_classified
            if total_classified > 0 else 0
        )

        print(f"{name:25s}: {count:7,d} ({percentage:.2f}%)")
