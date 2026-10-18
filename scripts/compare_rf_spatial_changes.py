
from pathlib import Path
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ROOT / "outputs"

PAIRS = [
    ("RF1", "RF2"),
    ("RF2", "RF3"),
    ("RF3", "RF4")
]

print("\nMAPAS DE CAMBIOS RF1-RF4")
print("-" * 50)

for model_a, model_b in PAIRS:

    file_a = OUTPUTS / f"{model_a}_ArcGIS_Parameters_Classification.tif"
    file_b = OUTPUTS / f"{model_b}_ArcGIS_Parameters_Classification.tif"

    with rasterio.open(file_a) as src_a, rasterio.open(file_b) as src_b:

        if (
            src_a.shape != src_b.shape
            or src_a.transform != src_b.transform
            or src_a.crs != src_b.crs
        ):
            raise ValueError(
                f"Los rasteres {model_a} y {model_b} no estan alineados."
            )

        a = src_a.read(1)
        b = src_b.read(1)

        # 0 = Sin datos
        # 1 = No inundado en ambos
        # 2 = Inundado en ambos
        # 3 = Inundado -> No inundado
        # 4 = No inundado -> Inundado

        changes = np.zeros(src_a.shape, dtype=np.uint8)

        changes[(a == 1) & (b == 1)] = 1
        changes[(a == 2) & (b == 2)] = 2
        changes[(a == 2) & (b == 1)] = 3
        changes[(a == 1) & (b == 2)] = 4

        profile = src_a.profile.copy()
        profile.update(
            driver="GTiff",
            dtype="uint8",
            count=1,
            nodata=0,
            compress="lzw"
        )

        output = OUTPUTS / f"{model_a}_vs_{model_b}_Changes.tif"

        with rasterio.open(output, "w", **profile) as dst:
            dst.write(changes, 1)

            # Colores para facilitar la visualizacion
            dst.write_colormap(1, {
                0: (0, 0, 0, 0),
                1: (225, 225, 225, 255),
                2: (40, 110, 190, 255),
                3: (230, 140, 50, 255),
                4: (60, 160, 100, 255)
            })

    print(f"\n{model_a} vs {model_b}")
    print("Sin cambios - No inundado:", np.count_nonzero(changes == 1))
    print("Sin cambios - Inundado:", np.count_nonzero(changes == 2))
    print("Inundado -> No inundado:", np.count_nonzero(changes == 3))
    print("No inundado -> Inundado:", np.count_nonzero(changes == 4))
    print("Archivo:", output)
