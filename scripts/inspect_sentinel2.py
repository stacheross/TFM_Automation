from pathlib import Path
from zipfile import ZipFile


# 1. Localizar la carpeta principal del proyecto
PROJECT_DIR = Path(__file__).resolve().parent.parent


# 2. Localizar la carpeta de Sentinel-2
S2_DIR = (
    PROJECT_DIR
    / "data"
    / "sentinel2"
)


# 3. Buscar productos Sentinel-2 comprimidos
zip_files = list(
    S2_DIR.glob("*.zip")
)


# 4. Comprobar que se encontró al menos uno
if len(zip_files) == 0:
    raise FileNotFoundError(
        "No se encontró ningún archivo ZIP "
        "en data\\sentinel2."
    )


print("Productos Sentinel-2 encontrados:")
print(len(zip_files))


# 5. Examinar cada producto
for zip_file in zip_files:

    print("\nProducto:")
    print(zip_file.name)

    with ZipFile(zip_file, "r") as sentinel_zip:

        files = sentinel_zip.namelist()

        # Buscar B03 a 10 m
        b03_files = [
            name
            for name in files
            if "IMG_DATA/R10m/" in name
            and name.endswith("_B03_10m.jp2")
        ]

        # Buscar B11 a 20 m
        b11_files = [
            name
            for name in files
            if "IMG_DATA/R20m/" in name
            and name.endswith("_B11_20m.jp2")
        ]

        # Buscar Scene Classification Layer a 20 m
        scl_files = [
            name
            for name in files
            if "IMG_DATA/R20m/" in name
            and name.endswith("_SCL_20m.jp2")
        ]

        print("\nB03 10 m:")
        for name in b03_files:
            print(name)

        print("\nB11 20 m:")
        for name in b11_files:
            print(name)

        print("\nSCL 20 m:")
        for name in scl_files:
            print(name)

        print("\nResumen:")
        print("B03 encontrados:", len(b03_files))
        print("B11 encontrados:", len(b11_files))
        print("SCL encontrados:", len(scl_files))