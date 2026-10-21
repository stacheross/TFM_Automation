from pathlib import Path
import numpy as np
import rasterio
from scipy import ndimage as ndi

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUT = PROJECT_DIR / "outputs"
DEPTH_DIR = OUT / "depth_prototype"
FLOOD = OUT / "Flood_Final_Candidate_Reconstructed.tif"
DEM = OUT / "DEM_AOI_S1grid.tif"
DEPTH_TIF = DEPTH_DIR / "Depth_FwDET_10m_Prototype.tif"
DIST_TIF = DEPTH_DIR / "Depth_FwDET_10m_DistToBoundary_m.tif"
NODATA = -9999.0


def main():
    DEPTH_DIR.mkdir(exist_ok=True)
    for p in (DEPTH_TIF, DIST_TIF):
        if p.exists():
            raise SystemExit(f"Ya existe {p.name}; no se sobrescribe.")

    with rasterio.open(FLOOD) as f:
        flood = f.read(1) == 1
        profile = f.profile
        t = f.transform
    with rasterio.open(DEM) as d:
        dem = d.read(1).astype("float64")
        dem_ok = dem != d.nodata

    flood = flood & dem_ok
    h, w = flood.shape

    # Tamano de pixel en metros (aprox.) a la latitud central
    lat = t.f + t.e * h / 2
    dy = abs(t.e) * 111320.0
    dx = abs(t.a) * 111320.0 * np.cos(np.radians(lat))

    # Borde de la mancha; el borde del raster no cuenta como orilla
    interior = ndi.binary_erosion(flood, border_value=1)
    boundary = flood & ~interior

    # Cota del borde mas cercano para cada pixel
    dist, idx = ndi.distance_transform_edt(~boundary, sampling=(dy, dx), return_indices=True)
    level = dem[idx[0], idx[1]]

    depth = np.where(flood, np.maximum(level - dem, 0.0), NODATA).astype("float32")
    dist_out = np.where(flood, dist, NODATA).astype("float32")

    profile.update(dtype="float32", nodata=NODATA, count=1, compress="lzw")
    for path, arr in ((DEPTH_TIF, depth), (DIST_TIF, dist_out)):
        with rasterio.open(path, "w", **profile) as dst:
            dst.write(arr, 1)

    dd = depth[flood]
    dist_f = dist[flood]
    print("Pixeles inundados:", int(flood.sum()), "| pixeles de borde:", int(boundary.sum()))
    print(f"Tamano de pixel aprox. (m): {dy:.2f} x {dx:.2f}")
    print("Profundidad (m) media / mediana / p95 / max:",
          np.round([dd.mean(), np.median(dd), np.percentile(dd, 95), dd.max()], 2))
    print("% con profundidad > 0:", round(100 * (dd > 0).mean(), 1))
    print("% con profundidad > 5 m:", round(100 * (dd > 5).mean(), 2))
    print("Distancia al borde (m) mediana / p95 / max:",
          np.round([np.median(dist_f), np.percentile(dist_f, 95), dist_f.max()], 1))
    print("Volumen aprox. (millones de m3):", round(float(dd.sum()) * dx * dy / 1e6, 3))
    print("Guardado en:", DEPTH_DIR)


if __name__ == "__main__":
    main()
