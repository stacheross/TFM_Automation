from pathlib import Path
import numpy as np
import geopandas as gpd
import rasterio
import shapely
from shapely.geometry import box
from pyproj import Transformer

PROJ = Path(__file__).resolve().parent.parent
HYDRO = PROJ / "data" / "hydro"
files = sorted(p for p in HYDRO.glob("*") if p.suffix.lower() in (".shp", ".gpkg", ".geojson")) if HYDRO.exists() else []
if not files:
    raise SystemExit("No hay .shp/.gpkg/.geojson en data\\hydro")
print("Archivos:", [p.name for p in files])

aoi = box(119539.0, 244378.5, 131039.0, 253228.5)
with rasterio.open(PROJ / "outputs" / "Flood_Final_Candidate_Reconstructed.tif") as f:
    a = f.read(1)
    t = f.transform
r_, c_ = np.where(a == 1)
x = t.c + (c_ + 0.5) * t.a
y = t.f + (r_ + 0.5) * t.e
X, Y = Transformer.from_crs(4326, 6566, always_xy=True).transform(x, y)
pts = shapely.points(X, Y)

for p in files:
    gdf = gpd.read_file(p)
    print("\n==", p.name)
    print("CRS:", gdf.crs)
    print("Entidades:", len(gdf), "| tipos:", gdf.geom_type.value_counts().to_dict())
    print("Columnas:", [c for c in gdf.columns if c != "geometry"])
    for c in gdf.columns:
        if c != "geometry" and gdf[c].dtype == object and gdf[c].nunique() <= 30:
            print(f"  {c}:", gdf[c].value_counts().head(10).to_dict())
    g = gdf.to_crs(6566)
    clipped = g.geometry.intersection(aoi)
    clipped = clipped[~clipped.is_empty]
    print("Entidades que tocan el area:", len(clipped))
    print("Longitud total (km):", round(g.length.sum() / 1000, 2),
          "| dentro del area (km):", round(clipped.length.sum() / 1000, 2))
    if len(clipped):
        d = shapely.distance(pts, clipped.union_all())
        print("Distancia de los pixeles inundados a la linea (m) mediana / p95 / max:",
              np.round([np.median(d), np.percentile(d, 95), d.max()], 0))
        print("% a <= 100 m:", round(100 * (d <= 100).mean(), 1), "| % a <= 500 m:", round(100 * (d <= 500).mean(), 1))
