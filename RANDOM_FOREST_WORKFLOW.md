# Flujo de trabajo — Random Forest RF1–RF4

## 1. Objetivo

Este documento describe la reconstrucción mediante Python de cuatro modelos Random Forest utilizados para clasificar superficies inundadas y no inundadas tras el huracán María de septiembre de 2017, en el tramo bajo del río Grande de Añasco, Puerto Rico.

El propósito de la automatización es reproducir los procedimientos de clasificación desarrollados originalmente en ArcGIS Pro, evaluar los modelos mediante los puntos de validación originales y comparar espacialmente los resultados.

## 2. Datos utilizados

Los modelos emplean imágenes Sentinel-1 SAR en polarización VH correspondientes al 16 y 22 de septiembre de 2017, junto con variables auxiliares derivadas de información topográfica, hidrográfica y de cobertura del suelo.

Los rásteres multibanda originales de RF1–RF4 se encuentran en la carpeta `data`. Las muestras de entrenamiento y los 201 puntos de validación también proceden del proyecto original de ArcGIS Pro.

La reconstrucción utiliza una resolución espacial de 10 m y conserva la cuadrícula de los rásteres originales exportados.

## 3. Configuración de los modelos

Se reconstruyeron cuatro clasificadores con diferentes conjuntos de variables predictoras.

| Modelo | Variables |
|---|---|
| RF1 | VH preevento y VH postevento |
| RF2 | RF1 + diferencia VH |
| RF3 | RF2 + elevación y pendiente |
| RF4 | RF3 + distancia al río y cobertura del suelo |

El entrenamiento se realizó con `RandomForestClassifier` de scikit-learn, utilizando 100 árboles, una profundidad máxima de 30 y una selección de 1.000 muestras por clase, con semilla aleatoria 42.

Estos parámetros constituyen una aproximación a la configuración utilizada en ArcGIS Pro. No garantizan la reproducción exacta de su algoritmo ni de sus resultados.

## 4. Preparación de las muestras

Las muestras originales de entrenamiento se exportaron desde ArcGIS Pro y se prepararon mediante Python.

El procesamiento incluyó la reparación de geometrías, la rasterización de las clases y la extracción de los valores de las variables predictoras.

Los archivos de entrenamiento utilizan dos clases: `1 = No inundado` y `2 = Inundado`.

Los scripts principales de esta etapa incluyen `repair_rf_training_samples.py` y `rasterize_rf_training.py`.

## 5. Entrenamiento

Cada modelo se entrenó utilizando su correspondiente ráster multibanda original y las muestras seleccionadas.

Los principales scripts de entrenamiento son `train_rf1_arcgis_parameters_test.py`, `train_rf2_arcgis_parameters_test.py`, `train_rf3_arcgis_parameters_test.py` y `train_rf4_arcgis_parameters_test.py`.

Los modelos entrenados se almacenan en formato `.joblib` dentro de la carpeta `outputs`.

## 6. Validación

Los cuatro modelos se evaluaron mediante 201 puntos originales de validación, utilizando las referencias de inundación y no inundación.

La evaluación incluyó el cálculo de matrices de confusión, exactitud global, índice Kappa y errores de clasificación.

| Modelo | Exactitud global | Kappa |
|---|---:|---:|
| RF1 | 91,04 % | 0,8213 |
| RF2 | 95,02 % | 0,9006 |
| RF3 | 96,02 % | 0,9204 |
| RF4 | 96,02 % | 0,9204 |

Estos resultados corresponden a las reconstrucciones realizadas mediante Python.

## 7. Generación de mapas

Los mapas completos se generaron mediante el script `predict_rf_all_arcgis_parameters.py`, que aplica los modelos entrenados sobre los rásteres multibanda originales.

Los archivos principales son:

`outputs/RF1_ArcGIS_Parameters_Classification.tif`

`outputs/RF2_ArcGIS_Parameters_Classification.tif`

`outputs/RF3_ArcGIS_Parameters_Classification.tif`

`outputs/RF4_ArcGIS_Parameters_Classification.tif`

En estos mapas, el valor 1 representa la clase no inundada, el valor 2 corresponde a la clase inundada y el valor 0 identifica píxeles sin clasificación.

## 8. Resultados espaciales

Las superficies clasificadas como inundadas disminuyeron progresivamente desde RF1 hasta RF4.

| Modelo | Superficie inundada |
|---|---:|
| RF1 | 7,5871 km² |
| RF2 | 6,1093 km² |
| RF3 | 5,2600 km² |
| RF4 | 5,0373 km² |

Estos valores representan superficies clasificadas por los modelos Random Forest y no deben confundirse con la delimitación potencial de inundación obtenida mediante el procedimiento SAR.

## 9. Comparación con ArcGIS Pro

Los mapas reconstruidos se compararon con las clasificaciones originales de ArcGIS Pro sobre una cuadrícula espacial coincidente.

La comparación utilizó el índice de intersección sobre unión (IoU) para medir la superposición de las superficies identificadas como inundadas.

| Modelo | IoU |
|---|---:|
| RF1 | 0,7746 |
| RF2 | 0,7991 |
| RF3 | 0,8535 |
| RF4 | 0,5804 |

RF3 presentó la mayor coincidencia espacial. RF4 mostró discrepancias más importantes respecto a su clasificación original, sin que se haya establecido una causa definitiva.

## 10. Ejecución

Los scripts deben ejecutarse desde la carpeta principal `TFM_Automation`, manteniendo las rutas originales.

Para generar nuevamente los cuatro mapas a partir de los modelos ya entrenados, se utiliza:

```powershell
python .\scripts\predict_rf_all_arcgis_parameters.py
```

También se ha creado el archivo `run_random_forest.bat`, que permite ejecutar este procedimiento desde Windows utilizando el entorno virtual del proyecto.

Ambos métodos vuelven a generar los GeoTIFF de clasificación y pueden sobrescribir los archivos existentes. No deben ejecutarse si únicamente se desea consultar los resultados actuales.

## 11. Limitaciones

La reconstrucción utiliza scikit-learn y reproduce determinados parámetros de entrenamiento de ArcGIS Pro, pero ambas implementaciones pueden generar resultados diferentes.

La coincidencia entre las métricas obtenidas con los puntos de validación no implica una reproducción espacial exacta.

Por otra parte, las superficies clasificadas como inundadas requieren interpretación y contraste con información independiente antes de considerarse una delimitación confirmada de la inundación.

## 12. Organización de los scripts

Los scripts originales permanecen directamente en la carpeta `scripts`, conservando las rutas utilizadas durante el desarrollo del proyecto.

La carpeta `scripts/random_forest` contiene copias organizadas de los programas empleados para preparar las muestras de entrenamiento, procesar las variables predictoras, entrenar los modelos RF1–RF4, generar los mapas de clasificación y evaluar los resultados.

Estas copias tienen una finalidad organizativa y documental. Para ejecutar los procedimientos automatizados deben utilizarse los scripts originales, situados directamente en `scripts`, ya que las rutas internas de las copias no se han adaptado a su nueva ubicación.

La automatización de Random Forest comprende exclusivamente los cuatro modelos reconstruidos a partir del TFM original, manteniendo sus respectivas configuraciones, variables predictoras y resultados de validación.