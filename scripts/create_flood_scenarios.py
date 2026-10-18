from pathlib import Path
import numpy as np
import rasterio


# 1. Localizar la carpeta principal
PROJECT_DIR = Path(__file__).resolve().parent.parent


# 2. Ráster de cambio VH
VH_CHANGE_FILE = (
    PROJECT_DIR
    / "outputs"
    / "S1_VH_change_Post_minus_Pre.tif"
)


# 3. Umbrales VH que queremos evaluar
VH_THRESHOLDS = [-3]


# 4. Umbrales de pendiente
SLOPE_THRESHOLDS = [1,2,3,4,5,6, 7]


# 5. Proporción mínima de terreno que debe cumplir
# el criterio de pendiente
MIN_SLOPE_PROPORTION = 0.50


# 6. Abrir el ráster de cambio VH
with rasterio.open(VH_CHANGE_FILE) as vh_src:

    vh = vh_src.read(1)

    vh_valid = vh != vh_src.nodata

    profile = vh_src.profile.copy()

    profile.update(
        dtype="uint8",
        count=1,
        nodata=255,
        compress="lzw"
    )

    # 7. Recorrer los cinco umbrales de pendiente
    for slope_threshold in SLOPE_THRESHOLDS:

        SLOPE_FILE = (
            PROJECT_DIR
            / "outputs"
            / f"Slope_proportion_le_{slope_threshold}deg_S1grid.tif"
        )

        with rasterio.open(SLOPE_FILE) as slope_src:

            slope_proportion = slope_src.read(1)

            slope_valid = (
                slope_proportion != slope_src.nodata
            )

            # Comprobar que ambas cuadrículas coinciden
            if (
                vh_src.crs != slope_src.crs
                or vh_src.transform != slope_src.transform
                or vh_src.width != slope_src.width
                or vh_src.height != slope_src.height
            ):
                raise ValueError(
                    "VH y pendiente no están "
                    "perfectamente alineados."
                )

            valid = vh_valid & slope_valid

            # 8. Recorrer los cinco umbrales VH
            for vh_threshold in VH_THRESHOLDS:

                result = np.full(
                    vh.shape,
                    255,
                    dtype=np.uint8
                )

                # Los píxeles válidos empiezan como 0
                result[valid] = 0

                # 9. Aplicar simultáneamente ambos criterios
                flood_mask = (
                    valid
                    & (vh <= vh_threshold)
                    & (
                        slope_proportion
                        >= MIN_SLOPE_PROPORTION
                    )
                )

                result[flood_mask] = 1

                # 10. Crear nombre de salida
                OUTPUT_FILE = (
                    PROJECT_DIR
                    / "outputs"
                    / (
                        f"Flood_VH_minus_{abs(vh_threshold)}dB_"
                        f"Slope_le_{slope_threshold}deg_"
                        f"Prop50.tif"
                    )
                )

                # 11. Guardar
                with rasterio.open(
                    OUTPUT_FILE,
                    "w",
                    **profile
                ) as dst:

                    dst.write(result, 1)

                selected = np.count_nonzero(
                    result == 1
                )

                print(
                    f"VH <= {vh_threshold} dB | "
                    f"Pendiente <= {slope_threshold}° | "
                    f"Prop >= 50%: "
                    f"{selected:,} píxeles"
                )


print(
    "\n25 escenarios de inundación creados correctamente."
)