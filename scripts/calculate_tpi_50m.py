
from pathlib import Path
import numpy as np
import rasterio
from scipy.ndimage import convolve

ROOT = Path(__file__).resolve().parent.parent

INPUT = ROOT / "outputs" / "DEM_AOI_10m_Bilinear.tif"
OUTPUT = ROOT / "outputs" / "RF5_TPI_50m.tif"

RADIUS_METERS = 50
NODATA = -9999.0

with rasterio.open(INPUT) as src:
    dem = src.read(1, masked=True)

    valid = (
        ~np.ma.getmaskarray(dem)
        & np.isfinite(dem.data)
    )

    # Convertir radio de metros a píxeles
    resolution = abs(src.res[0])
    radius_pixels = int(round(RADIUS_METERS / resolution))

    # Crear una ventana circular de 50 m de radio
    y, x = np.ogrid[
        -radius_pixels:radius_pixels + 1,
        -radius_pixels:radius_pixels + 1
    ]

    kernel = (
        x**2 + y**2 <= radius_pixels**2
    ).astype(np.float64)

    # Excluir la celda central del promedio
    kernel[radius_pixels, radius_pixels] = 0

    # Evitar que NoData afecte la media
    elevations = np.where(
        valid,
        dem.data,
        0.0
    ).astype(np.float64)

    elevation_sum = convolve(
        elevations,
        kernel,
        mode="constant",
        cval=0.0
    )

    valid_count = convolve(
        valid.astype(np.float64),
        kernel,
        mode="constant",
        cval=0.0
    )

    neighborhood_mean = np.divide(
        elevation_sum,
        valid_count,
        out=np.full_like(elevation_sum, np.nan),
        where=valid_count > 0
    )

    # Calcular el TPI
    tpi = np.full(
        src.shape,
        NODATA,
        dtype=np.float32
    )

    calculation_mask = valid & (valid_count > 0)

    tpi[calculation_mask] = (
        dem.data[calculation_mask]
        - neighborhood_mean[calculation_mask]
    ).astype(np.float32)

    # Conservar propiedades espaciales del DEM
    profile = src.profile.copy()
    profile.update(
        dtype="float32",
        count=1,
        nodata=NODATA,
        compress="lzw"
    )

    with rasterio.open(OUTPUT, "w", **profile) as dst:
        dst.write(tpi, 1)

    print("\nCALCULO TPI - RADIO 50 m")
    print("-" * 50)
    print("Archivo:", OUTPUT)
    print("Radio:", RADIUS_METERS, "m")
    print("Radio en pixeles:", radius_pixels)
    print("Pixeles validos:", np.count_nonzero(calculation_mask))
    print("Pixeles sin datos:", np.count_nonzero(~calculation_mask))

    if calculation_mask.any():
        values = tpi[calculation_mask]

        print("TPI minimo:", float(values.min()))
        print("TPI maximo:", float(values.max()))
        print("TPI medio:", float(values.mean()))
        print("TPI mediana:", float(np.median(values)))
