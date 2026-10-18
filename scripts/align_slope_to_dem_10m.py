
from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import from_bounds, transform as window_transform

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"

dem_file = OUT / "DEM_AOI_10m_Bilinear.tif"
slope_file = OUT / "Slope_AOI_10m_Planar.tif"
output_file = OUT / "Slope_AOI_10m_Aligned.tif"

with rasterio.open(dem_file) as dem, rasterio.open(slope_file) as slope:

    if dem.crs != slope.crs:
        raise ValueError("Los CRS no coinciden.")

    if not np.allclose(dem.res, slope.res):
        raise ValueError("Las resoluciones no coinciden.")

    window = from_bounds(*dem.bounds, transform=slope.transform)
    window = window.round_offsets().round_lengths()

    if (
        window.col_off < 0
        or window.row_off < 0
        or window.col_off + window.width > slope.width
        or window.row_off + window.height > slope.height
    ):
        raise ValueError("La extensión del DEM no está cubierta por la pendiente.")

    aligned_transform = window_transform(window, slope.transform)

    if (
        window.width != dem.width
        or window.height != dem.height
        or not np.allclose(
            tuple(aligned_transform),
            tuple(dem.transform),
            atol=1e-7,
            rtol=0
        )
    ):
        raise ValueError("Las cuadrículas no coinciden exactamente.")

    slope_data = slope.read(1, window=window)
    dem_mask = dem.read_masks(1) > 0
    slope_mask = slope.read_masks(1, window=window) > 0

    nodata = -9999.0

    valid = (
        dem_mask
        & slope_mask
        & np.isfinite(slope_data)
    )

    result = np.full(dem.shape, nodata, dtype=np.float32)
    result[valid] = slope_data[valid]

    profile = dem.profile.copy()
    profile.update(
        dtype="float32",
        count=1,
        nodata=nodata,
        compress="lzw"
    )

    with rasterio.open(output_file, "w", **profile) as dst:
        dst.write(result, 1)

print("PENDIENTE ALINEADA")
print("-" * 50)
print("Archivo:", output_file)

with rasterio.open(dem_file) as dem, rasterio.open(output_file) as slope:
    print("Dimensiones:", slope.shape)
    print("Resolución:", slope.res)
    print("Misma cuadrícula:", (
        dem.crs == slope.crs
        and dem.transform == slope.transform
        and dem.shape == slope.shape
    ))
    print("NoData:", slope.nodata)
