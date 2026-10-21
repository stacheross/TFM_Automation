from pathlib import Path
import numpy as np
import rasterio
from pyproj import Transformer

out = Path(__file__).resolve().parent.parent / "outputs"
tr = Transformer.from_crs("EPSG:4326", "EPSG:6566", always_xy=True)

with rasterio.open(out / "Flood_Final_Candidate_Reconstructed.tif") as f:
    a = f.read(1)
    t = f.transform
rows, cols = np.where(a == 1)
x0 = t.c + cols * t.a
y0 = t.f + rows * t.e

# Area exacta: esquinas de cada pixel en EPSG:6566 y formula del poligono
cx = [x0, x0 + t.a, x0 + t.a, x0]
cy = [y0, y0, y0 + t.e, y0 + t.e]
X, Y = [], []
for xi, yi in zip(cx, cy):
    px, py = tr.transform(xi, yi)
    X.append(px); Y.append(py)
area = np.zeros(len(rows))
for i in range(4):
    j = (i + 1) % 4
    area += X[i] * Y[j] - X[j] * Y[i]
area = 0.5 * np.abs(area)
print("Pixeles inundados:", len(rows))
print("Area (km2) en EPSG:6566:", round(area.sum() / 1e6, 4))

# Elevacion del DEM en el centro de cada pixel
xc, yc = tr.transform(x0 + t.a / 2, y0 + t.e / 2)
with rasterio.open(out / "DEM_AOI_05m.tif") as d:
    b = d.bounds
    inside = (xc >= b.left) & (xc <= b.right) & (yc >= b.bottom) & (yc <= b.top)
    print("Pixeles dentro de la extension del DEM:", int(inside.sum()))
    pts = list(zip(xc[inside], yc[inside]))
    z = np.array([v[0] for v in d.sample(pts)], dtype="float64")
valid = z != d.nodata
z = z[valid]
print("Pixeles con elevacion valida:", len(z))
print("Elevacion (m) min / p5 / mediana / p95 / max:",
      np.round([z.min(), *np.percentile(z, [5, 50, 95]), z.max()], 2))
