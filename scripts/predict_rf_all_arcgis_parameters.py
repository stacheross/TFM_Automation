
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
import joblib

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUTPUTS = ROOT / "outputs"

MODELS = {
    "RF1": {
        "raster": DATA / "RF1_SAR_PrePost_Original.tif",
        "model": OUTPUTS / "RF1_ArcGIS_Parameters_Test.joblib",
        "features": ["VH_Pre", "VH_Post"]
    },
    "RF2": {
        "raster": DATA / "RF2_SAR_Cambio_Original.tif",
        "model": OUTPUTS / "RF2_ArcGIS_Parameters_Test.joblib",
        "features": ["VH_Pre", "VH_Post", "VH_Change"]
    },
    "RF3": {
        "raster": DATA / "RF3_SAR_Topografia_Original.tif",
        "model": OUTPUTS / "RF3_ArcGIS_Parameters_Test.joblib",
        "features": [
            "VH_Pre", "VH_Post", "VH_Change",
            "Elevacion", "Pendiente"
        ]
    },
    "RF4": {
        "raster": DATA / "RF4_Todas_Variables_Original.tif",
        "model": OUTPUTS / "RF4_ArcGIS_Parameters_Test.joblib",
        "features": [
            "VH_Pre", "VH_Post", "VH_Change",
            "Elevacion", "Pendiente",
            "Distancia_Rio", "Cobertura_Suelo"
        ]
    }
}

print("\nMAPAS RANDOM FOREST RF1-RF4")
print("-" * 55)

for name, config in MODELS.items():

    rf = joblib.load(config["model"])

    with rasterio.open(config["raster"]) as src:

        if src.count != len(config["features"]):
            raise ValueError(
                f"{name}: numero de bandas incorrecto."
            )

        bands = src.read()

        # Excluir el fondo comun de las bandas SAR
        valid = (
            np.all(np.isfinite(bands), axis=0)
            & ~np.all(bands[:, :, :] [:3] == 0, axis=0)
        )

        classification = np.zeros(
            src.shape,
            dtype=np.uint8
        )

        X = pd.DataFrame({
            feature: bands[i][valid]
            for i, feature in enumerate(config["features"])
        })

        classification[valid] = rf.predict(X).astype(np.uint8)

        profile = src.profile.copy()
        profile.update(
            driver="GTiff",
            dtype="uint8",
            count=1,
            nodata=0,
            compress="lzw"
        )

        output = OUTPUTS / f"{name}_ArcGIS_Parameters_Classification.tif"

        with rasterio.open(output, "w", **profile) as dst:
            dst.write(classification, 1)

    flooded = np.count_nonzero(classification == 2)
    not_flooded = np.count_nonzero(classification == 1)
    nodata = np.count_nonzero(classification == 0)

    print(f"\n{name}")
    print("Archivo:", output)
    print("No inundado:", not_flooded)
    print("Inundado:", flooded)
    print("Sin datos:", nodata)
    print(
        "Superficie clasificada como inundada:",
        round(flooded * 0.0001, 4),
        "km2"
    )
