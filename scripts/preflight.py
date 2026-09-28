"""Check the host before compiling or running EOGS."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys


def command_output(command: list[str]) -> str | None:
    try:
        return subprocess.run(command, check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def main() -> None:
    packages = ["torch", "rasterio", "rpcm", "pyproj", "utm", "plyfile"]
    report = {
        "python": sys.version,
        "executables": {name: shutil.which(name) for name in ["nvidia-smi", "nvcc", "cl", "gcc", "g++"]},
        "packages": {name: importlib.util.find_spec(name) is not None for name in packages},
        "nvidia_smi": command_output(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"]),
    }
    if report["packages"]["torch"]:
        import torch

        report["torch"] = {
            "version": torch.__version__,
            "cuda_runtime": torch.version.cuda,
            "cuda_available": torch.cuda.is_available(),
            "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
