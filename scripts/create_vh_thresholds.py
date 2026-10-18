from pathlib import Path
import numpy as np
import rasterio

# 1. Localizar la carpeta principal del proyecto
PROJECT_DIR = Path(__file__).resolve().parent.parent

# 2. Definir el ráster de cambio VH
CHANGE_FILE = (
    PROJECT_DIR
    / "outputs"
    / "S1_VH_change_Post_minus_Pre.tif"
)

# 3. Definir los umbrales que queremos evaluar
thresholds = [-1, -2, -3, -4, -5]

# 4. Abrir el ráster de cambio
with rasterio.open(CHANGE_FILE) as src:

    vh_change = src.read(1, masked=True)
    profile = src.profile.copy()

    # Los rásteres de umbral serán:
    # 1 = cumple el criterio
    # 0 = no cumple
    # 255 = NoData
    nodata_value = 255

    profile.update(
        dtype="uint8",
        count=1,
        nodata=nodata_value
    )

    # 5. Crear un ráster para cada umbral
    for threshold in thresholds:

        threshold_raster = np.full(
            vh_change.shape,
            nodata_value,
            dtype=np.uint8
        )

        valid_pixels = ~vh_change.mask

        threshold_raster[valid_pixels] = (
            vh_change.data[valid_pixels] <= threshold
        ).astype(np.uint8)

        # Convertir -1 en 1, -2 en 2, etc. para el nombre
        threshold_name = abs(threshold)

        output_file = (
            PROJECT_DIR
            / "outputs"
            / f"S1_VH_threshold_minus_{threshold_name}dB.tif"
        )

        with rasterio.open(output_file, "w", **profile) as dst:
            dst.write(threshold_raster, 1)

        selected_pixels = np.sum(threshold_raster == 1)

        print(
            f"Umbral <= {threshold} dB: "
            f"{selected_pixels} píxeles seleccionados"
        )

        print("Archivo:", output_file)

print("\nTodos los umbrales han sido generados correctamente.")