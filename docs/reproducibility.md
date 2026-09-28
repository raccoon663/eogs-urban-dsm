# Reproducibility

## Recorded experiment identity

- EOGS repository: <https://github.com/mezzelfo/EOGS>
- Branch: `master`
- Exact upstream commit: `cca973e7ea512091b52c8ff741c80ddade5793d2`
- Local changes: `code_changes.patch`
- Scene: `JAX_004`
- Train/test views: 9/2; fixed held-out IDs in `configs/test_views.txt`
- Input resolution: native, `--resolution 1` (665–814 px wide; 697–827 px high)
- Training: 5,000 iterations, seed 0, SH degree 0
- DSM: 0.5 m, 512 × 512, EPSG:32617

The patch replaces a shell copy with `shutil.copy2` and expands fixed/test backgrounds to the five EOGS channels. It is inherited by both machines and does not introduce a new reconstruction method.

## Environment

The RTX 5080 runs used WSL2 Ubuntu 24.04.5, Python 3.10.21, PyTorch 2.7.1+cu128, torchvision 0.22.1+cu128, CUDA 12.8, nvcc 12.8.93, GCC/G++ 11.5.0, NVIDIA driver 616.56, and an RTX 5080 with 16,303 MiB reported VRAM. `environment.yml` and `requirements.txt` capture the key environment. Local CUDA extensions must be rebuilt for the target GPU.

The RTX 4060 baseline used Python 3.10.21, PyTorch 2.1.2, CUDA 11.8, driver 591.74, and an RTX 4060 Laptop GPU. This stack difference prevents a bitwise cross-device reproduction claim.

## 1. Obtain EOGS and apply the recorded patch

```bash
git clone https://github.com/mezzelfo/EOGS.git eogs-upstream
cd eogs-upstream
git checkout cca973e7ea512091b52c8ff741c80ddade5793d2
git apply /path/to/eogs-urban-dsm/code_changes.patch
export EOGS_ROOT="$PWD"
cd /path/to/eogs-urban-dsm
```

## 2. Create the environment and build extensions

```bash
conda env create -f environment.yml
conda activate eogs-jax004
sudo apt-get install gcc-11 g++-11
EOGS_ROOT="$EOGS_ROOT" bash scripts/build_extensions.sh
python scripts/preflight.py
```

PyTorch CUDA wheels must match the target driver and toolkit. If a different supported stack is necessary, record it because compiled kernels and numerical results may change.

## 3. Prepare the scene and affine cameras

```bash
python scripts/prepare_data.py --scene JAX_004 --data-dir data
python scripts/dataset_creation/to_affine.py --scene_name JAX_004
python scripts/select_views.py --root .
```

`select_views.py` reproduces the nested selection: it fixes the original reference view, exhaustively maximizes minimum pairwise look-direction angle for four views, and then selects an eight-view superset by the same criterion. Compare the outputs with `configs/views_4.txt`, `views_8.txt`, and `views_9.txt` before training.

## 4. Train, render, register, and evaluate

```bash
EOGS_ROOT="$EOGS_ROOT" bash scripts/run_ablation.sh
```

The launcher runs 4, 8, and 9 views with the saved settings, records training resource use, renders DSMs, applies the official `scripts/eval/eval_dsm.py`/`dsmr` registration, exports GeoTIFFs, verifies the grid, and evaluates overall plus building/ground/vegetation metrics.

The actual RTX 5080 wall times for initialization, training, and save were 267.890 s (4 views), 215.282 s (8), and 213.834 s (9). Peak PyTorch allocated memory was 901.131, 700.156, and 675.853 MiB respectively. These measurements exclude preprocessing, separate rendering, and evaluation.

## Evaluation conventions

The primary ablation table uses the intersection of valid pixels across all three RTX 5080 DSMs: 260,610 pixels. Semantic codes are ground 2, high vegetation 5, and building 6. Each per-run JSON in `results/provenance` preserves its original valid-mask result. The 4060 predicted DSM was not transferred, so its metrics cannot be recomputed on the 5080 common mask.

The official registration fits horizontal and vertical offsets against the reference and clips predictions to the reference extrema ±10 m. No additional median shift was applied. The numbers are registered relative DSM errors; the vertical datum was not independently verified.
