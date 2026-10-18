from pathlib import Path

# Carpeta principal del proyecto TFM_Automation
PROJECT_DIR = Path(__file__).resolve().parent.parent

# Carpeta donde guardamos los Sentinel-1 originales
S1_DIR = PROJECT_DIR / "data" / "sentinel1"

# Buscar todos los archivos ZIP dentro de esa carpeta
sentinel_files = list(S1_DIR.glob("*.zip"))

print("Carpeta Sentinel-1:")
print(S1_DIR)

print("\nProductos Sentinel-1 encontrados:")

for file in sentinel_files:
    print(file.name)
    