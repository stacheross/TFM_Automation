
from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.features import geometry_mask
from rasterio.transform import from_origin
import fiona

PROJECT_DIR = Path(__file__).resolve().parent.parent

DEM_FILE = PROJECT_DIR / "outputs" / "DEM_AOI_05m.tif"
AOI_FILE = PROJECT_DIR / "data" / "aoi" / "AOI_Raster_Footprint.shp"

OUTPUT_FILE = PROJECT_DIR / "outputs" / "DEM_AOI_10m_Bilinear.tif"

NODATA = -9999.0
RESOLUTION = 10.0

with rasterio.open(DEM_FILE) as src, fiona.open(AOI_FILE) as aoi:

    if src.crs is None:
        raise ValueError("El DEM no tiene CRS.")

    if src.crs.to_epsg() != 6566:
        raise ValueError("El DEM no está en EPSG:6566.")

    # El AOI debe compartir el sistema horizontal del DEM
    if aoi.crs_wkt:
        from pyproj import CRS

        aoi_crs = CRS.from_wkt(aoi.crs_wkt)
        dem_crs = CRS.from_user_input(src.crs)

        # Extraer el sistema horizontal si el AOI tiene un CRS compuesto
        aoi_horizontal = (
            aoi_crs.sub_crs_list[0]
            if aoi_crs.is_compound
            else aoi_crs
        )

        if not aoi_horizontal.equals(dem_crs, ignore_axis_order=True):
            raise ValueError(
                "El sistema horizontal del AOI no coincide con el DEM."
            )

    print("CRS horizontal del AOI:", aoi_horizontal.to_epsg())
    print("CRS del DEM:", dem_crs.to_epsg())
    print("Sistemas horizontales compatibles.")

    geometries = [
        feature["geometry"].__geo_interface__
        for feature in aoi
    ]

    if not geometries:
        raise ValueError("El AOI no contiene geometrías.")

    # Mantener el origen del DEM y construir celdas de 10 m
    width = int(np.ceil(src.width * src.res[0] / RESOLUTION))
    height = int(np.ceil(src.height * src.res[1] / RESOLUTION))

    transform = from_origin(
        src.bounds.left,
        src.bounds.top,
        RESOLUTION,
        RESOLUTION
    )

    dem_10m = np.full(
        (height, width),
        NODATA,
        dtype=np.float32
    )

    # Remuestreo bilineal
    reproject(
        source=rasterio.band(src, 1),
        destination=dem_10m,
        src_transform=src.transform,
        src_crs=src.crs,
        src_nodata=src.nodata,
        dst_transform=transform,
        dst_crs=src.crs,
        dst_nodata=NODATA,
        resampling=Resampling.bilinear
    )

    # Máscara del AOI
    inside_aoi = geometry_mask(
        geometries,
        out_shape=(height, width),
        transform=transform,
        invert=True,
        all_touched=False
    )

    dem_10m[~inside_aoi] = NODATA

    profile = src.profile.copy()
    profile.update(
        driver="GTiff",
        width=width,
        height=height,
        transform=transform,
        dtype="float32",
        count=1,
        nodata=NODATA,
        compress="lzw"
    )

    with rasterio.open(OUTPUT_FILE, "w", **profile) as dst:
        dst.write(dem_10m, 1)

    valid = (dem_10m != NODATA) & np.isfinite(dem_10m)

    print("DEM REMUESTREADO A 10 M")
    print("-" * 55)
    print("Archivo:", OUTPUT_FILE)
    print("CRS:", src.crs)
    print("Resolución:", RESOLUTION, "x", RESOLUTION, "m")
    print("Dimensiones:", width, "x", height)
    print("Píxeles válidos:", np.count_nonzero(valid))
    print("Píxeles NoData:", np.count_nonzero(~valid))

    if np.any(valid):
        print("Elevación mínima:", dem_10m[valid].min())
        print("Elevación máxima:", dem_10m[valid].max())
        print("Elevación media:", dem_10m[valid].mean())
