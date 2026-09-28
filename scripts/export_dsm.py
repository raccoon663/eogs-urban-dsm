"""Export the raw and officially registered EOGS DSMs with a verified map grid."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_origin


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("model_dir", type=Path)
    parser.add_argument("--scene", default="JAX_004")
    parser.add_argument("--iteration", type=int, default=5000)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--epsg", type=int, default=32617)
    parser.add_argument("--output", type=Path, default=Path("outputs/dsm/JAX_004_aligned.tif"))
    parser.add_argument("--raw-output", type=Path, default=Path("outputs/dsm/JAX_004_predicted.iio"))
    args = parser.parse_args()

    rendered = args.model_dir / "test_opNone" / f"ours_{args.iteration}" / "dsm"
    candidates = sorted(rendered.glob("*.iio"))
    if not candidates:
        raise FileNotFoundError(f"No rendered DSMs in {rendered}")
    raw = candidates[-1]
    registered = args.model_dir / f"{args.scene}_rdsm.tif"
    if not registered.exists():
        raise FileNotFoundError(f"Official registered DSM not found: {registered}")

    easting, northing, pixels, gsd = np.loadtxt(args.metadata)
    pixels = int(pixels)
    with rasterio.open(registered) as source:
        array = source.read(1).astype(np.float32)
    if array.shape != (pixels, pixels):
        raise ValueError(f"Registered DSM shape {array.shape} != metadata grid {(pixels, pixels)}")

    profile = {
        "driver": "GTiff",
        "height": pixels,
        "width": pixels,
        "count": 1,
        "dtype": "float32",
        "crs": CRS.from_epsg(args.epsg),
        "transform": from_origin(easting, northing + pixels * gsd, gsd, gsd),
        "nodata": np.nan,
        "compress": "deflate",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(args.output, "w", **profile) as destination:
        destination.write(array, 1)
    args.raw_output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(raw, args.raw_output)
    print(f"Raw DSM: {args.raw_output}")
    print(f"Registered GeoTIFF: {args.output}")


if __name__ == "__main__":
    main()
