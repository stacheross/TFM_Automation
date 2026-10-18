
from pathlib import Path
import geopandas as gpd
from shapely.validation import make_valid

ROOT = Path(__file__).resolve().parent.parent

INPUT = ROOT / "data" / "RF_Muestras_Entrenamiento_Final.shp"
OUTPUT = ROOT / "data" / "RF_Muestras_Entrenamiento_Repaired.gpkg"

gdf = gpd.read_file(INPUT)

print("Geometrías inválidas antes:",
      (~gdf.geometry.is_valid).sum())

# Reparar geometrías sin modificar las muestras originales
gdf["geometry"] = gdf.geometry.apply(make_valid)

# Comprobar el resultado
print("Geometrías inválidas después:",
      (~gdf.geometry.is_valid).sum())

print("Tipos de geometría:",
      gdf.geom_type.value_counts().to_dict())

print("Clases:",
      gdf["Classvalue"].tolist())

# Guardar copia corregida
gdf.to_file(
    OUTPUT,
    layer="RF_Training_Repaired",
    driver="GPKG"
)

print("\nArchivo creado:", OUTPUT)
