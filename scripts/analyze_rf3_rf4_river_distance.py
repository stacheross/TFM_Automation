
from pathlib import Path
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parent.parent

CHANGES = ROOT / "outputs" / "RF3_vs_RF4_Changes.tif"
RF4 = ROOT / "data" / "RF4_Todas_Variables_Original.tif"

with rasterio.open(CHANGES) as changes_src, rasterio.open(RF4) as rf4_src:

    if (
        changes_src.shape != rf4_src.shape
        or changes_src.transform != rf4_src.transform
        or changes_src.crs != rf4_src.crs
    ):
        raise ValueError(
            "Los rasteres no tienen la misma cuadricula."
        )

    changes = changes_src.read(1)

    # La banda 6 de RF4 contiene la distancia al rio
    distance = rf4_src.read(6)

    valid_distance = (
        np.isfinite(distance)
        & (distance >= 0)
        & (changes > 0)
    )

    categories = {
        2: "Inundado en ambos modelos",
        3: "Descartado por RF4",
        4: "Incorporado por RF4"
    }

    print("\nANALISIS DE DISTANCIA AL RIO - RF3 VS RF4")
    print("-" * 55)

    for value, name in categories.items():

        mask = (changes == value) & valid_distance
        values = distance[mask]

        print(f"\n{name}")
        print("Pixeles:", len(values))

        if len(values) == 0:
            continue

        print("Distancia media:", round(float(np.mean(values)), 2), "m")
        print("Distancia mediana:", round(float(np.median(values)), 2), "m")
        print("Percentil 25:", round(float(np.percentile(values, 25)), 2), "m")
        print("Percentil 75:", round(float(np.percentile(values, 75)), 2), "m")
        print("Distancia maxima:", round(float(np.max(values)), 2), "m")

        print(
            "Pixeles a mas de 500 m:",
            int(np.count_nonzero(values > 500))
        )

        print(
            "Pixeles a mas de 1000 m:",
            int(np.count_nonzero(values > 1000))
        )
