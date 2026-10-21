from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
import shapely
from shapely.geometry import box
from shapely.strtree import STRtree
from pyproj import Transformer

PROJ = Path(__file__).resolve().parent.parent
aoi = box(119539.0, 244378.5, 131039.0, 253228.5)

shp = next((PROJ / "data" / "hydro").glob("rio_linea_*.shp"))
g = gpd.read_file(shp).to_crs(6566)
g = g[g.intersects(aoi)].reset_index(drop=True)
g["len_aoi_km"] = g.geometry.intersection(aoi).length / 1000

with rasterio.open(PROJ / "outputs" / "Flood_Final_Candidate_Reconstructed.tif") as f:
    a = f.read(1)
    t = f.transform
with rasterio.open(PROJ / "outputs" / "DEM_AOI_S1grid.tif") as d:
    dem = d.read(1).astype("float64")

r_, c_ = np.where(a == 1)
X, Y = Transformer.from_crs(4326, 6566, always_xy=True).transform(
    t.c + (c_ + 0.5) * t.a, t.f + (r_ + 0.5) * t.e)
pts = shapely.points(X, Y)
z = dem[r_, c_]

geoms = g.geometry.values
idx = STRtree(geoms).nearest(pts)
dist = shapely.distance(pts, geoms[idx])
g["n_pix"] = np.bincount(idx, minlength=len(g))
g["dist_med_m"] = [np.median(dist[idx == i]) if (idx == i).any() else np.nan for i in range(len(g))]

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 20)
cols = ["OBJECTID_1", "GNIS_Name", "FType", "FCode", "MainPath", "FlowDir", "len_aoi_km", "n_pix", "dist_med_m"]
print(g[cols].sort_values("n_pix", ascending=False).round(2).to_string(index=False))

print("\nDistancia a la linea mas cercana | pixeles | elev mediana | elev p95 | X mediana | Y mediana")
for lo, hi in [(0, 100), (100, 500), (500, 1500), (1500, 1e9)]:
    m = (dist >= lo) & (dist < hi)
    if m.any():
        print(f"{lo:>5.0f}-{min(hi, 99999):<6.0f} | {int(m.sum()):6d} | {np.median(z[m]):6.2f} | "
              f"{np.percentile(z[m], 95):6.2f} | {np.median(X[m]):9.0f} | {np.median(Y[m]):9.0f}")
