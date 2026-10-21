# Estimación de profundidad de inundación (María, 20–22 sep 2017)

Estado: **estimación experimental, sin validar.** Rama local: `depth-estimation`.

## Qué es y qué no es
- El SAR (Sentinel-1) solo da **extensión** inundada. La profundidad se deriva
  combinando esa extensión con el DEM de 0,5 m.
- Extensión base: reconstrucción SAR en Python
  (`outputs/Flood_Final_Candidate_Reconstructed.tif`, ≈ 2,78 km²), distinta del
  resultado revisado original del TFM (≈ 2,31 km²). No se mezclan.
- **No es un resultado validado ni un modelo hidráulico.** No sustituye a HEC-RAS.

## Método (perfil del río)
Script: `scripts/estimate_flood_depth_river_profile.py`

1. Se cargan la extensión de inundación y el DEM (malla 10 m de Sentinel-1,
   `outputs/DEM_AOI_S1grid.tif`).
2. Se descartan los píxeles dentro de los polígonos descartados a mano por
   falsos positivos (`Flood_Removed_Manual_Review`, capa de
   `outputs/Flood_Reconstruction_Review.gpkg`).
3. Se une la línea del río (`data/hydro/rio_linea_añs.shp`), orientada aguas abajo
   según el DEM, y se calcula la posición a lo largo del río de cada píxel.
4. Se excluye una franja de ±40 m alrededor del puente (7 píxeles).
5. Los píxeles a más de 500 m del cauce quedan sin profundidad.
6. En el borde exterior de la mancha inundada se toma la cota del DEM; por
   tramos de 250 m (mínimo 10 píxeles de borde) se calcula un percentil (p50 y
   p90) como nivel del agua.
7. El nivel se interpola, se fuerza a no aumentar aguas abajo (regresión
   isotónica) y se suaviza ligeramente.
8. Profundidad = max(nivel − DEM, 0).

Parámetros: DMAX = 500 m, BIN = 250 m, MIN_BOUNDARY = 10, SMOOTH_BINS = 3,
sin extrapolación.

## Resultados (máscara revisada, versión `_v2`)
Salidas en `outputs/depth_prototype/`:
`Depth_RiverProfile_Reviewed_10m_{p50,p90,Flag}_v2.tif`

Píxeles de inundación: 26.057. Con profundidad: 22.758 (87,3 %). Sin
profundidad por estar lejos del cauce: 3.292 (≈ 0,31 km²). Puente: 7.

| | p50 | p90 |
|---|---|---|
| Media (m) | 0,45 | 1,21 |
| Mediana (m) | 0 | 0,95 |
| p95 (m) | 2,11 | 3,30 |
| Máx. (m) | 5,20 | 6,94 |
| % píxeles > 0 | 48,7 | 89,4 |
| Volumen (Mm³) | 0,975 | 2,614 |

Códigos del ráster `Flag`: 1 con profundidad; 2 lejos del río; 3 franja del
puente; 4 descartado por revisión manual; 5 sin soporte (no ocurrió).

## Limitaciones (obligatorio citarlas)
- **Sin validación.** El informe SIR 2022-5040 del USGS no incluye marcas de agua
  ni mediciones indirectas en la cuenca del Río Grande de Añasco. La estación
  50144000 está ≈ 3–4 km aguas arriba de la zona de estudio (18,2822° N,
  −67,0506° W); da contexto del evento (pico 35,84–35,85 ft, 185.000 ft³/s,
  20/09/2017), no valida profundidades. Las 181 marcas de agua de Byrne (2019)
  están en el USGS Flood Event Viewer y no se han consultado.
- **El rango p50–p90 no es un intervalo de confianza.** El percentil es una
  suposición que domina la incertidumbre. Los parámetros técnicos varían poco
  (p95 ≈ 0,2–0,3 m).
- El DEM suele registrar la superficie del agua en cauces; no se modelan
  estructuras hidráulicas.
