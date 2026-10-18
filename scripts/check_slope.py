from pathlib import Path
import numpy as np
import rasterio


# 1. Localizar la carpeta principal del proyecto
PROJECT_DIR = Path(__file__).resolve().parent.parent


# 2. Definir el ráster de pendiente
SLOPE_FILE = (
    PROJECT_DIR
    / "outputs"
    / "Slope_AOI_05m_degrees.tif"
)


# 3. Abrir el ráster
with rasterio.open(SLOPE_FILE) as src:

    slope = src.read(1, masked=True)

    print("CRS:")
    print(src.crs)

    print("\nResolución:")
    print(src.res)

    print("\nDimensiones:")
    print(src.width, "x", src.height)

    print("\nNoData:")
    print(src.nodata)

    print("\nTipo de dato:")
    print(src.dtypes[0])

    print("\nPendiente mínima:")
    print(float(slope.min()), "grados")

    print("\nPendiente máxima:")
    print(float(slope.max()), "grados")

    print("\nPendiente media:")
    print(float(slope.mean()), "grados")

    print("\nPíxeles NoData:")
    print(np.ma.count_masked(slope))

    print("\nPíxeles válidos:")
    print(slope.count())