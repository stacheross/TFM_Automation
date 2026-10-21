from pathlib import Path
import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

OUT = Path(__file__).resolve().parent.parent / "outputs"
with rasterio.open(OUT / "Flood_Final_Candidate_Reconstructed.tif") as f:
    flood = f.read(1) == 1
    t = f.transform
with rasterio.open(OUT / "DEM_AOI_S1grid.tif") as d:
    dem = d.read(1).astype("float64")
    flood &= dem != d.nodata

h, w = flood.shape
lat = t.f + t.e * h / 2
dy = abs(t.e) * 111320.0
dx = abs(t.a) * 111320.0 * np.cos(np.radians(lat))

filled = ndi.binary_fill_holes(flood)
bB = filled & ~ndi.binary_erosion(filled, border_value=1)
idx = ndi.distance_transform_edt(~bB, sampling=(dy, dx), return_indices=True)[1]
levelB = dem[idx[0], idx[1]]

br, bc = np.where(bB)
tree = cKDTree(np.column_stack([bc * dx, br * dy]))
zb = dem[br, bc]
fr, fc = np.where(flood)
pts = np.column_stack([fc * dx, fr * dy])
zf = dem[fr, fc]

QS = [50, 75, 90]
print("Radio_m | pct | mediana | p95 | max | %>0")
base = np.maximum(levelB[fr, fc] - zf, 0)
print(f"cercano |  -  | {np.median(base):.2f} | {np.percentile(base,95):.2f} | {base.max():.2f} | {100*(base>0).mean():.1f}")

for R in [50, 100, 150, 300]:
    neigh = tree.query_ball_point(pts, r=R)
    lv = {q: levelB[fr, fc].copy() for q in QS}
    for k, l in enumerate(neigh):
        if l:
            vals = np.percentile(zb[l], QS)
            for q, v in zip(QS, vals):
                lv[q][k] = v
    for q in QS:
        dd = np.maximum(lv[q] - zf, 0)
        print(f"{R:7d} | {q:3d} | {np.median(dd):.2f} | {np.percentile(dd,95):.2f} | {dd.max():.2f} | {100*(dd>0).mean():.1f}")
