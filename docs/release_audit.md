# Release audit

Audit date: 2026-09-27

## Source integrity

- RTX 4060 handoff SHA-256: `aa56cb706ef23e7aa8e92f3408e5c74af674bb12ed0dbdd3910b7f476f11d190`
- RTX 5080 results ZIP SHA-256: `2c7c91b10ef5fabbf5ca35ef56b604e0a51f862acb6303827bfb63c040293e01`
- Every RTX 5080 payload file matched its packaged `CHECKSUMS_SHA256.txt` entry.
- The three common-mask MAE/RMSE values were independently recomputed from the packaged error GeoTIFFs and matched `common_mask_metrics.json` within `1e-6` m.

## Compatibility conclusion

Both machines used `JAX_004`, the same transferred EOGS source snapshot identified as upstream commit `cca973e7ea512091b52c8ff741c80ddade5793d2`, the inherited two-file patch, nine training/two held-out views for the full run, resolution scale 1, 5,000 iterations, SH degree 0, the same 512 × 512 reference grid, and byte-identical registration/evaluation scripts.

The GPU, driver, PyTorch, and CUDA versions differ. Cross-device bitwise determinism was not established. Runtime boundaries differ and 4060 peak VRAM was not recorded. The 4060/full-view accuracy values are close reproducibility evidence, but they are not a controlled hardware benchmark. The primary 4/8/9 analysis comes entirely from the RTX 5080 runs and one shared valid mask.

## Public-repository scan

`python scripts/validate_release.py` checked:

- README local links;
- CSV values against the packaged common-mask JSON;
- absence of machine-specific absolute paths in scripts;
- absence of TIFF/IIO/LAS/LAZ, checkpoints, ZIPs, caches, and files above 10 MiB;
- final payload size and file count.

The final scan passed with 49 files before this audit note was added, a 4,226,201-byte payload, and no prohibited data. The original WorldView-3 imagery, RPC source metadata, reference/label rasters, model outputs, checkpoints, full environments, and dataset archives are excluded.

## Material removed from the publishable tree

- embedded EOGS and GLM source copies: replaced by the exact upstream commit and patch;
- paper/site assets and unrelated example scenes: outside this experiment;
- raw/aligned DSM GeoTIFFs and IIO files: large derived artifacts unnecessary for the compact research repository;
- original imagery, RPC JSON, reference DSM, and labels: redistribution rights were not assumed;
- checkpoints, compiled extensions, build directories, caches, logs, and Conda directories: generated or machine-specific;
- duplicate and debugging figures: four publication-facing figures are retained;
- original machine-specific launch records: normalized configs and a portable launcher are retained, while scrubbed provenance JSON preserves measured resources.

Removed material was moved to a sibling local archive during preparation so it can be recovered; it is outside the public repository.
