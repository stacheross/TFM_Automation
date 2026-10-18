
from pathlib import Path
import csv
import numpy as np
import rasterio

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "outputs"

files = {
    "Original": "SAR_components_Original_8neighbors.tif",
    "Min6": "SAR_components_Min6_8neighbors.tif",
    "Min21": "SAR_components_Min21_8neighbors.tif",
}

dem_path = OUTPUT_DIR / "DEM_AOI_S1grid.tif"

# Intervalos descriptivos de elevación (metros)
bins = [-np.inf, 5, 10, 20, 50, np.inf]
labels = ["<5 m", "5-10 m", "10-20 m", "20-50 m", ">=50 m"]

with rasterio.open(dem_path) as dem_src:
    dem = dem_src.read(1, masked=True)
    elevation = dem.filled(np.nan)
    valid_dem = np.isfinite(elevation)

    masks = {}

    for name, filename in files.items():
        with rasterio.open(OUTPUT_DIR / filename) as src:

            if (
                src.crs != dem_src.crs
                or src.transform != dem_src.transform
                or src.shape != dem_src.shape
            ):
                raise ValueError(
                    f"{name} no coincide con la cuadrícula del DEM."
                )

            masks[name] = src.read(1) == 1

# Comprobar que los escenarios filtrados sean subconjuntos
if np.any(masks["Min6"] & ~masks["Original"]):
    raise ValueError("Min6 no es subconjunto de Original.")

if np.any(masks["Min21"] & ~masks["Original"]):
    raise ValueError("Min21 no es subconjunto de Original.")

masks["Eliminados_Min21"] = (
    masks["Original"] & ~masks["Min21"]
)

summary_rows = []
interval_rows = []

print("ANÁLISIS DE ELEVACIONES SAR")
print("=" * 65)

for name, mask in masks.items():

    total = int(np.count_nonzero(mask))
    valid_mask = mask & valid_dem
    valid_count = int(np.count_nonzero(valid_mask))
    missing = total - valid_count

    values = elevation[valid_mask]

    print(f"\nESCENARIO: {name}")
    print("-" * 65)
    print(f"Detecciones totales: {total:,}")
    print(f"Con elevación válida: {valid_count:,}")
    print(f"Sin elevación válida: {missing:,}")

    if valid_count == 0:
        raise ValueError(
            f"No hay elevaciones válidas para {name}."
        )

    stats = {
        "Escenario": name,
        "Pixeles_totales": total,
        "Pixeles_con_DEM": valid_count,
        "Pixeles_sin_DEM": missing,
        "Cobertura_DEM_pct": round(
            100 * valid_count / total, 2
        ),
        "Elevacion_min_m": round(float(np.min(values)), 2),
        "Elevacion_p25_m": round(
            float(np.percentile(values, 25)), 2
        ),
        "Elevacion_mediana_m": round(
            float(np.median(values)), 2
        ),
        "Elevacion_media_m": round(
            float(np.mean(values)), 2
        ),
        "Elevacion_p75_m": round(
            float(np.percentile(values, 75)), 2
        ),
        "Elevacion_max_m": round(float(np.max(values)), 2),
    }

    summary_rows.append(stats)

    print(f"Elevación mínima: {stats['Elevacion_min_m']} m")
    print(f"Percentil 25: {stats['Elevacion_p25_m']} m")
    print(f"Mediana: {stats['Elevacion_mediana_m']} m")
    print(f"Media: {stats['Elevacion_media_m']} m")
    print(f"Percentil 75: {stats['Elevacion_p75_m']} m")
    print(f"Elevación máxima: {stats['Elevacion_max_m']} m")

    print("\nDistribución por intervalos:")

    for i, label in enumerate(labels):
        count = int(np.count_nonzero(
            (values >= bins[i]) & (values < bins[i + 1])
        ))

        percentage = 100 * count / valid_count

        interval_rows.append({
            "Escenario": name,
            "Intervalo": label,
            "Pixeles": count,
            "Porcentaje_pct": round(percentage, 2)
        })

        print(
            f"  {label:10s}: {count:6,d} "
            f"({percentage:6.2f}%)"
        )

# Guardar resumen estadístico
summary_path = OUTPUT_DIR / "SAR_elevation_summary.csv"

with open(
    summary_path, "w", newline="", encoding="utf-8-sig"
) as f:
    writer = csv.DictWriter(
        f, fieldnames=summary_rows[0].keys()
    )
    writer.writeheader()
    writer.writerows(summary_rows)

# Guardar distribución por intervalos
interval_path = OUTPUT_DIR / "SAR_elevation_intervals.csv"

with open(
    interval_path, "w", newline="", encoding="utf-8-sig"
) as f:
    writer = csv.DictWriter(
        f, fieldnames=interval_rows[0].keys()
    )
    writer.writeheader()
    writer.writerows(interval_rows)

print("\nARCHIVOS GENERADOS")
print(summary_path)
print(interval_path)
