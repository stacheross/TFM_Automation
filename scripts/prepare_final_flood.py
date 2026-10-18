
from pathlib import Path
import shutil

import numpy as np
import rasterio
from rasterio.features import shapes
from rasterio.warp import transform_geom

import fiona
from shapely.geometry import shape, mapping
from pyproj import Geod

# 1. Rutas
PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "outputs"

input_path = (
    OUTPUT_DIR / "SAR_components_Min21_8neighbors.tif"
)

raster_output = OUTPUT_DIR / "Flood_SAR_Min21_Final.tif"
vector_output = OUTPUT_DIR / "Flood_SAR_Min21_Final.gpkg"

# 2. Copiar el ráster sin modificarlo
shutil.copy2(input_path, raster_output)

# 3. Leer las detecciones
with rasterio.open(raster_output) as src:

    data = src.read(1)
    mask = data == 1

    transform = src.transform
    crs = src.crs

    pixel_count = int(np.count_nonzero(mask))

    if crs is None:
        raise ValueError("El ráster no tiene CRS.")

    if pixel_count == 0:
        raise ValueError("No se encontraron detecciones.")

    # 4. Convertir los píxeles detectados en polígonos
    polygons = []

    for geom, value in shapes(
        data,
        mask=mask,
        transform=transform,
        connectivity=8
    ):
        if value == 1:
            polygons.append(shape(geom))

# 5. Calcular superficies geodésicas
geod = Geod(ellps="WGS84")

# Eliminar una salida anterior, si existe
if vector_output.exists():
    vector_output.unlink()

schema = {
    "geometry": "Polygon",
    "properties": {
        "id": "int",
        "area_m2": "float",
        "area_km2": "float"
    }
}

total_area_m2 = 0.0

# 6. Guardar GeoPackage
with fiona.open(
    vector_output,
    "w",
    driver="GPKG",
    layer="Flood_SAR_Min21",
    schema=schema,
    crs=crs.to_wkt()
) as dst:

    for i, polygon in enumerate(polygons, start=1):

        # Transformar temporalmente a WGS84
        # para calcular el área geodésica
        geom_wgs84 = transform_geom(
            crs,
            "EPSG:4326",
            mapping(polygon)
        )

        polygon_wgs84 = shape(geom_wgs84)

        area_m2 = abs(
            geod.geometry_area_perimeter(
                polygon_wgs84
            )[0]
        )

        total_area_m2 += area_m2

        dst.write({
            "geometry": mapping(polygon),
            "properties": {
                "id": i,
                "area_m2": area_m2,
                "area_km2": area_m2 / 1_000_000
            }
        })

# 7. Resultados
print("DELIMITACIÓN SAR FINAL — MIN21")
print("-" * 60)

print("Píxeles detectados:", pixel_count)
print("Polígonos generados:", len(polygons))

print(
    "Superficie total:",
    round(total_area_m2 / 1_000_000, 4),
    "km²"
)

print("\nArchivos generados:")
print(raster_output)
print(vector_output)
