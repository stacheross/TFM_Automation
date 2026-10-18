
from pathlib import Path
import numpy as np
import rasterio

# 1. Rutas de los archivos
PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "outputs"

flood_path = (
    OUTPUT_DIR
    / "Flood_VH_minus_3dB_Slope_le_5deg_Prop50.tif"
)

landcover_path = (
    OUTPUT_DIR
    / "NOAA_LandCover_2010_S1grid.tif"
)

# 2. Abrir los rásteres
with rasterio.open(flood_path) as flood_src, \
     rasterio.open(landcover_path) as lc_src:

    if (
        flood_src.crs != lc_src.crs
        or flood_src.transform != lc_src.transform
        or flood_src.shape != lc_src.shape
    ):
        raise ValueError("Las cuadrículas no coinciden.")

    flood = flood_src.read(1)
    landcover = lc_src.read(1)

    # 3. Identificar las detecciones SAR
    detected = flood == 1

    # Código 21: Open Water (NOAA 2010)
    open_water = landcover == 21

    # Excluir zonas sin clasificación NOAA
    valid_landcover = landcover != 255

    # 4. Separar los dos conjuntos
    sar_on_water = detected & open_water

    sar_outside_water = (
        detected
        & valid_landcover
        & ~open_water
    )

    # 5. Guardar los resultados
    profile = flood_src.profile.copy()

    profile.update(
        driver="GTiff",
        dtype="uint8",
        count=1,
        nodata=255,
        compress="lzw"
    )

    outputs = {
        "SAR_on_OpenWater_2010.tif": sar_on_water,
        "SAR_outside_OpenWater_2010.tif": sar_outside_water
    }

    for filename, selection in outputs.items():

        result = np.full(
            flood.shape,
            255,
            dtype="uint8"
        )

        # 1 = píxel seleccionado
        # 0 = píxel no seleccionado dentro
        #     de la cobertura NOAA válida
        result[valid_landcover] = 0
        result[selection] = 1

        output_path = OUTPUT_DIR / filename

        with rasterio.open(
            output_path, "w", **profile
        ) as dst:
            dst.write(result, 1)

        print(f"\nArchivo: {filename}")
        print(
            "Píxeles seleccionados:",
            np.count_nonzero(selection)
        )

    print("\nTotal SAR original:", np.count_nonzero(detected))

    print(
        "Total separado:",
        np.count_nonzero(sar_on_water)
        + np.count_nonzero(sar_outside_water)
    )
