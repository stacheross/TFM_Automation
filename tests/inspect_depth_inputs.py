from pathlib import Path
import numpy as np
import rasterio

out = Path(__file__).resolve().parent.parent / "outputs"

for name in ["Flood_Final_Candidate_Reconstructed.tif", "DEM_AOI_05m.tif"]:
    with rasterio.open(out / name) as src:
        print(f"\n== {name}")
        print("CRS:", src.crs)
        print("Tamaño (filas x cols):", src.height, "x", src.width)
        print("Resolución:", src.res)
        print("Extensión:", src.bounds)
        print("Tipo / NoData:", src.dtypes[0], "/", src.nodata)
        if name.startswith("Flood"):
            a = src.read(1)
            vals, cnt = np.unique(a, return_counts=True)
            print("Valores y conteos:", dict(zip(vals.tolist(), cnt.tolist())))
            px = abs(src.res[0] * src.res[1])
            print("Área de valor 1 (km²):", round(cnt[vals == 1].sum() * px / 1e6, 4) if (vals == 1).any() else "no hay valor 1")
