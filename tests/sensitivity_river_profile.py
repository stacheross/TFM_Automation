from pathlib import Path
import numpy as np
import geopandas as gpd
import rasterio
import shapely
from pyproj import Transformer
from scipy import ndimage as ndi
from shapely.geometry import LineString
from shapely.ops import linemerge, unary_union
from sklearn.isotonic import IsotonicRegression

PROJ = Path(__file__).resolve().parent.parent
OUT = PROJ / "outputs"
BRIDGES = [((-67.1614992, 18.2724909), (-67.1617715, 18.2729469), 40.0)]

with rasterio.open(OUT / "Flood_Final_Candidate_Reconstructed.tif") as f:
    flood = f.read(1) == 1
    t = f.transform
with rasterio.open(OUT / "DEM_AOI_S1grid.tif") as d:
    dem = d.read(1).astype("float64")
    dnod = d.nodata
flood &= dem != dnod
h, w = flood.shape

to6566 = Transformer.from_crs(4326, 6566, always_xy=True)
to4326 = Transformer.from_crs(6566, 4326, always_xy=True)

def dem_at(xs, ys):
    lon, lat = to4326.transform(xs, ys)
    cols = np.floor((np.asarray(lon) - t.c) / t.a).astype(int)
    rows = np.floor((np.asarray(lat) - t.f) / t.e).astype(int)
    ok = (rows >= 0) & (rows < h) & (cols >= 0) & (cols < w)
    z = np.full(len(cols), np.nan)
    z[ok] = dem[rows[ok], cols[ok]]
    z[z == dnod] = np.nan
    return z

shp = next((PROJ / "data" / "hydro").glob("rio_linea_*.shp"))
g = gpd.read_file(shp).to_crs(6566)
line = linemerge(unary_union([shapely.force_2d(x) for x in g.geometry]))
if line.geom_type == "MultiLineString":
    line = max(line.geoms, key=lambda p: p.length)
s0 = np.arange(0.0, line.length, 25.0)
p0 = shapely.line_interpolate_point(line, s0)
zl = dem_at(shapely.get_x(p0), shapely.get_y(p0))
zz = zl[~np.isnan(zl)]
k = max(1, len(zz) // 10)
if np.median(zz[:k]) < np.median(zz[-k:]):
    line = shapely.reverse(line)
L = line.length

rows, cols = np.where(flood)
X, Y = to6566.transform(t.c + (cols + 0.5) * t.a, t.f + (rows + 0.5) * t.e)
pts = shapely.points(X, Y)
s_pix = shapely.line_locate_point(line, pts)
dist = shapely.distance(pts, line)
z_pix = dem[rows, cols]

on_bridge = np.zeros(len(rows), dtype=bool)
for (lo1, la1), (lo2, la2), half in BRIDGES:
    x1, y1 = to6566.transform(lo1, la1)
    x2, y2 = to6566.transform(lo2, la2)
    on_bridge |= shapely.distance(pts, LineString([(x1, y1), (x2, y2)])) <= half

filled = ndi.binary_fill_holes(flood)
bmask = (filled & ~ndi.binary_erosion(filled, border_value=1) & flood)[rows, cols]

lat = t.f + t.e * h / 2
px_area = abs(t.e) * 111320.0 * abs(t.a) * 111320.0 * np.cos(np.radians(lat))
common = (dist <= 300.0) & ~on_bridge
print("Pixeles comparados (<= 300 m del cauce, fuera de puentes):", int(common.sum()))

def depth_for(q, dmax, bin_, minb, smooth):
    use_b = bmask & (dist <= dmax) & ~on_bridge
    nb = int(np.ceil(L / bin_))
    centers = (np.arange(nb) + 0.5) * bin_
    bi = np.minimum((s_pix // bin_).astype(int), nb - 1)
    counts = np.bincount(bi[use_b], minlength=nb)
    lv = np.full(nb, np.nan)
    for i in range(nb):
        if counts[i] >= minb:
            lv[i] = np.percentile(z_pix[use_b & (bi == i)], q)
    valid = ~np.isnan(lv)
    if valid.sum() < 2:
        return None
    lv = np.interp(centers, centers[valid], lv[valid])
    wts = np.where(valid, counts, 1).astype(float)
    lv = IsotonicRegression(increasing=False).fit_transform(centers, lv, sample_weight=wts)
    lv = ndi.uniform_filter1d(lv, size=smooth, mode="nearest")
    return np.maximum(np.interp(s_pix, centers, lv) - z_pix, 0.0)

base = (500.0, 250.0, 10, 3)
combos = [(dm, bn, 10, 3) for dm in (300.0, 500.0, 800.0) for bn in (150.0, 250.0, 500.0)]
combos += [(500.0, 250.0, 5, 3), (500.0, 250.0, 20, 3), (500.0, 250.0, 10, 1), (500.0, 250.0, 10, 5)]
basedep = {q: depth_for(q, *base) for q in (50, 90)}

print("\nDMAX | tramo | minB | suav | p50: media/mediana/p95/max (Delta) | p90: media/mediana/p95/max (Delta)")
for c in combos:
    cells = []
    for q in (50, 90):
        dep = depth_for(q, *c)
        if dep is None:
            cells.append("sin datos suficientes")
            continue
        dd = dep[common]
        dl = np.abs(dep - basedep[q])[common].mean()
        cells.append(f"{dd.mean():.2f}/{np.median(dd):.2f}/{np.percentile(dd, 95):.2f}/{dd.max():.2f} (D {dl:.2f})")
    mark = "  <- base" if c == base else ""
    print(f"{c[0]:4.0f} | {c[1]:5.0f} | {c[2]:4d} | {c[3]:4d} | p50 {cells[0]} | p90 {cells[1]}{mark}")
