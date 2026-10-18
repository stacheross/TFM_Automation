
from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling

ROOT = Path(__file__).resolve().parent.parent

REFERENCE = ROOT / "outputs" / "RF_Training_10m.tif"

INPUTS = {
    "pre": ROOT / "outputs" / "S1_20170916_VH_dB.tif",
    "post": ROOT / "outputs" / "S1_20170922_VH_dB_aligned.tif",
}

OUTPUTS = {
    "pre": ROOT / "outputs" / "RF_VH_Pre_10m.tif",
    "post": ROOT / "outputs" / "RF_VH_Post_10m.tif",
    "change": ROOT / "outputs" / "RF_VH_Change_10m.tif",
}

NODATA = -9999.0

with rasterio.open(REFERENCE) as ref:
    profile = ref.profile.copy()
    profile.update(
        dtype="float32",
        count=1,
        nodata=NODATA,
        compress="lzw"
    )

    aligned = {}

    for key, input_path in INPUTS.items():

        destination = np.full(
            ref.shape,
            NODATA,
            dtype=np.float32
        )

        with rasterio.open(input_path) as src:
            reproject(
                source=rasterio.band(src, 1),
                destination=destination,
                src_transform=src.transform,
                src_crs=src.crs,
                src_nodata=src.nodata,
                dst_transform=ref.transform,
                dst_crs=ref.crs,
                dst_nodata=NODATA,
                resampling=Resampling.bilinear
            )

        valid = np.isfinite(destination) & (destination != NODATA)
        destination[~valid] = NODATA

        aligned[key] = destination

        with rasterio.open(OUTPUTS[key], "w", **profile) as dst:
            dst.write(destination, 1)

    # Calcular cambio VH: postevento menos preevento
    pre = aligned["pre"]
    post = aligned["post"]

    valid = (
        (pre != NODATA)
        & (post != NODATA)
        & np.isfinite(pre)
        & np.isfinite(post)
    )

    change = np.full(ref.shape, NODATA, dtype=np.float32)
    change[valid] = post[valid] - pre[valid]

    with rasterio.open(OUTPUTS["change"], "w", **profile) as dst:
        dst.write(change, 1)

    print("\nVARIABLES SAR PARA RANDOM FOREST")
    print("-" * 45)

    for key, array in [
        ("VH preevento", pre),
        ("VH postevento", post),
        ("Cambio VH", change)
    ]:
        mask = np.isfinite(array) & (array != NODATA)

        print(f"\n{key}")
        print("Píxeles válidos:", np.count_nonzero(mask))

        if np.any(mask):
            print("Mínimo:", float(array[mask].min()))
            print("Máximo:", float(array[mask].max()))

    training = ref.read(1)

    valid_training = (training > 0) & valid

    print("\nMuestras con VH pre y post válidos:",
          np.count_nonzero(valid_training))

    print("Muestras sin datos SAR:",
          np.count_nonzero(training > 0) -
          np.count_nonzero(valid_training))
