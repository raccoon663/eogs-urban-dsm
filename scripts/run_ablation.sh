#!/usr/bin/env bash
set -euo pipefail

research_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
eogs_root="${EOGS_ROOT:?Set EOGS_ROOT to the patched EOGS checkout}"
export MPLBACKEND=Agg

cd "$research_root"
python scripts/select_views.py --root "$research_root"

for label in 4 8 full; do
  case "$label" in
    4|8) display="$label" ;;
    full) display="9" ;;
  esac

  model="$research_root/output/${display}_views_JAX_004"
  result="$research_root/outputs_5080/${display}_views"
  log_dir="$research_root/outputs_5080/logs"
  mkdir -p "$result/dsm" "$result/error_maps" "$log_dir"

  cd "$eogs_root/src/gaussiansplatting"
  python "$research_root/scripts/measure_entry.py" train.py "$result/training_resources.json" \
    -s "$research_root/data/ablation/$label" \
    --images "$research_root/data/images/JAX_004" \
    --eval -m "$model" --sh_degree 0 --resolution 1 --iterations 5000 \
    > "$log_dir/${display}_train.log" 2>&1

  python "$research_root/scripts/measure_entry.py" render.py "$result/render_resources.json" \
    -m "$model" --iteration 5000 --res 0.5 \
    > "$log_dir/${display}_render.log" 2>&1

  dsm="$(find "$model/test_opNone/ours_5000/dsm" -maxdepth 1 -type f | sort -V | tail -n 1)"
  cd "$research_root"
  python scripts/eval/eval_dsm.py \
    --pred-dsm-path "$dsm" --gt-dir data/truth/JAX_004 \
    --out-dir "$model" --aoi-id JAX_004 \
    > "$log_dir/${display}_registration.log" 2>&1

  python scripts/export_dsm.py "$model" \
    --metadata data/truth/JAX_004/JAX_004_DSM.txt \
    --output "$result/dsm/JAX_004_registered.tif" \
    --raw-output "$result/dsm/JAX_004_raw.iio"

  python scripts/align_dsm.py \
    "$result/dsm/JAX_004_registered.tif" \
    data/truth/JAX_004/JAX_004_DSM.tif \
    data/truth/JAX_004/JAX_004_DSM.txt \
    "$result/dsm/JAX_004_aligned.tif" \
    --reference-output outputs_5080/reference.tif \
    --labels data/truth/JAX_004/JAX_004_CLS.tif \
    --labels-output outputs_5080/labels.tif

  python scripts/evaluate_dsm.py \
    "$result/dsm/JAX_004_aligned.tif" outputs_5080/reference.tif \
    --labels outputs_5080/labels.tif \
    --json "$result/metrics.json" --csv "$result/metrics.csv" \
    --error-map "$result/error_maps/signed_error.tif"

  echo "Completed ${display}-view JAX_004"
done
