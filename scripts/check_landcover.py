
from pathlib import Path
import rasterio
import numpy as np

PROJECT_DIR = Path(__file__).resolve().parent.parent

raster_path = (
    PROJECT_DIR
    / "data"
    / "landcover"
    / "NOAA_LandCover_2010_Clip.tif"
)

with rasterio.open(raster_path) as src:
    data = src.read(1, masked=True)

    print("CRS:", src.crs)
    print("Resolución:", src.res)
    print("Dimensiones:", src.width, "x", src.height)
    print("NoData:", src.nodata)
    print("Tipo de dato:", src.dtypes[0])

    values, counts = np.unique(
        data.compressed(),
        return_counts=True
    )

    print("\nCódigos de cobertura encontrados:")

    for value, count in zip(values, counts):
        print(f"Clase {value}: {count:,} píxeles")
