from pathlib import Path
import os
import subprocess


# 1. Localizar las carpetas del proyecto
PROJECT_DIR = Path(__file__).resolve().parent.parent

S1_DIR = PROJECT_DIR / "data" / "sentinel1"
OUTPUT_DIR = PROJECT_DIR / "outputs"


# 2. Localizar SNAP GPT
GPT_PATH = Path(
    os.environ.get(
        "SNAP_GPT_PATH",
        r"C:\Program Files\esa-snap\bin\gpt.exe"
    )
)


# 3. Buscar productos Sentinel-1 ZIP
sentinel_files = list(S1_DIR.glob("*.zip"))

if len(sentinel_files) == 0:
    raise FileNotFoundError(
        "No se encontró ningún producto Sentinel-1 en data/sentinel1."
    )

input_file = sentinel_files[0]


# 4. Definir el archivo que producirá SNAP
output_file = OUTPUT_DIR / "S1_20170916_Orbit.dim"


# 5. Construir el comando para SNAP GPT
command = [
    str(GPT_PATH),
    "Apply-Orbit-File",
    f"-Ssource={input_file}",
    "-PorbitType=Sentinel Precise (Auto Download)",
    "-PpolyDegree=3",
    "-PcontinueOnFail=false",
    "-f",
    "BEAM-DIMAP",
    "-t",
    str(output_file),
]


# 6. Mostrar qué vamos a procesar
print("Producto de entrada:")
print(input_file)

print("\nProducto de salida:")
print(output_file)

print("\nEjecutando Apply-Orbit-File...")


# 7. Ejecutar SNAP
subprocess.run(command, check=True)


print("\nProceso terminado correctamente.")