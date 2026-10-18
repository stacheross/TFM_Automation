
from pathlib import Path
import numpy as np
import geopandas as gpd
import rasterio

ROOT = Path(__file__).resolve().parent.parent

POINTS = ROOT / "data" / "RF1_Puntos_Validacion_Original.shp"

ORIGINAL = ROOT / "data" / "RF2_SAR_Cambio_Original.tif"

RECONSTRUCTED = {
    "VH_Pre": ROOT / "outputs" / "RF_VH_Pre_10m.tif",
    "VH_Post": ROOT / "outputs" / "RF_VH_Post_10m.tif",
    "VH_Change": ROOT / "outputs" / "RF_VH_Change_10m.tif"
}

points = gpd.read_file(POINTS)

with rasterio.open(ORIGINAL) as src:
    original_points = points.to_crs(src.crs)

    coords = [
        (geometry.x, geometry.y)
        for geometry in original_points.geometry
    ]

    original_values = np.array(
        list(src.sample(coords, masked=True))
    )

    print("\nCOMPARACION DE VARIABLES SAR")
    print("-" * 50)

    for band, (name, path) in enumerate(
        RECONSTRUCTED.items()
    ):
        with rasterio.open(path) as reconstructed:
            aligned_points = points.to_crs(reconstructed.crs)

            reconstructed_coords = [
                (geometry.x, geometry.y)
                for geometry in aligned_points.geometry
            ]

            reconstructed_values = np.array(
                list(
                    reconstructed.sample(
                        reconstructed_coords,
                        masked=True
                    )
                )
            )[:, 0]

            original_band = original_values[:, band]

            valid = (
                np.isfinite(original_band)
                & np.isfinite(reconstructed_values)
            )

            difference = np.abs(
                original_band[valid]
                - reconstructed_values[valid]
            )

            print(f"\n{name}")
            print("Puntos comparados:", np.count_nonzero(valid))

            if difference.size:
                print("Diferencia media:", float(difference.mean()))
                print("Diferencia máxima:", float(difference.max()))
