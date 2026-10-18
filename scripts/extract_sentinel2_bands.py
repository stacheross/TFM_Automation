from pathlib import Path
from zipfile import ZipFile
import shutil


# 1. Localizar la carpeta principal del proyecto
PROJECT_DIR = Path(__file__).resolve().parent.parent


# 2. Carpetas de entrada y salida
S2_DIR = (
    PROJECT_DIR
    / "data"
    / "sentinel2"
)

OUTPUT_DIR = (
    S2_DIR
    / "extracted"
)


# 3. Crear la carpeta de salida si no existe
OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# 4. Buscar el producto Sentinel-2
zip_files = list(
    S2_DIR.glob("*.zip")
)

if len(zip_files) == 0:
    raise FileNotFoundError(
        "No se encontró ningún Sentinel-2 ZIP."
    )

S2_ZIP = zip_files[0]


# 5. Abrir el ZIP
with ZipFile(S2_ZIP, "r") as sentinel_zip:

    files = sentinel_zip.namelist()

    # 6. Localizar las tres capas necesarias
    targets = [
        name
        for name in files
        if (
            name.endswith("_B03_10m.jp2")
            or name.endswith("_B11_20m.jp2")
            or name.endswith("_SCL_20m.jp2")
        )
    ]

    # 7. Comprobar que encontramos exactamente tres
    if len(targets) != 3:
        raise ValueError(
            f"Se esperaban 3 archivos, "
            f"pero se encontraron {len(targets)}."
        )

    # 8. Extraer cada archivo
    for internal_path in targets:

        output_file = (
            OUTPUT_DIR
            / Path(internal_path).name
        )

        with sentinel_zip.open(
            internal_path
        ) as source:

            with open(
                output_file,
                "wb"
            ) as destination:

                shutil.copyfileobj(
                    source,
                    destination
                )

        print(
            "Extraído:",
            output_file.name
        )


print("\nExtracción completada.")
print("Carpeta:")
print(OUTPUT_DIR)