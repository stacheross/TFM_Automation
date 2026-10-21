from pathlib import Path
import numpy as np
import geopandas as gpd
import rasterio
import shapely
from pyproj import Transformer
from scipy import ndimage as ndi
from shapely.geometry import LineString
from shapely.ops import linemerge, unary_union
from sklearn.isotonic import IsotonicRegression

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUT = PROJECT_DIR / "outputs"
DEPTH_DIR = OUT / "depth_prototype"
FLOOD = OUT / "Flood_Final_Candidate_Reconstructed.tif"
DEM = OUT / "DEM_AOI_S1grid.tif"
RIVER_DIR = PROJECT_DIR / "data" / "hydro"
GPKG = OUT / "Flood_Reconstruction_Review.gpkg"
REMOVED_LAYER = "Flood_Removed_Manual_Review"   # poligonos descartados (falsos positivos)
NODATA = -9999.0

# Parametros de prueba (elegidos sin calibrar)
DMAX = 500.0        # m: distancia maxima al cauce para asignar profundidad
BIN = 250.0         # m: longitud de cada tramo del perfil
MIN_BOUNDARY = 10   # pixeles de borde minimos por tramo
SMOOTH_BINS = 3     # ventana de suavizado (tramos)
PCTS = {"p50": 50, "p90": 90}
ALLOW_EXTRAPOLATION = False   # False: sin profundidad fuera del rango de tramos con borde suficiente

# Puentes: ((lon, lat) extremo 1, (lon, lat) extremo 2, semiancho de franja en m).
BRIDGES = [
    ((-67.1614992, 18.2724909), (-67.1617715, 18.2729469), 40.0),
]

# Si es True, los pixeles en poligonos descartados en la revision manual salen de la mancha.
USE_REVIEW_MASK = True
PREFIX = "Depth_RiverProfile_Reviewed_10m" if USE_REVIEW_MASK else "Depth_RiverProfile_10m"


def free_names():
    """Nombres de salida que no existen aun (nunca sobrescribe)."""
    n = 1
    while True:
        tag = "" if n == 1 else f"_v{n}"
        paths = {k: DEPTH_DIR / f"{PREFIX}_{k}{tag}.tif" for k in PCTS}
        flag = DEPTH_DIR / f"{PREFIX}_Flag{tag}.tif"
        if not any(p.exists() for p in [*paths.values(), flag]):
            return paths, flag, tag
        n += 1


