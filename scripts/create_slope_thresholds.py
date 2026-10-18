from pathlib import Path
import numpy as np
import rasterio


# 1. Localizar la carpeta principal del proyecto
PROJECT_DIR = Path(__file__).resolve().parent.parent


# 2. Definir el ráster de pendiente
SLOPE_FILE = (
    PROJECT_DIR
    / "outputs"
    / "Slope_AOI_05m_degrees.tif"
)


# 3. Definir los umbrales que queremos probar
THRESHOLDS = [6,7]


# 4. Abrir el ráster de pendiente
with rasterio.open(SLOPE_FILE) as src:

    slope = src.read(1, masked=True)

    # Copiar las propiedades espaciales
    profile = src.profile.copy()

    # Preparar el perfil para rásteres binarios
    profile.update(
        dtype="uint8",
        count=1,
        nodata=255,
        compress="lzw"
    )

    # 5. Crear un ráster para cada umbral
    for threshold in THRESHOLDS:

        # Crear inicialmente todo como NoData
        result = np.full(
            slope.shape,
            255,
            dtype=np.uint8
        )

        # Identificar los píxeles válidos
        valid_mask = ~slope.mask

        # Asignar 0 a todos los píxeles válidos
        result[valid_mask] = 0

        # Asignar 1 donde la pendiente cumple el umbral
        result[
            valid_mask
            & (slope.data <= threshold)
        ] = 1

        # Definir el archivo de salida
        OUTPUT_FILE = (
            PROJECT_DIR
            / "outputs"
            / f"Slope_threshold_le_{threshold}deg.tif"
        )

        # Guardar el resultado
        with rasterio.open(
            OUTPUT_FILE,
            "w",
            **profile
        ) as dst:

            dst.write(result, 1)

        # Contar los píxeles seleccionados
        selected_pixels = np.count_nonzero(
            result == 1
        )

        print(
            f"Pendiente <= {threshold}°:",
            f"{selected_pixels:,}",
            "píxeles seleccionados"
        )


print("\nUmbrales de pendiente creados correctamente.")