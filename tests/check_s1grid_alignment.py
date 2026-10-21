from pathlib import Path
import numpy as np
import rasterio

out = Path(__file__).resolve().parent.parent / "outputs"

with rasterio.open(out / "Flood_Final_Candidate_Reconstructed.tif") as f:
    ft, fcrs, fshape = f.transform, f.crs, (f.height, f.width)
    flood = f.read(1)

with rasterio.open(out / "DEM_AOI_S1grid.tif") as d:
    print("DEM_AOI_S1grid.tif")
    print("CRS:", d.crs)
    print("Tamano (filas x cols):", d.height, "x", d.width)
    print("Resolucion:", d.res)
    print("Extension:", d.bounds)
    print("Tipo / NoData:", d.dtypes[0], "/", d.nodata)
    print()
    print("Mismo CRS:", d.crs == fcrs)
    print("Mismo tamano:", (d.height, d.width) == fshape)
    print("Misma transformacion (tolerancia 1e-9):",
          np.allclose(tuple(d.transform)[:6], tuple(ft)[:6], atol=1e-9))
    if (d.height, d.width) == fshape:
        z = d.read(1).astype("float64")
        m = flood == 1
        zz = z[m]
        ok = zz != d.nodata
        print("Pixeles inundados:", int(m.sum()))
        print("Con elevacion valida:", int(ok.sum()))
        print("Elevacion (m) min / p5 / mediana / p95 / max:",
              np.round([zz[ok].min(), *np.percentile(zz[ok], [5, 50, 95]), zz[ok].max()], 2))
