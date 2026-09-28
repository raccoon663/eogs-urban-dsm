"""Resample a predicted DSM onto the official DFC2019 reference grid."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject


def reference_grid(reference: Path, metadata: Path, epsg: int):
    easting, northing, pixels, gsd = np.loadtxt(metadata)
    with rasterio.open(reference) as dataset:
        shape = (dataset.height, dataset.width)
    if shape != (int(pixels), int(pixels)):
        raise ValueError(f"Reference shape {shape} disagrees with {metadata}: {int(pixels)} square")
    transform = from_origin(easting, northing + pixels * gsd, gsd, gsd)
    return shape, transform, CRS.from_epsg(epsg)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("predicted", type=Path)
    parser.add_argument("reference", type=Path)
    parser.add_argument("metadata", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--reference-output", type=Path)
    parser.add_argument("--labels", type=Path)
    parser.add_argument("--labels-output", type=Path)
    parser.add_argument("--epsg", type=int, default=32617, help="JAX is UTM zone 17N")
    parser.add_argument("--vertical-median-shift", action="store_true")
    args = parser.parse_args()

    shape, dst_transform, dst_crs = reference_grid(args.reference, args.metadata, args.epsg)
    aligned = np.full(shape, np.nan, dtype=np.float32)
    with rasterio.open(args.predicted) as source:
        if source.crs is None:
            raise ValueError("Predicted DSM has no CRS; alignment cannot be verified")
        reproject(
            source=rasterio.band(source, 1),
            destination=aligned,
            src_transform=source.transform,
            src_crs=source.crs,
            src_nodata=source.nodata,
            dst_transform=dst_transform,
            dst_crs=dst_crs,
            dst_nodata=np.nan,
            resampling=Resampling.bilinear,
        )

    vertical_shift = 0.0
    if args.vertical_median_shift:
        with rasterio.open(args.reference) as reference_ds:
            reference = reference_ds.read(1).astype(np.float32)
        valid = np.isfinite(aligned) & np.isfinite(reference)
        if not valid.any():
            raise ValueError("No valid overlap after horizontal alignment")
        vertical_shift = float(np.median(reference[valid] - aligned[valid]))
        aligned[valid] += vertical_shift

    args.output.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver": "GTiff",
        "height": shape[0],
        "width": shape[1],
        "count": 1,
        "dtype": "float32",
        "crs": dst_crs,
        "transform": dst_transform,
        "nodata": np.nan,
        "compress": "deflate",
    }
    with rasterio.open(args.output, "w", **profile) as destination:
        destination.write(aligned, 1)

    if args.reference_output:
        with rasterio.open(args.reference) as source:
            reference = source.read(1).astype(np.float32)
        args.reference_output.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(args.reference_output, "w", **profile) as destination:
            destination.write(reference, 1)

    if bool(args.labels) != bool(args.labels_output):
        raise ValueError("--labels and --labels-output must be supplied together")
    if args.labels:
        with rasterio.open(args.labels) as source:
            labels = source.read(1)
        if labels.shape != shape:
            raise ValueError(f"Label shape {labels.shape} does not match reference {shape}")
        label_profile = profile | {"dtype": str(labels.dtype), "nodata": None}
        args.labels_output.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(args.labels_output, "w", **label_profile) as destination:
            destination.write(labels, 1)
    print(f"Wrote {args.output}; vertical_shift_m={vertical_shift:.6f}")


if __name__ == "__main__":
    main()
