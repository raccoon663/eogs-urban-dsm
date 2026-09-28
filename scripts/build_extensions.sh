#!/usr/bin/env bash
set -euo pipefail

eogs_root="${EOGS_ROOT:?Set EOGS_ROOT to the exact EOGS checkout}"
if ! command -v gcc-11 >/dev/null || ! command -v g++-11 >/dev/null; then
  echo "Install GCC 11 first: sudo apt-get install gcc-11 g++-11" >&2
  exit 1
fi

export CUDA_HOME="${CONDA_PREFIX:?Activate the eogs Conda environment first}"
export CC=/usr/bin/gcc-11
export CXX=/usr/bin/g++-11
export CUDAHOSTCXX=/usr/bin/g++-11
export MAX_JOBS="${MAX_JOBS:-2}"

python -m pip install --no-build-isolation \
  "${eogs_root}/src/gaussiansplatting/submodules/diff-gaussian-rasterization" \
  "${eogs_root}/src/gaussiansplatting/submodules/simple-knn"