def main():
    DEPTH_DIR.mkdir(exist_ok=True)
    outs, flag_tif, tag = free_names()
    if tag:
        print(f"Ya existian salidas anteriores; se guardan con el sufijo {tag}")

    with rasterio.open(FLOOD) as f:
        flood = f.read(1) == 1
        t = f.transform
        profile = f.profile
    with rasterio.open(DEM) as d:
        dem = d.read(1).astype("float64")
        dnod = d.nodata
    flood &= dem != dnod
    h, w = flood.shape
    if profile["crs"].to_epsg() != 4326:
        raise SystemExit("Se esperaba la mancha en EPSG:4326")

    # Mascara de revision: fuera los pixeles en poligonos descartados
    removed_rc = (np.array([], dtype=int), np.array([], dtype=int))
    if USE_REVIEW_MASK:
        rem = gpd.read_file(GPKG, layer=REMOVED_LAYER).to_crs(4326).geometry.union_all()
        shapely.prepare(rem)
        r0, c0 = np.where(flood)
        gone = shapely.contains_xy(rem, t.c + (c0 + 0.5) * t.a, t.f + (r0 + 0.5) * t.e)
        removed_rc = (r0[gone], c0[gone])
        flood[removed_rc] = False
        print(f"Mascara de revision: {int(gone.sum())} pixeles en poligonos descartados salen de la mancha "
              f"({int(flood.sum())} pixeles quedan)")

    to6566 = Transformer.from_crs(4326, 6566, always_xy=True)
    to4326 = Transformer.from_crs(6566, 4326, always_xy=True)

    def dem_at(xs, ys):
        lon, lat = to4326.transform(xs, ys)
        cols = np.floor((np.asarray(lon) - t.c) / t.a).astype(int)
        rows = np.floor((np.asarray(lat) - t.f) / t.e).astype(int)
        ok = (rows >= 0) & (rows < h) & (cols >= 0) & (cols < w)
        z = np.full(len(cols), np.nan)
        z[ok] = dem[rows[ok], cols[ok]]
        z[z == dnod] = np.nan
        return z

    # Cauce principal: union de segmentos y parte mas larga
    shp = next(RIVER_DIR.glob("rio_linea_*.shp"))
    g = gpd.read_file(shp).to_crs(6566)
    line = linemerge(unary_union([shapely.force_2d(x) for x in g.geometry]))
    if line.geom_type == "MultiLineString":
        line = max(line.geoms, key=lambda p: p.length)

    def sample_line(ln):
        s = np.arange(0.0, ln.length, 25.0)
        p = shapely.line_interpolate_point(ln, s)
        return shapely.get_x(p), shapely.get_y(p)

    zl = dem_at(*sample_line(line))
    zz = zl[~np.isnan(zl)]
    k = max(1, len(zz) // 10)
    if np.median(zz[:k]) < np.median(zz[-k:]):
        line = shapely.reverse(line)
        print("Linea invertida: el inicio pasa a ser aguas arriba")
    L = line.length
    print(f"Cauce: {L/1000:.2f} km | elevacion inicio/fin (m): "
          f"{np.median(zz[:k]):.1f} / {np.median(zz[-k:]):.1f}")

    # Posicion a lo largo del rio y distancia lateral de cada pixel inundado
    rows, cols = np.where(flood)
    X, Y = to6566.transform(t.c + (cols + 0.5) * t.a, t.f + (rows + 0.5) * t.e)
    pts = shapely.points(X, Y)
    s_pix = shapely.line_locate_point(line, pts)
    dist = shapely.distance(pts, line)
    z_pix = dem[rows, cols]

    # Puentes: franja alrededor del eje (segmento entre los dos extremos)
    on_bridge = np.zeros(len(rows), dtype=bool)
    for (lon1, lat1), (lon2, lat2), half in BRIDGES:
        x1, y1 = to6566.transform(lon1, lat1)
        x2, y2 = to6566.transform(lon2, lat2)
        axis = LineString([(x1, y1), (x2, y2)])
        dl = shapely.distance(pts, axis)
        print(f"Puente ({x1:.0f},{y1:.0f})-({x2:.0f},{y2:.0f}): eje {axis.length:.0f} m, "
              f"franja +-{half:.0f} m, distancia del eje al cauce {axis.distance(line):.0f} m, "
              f"pixeles excluidos: {int((dl <= half).sum())}")
        on_bridge |= dl <= half

    within = dist <= DMAX
    near = within & ~on_bridge      # candidatos a recibir profundidad
    far = ~within & ~on_bridge      # demasiado lejos del cauce

    # Borde exterior de la mancha (sin huecos internos ni borde del raster)
    filled = ndi.binary_fill_holes(flood)
    bmask = filled & ~ndi.binary_erosion(filled, border_value=1) & flood
    use_b = bmask[rows, cols] & near

    nb = int(np.ceil(L / BIN))
    centers = (np.arange(nb) + 0.5) * BIN
    bi = np.minimum((s_pix // BIN).astype(int), nb - 1)
    counts = np.bincount(bi[use_b], minlength=nb)

    # Rango de tramos con borde suficiente (fuera de el, el nivel seria extrapolado)
    sup = counts >= MIN_BOUNDARY
    if sup.sum() < 2:
        raise SystemExit("Muy pocos tramos con borde suficiente.")
    first = int(np.argmax(sup))
    last = nb - 1 - int(np.argmax(sup[::-1]))
    in_range = (bi >= first) & (bi <= last)
    if ALLOW_EXTRAPOLATION:
        unsupported = np.zeros(len(rows), dtype=bool)
    else:
        unsupported = near & ~in_range
    near_final = near & ~unsupported

    weak = np.where(~sup)[0]
    print(f"\nTramos con menos de {MIN_BOUNDARY} px de borde: {len(weak)} de {nb} | "
          f"rango con soporte: {first * BIN / 1000:.2f}-{min((last + 1) * BIN, L) / 1000:.2f} km (de {L / 1000:.2f} km)")
    for i in weak:
        kind = "extrapolado" if (i < first or i > last) else "interpolado"
        print(f"  tramo {i}: {i * BIN / 1000:.2f}-{min((i + 1) * BIN, L) / 1000:.2f} km | px borde {counts[i]} | "
              f"px candidatos {int((near & (bi == i)).sum())} | {kind}")
    print(f"Pixeles sin soporte (fuera del rango, sin profundidad): {int(unsupported.sum())}")

    raw, levels = {}, {}
    for name, q in PCTS.items():
        lv = np.full(nb, np.nan)
        for i in range(nb):
            if counts[i] >= MIN_BOUNDARY:
                lv[i] = np.percentile(z_pix[use_b & (bi == i)], q)
        raw[name] = lv.copy()
        valid = ~np.isnan(lv)
        lv = np.interp(centers, centers[valid], lv[valid])
        wts = np.where(valid, counts, 1).astype(float)
        lv = IsotonicRegression(increasing=False).fit_transform(centers, lv, sample_weight=wts)
        levels[name] = ndi.uniform_filter1d(lv, size=SMOOTH_BINS, mode="nearest")

    pc = shapely.line_interpolate_point(line, centers)
    zc = dem_at(shapely.get_x(pc), shapely.get_y(pc))
    print("\nPerfil del nivel del agua (aguas arriba -> aguas abajo)")
    print("s_km | px_borde | p50 bruto | p50 final | p90 final | cota DEM en la linea")
    for i in range(0, nb, 8):
        print(f"{centers[i]/1000:5.1f} | {counts[i]:7d} | {raw['p50'][i]:9.2f} | "
              f"{levels['p50'][i]:9.2f} | {levels['p90'][i]:9.2f} | {zc[i]:9.2f}")

    lat = t.f + t.e * h / 2
    dy = abs(t.e) * 111320.0
    dx = abs(t.a) * 111320.0 * np.cos(np.radians(lat))
    print(f"\nPixeles inundados (tras la mascara): {len(rows)}")
    print(f"  con profundidad estimada: {int(near_final.sum())} ({100 * near_final.mean():.1f} %)")
    print(f"  excluidos por puente: {int(on_bridge.sum())} | demasiado lejos del cauce: {int(far.sum())} "
          f"| sin soporte de borde: {int(unsupported.sum())}")
    print("Pixeles de borde usados en el perfil:", int(use_b.sum()))

    prof_d = profile.copy()
    prof_d.update(dtype="float32", nodata=NODATA, count=1, compress="lzw")
    for name in PCTS:
        lev = np.interp(s_pix, centers, levels[name])
        depth = np.maximum(lev - z_pix, 0.0)
        arr = np.full((h, w), NODATA, dtype="float32")
        arr[rows[near_final], cols[near_final]] = depth[near_final].astype("float32")
        with rasterio.open(outs[name], "w", **prof_d) as dst:
            dst.write(arr, 1)
        dd = depth[near_final]
        print(f"{name}: media {dd.mean():.2f} | mediana {np.median(dd):.2f} | p95 {np.percentile(dd, 95):.2f} "
              f"| max {dd.max():.2f} | %>0 {100 * (dd > 0).mean():.1f} | volumen {dd.sum() * dx * dy / 1e6:.3f} Mm3")

    # Marcas: 1 = profundidad estimada, 2 = demasiado lejos del cauce, 3 = puente,
    #         4 = descartado en la revision manual (falso positivo),
    #         5 = sin soporte de borde (extrapolacion no permitida)
    flag = np.full((h, w), 255, dtype="uint8")
    flag[rows[near_final], cols[near_final]] = 1
    flag[rows[far], cols[far]] = 2
    flag[rows[on_bridge], cols[on_bridge]] = 3
    flag[rows[unsupported], cols[unsupported]] = 5
    if USE_REVIEW_MASK:
        flag[removed_rc] = 4
    prof_f = profile.copy()
    prof_f.update(compress="lzw")
    with rasterio.open(flag_tif, "w", **prof_f) as dst:
        dst.write(flag, 1)
    print("Guardado en:", DEPTH_DIR)
    print("Archivos:", [p.name for p in outs.values()], flag_tif.name)


if __name__ == "__main__":
    main()
