import subprocess

GPT_PATH = r"C:\Program Files\esa-snap\bin\gpt.exe"

print("Comprobando conexión con SNAP GPT...")

result = subprocess.run(
    [GPT_PATH],
    capture_output=True,
    text=True
)

print(result.stdout)

if result.returncode == 0:
    print("\nSNAP GPT funciona correctamente desde Python.")
else:
    print("\nSNAP GPT se ejecutó, pero devolvió el código:", result.returncode)
