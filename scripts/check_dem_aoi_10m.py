
from pathlib import Path
import rasterio
import fiona

PROJECT_DIR = Path(__file__).resolve().parent.parent

DEM_FILE = PROJECT_DIR / "outputs" / "DEM_AOI_05m.tif"
AOI_FILE = PROJECT_DIR / "data" / "aoi" / "AOI_Raster_Footprint.shp"

print("DEM ORIGINAL")
print("-" * 55)

with rasterio.open(DEM_FILE) as dem:
    print("CRS:", dem.crs)
    print("Resolución:", dem.res)
    print("Dimensiones:", dem.width, "x", dem.height)
    print("NoData:", dem.nodata)
    print("Límites:", dem.bounds)

print("\nAOI RASTER FOOTPRINT")
print("-" * 55)

with fiona.open(AOI_FILE) as aoi:
    print("CRS:", aoi.crs_wkt or aoi.crs)
    print("Número de polígonos:", len(aoi))
    print("Límites:", aoi.bounds)
