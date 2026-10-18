from pathlib import Path
import os
import subprocess
import geopandas as gpd
from shapely import force_2d

# 1. Localizar la carpeta principal del proyecto
PROJECT_DIR = Path(__file__).resolve().parent.parent

# 2. Definir los archivos necesarios
GPT = Path(
    os.environ.get(
        "SNAP_GPT_PATH",
        r"C:\Program Files\esa-snap\bin\gpt.exe"
    )
)

S1_DIR = PROJECT_DIR / "data" / "sentinel1"

post_files = list(S1_DIR.glob("*20170922*.zip"))

if len(post_files) == 0:
    raise FileNotFoundError(
        "No se encontró el Sentinel-1 POST del 22/09/2017."
    )

POST_FILE = post_files[0]

print("Archivo POST encontrado:")
print(POST_FILE)

AOI_FILE = (
    PROJECT_DIR
    / "data"
    / "aoi"
    / "AOI_Raster_Footprint.shp"
)

GRAPH_TEMPLATE = (
    PROJECT_DIR
    / "graphs"
    / "S1_preprocessing_dim.xml"
)

TEMP_GRAPH = (
    PROJECT_DIR
    / "graphs"
    / "S1_preprocessing_dim_temp.xml"
)

OUTPUT_FILE = (
    PROJECT_DIR
    / "outputs"
    / "S1_20170922_VH_dB.dim"
)

# 3. Leer el AOI y convertirlo a WGS84
aoi = gpd.read_file(AOI_FILE)
aoi = aoi.to_crs("EPSG:4326")

# Unir las geometrías y eliminar la dimensión Z
geometry = force_2d(aoi.geometry.union_all())

# Convertir la geometría a texto WKT
aoi_wkt = geometry.wkt

# 4. Leer el grafo XML y colocar dentro el AOI
graph_text = GRAPH_TEMPLATE.read_text(encoding="utf-8")

graph_text = graph_text.replace(
    "${aoi_wkt}",
    aoi_wkt
)

TEMP_GRAPH.write_text(
    graph_text,
    encoding="utf-8"
)

# 5. Ejecutar SNAP GPT para la imagen POST
command = [
    str(GPT),
    str(TEMP_GRAPH),
    f"-Pinput={POST_FILE}",
    f"-Poutput={OUTPUT_FILE}"
]

print("Procesando Sentinel-1 POST en formato BEAM-DIMAP...")

subprocess.run(
    command,
    check=True
)

print("\nProducto POST creado correctamente.")
print("Archivo:")
print(OUTPUT_FILE)