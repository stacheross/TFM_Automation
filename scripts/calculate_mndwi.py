from pathlib import Path

import numpy as np
import rasterio


# 1. Localizar el proyecto
PROJECT_DIR = Path(__file__).resolve().parent.parent


# 2. Archivos
B03_FILE = (
    PROJECT_DIR
    / "data"
    / "sentinel2"
    / "extracted"
    / "T19QFA_20171020T150709_B03_10m.jp2"
)

B11_FILE = (
    PROJECT_DIR
    / "outputs"
    / "S2_B11_10m_aligned_to_B03.tif"
)

CLOUDMASK_FILE = (
    PROJECT_DIR
    / "outputs"
    / "S2_cloudmask_10m_aligned_to_B03.tif"
)

OUTPUT_FILE = (
    PROJECT_DIR
    / "outputs"
    / "MNDWI_20171020_cloudmasked.tif"
)


# 3. Abrir las tres capas
with rasterio.open(B03_FILE) as b03_src, \
     rasterio.open(B11_FILE) as b11_src, \
     rasterio.open(CLOUDMASK_FILE) as mask_src:

    # Leer las matrices
    b03 = b03_src.read(1).astype(np.float32)
    b11 = b11_src.read(1).astype(np.float32)
    cloudmask = mask_src.read(1)

    # Crear salida inicialmente como NoData
    NODATA = -9999.0

    mndwi = np.full(
        b03.shape,
        NODATA,
        dtype=np.float32
    )

    # Denominador de la ecuación
    denominator = b03 + b11

    # Píxeles que podemos utilizar
    valid = (
        (cloudmask == 1)
        & (b03 > 0)
        & (b11 > 0)
        & (denominator != 0)
    )

    # Calcular MNDWI solamente en píxeles válidos
    mndwi[valid] = (
        (b03[valid] - b11[valid])
        / denominator[valid]
    )

    # Copiar metadatos de B03
    profile = b03_src.profile.copy()

    profile.update(
        driver="GTiff",
        dtype="float32",
        count=1,
        nodata=NODATA,
        compress="lzw"
    )


# 4. Guardar resultado
with rasterio.open(
    OUTPUT_FILE,
    "w",
    **profile
) as dst:

    dst.write(
        mndwi,
        1
    )


# 5. Estadísticas
valid_mndwi = mndwi[mndwi != NODATA]

print("MNDWI creado:")
print(OUTPUT_FILE)

print("\nPíxeles válidos:")
print(f"{valid_mndwi.size:,}")

print("\nEstadísticas MNDWI:")
print("Mínimo:", float(valid_mndwi.min()))
print("Máximo:", float(valid_mndwi.max()))
print("Media:", float(valid_mndwi.mean()))
print("Mediana:", float(np.median(valid_mndwi)))

print("\nPercentiles:")
for percentile in [1, 5, 25, 50, 75, 95, 99]:

    value = np.percentile(
        valid_mndwi,
        percentile
    )

    print(
        f"P{percentile:02d}:",
        float(value)
    )