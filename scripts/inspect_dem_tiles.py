from pathlib import Path
import os
import rasterio
import geopandas as gpd
from shapely.geometry import box

# 1. Localizar la carpeta principal del proyecto
PROJECT_DIR = Path(__file__).resolve().parent.parent

# 2. Carpeta que contiene las teselas originales del DEM
DEM_DIR = Path(
    os.environ.get(
        "DEM_SOURCE_FOLDER",
        str(PROJECT_DIR / "data" / "dem")
    )
)


# 3. Definir el archivo del área de interés
AOI_FILE = (
    PROJECT_DIR
    / "data"
    / "aoi"
    / "AOI_Raster_Footprint.shp"
)

# 4. Buscar todos los GeoTIFF del DEM
dem_files = sorted(DEM_DIR.glob("*.tif"))

print("Número de archivos TIF encontrados:", len(dem_files))

if len(dem_files) == 0:
    raise FileNotFoundError(
        "No se encontraron archivos .tif en la carpeta del DEM."
    )

# 5. Abrir la primera tesela para inspeccionar sus propiedades
first_dem = dem_files[0]

print("\nPrimera tesela:")
print(first_dem.name)

with rasterio.open(first_dem) as src:

    print("\nCRS:")
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


# 6. Leer el área de interés
aoi = gpd.read_file(AOI_FILE)

# Convertir el AOI al mismo sistema de coordenadas que el DEM
aoi = aoi.to_crs("EPSG:6566")

# Unir todas las geometrías del AOI en una sola
aoi_geometry = aoi.geometry.union_all()


# 7. Crear una lista vacía para las teselas que intersectan el AOI
intersecting_tiles = []


# 8. Revisar las 61 teselas
for dem_file in dem_files:

    with rasterio.open(dem_file) as src:

        # Crear un rectángulo con la extensión de la tesela
        tile_geometry = box(
            src.bounds.left,
            src.bounds.bottom,
            src.bounds.right,
            src.bounds.top
        )

        # Comprobar si la tesela intersecta el AOI
        if tile_geometry.intersects(aoi_geometry):
            intersecting_tiles.append(dem_file)


# 9. Mostrar las teselas encontradas
print("\nTeselas que intersectan el AOI:")
print(len(intersecting_tiles))

for tile in intersecting_tiles:
    print(tile.name)

# 10. Comprobar los valores de elevación de la primera tesela original
with rasterio.open(first_dem) as src:

    dem_data = src.read(1, masked=True)

    print("\nCOMPROBACIÓN DE ELEVACIONES")

    print("\nElevación mínima:")
    print(float(dem_data.min()), "m")

    print("\nElevación máxima:")
    print(float(dem_data.max()), "m")

    print("\nElevación media:")
    print(float(dem_data.mean()), "m")

    print("\nPíxeles válidos:")
    print(dem_data.count())