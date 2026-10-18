from pathlib import Path
import rasterio
from rasterio.warp import reproject, Resampling

# 1. Localizar la carpeta principal del proyecto
PROJECT_DIR = Path(__file__).resolve().parent.parent

# 2. Definir los archivos
PRE_FILE = PROJECT_DIR / "outputs" / "S1_20170916_VH_dB.tif"
POST_FILE = PROJECT_DIR / "outputs" / "S1_20170922_VH_dB.tif"
ALIGNED_FILE = PROJECT_DIR / "outputs" / "S1_20170922_VH_dB_aligned.tif"

# 3. Abrir PRE y POST
with rasterio.open(PRE_FILE) as pre, rasterio.open(POST_FILE) as post:

    # Copiar las propiedades espaciales del PRE
    profile = post.profile.copy()

    profile.update(
        crs=pre.crs,
        transform=pre.transform,
        width=pre.width,
        height=pre.height
    )

    # 4. Crear el nuevo POST alineado
    with rasterio.open(ALIGNED_FILE, "w", **profile) as aligned:

        # 5. Alinear cada banda del POST
        for band in range(1, post.count + 1):

            reproject(
                source=rasterio.band(post, band),
                destination=rasterio.band(aligned, band),
                src_transform=post.transform,
                src_crs=post.crs,
                dst_transform=pre.transform,
                dst_crs=pre.crs,
                resampling=Resampling.bilinear
            )

print("POST alineado correctamente.")
print("Archivo creado:")
print(ALIGNED_FILE)