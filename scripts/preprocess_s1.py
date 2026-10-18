from pathlib import Path
import os
import subprocess
import geopandas as gpd
from shapely import force_2d

# 1. Localizar la carpeta principal del proyecto
PROJECT_DIR = Path(__file__).resolve().parent.parent


# 2. Definir las carpetas y archivos que utilizaremos
S1_DIR = PROJECT_DIR / "data" / "sentinel1"
OUTPUT_DIR = PROJECT_DIR / "outputs"
GRAPH_FILE = PROJECT_DIR / "graphs" / "S1_preprocessing.xml"
AOI_FILE = PROJECT_DIR / "data" / "aoi" / "AOI_Raster_Footprint.shp"

GPT_PATH = Path(
    os.environ.get(
        "SNAP_GPT_PATH",
        r"C:\Program Files\esa-snap\bin\gpt.exe"
    )
)


# 3. Buscar los productos Sentinel-1
sentinel_files = list(S1_DIR.glob("*.zip"))
sentinel_files = sorted(sentinel_files)

if len(sentinel_files) == 0:
    raise FileNotFoundError(
        "No se encontró ningún producto Sentinel-1 en data/sentinel1."
    )

# Leer el área de estudio
aoi = gpd.read_file(AOI_FILE)

# Transformarla a coordenadas geográficas WGS84
aoi_wgs84 = aoi.to_crs("EPSG:4326")

# Unir las geometrías y eliminar la dimensión Z
geometry = aoi_wgs84.geometry.union_all()
geometry = force_2d(geometry)

# Convertir la geometría al formato WKT que utiliza SNAP
aoi_wkt = geometry.wkt

# Leer el grafo XML original como texto
graph_text = GRAPH_FILE.read_text(encoding="utf-8")

# Sustituir la variable ${aoi_wkt} por la geometría WKT completa
graph_text = graph_text.replace("${aoi_wkt}", aoi_wkt)

# Crear la ruta para una copia temporal del grafo
TEMP_GRAPH_FILE = PROJECT_DIR / "graphs" / "S1_preprocessing_temp.xml"

# Guardar el grafo temporal
TEMP_GRAPH_FILE.write_text(graph_text, encoding="utf-8")


# 4. Procesar cada producto Sentinel-1
for input_file in sentinel_files:
# Obtener la fecha a partir del nombre del producto Sentinel-1
    filename = input_file.name

    if "20170916" in filename:
        date = "20170916"
    elif "20170922" in filename:
        date = "20170922"
    else:
        print(f"Producto omitido porque no corresponde a una fecha esperada: {filename}")
        continue

# Definir el GeoTIFF de salida para esta fecha
    output_file = OUTPUT_DIR / f"S1_{date}_VH_dB.tif"

# Construir el comando que ejecutará SNAP
    command = [
        str(GPT_PATH),
        str(TEMP_GRAPH_FILE),
        f"-Pinput={input_file}",
        f"-Poutput={output_file}",
    ]

# Mostrar información antes del procesamiento
    print("\nProducto Sentinel-1 de entrada:")
    print(input_file)

    print("\nGrafo SNAP:")
    print(TEMP_GRAPH_FILE)

    print("\nProducto de salida:")
    print(output_file)

    print("\nEjecutando preprocesamiento SNAP...")

# Ejecutar el grafo
    subprocess.run(command, check=True)

    print(f"\nProcesamiento de {date} terminado correctamente.")

print("\nTodos los productos Sentinel-1 han sido procesados.")