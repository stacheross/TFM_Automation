from pathlib import Path
import geopandas as gpd
from shapely import force_2d

# 1. Localizar la carpeta principal del proyecto
PROJECT_DIR = Path(__file__).resolve().parent.parent


# 2. Localizar el shapefile del área de estudio
AOI_FILE = PROJECT_DIR / "data" / "aoi" / "AOI_Raster_Footprint.shp"


# 3. Comprobar que el archivo existe
if not AOI_FILE.exists():
    raise FileNotFoundError(
        f"No se encontró el AOI: {AOI_FILE}"
    )


# 4. Leer el shapefile
aoi = gpd.read_file(AOI_FILE)


# 5. Mostrar información básica
print("Archivo AOI:")
print(AOI_FILE)

print("\nCRS original:")
print(aoi.crs)

print("\nNúmero de geometrías:")
print(len(aoi))

print("\nTipo de geometría:")
print(aoi.geometry.geom_type)


# 6. Transformar una copia a WGS84
aoi_wgs84 = aoi.to_crs("EPSG:4326")


# 7. Unir las geometrías si hubiera más de una
geometry = aoi_wgs84.geometry.union_all()
geometry = force_2d(geometry)


# 8. Mostrar la geometría en formato WKT
print("\nTipo de geometría unificada:")
print(geometry.geom_type)

print("\nPrimeros 200 caracteres del WKT:")
print(geometry.wkt[:200])

print("\nExtensión geográfica (minX, minY, maxX, maxY):")
print(geometry.bounds)

print("\nLongitud del WKT:")
print(len(geometry.wkt))