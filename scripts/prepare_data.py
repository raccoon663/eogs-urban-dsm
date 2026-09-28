"""Download the official EOGS release and extract one scene only."""

from __future__ import annotations

import argparse
import tempfile
import zipfile
from pathlib import Path

import requests


DATA_URL = "https://github.com/mezzelfo/EOGS/releases/download/dataset_v01/data.zip"


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with destination.open("wb") as output:
            for chunk in response.iter_content(1024**2):
                if chunk:
                    output.write(chunk)


def extract_scene(archive: Path, data_dir: Path, scene: str) -> int:
    prefixes = (f"images/{scene}/", f"rpcs/{scene}/", f"truth/{scene}/")
    with zipfile.ZipFile(archive) as source:
        members = [name for name in source.namelist() if name.startswith(prefixes)]
        if not members:
            raise ValueError(f"Scene {scene!r} is not present in {archive}")
        source.extractall(data_dir, members)
    return len(members)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", default="JAX_004")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--keep-archive", action="store_true")
    args = parser.parse_args()

    temporary = args.archive is None
    archive = args.archive or Path(tempfile.gettempdir()) / "eogs-data.zip"
    if not archive.exists():
        download(DATA_URL, archive)
    count = extract_scene(archive, args.data_dir, args.scene)
    print(f"Extracted {count} entries for {args.scene} into {args.data_dir}")
    if temporary and not args.keep_archive:
        archive.unlink()


if __name__ == "__main__":
    main()
