from pathlib import Path
import os
import geopandas as gpd
import rasterio
from rasterio.merge import merge
from rasterio.mask import mask
from shapely.geometry import box, mapping


# 1. Localizar la carpeta principal del proyecto
PROJECT_DIR = Path(__file__).resolve().parent.parent


# 2. Definir las rutas
DEM_DIR = Path(
    os.environ.get(
        "DEM_SOURCE_FOLDER",
        str(PROJECT_DIR / "data" / "dem")
    )
)


AOI_FILE = (
    PROJECT_DIR
    / "data"
    / "aoi"
    / "AOI_Raster_Footprint.shp"
)

OUTPUT_FILE = (
    PROJECT_DIR
    / "outputs"
    / "DEM_AOI_05m.tif"
)

TEMP_FILE = (
    PROJECT_DIR
    / "outputs"
    / "DEM_AOI_temp.tif"
)


# 3. Definir un valor NoData seguro
NODATA_VALUE = -9999.0


# 4. Leer el AOI
aoi = gpd.read_file(AOI_FILE)

# Convertir el AOI al mismo CRS que los DEM
aoi = aoi.to_crs("EPSG:6566")

# Unir las geometrías del AOI
aoi_geometry = aoi.geometry.union_all()


# 5. Buscar todas las teselas DEM
dem_files = sorted(DEM_DIR.glob("*.tif"))


# 6. Identificar las teselas que intersectan el AOI
intersecting_tiles = []

for dem_file in dem_files:

    with rasterio.open(dem_file) as src:

        tile_geometry = box(
            src.bounds.left,
            src.bounds.bottom,
            src.bounds.right,
            src.bounds.top
        )

        if tile_geometry.intersects(aoi_geometry):
            intersecting_tiles.append(dem_file)


print("Teselas utilizadas:", len(intersecting_tiles))


# 7. Abrir las teselas seleccionadas
datasets = [
    rasterio.open(tile)
    for tile in intersecting_tiles
]


# 8. Obtener la extensión rectangular del AOI
minx, miny, maxx, maxy = aoi_geometry.bounds


# 9. Crear el mosaico
mosaic, mosaic_transform = merge(
    datasets,
    bounds=(minx, miny, maxx, maxy),
    nodata=NODATA_VALUE,
    dtype="float32"
)


# 10. Preparar las propiedades del mosaico
profile = datasets[0].profile.copy()

profile.update(
    dtype="float32",
    nodata=NODATA_VALUE,
    height=mosaic.shape[1],
    width=mosaic.shape[2],
    transform=mosaic_transform,
    count=1
)


# 11. Guardar temporalmente el mosaico rectangular
with rasterio.open(
    TEMP_FILE,
    "w",
    **profile
) as dst:

    dst.write(mosaic)


# 12. Cerrar las teselas originales
for dataset in datasets:
    dataset.close()


# 13. Recortar el mosaico exactamente con el AOI
with rasterio.open(TEMP_FILE) as src:

    clipped_dem, clipped_transform = mask(
        src,
        [mapping(aoi_geometry)],
        crop=True,
        nodata=NODATA_VALUE,
        filled=True
    )

    clipped_profile = src.profile.copy()

    clipped_profile.update(
        dtype="float32",
        nodata=NODATA_VALUE,
        height=clipped_dem.shape[1],
        width=clipped_dem.shape[2],
        transform=clipped_transform
    )


# 14. Guardar el DEM definitivo
with rasterio.open(
    OUTPUT_FILE,
    "w",
    **clipped_profile
) as dst:

    dst.write(clipped_dem)


# 15. Eliminar el archivo temporal
TEMP_FILE.unlink()


print("\nDEM del AOI creado correctamente.")
print("NoData utilizado:", NODATA_VALUE)
print("Archivo:")
print(OUTPUT_FILE)