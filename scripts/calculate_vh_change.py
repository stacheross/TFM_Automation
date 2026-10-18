from pathlib import Path
import numpy as np
import rasterio

# 1. Localizar la carpeta principal del proyecto
PROJECT_DIR = Path(__file__).resolve().parent.parent

# 2. Definir los archivos de entrada y salida
PRE_FILE = PROJECT_DIR / "outputs" / "S1_20170916_VH_dB.tif"
POST_FILE = PROJECT_DIR / "outputs" / "S1_20170922_VH_dB_aligned.tif"
CHANGE_FILE = PROJECT_DIR / "outputs" / "S1_VH_change_Post_minus_Pre.tif"

# 3. Abrir PRE y POST
with rasterio.open(PRE_FILE) as pre, rasterio.open(POST_FILE) as post:

    # Leer la primera banda de cada GeoTIFF
    pre_data = pre.read(1)
    post_data = post.read(1)

    # 4. Crear una máscara común de píxeles válidos
    valid_mask = (
        (pre_data != 0) &
        (post_data != 0)
    )

    # Valor que utilizaremos para representar NoData
    nodata_value = -9999.0

    # Crear el ráster de salida inicialmente lleno de NoData
    vh_change = np.full(
        pre_data.shape,
        nodata_value,
        dtype=np.float32
    )

    # 5. Calcular POST - PRE solamente en píxeles válidos
    vh_change[valid_mask] = (
        post_data[valid_mask] - pre_data[valid_mask]
    )

    # 6. Copiar las propiedades espaciales del PRE
    profile = pre.profile.copy()

    profile.update(
        dtype="float32",
        count=1,
        nodata=nodata_value
    )

    # 7. Guardar el ráster de cambio
    with rasterio.open(CHANGE_FILE, "w", **profile) as dst:
        dst.write(vh_change, 1)

print("Cambio de retrodispersión VH calculado correctamente.")
print("Operación realizada: POST - PRE")
print("NoData:", nodata_value)
print("Archivo creado:")
print(CHANGE_FILE)