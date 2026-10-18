from pathlib import Path
import numpy as np
import rasterio


# 1. Localizar la carpeta principal
PROJECT_DIR = Path(__file__).resolve().parent.parent


# 2. Umbrales de pendiente
SLOPE_THRESHOLDS = [1, 2, 3, 4, 5]


# 3. Proporciones que queremos evaluar
PROPORTION_THRESHOLDS = [
    0.25,
    0.50,
    0.75,
    0.90,
    0.99
]


# 4. Analizar cada ráster
for slope_threshold in SLOPE_THRESHOLDS:

    RASTER_FILE = (
        PROJECT_DIR
        / "outputs"
        / f"Slope_proportion_le_{slope_threshold}deg_S1grid.tif"
    )

    with rasterio.open(RASTER_FILE) as src:

        data = src.read(1)

        valid_mask = data != src.nodata
        valid_data = data[valid_mask]

        print(
            f"\nPendiente <= {slope_threshold}°"
        )

        print(
            "Píxeles válidos:",
            f"{valid_data.size:,}"
        )

        for proportion in PROPORTION_THRESHOLDS:

            selected = np.count_nonzero(
                valid_data >= proportion
            )

            percentage = (
                selected
                / valid_data.size
                * 100
            )

            print(
                f"  >= {proportion:.0%}:",
                f"{selected:,} píxeles",
                f"({percentage:.2f} %)"
            )