"""Compute DSM metrics only after strict grid and CRS validation."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import rasterio


CLASSES = {"ground": 2, "vegetation": 5, "building": 6, "water": 9, "bridge": 17}


def metrics(error: np.ndarray) -> dict[str, float | int]:
    absolute = np.abs(error)
    return {
        "mae_m": float(np.mean(absolute)),
        "rmse_m": float(np.sqrt(np.mean(error**2))),
        "median_ae_m": float(np.median(absolute)),
        "p90_ae_m": float(np.percentile(absolute, 90)),
        "bias_m": float(np.mean(error)),
        "valid_pixels": int(error.size),
    }


def same_grid(left: rasterio.DatasetReader, right: rasterio.DatasetReader) -> None:
    if left.shape != right.shape:
        raise ValueError(f"Shape mismatch: {left.shape} vs {right.shape}")
    if left.crs != right.crs:
        raise ValueError(f"CRS mismatch: {left.crs} vs {right.crs}")
    if not left.transform.almost_equals(right.transform):
        raise ValueError(f"Transform mismatch: {left.transform} vs {right.transform}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("predicted", type=Path)
    parser.add_argument("reference", type=Path)
    parser.add_argument("--labels", type=Path)
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--error-map", type=Path, required=True)
    args = parser.parse_args()

    with rasterio.open(args.predicted) as predicted_ds, rasterio.open(args.reference) as reference_ds:
        same_grid(predicted_ds, reference_ds)
        predicted = predicted_ds.read(1).astype(np.float32)
        reference = reference_ds.read(1).astype(np.float32)
        profile = predicted_ds.profile.copy()
    valid = np.isfinite(predicted) & np.isfinite(reference)
    if not valid.any():
        raise ValueError("No finite overlapping pixels")
    error_map = np.full(predicted.shape, np.nan, dtype=np.float32)
    error_map[valid] = predicted[valid] - reference[valid]
    result = {"overall": metrics(error_map[valid])}
    result["overall"]["valid_percent"] = float(100 * valid.sum() / valid.size)

    if args.labels:
        with rasterio.open(args.labels) as label_ds, rasterio.open(args.predicted) as predicted_ds:
            same_grid(predicted_ds, label_ds)
            labels = label_ds.read(1)
        result["surface_types"] = {}
        for name, code in CLASSES.items():
            mask = valid & (labels == code)
            if mask.any():
                result["surface_types"][name] = metrics(error_map[mask])

    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    rows = [("overall", result["overall"])] + list(result.get("surface_types", {}).items())
    with args.csv.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        keys = ["mae_m", "rmse_m", "median_ae_m", "p90_ae_m", "bias_m", "valid_pixels"]
        writer.writerow(["surface_type", *keys])
        for name, values in rows:
            writer.writerow([name] + [values[key] for key in keys])

    args.error_map.parent.mkdir(parents=True, exist_ok=True)
    profile.update(dtype="float32", count=1, nodata=np.nan, compress="deflate")
    with rasterio.open(args.error_map, "w", **profile) as destination:
        destination.write(error_map, 1)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
