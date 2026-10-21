from pathlib import Path
import numpy as np
import rasterio
from scipy import ndimage as ndi

OUT = Path(__file__).resolve().parent.parent / "outputs"
PIX_M2 = 10.0 * 9.5

with rasterio.open(OUT / "Flood_Final_Candidate_Reconstructed.tif") as f:
    flood = f.read(1) == 1
with rasterio.open(OUT / "DEM_AOI_S1grid.tif") as d:
    dem = d.read(1).astype("float64")
with rasterio.open(OUT / "depth_prototype" / "Depth_FwDET_10m_Prototype.tif") as p:
    depth = p.read(1).astype("float64")

lab, n = ndi.label(flood, structure=np.ones((3, 3)))
sizes = np.bincount(lab.ravel())[1:]
print("Componentes conectados (8 vecinos):", n)
print("Tamano (pixeles) mediana / p90 / max:", np.median(sizes), np.percentile(sizes, 90), sizes.max())

for lo, hi in [(1, 10), (11, 100), (101, 1000), (1001, 10**9)]:
    sel = (sizes >= lo) & (sizes <= hi)
    px = int(sizes[sel].sum())
    print(f"Componentes de {lo}-{hi} px: {int(sel.sum())} | pixeles: {px} ({100*px/sizes.sum():.1f} %)")

print("\nTop 10 componentes:")
print("id | px | ha | elev min/mediana/max (m) | prof mediana/p95/max (m)")
for i in np.argsort(sizes)[::-1][:10]:
    m = lab == (i + 1)
    z, dp = dem[m], depth[m]
    print(i + 1, "|", sizes[i], "|", round(sizes[i] * PIX_M2 / 1e4, 1), "|",
          np.round([z.min(), np.median(z), z.max()], 1).tolist(), "|",
          np.round([np.median(dp), np.percentile(dp, 95), dp.max()], 2).tolist())
