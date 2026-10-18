from pathlib import Path
import numpy as np
import rasterio

# 1. Localizar la carpeta principal del proyecto
PROJECT_DIR = Path(__file__).resolve().parent.parent

# 2. Definir las imágenes PRE y POST
PRE_FILE = (
    PROJECT_DIR
    / "outputs"
    / "S1_20170916_VH_dB.tif"
)

POST_FILE = (
    PROJECT_DIR
    / "outputs"
    / "S1_20170922_VH_dB.tif"
)

# 3. Función para calcular mínimo y máximo
def calculate_min_max(raster_file):

    with rasterio.open(raster_file) as src:

        data = src.read(1)

        # Excluir los píxeles de valor 0
        valid_data = data[data != 0]

        minimum = np.min(valid_data)
        maximum = np.max(valid_data)

        return minimum, maximum


# 4. Calcular estadísticas del PRE
pre_min, pre_max = calculate_min_max(PRE_FILE)

# 5. Calcular estadísticas del POST
post_min, post_max = calculate_min_max(POST_FILE)

# 6. Mostrar resultados
print("PRE - 16/09/2017")
print("Mínimo:", pre_min, "dB")
print("Máximo:", pre_max, "dB")

print()

print("POST - 22/09/2017")
print("Mínimo:", post_min, "dB")
print("Máximo:", post_max, "dB")