from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
import shapely

PROJ = Path(__file__).resolve().parent.parent
OUT = PROJ / "outputs"
DD = OUT / "depth_prototype"
FLAG = max(DD.glob("Depth_RiverProfile_10m_Flag*.tif"), key=lambda p: p.stat().st_mtime)
F50 = FLAG.with_name(FLAG.name.replace("_Flag", "_p50"))
F90 = FLAG.with_name(FLAG.name.replace("_Flag", "_p90"))
GPKG = OUT / "Flood_Reconstruction_Review.gpkg"
print("Marcas:", FLAG.name, "| profundidades:", F50.name, F90.name)

with rasterio.open(FLAG) as f:
    fa = f.read(1)
    t = f.transform
    fcrs = f.crs.to_string()
with rasterio.open(F50) as r:
    d50 = r.read(1).astype("float64")
with rasterio.open(F90) as r:
    d90 = r.read(1).astype("float64")

rows, cols = np.where(fa != 255)
fv = fa[rows, cols]
x = t.c + (cols + 0.5) * t.a
y = t.f + (rows + 0.5) * t.e
v50 = np.where(d50[rows, cols] == -9999.0, np.nan, d50[rows, cols])
v90 = np.where(d90[rows, cols] == -9999.0, np.nan, d90[rows, cols])

def load(layer):
    g = gpd.read_file(GPKG, layer=layer).to_crs(fcrs)
    geom = g.geometry.union_all()
    shapely.prepare(geom)
    return geom

kept = load("Flood_Final_Reviewed_Reconstructed")
rem = load("Flood_Removed_Manual_Review")
in_rem = shapely.contains_xy(rem, x, y)
in_kept = shapely.contains_xy(kept, x, y)
cat = np.where(in_rem & ~in_kept, "descartados",
      np.where(in_kept & ~in_rem, "conservados",
      np.where(in_rem & in_kept, "en ambos", "fuera de ambas")))

names = {1: "1 estimado", 2: "2 lejos del cauce", 3: "3 puente"}
ct = pd.crosstab(pd.Series(fv).map(names).values, cat)
print("\nPixeles por marca (filas) y poligonos de la revision (columnas)")
print(ct.to_string())
print("\n% por marca")
print((ct.div(ct.sum(axis=1), axis=0) * 100).round(1).to_string())

print("\nProfundidad de la marca 1 segun la revision (media/mediana/p95)")
for c in sorted(set(cat)):
    m = (fv == 1) & (cat == c)
    if m.sum():
        a, b = v50[m], v90[m]
        print(f"{c}: {int(m.sum())} px | p50 {np.nanmean(a):.2f}/{np.nanmedian(a):.2f}/{np.nanpercentile(a, 95):.2f}"
              f" | p90 {np.nanmean(b):.2f}/{np.nanmedian(b):.2f}/{np.nanpercentile(b, 95):.2f}")
