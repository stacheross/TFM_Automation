
from pathlib import Path
import numpy as np
import rasterio
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"

flood_path = OUT / "Flood_3dB_NoLayoverShadow_Slope5_Reconstructed.tif"
diagnostic_path = OUT / "Flood_Extra_Pixels_By_Source.tif"

with rasterio.open(flood_path) as src:
    flood = src.read(1) == 1
    transform = src.transform
    crs = src.crs
    shape = src.shape

with rasterio.open(diagnostic_path) as src:
    if src.shape != shape or src.transform != transform or src.crs != crs:
        raise ValueError("Las cuadrículas no coinciden.")

    # Clase 1: píxeles adicionales detectados solo por Min25
    extra_min25 = src.read(1) == 1

# Identificar regiones conectadas del criterio SAR inicial
structure = np.ones((3, 3), dtype=np.uint8)
labels, n_regions = ndimage.label(flood, structure=structure)

sizes = np.bincount(labels.ravel())

# Regiones que contienen píxeles adicionales amarillos
region_ids = np.unique(labels[extra_min25])
region_ids = region_ids[region_ids > 0]

region_sizes = sizes[region_ids]

print("\nREGIONES ASOCIADAS A PÍXELES ADICIONALES MIN25")
print("-" * 55)
print("Regiones identificadas:", len(region_ids))
print("Píxeles adicionales amarillos:", np.count_nonzero(extra_min25))

for minimum, maximum in [
    (25, 27),
    (28, 49),
    (50, 99),
    (100, 249),
    (250, 999),
    (1000, 999999999)
]:
    count = np.count_nonzero(
        (region_sizes >= minimum) &
        (region_sizes <= maximum)
    )

    print(f"Regiones de {minimum} a {maximum} píxeles: {count}")

print("\nDiez regiones más grandes:")
for size in sorted(region_sizes, reverse=True)[:10]:
    print(f"  {size} píxeles")

print("\nPÍXELES ADICIONALES POR TAMAÑO DE REGIÓN")
print("-" * 55)

pixel_region_sizes = sizes[labels[extra_min25]]

for minimum, maximum in [
    (25, 27),
    (28, 49),
    (50, 99),
    (100, 249),
    (250, 999),
    (1000, 999999999)
]:
    count = np.count_nonzero(
        (pixel_region_sizes >= minimum) &
        (pixel_region_sizes <= maximum)
    )

    percentage = 100 * count / np.count_nonzero(extra_min25)

    print(
        f"{minimum:>4}–{maximum:<9}: "
        f"{count:>5} píxeles ({percentage:.1f} %)"
    )