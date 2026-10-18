
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
    data = src.read(1)
    mask = src.read_masks(1)

    print("NoData declarado:", src.nodata)
    print("Valores de máscara:", np.unique(mask))

    for value in [0, 255]:
        pixels = data == value

        print(f"\nValor {value}:")
        print("Total:", np.count_nonzero(pixels))
        print(
            "Con máscara válida:",
            np.count_nonzero(pixels & (mask > 0))
        )
        print(
            "Con máscara inválida:",
            np.count_nonzero(pixels & (mask == 0))
        )
