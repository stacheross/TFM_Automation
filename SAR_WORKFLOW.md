# Flujo de trabajo — Análisis Sentinel-1 SAR

## 1. Objetivo

Este documento describe el procedimiento de reconstrucción del análisis multitemporal Sentinel-1 SAR utilizado para identificar superficies potencialmente inundadas tras el huracán María en el tramo bajo del río Grande de Añasco, Puerto Rico.

El procesamiento se desarrolló mediante Python, tomando como referencia el procedimiento original del TFM y utilizando herramientas de procesamiento geoespacial y teledetección.

## 2. Datos de entrada

El análisis utiliza imágenes Sentinel-1 SAR correspondientes al 16 de septiembre de 2017, como fecha preevento, y al 22 de septiembre de 2017, como fecha postevento. Se emplea principalmente la polarización VH.

También se utiliza información topográfica procedente del Modelo Digital de Elevación del USGS, junto con otras capas auxiliares para evaluar y depurar las superficies potencialmente inundadas.

## 3. Preparación y procesamiento SAR

La preparación comprende las operaciones necesarias para obtener imágenes de retrodispersión comparables entre las dos fechas.

Los scripts del proyecto incluyen procedimientos para preparar los productos Sentinel-1, aplicar operaciones de preprocesamiento, generar imágenes de retrodispersión y alinear espacialmente los rásteres resultantes.

Entre los programas asociados a estas operaciones se encuentran `preprocess_s1.py`, `apply_orbit.py`, `align_s1_rasters.py` y `calculate_vh_change.py`.

Estos archivos representan componentes del procesamiento y no deben interpretarse como una secuencia de ejecución completa sin comprobar previamente sus entradas y dependencias.

## 4. Detección multitemporal de cambios

El análisis utiliza la diferencia de retrodispersión VH entre las imágenes posteriores y anteriores al huracán:

**ΔVH = VH postevento − VH preevento**

La disminución de retrodispersión permite identificar posibles cambios asociados con la presencia de agua superficial.

Se evaluaron diferentes umbrales de disminución, incluyendo **ΔVH ≤ −3 dB**, junto con criterios topográficos para limitar detecciones potencialmente incorrectas.

## 5. Aplicación de criterios topográficos

El procesamiento incorpora información de elevación y pendiente derivada del DEM del USGS. Estas variables se utilizan para examinar la distribución topográfica de las detecciones y aplicar restricciones espaciales.

Los scripts desarrollados incluyen procedimientos para preparar el DEM, calcular la pendiente, ajustar su resolución cuando corresponde y evaluar diferentes criterios de pendiente.

La resolución y el tratamiento del DEM dependen de la etapa analítica. En el procedimiento SAR original del TFM se utilizó información topográfica de 0,5 m, mientras que las variables de Random Forest se estandarizaron a 10 m.

## 6. Delimitación de superficies potencialmente inundadas

La delimitación combina los cambios de retrodispersión con criterios topográficos y procedimientos de filtrado espacial.

Durante la reconstrucción se generaron diferentes escenarios de umbralización, máscaras de inundación y resultados intermedios que permiten examinar la sensibilidad del procedimiento a distintos criterios.

El resultado candidato reconstruido se encuentra almacenado en:

`outputs/Flood_Final_Candidate_Reconstructed.tif`

## 7. Resultados

La reconstrucción automatizada generó una delimitación candidata de aproximadamente **2,7791 km²** de superficie potencialmente inundada.

Este valor se diferencia del resultado revisado del TFM original, que fue de aproximadamente **2,31 km²**.

La diferencia debe interpretarse considerando las particularidades del procesamiento automatizado y las operaciones de revisión espacial aplicadas durante el estudio original.

## 8. Ejecución y reproducibilidad

Los scripts originales se conservan directamente en la carpeta `scripts` del proyecto. Las copias situadas en `scripts/sar_analysis` tienen una finalidad organizativa y documental.

Actualmente no se dispone de un único archivo de ejecución que reproduzca automáticamente todas las etapas SAR desde los productos originales.

Antes de automatizar la secuencia completa sería necesario documentar las dependencias entre scripts, los datos requeridos en cada etapa y los archivos generados.

Por este motivo, no se recomienda ejecutar indiscriminadamente todos los programas SAR ni modificar los resultados existentes sin definir previamente un flujo de ejecución controlado.