from pathlib import Path
import numpy as np
import geopandas as gpd
import rasterio
import shapely
from shapely.ops import linemerge, unary_union
from pyproj import Transformer

PROJ = Path(__file__).resolve().parent.parent
shp = next((PROJ / "data" / "hydro").glob("rio_linea_*.shp"))
g = gpd.read_file(shp).to_crs(6566)

with rasterio.open(PROJ / "outputs" / "DEM_AOI_S1grid.tif") as d:
    dem = d.read(1).astype("float64")
    dt, dnod = d.transform, d.nodata
h, w = dem.shape
to4326 = Transformer.from_crs(6566, 4326, always_xy=True)

def elev(xs, ys):
    lon, lat = to4326.transform(xs, ys)
    cols = np.floor((np.asarray(lon) - dt.c) / dt.a).astype(int)
    rows = np.floor((np.asarray(lat) - dt.f) / dt.e).astype(int)
    ok = (rows >= 0) & (rows < h) & (cols >= 0) & (cols < w)
    z = np.full(len(cols), np.nan)
    z[ok] = dem[rows[ok], cols[ok]]
    z[z == dnod] = np.nan
    return z

print("Segmentos (sentido de digitalizacion)")
print("OBJECTID | longitud | inicio (x,y) z | fin (x,y) z")
for _, r in g.iterrows():
    geom = shapely.force_2d(r.geometry)
    if geom.geom_type == "MultiLineString":
        geom = linemerge(geom)
    if geom.geom_type != "LineString":
        print(int(r.OBJECTID_1), "| multi-parte, omitido")
        continue
    (x0, y0), (x1, y1) = geom.coords[0], geom.coords[-1]
    z0, z1 = elev(np.array([x0, x1]), np.array([y0, y1]))
    print(f"{int(r.OBJECTID_1):6d} | {geom.length/1000:5.2f} km | ({x0:.0f},{y0:.0f}) z={z0:.1f} | ({x1:.0f},{y1:.0f}) z={z1:.1f}")

merged = linemerge(unary_union([shapely.force_2d(x) for x in g.geometry]))
parts = list(merged.geoms) if merged.geom_type == "MultiLineString" else [merged]
parts.sort(key=lambda p: p.length, reverse=True)
print("\nPartes tras unir segmentos:", len(parts), "| longitud total (km):", round(sum(p.length for p in parts) / 1000, 2))

for i, p in enumerate(parts):
    s = np.arange(0, p.length, 25.0)
    pts = shapely.line_interpolate_point(p, s)
    z = elev(shapely.get_x(pts), shapely.get_y(pts))
    ok = ~np.isnan(z)
    a, b = shapely.Point(p.coords[0]), shapely.Point(p.coords[-1])
    rest = [q for j, q in enumerate(parts) if j != i]
    ga = a.distance(unary_union(rest)) if rest else float("nan")
    gb = b.distance(unary_union(rest)) if rest else float("nan")
    k = max(1, int(ok.sum()) // 10)
    zz = z[ok]
    print(f"Parte {i}: {p.length/1000:.2f} km | inicio ({a.x:.0f},{a.y:.0f}) a {ga:.0f} m de otra parte | "
          f"fin ({b.x:.0f},{b.y:.0f}) a {gb:.0f} m | elev inicio/fin (mediana de 10%): "
          f"{np.median(zz[:k]):.1f}/{np.median(zz[-k:]):.1f} m | sin dato: {int((~ok).sum())} de {len(z)}")
