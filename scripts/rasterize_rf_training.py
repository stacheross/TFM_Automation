
from pathlib import Path
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.features import rasterize

ROOT = Path(__file__).resolve().parent.parent

TRAINING = ROOT / "data" / "RF_Muestras_Entrenamiento_Repaired.gpkg"
REFERENCE = ROOT / "outputs" / "DEM_AOI_10m_Bilinear.tif"
OUTPUT = ROOT / "outputs" / "RF_Training_10m.tif"

# Leer muestras originales reparadas
gdf = gpd.read_file(TRAINING)

with rasterio.open(REFERENCE) as ref:

    # Alinear las geometrías al sistema de referencia
    gdf = gdf.to_crs(ref.crs)

    # Preparar geometrías y etiquetas
    shapes = [
        (geometry, int(classvalue))
        for geometry, classvalue in zip(
            gdf.geometry,
            gdf["Classvalue"]
        )
    ]

    # Rasterizar sobre la cuadrícula del DEM
    training = rasterize(
        shapes=shapes,
        out_shape=ref.shape,
        transform=ref.transform,
        fill=0,
        all_touched=False,
        dtype=np.uint8
    )

    # Excluir las celdas sin datos del DEM
    dem = ref.read(1, masked=True)
    training[np.ma.getmaskarray(dem)] = 0

    profile = ref.profile.copy()
    profile.update(
        dtype="uint8",
        count=1,
        nodata=0,
        compress="lzw"
    )

    with rasterio.open(OUTPUT, "w", **profile) as dst:
        dst.write(training, 1)

print("\nRASTERIZACIÓN DE MUESTRAS RANDOM FOREST")
print("-" * 50)
print("Archivo:", OUTPUT)
print("No inundado (1):", np.count_nonzero(training == 1))
print("Inundado (2):", np.count_nonzero(training == 2))
print("Total de píxeles de entrenamiento:",
      np.count_nonzero(training > 0))
