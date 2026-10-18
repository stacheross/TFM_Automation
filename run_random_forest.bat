
@echo off
cd /d "%~dp0"

echo ==============================================
echo TFM AUTOMATION - RANDOM FOREST RF1-RF4
echo ==============================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: No se encuentra el entorno virtual .venv
    pause
    exit /b 1
)

".venv\Scripts\python.exe" "scripts\predict_rf_all_arcgis_parameters.py"

if errorlevel 1 (
    echo.
    echo ERROR: No se pudieron generar los mapas.
    pause
    exit /b 1
)

echo.
echo Proceso completado.
echo Los resultados se encuentran en outputs.
pause
