
from pathlib import Path
import numpy as np
import rasterio
from scipy import ndimage

# 1. Rutas
PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "outputs"

input_path = (
    OUTPUT_DIR
    / "Flood_VH_minus_3dB_Slope_le_5deg_Prop50.tif"
)

output_path = (
    OUTPUT_DIR
    / "SAR_connected_components_8.tif"
)

# 2. Abrir el ráster
with rasterio.open(input_path) as src:

    data = src.read(1)

    # Solo los píxeles detectados como posible inundación
    detected = data == 1

    # 3. Definir conectividad de 8 vecinos
    structure = np.ones((3, 3), dtype=np.uint8)

    # 4. Identificar componentes conectados
    labels, number = ndimage.label(
        detected,
        structure=structure
    )

    # 5. Contar píxeles de cada componente
    sizes = np.bincount(labels.ravel())[1:]

    print("ANÁLISIS DE CONECTIVIDAD SAR")
    print("-" * 55)

    print("Píxeles SAR:", np.count_nonzero(detected))
    print("Número de componentes:", number)

    if number > 0:

        print("\nTamaño de los componentes:")
        print("Mayor:", sizes.max(), "píxeles")
        print("Mediana:", np.median(sizes), "píxeles")

        ranges = {
            "1 píxel": (1, 1),
            "2 a 5 píxeles": (2, 5),
            "6 a 20 píxeles": (6, 20),
            "21 a 100 píxeles": (21, 100),
            "Más de 100 píxeles": (101, np.inf)
        }

        print("\nDISTRIBUCIÓN POR TAMAÑO")
        print("-" * 55)

        for name, (minimum, maximum) in ranges.items():

            selected = (
                (sizes >= minimum)
                & (sizes <= maximum)
            )

            component_count = np.count_nonzero(selected)
            pixel_count = sizes[selected].sum()

            print(
                f"{name:22s} | "
                f"{component_count:5,d} componentes | "
                f"{pixel_count:7,d} píxeles"
            )

        # 6. Los diez componentes mayores
        largest_ids = np.argsort(sizes)[::-1][:10]

        print("\nDIEZ COMPONENTES MAYORES")
        print("-" * 55)

        for position, index in enumerate(largest_ids, start=1):
            print(
                f"{position:2d}. "
                f"Componente {index + 1}: "
                f"{sizes[index]:,} píxeles"
            )

    # 7. Guardar etiquetas de componentes
    # 0 = fondo; números positivos = identificadores
    # NoData original se conserva como -1
    output = labels.astype("int32")

    if src.nodata is not None:
        output[data == src.nodata] = -1

    profile = src.profile.copy()

    profile.update(
        driver="GTiff",
        dtype="int32",
        nodata=-1,
        compress="lzw"
    )

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(output, 1)

    print("\nRáster generado:")
    print(output_path)
