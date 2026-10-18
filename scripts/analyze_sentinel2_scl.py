from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio

from rasterio.mask import mask
from shapely.geometry import mapping


# 1. Localizar la carpeta principal
PROJECT_DIR = Path(__file__).resolve().parent.parent


# 2. Definir los archivos
SCL_FILE = (
    PROJECT_DIR
    / "data"
    / "sentinel2"
    / "extracted"
    / "T19QFA_20171020T150709_SCL_20m.jp2"
)

AOI_FILE = (
    PROJECT_DIR
    / "data"
    / "aoi"
    / "AOI_Raster_Footprint.shp"
)


# 3. Nombres de las clases SCL
SCL_CLASSES = {
    0: "No Data",
    1: "Saturated / defective",
    2: "Dark area pixels",
    3: "Cloud shadows",
    4: "Vegetation",
    5: "Bare soils",
    6: "Water",
    7: "Unclassified",
    8: "Cloud medium probability",
    9: "Cloud high probability",
    10: "Thin cirrus",
    11: "Snow / ice"
}


# 4. Leer el AOI
aoi = gpd.read_file(AOI_FILE)


# 5. Abrir la clasificación SCL
with rasterio.open(SCL_FILE) as src:

    print("SCL Sentinel-2")
    print("CRS:", src.crs)
    print("Resolución:", src.res)
    print("Dimensiones:", src.width, "x", src.height)

    # Transformar el AOI al CRS de Sentinel-2
    aoi_s2 = aoi.to_crs(src.crs)

    # Unir las geometrías del AOI
    aoi_geometry = aoi_s2.geometry.union_all()

    # Recortar SCL al AOI
    scl_clip, transform = mask(
        src,
        [mapping(aoi_geometry)],
        crop=True,
        filled=False
    )


# 6. Obtener únicamente los píxeles válidos
scl = scl_clip[0]

valid_values = scl.compressed()


# 7. Contar cada clase
classes, counts = np.unique(
    valid_values,
    return_counts=True
)

total = counts.sum()


print("\nDistribución SCL dentro del AOI:\n")

for class_value, count in zip(classes, counts):

    class_value = int(class_value)
    count = int(count)

    percentage = (
        count
        / total
        * 100
    )

    class_name = SCL_CLASSES.get(
        class_value,
        "Clase desconocida"
    )

    print(
        f"Clase {class_value:2d} | "
        f"{class_name:25s} | "
        f"{count:8,d} píxeles | "
        f"{percentage:6.2f} %"
    )


# 8. Calcular cobertura problemática por nubes
cloud_classes = [3, 8, 9, 10]

cloud_pixels = np.count_nonzero(
    np.isin(
        valid_values,
        cloud_classes
    )
)

cloud_percentage = (
    cloud_pixels
    / total
    * 100
)


print("\nResumen:")
print("Píxeles analizados:", f"{total:,}")

print(
    "Nubes + sombras:",
    f"{cloud_pixels:,}",
    "píxeles"
)

print(
    "Porcentaje afectado:",
    f"{cloud_percentage:.2f} %"
)