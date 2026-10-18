from pathlib import Path
import numpy as np
import rasterio


# 1. Localizar la carpeta principal del proyecto
PROJECT_DIR = Path(__file__).resolve().parent.parent

# 2. Definir el DEM que queremos comprobar
DEM_FILE = (
    PROJECT_DIR
    / "outputs"
    / "DEM_AOI_05m.tif"
)


# 3. Abrir el DEM
with rasterio.open(DEM_FILE) as src:

    # Leer la banda 1 como matriz enmascarada
    dem = src.read(1, masked=True)

    print("CRS:")
    print(src.crs)

    print("\nResolución:")
    print(src.res)

    print("\nDimensiones:")
    print(src.width, "x", src.height)

    print("\nNoData:")
    print(src.nodata)

    print("\nExtensión:")
    print(src.bounds)

    print("\nTipo de dato:")
    print(src.dtypes[0])

    print("\nElevación mínima válida:")
    print(float(dem.min()), "m")

    print("\nElevación máxima válida:")
    print(float(dem.max()), "m")

    print("\nNúmero de píxeles:")
    print(dem.size)

    print("\nPíxeles NoData:")
    print(np.ma.count_masked(dem))

    print("\nPíxeles válidos:")
    print(dem.count())