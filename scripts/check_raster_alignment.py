from pathlib import Path
import rasterio

# 1. Localizar la carpeta principal del proyecto
PROJECT_DIR = Path(__file__).resolve().parent.parent

# 2. Definir los dos rásteres que vamos a comparar
PRE_FILE = PROJECT_DIR / "outputs" / "S1_20170916_VH_dB.tif"
POST_FILE = PROJECT_DIR / "outputs" / "S1_20170922_VH_dB_aligned.tif"

# 3. Abrir los dos GeoTIFF
with rasterio.open(PRE_FILE) as pre, rasterio.open(POST_FILE) as post:

    print("=== PRE ===")
    print("CRS:", pre.crs)
    print("Dimensiones:", pre.width, "x", pre.height)
    print("Tamaño de píxel:", pre.res)
    print("Transformación:", pre.transform)

    print("\n=== POST ===")
    print("CRS:", post.crs)
    print("Dimensiones:", post.width, "x", post.height)
    print("Tamaño de píxel:", post.res)
    print("Transformación:", post.transform)

    # 4. Comparar las propiedades espaciales
    same_crs = pre.crs == post.crs
    same_dimensions = (
        pre.width == post.width and
        pre.height == post.height
    )
    same_resolution = pre.res == post.res
    same_transform = pre.transform == post.transform

    print("\n=== COMPROBACIÓN ===")
    print("Mismo CRS:", same_crs)
    print("Mismas dimensiones:", same_dimensions)
    print("Misma resolución:", same_resolution)
    print("Misma transformación:", same_transform)

    print("\n=== DIFERENCIA ENTRE CUADRÍCULAS ===")
    print("Origen PRE (X):", pre.transform.c)
    print("Origen POST (X):", post.transform.c)
    print("Diferencia X:", post.transform.c - pre.transform.c)

    print("\nOrigen PRE (Y):", pre.transform.f)
    print("Origen POST (Y):", post.transform.f)
    print("Diferencia Y:", post.transform.f - pre.transform.f)

    if (
        same_crs
        and same_dimensions
        and same_resolution
        and same_transform
    ):
        print("\nRESULTADO: PRE y POST están perfectamente alineados.")
    else:
        print("\nRESULTADO: PRE y POST NO están perfectamente alineados.")