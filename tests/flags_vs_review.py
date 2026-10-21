from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import xy
from rasterio.warp import transform as rtransform

PROJ = Path(__file__).resolve().parent.parent
OUT = PROJ / "outputs"
FLAG = max((OUT / "depth_prototype").glob("Depth_RiverProfile_10m_Flag*.tif"), key=lambda p: p.stat().st_mtime)
REV = OUT / "Flood_Final_Reviewed_Original.tif"
GPKG = OUT / "Flood_Reconstruction_Review.gpkg"
print("Marcas:", FLAG.name)

with rasterio.open(REV) as r:
    print("\n== Flood_Final_Reviewed_Original.tif")
    print("CRS:", r.crs, "| tamano:", r.height, "x", r.width, "| resolucion:", r.res)
    print("Extension:", r.bounds)
    print("Tipo / NoData:", r.dtypes[0], "/", r.nodata)
    a = r.read(1)
    vals, cnt = np.unique(a, return_counts=True)
    print("Valores y conteos:", dict(zip(vals.tolist(), cnt.tolist())))

    with rasterio.open(FLAG) as f:
        fa = f.read(1)
        rows, cols = np.where(fa != 255)
        fv = fa[rows, cols]
        xs, ys = xy(f.transform, rows, cols)
        qx, qy = rtransform(f.crs, r.crs, xs, ys)
    sv = np.array([s[0] for s in r.sample(list(zip(qx, qy)))])

names = {1: "1 estimado", 2: "2 lejos del cauce", 3: "3 puente"}
ct = pd.crosstab(pd.Series(fv).map(names).values, sv)
ct.columns = [f"revisado={c}" for c in ct.columns]
print("\nPixeles por marca (filas) y valor del raster revisado (columnas)")
print(ct.to_string())
print("\n% de cada marca por valor del raster revisado")
print((ct.div(ct.sum(axis=1), axis=0) * 100).round(1).to_string())

try:
    import geopandas as gpd
    import pyogrio
    layers = pyogrio.list_layers(GPKG)
    print("\n== Flood_Reconstruction_Review.gpkg | capas:", layers.tolist())
    for name, gtype in layers:
        gdf = gpd.read_file(GPKG, layer=name)
        print(f"\nCapa {name}: {len(gdf)} entidades | tipo {gtype} | CRS: {gdf.crs}")
        print("Columnas:", [c for c in gdf.columns if c != "geometry"])
        g6 = gdf.to_crs(6566) if gdf.crs else gdf
        g6 = g6.assign(_a=g6.area)
        print("Area total (km2):", round(g6["_a"].sum() / 1e6, 4))
        for c in gdf.columns:
            if c not in ("geometry", "_a") and gdf[c].nunique() <= 15:
                tab = (g6.groupby(c)["_a"].sum() / 1e6).round(4)
                print(f"  {c}: entidades {gdf[c].value_counts().to_dict()} | area km2 {tab.to_dict()}")
except Exception as e:
    print("\nNo pude leer el gpkg:", e)
