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

def boundary_of(m):
    return m & ~ndi.binary_erosion(m, border_value=1)

def nearest_level(b):
    idx = ndi.distance_transform_edt(~b, sampling=(dy, dx), return_indices=True)[1]
    return dem[idx[0], idx[1]]

def stats(name, depth):
    dd = depth[flood]
    print(f"{name}: media {dd.mean():.2f} | mediana {np.median(dd):.2f} | "
          f"p95 {np.percentile(dd, 95):.2f} | max {dd.max():.2f} | %>0 {100*(dd>0).mean():.1f}")

filled = ndi.binary_fill_holes(flood)
holes = filled & ~flood
bA, bB = boundary_of(flood), boundary_of(filled)
print("Pixeles en huecos internos:", int(holes.sum()))
print("Pixeles de borde A (actual):", int(bA.sum()), "| B (solo contorno exterior):", int(bB.sum()))

levelB = nearest_level(bB)
stats("A (borde mas cercano, actual)   ", np.maximum(nearest_level(bA) - dem, 0))
stats("B (sin huecos, borde mas cercano)", np.maximum(levelB - dem, 0))

R = 150.0
br, bc = np.where(bB)
tree = cKDTree(np.column_stack([bc * dx, br * dy]))
zb = dem[br, bc]
fr, fc = np.where(flood)
neigh = tree.query_ball_point(np.column_stack([fc * dx, fr * dy]), r=R)
levelC = levelB.copy()
for k, l in enumerate(neigh):
    if l:
        levelC[fr[k], fc[k]] = np.percentile(zb[l], 75)
stats(f"C (sin huecos, p75 en {R:.0f} m)       ", np.maximum(levelC - dem, 0))
