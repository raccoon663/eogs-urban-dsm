"""Validate metrics, links, paths, and public-release hygiene."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROHIBITED_DIRS = {".git", "__pycache__", "wandb", "checkpoints", ".deps", "output"}
PROHIBITED_SUFFIXES = {".tif", ".tiff", ".iio", ".las", ".laz", ".ckpt", ".pth", ".pt", ".zip"}


def close(a: str | float, b: float, tolerance: float = 1e-9) -> bool:
    return abs(float(a) - float(b)) <= tolerance


def main() -> None:
    failures: list[str] = []
    common = json.loads((ROOT / "results/provenance/common_mask_metrics.json").read_text())
    runs = {str(run["views"]): run for run in common["runs"]}

    with (ROOT / "results/metrics.csv").open(newline="") as stream:
        for row in csv.DictReader(stream):
            source = runs[row["train_views"]]
            for csv_key, json_key in (("mae_m", "mae_m"), ("rmse_m", "rmse_m"),
                                      ("median_ae_m", "median_ae_m"), ("p90_ae_m", "p90_ae_m")):
                if not close(row[csv_key], source[json_key]):
                    failures.append(f"metrics mismatch: {row['configuration']} {csv_key}")

    with (ROOT / "results/surface_metrics.csv").open(newline="") as stream:
        for row in csv.DictReader(stream):
            source = runs[row["train_views"]]["surfaces"][row["surface"]]
            for key in ("mae_m", "rmse_m", "median_ae_m", "p90_ae_m"):
                if not close(row[key], source[key]):
                    failures.append(f"surface mismatch: {row['configuration']} {row['surface']} {key}")

    readme = (ROOT / "README.md").read_text()
    for target in re.findall(r"!?(?:\[[^]]*\])\(([^)]+)\)", readme):
        if "://" not in target and not (ROOT / target).exists():
            failures.append(f"broken README link: {target}")

    public_files = [path for path in ROOT.rglob("*") if path.is_file() and ".git" not in path.parts]
    for path in public_files:
        rel = path.relative_to(ROOT)
        if any(part in PROHIBITED_DIRS for part in rel.parts):
            failures.append(f"prohibited directory: {rel.as_posix()}")
        if path.suffix.lower() in PROHIBITED_SUFFIXES:
            failures.append(f"prohibited file type: {rel.as_posix()}")
        if path.stat().st_size > 10 * 1024 * 1024:
            failures.append(f"file exceeds 10 MiB: {rel.as_posix()}")

    absolute_pattern = re.compile(r"(?:/opt/|/mnt/|(?<![A-Za-z])[A-Za-z]:[\\/]|/Users/)")
    for path in (ROOT / "scripts").rglob("*"):
        if path.is_file() and path.resolve() != Path(__file__).resolve() and absolute_pattern.search(path.read_text(errors="ignore")):
            failures.append(f"absolute machine path in script: {path.relative_to(ROOT).as_posix()}")

    if failures:
        raise SystemExit("Release validation failed:\n- " + "\n- ".join(sorted(set(failures))))

    size = sum(path.stat().st_size for path in public_files)
    print(json.dumps({
        "status": "passed",
        "files_scanned": len(public_files),
        "payload_bytes_excluding_git": size,
        "common_valid_pixels": common["common_valid_pixels"],
        "restricted_or_large_files": 0,
        "broken_readme_links": 0,
        "absolute_machine_paths_in_scripts": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