- El nivel corresponde a la imagen del 22 de septiembre, no al pico del 20.
- DEM: producto "2018 USGS Lidar DEM: Post Hurricane Maria - Puerto Rico",
  horizontal NAD83 (2011) Puerto Rico y Islas Vírgenes (EPSG:6566), vertical
  PRVD02 (GEOID12B), en metros, según la descripción del producto. Se asume que
  `DEM_AOI_05m.tif` es un recorte sin cambio de datum; no se ha verificado
  contra el ráster. Al ser posterior a María incluye los cambios del cauce
  causados por el huracán, pero la captura (2018) es posterior a la imagen
  del 22 de septiembre de 2017, y el cauce pudo cambiar entre ambas fechas.
- ≈ 0,31 km² de inundación conservada lejos del cauce no tiene profundidad.
- No presentar el proyecto como reproducible desde cero ni esto como resultado
  final.

## Scripts de diagnóstico (`tests/`, solo lectura)
`inspect_depth_inputs.py`, `check_flood_vs_dem.py`, `check_s1grid_alignment.py`,
`diagnose_depth_components.py`, `sensitivity_depth_variants.py`,
`sweep_depth_parameters.py`, `inspect_river_line.py`,
`inspect_river_features.py`, `inspect_river_topology.py`, `flags_vs_review.py`,
`flags_vs_removed_polygons.py`, `sensitivity_river_profile.py`.
Los scripts `inspect_river_distance.py`, `inspect_tributaries.py` y
`flags_vs_landcover.py` no se usaron o no se ejecutaron.
`scripts/estimate_flood_depth_fwdet.py` es el prototipo inicial (nivel del borde
más cercano), sensible a parámetros, conservado solo como referencia.

## Comprobación de coherencia con el medidor 50144000 (no es validación)
- Medidor: Río Grande de Añasco cerca de San Sebastián, ≈ 3,6 km aguas arriba
  del borde este del ráster. Lat 18°17'03" N, long 67°03'03,46" O (NAD27).
- Datum del medidor: 105,45 ft (32,1 m) sobre PRVD02, según la ficha del USGS
  (revisada en agosto de 2025; informes anteriores pudieron usar otro datum).
- Pico del 20/09/2017: 35,85 ft de altura de agua, es decir 141,3 ft sobre
  PRVD02 (≈ 43,07 m). Caudal de pico 185.000 ft³/s, estimado por modelo
  hidráulico (SIR 2022-5040).
- Nivel del agua que implica el mapa (DEM + profundidad) en el borde este:
  ≈ 16 m (p50) y ≈ 18 m (p90), máximos 16,4 y 18,6 m. Es menor que el nivel
  del medidor aguas arriba, como cabe esperar; no confirma ni refuta el valor.
- Caudal diario del 22 de septiembre (día de la imagen): 9.020 ft³/s, ≈ 5 % del
  pico (media diaria, estimada por el USGS). El mapa representa la bajada.
- Imagen del mapa: escena Sentinel-1B `S1B_IW_GRDH_1SDV_20170922T223532_
  20170922T223557_007511_00D430_D309`, del 22/09/2017 a las 22:35 UTC
  (18:35 hora local, AST). La escena de referencia anterior al evento es
  `S1A_..._20170916T223625_...` (16/09/2017, 22:36 UTC).
- Caudal diario en el medidor (media, estimada por el USGS): 9.020 ft³/s el
  22/09 y 4.660 ft³/s el 23/09. El río seguía bajando cuando se tomó la imagen.
- No se encontraron lecturas instantáneas (15 min) de altura del medidor para
  las 18:35 del 22/09, así que no se comparó el nivel del mapa con el del
  medidor en el instante de la imagen. Queda como limitación.

## Visor web
Visor publicado como artifact privado en claude.ai (mapa, hidrograma de
septiembre de 2017 y comparación de septiembres desde 1963). Los datos van
incrustados en la página: no se actualizan solos si se regeneran los rásteres.
