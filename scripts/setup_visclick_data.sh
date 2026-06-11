#!/usr/bin/env bash
# Bootstrap VISCLICK_DATA on a Linux GPU box (no Google Drive).
# Downloads the public Zenodo unified bundle and creates the expected layout.
#
# Usage:
#   export VISCLICK_DATA=$HOME/visclick_data
#   bash scripts/setup_visclick_data.sh
#
# After this script, you still need:
#   $VISCLICK_DATA/weights/baseline_source/best_source_v8s.pt  (~22 MB)
# Copy from Colab Drive or scp from your laptop.

set -euo pipefail

DATA_ROOT="${VISCLICK_DATA:-$HOME/visclick_data}"
ZENODO="https://zenodo.org/records/19195885/files"

echo "VISCLICK_DATA = $DATA_ROOT"
mkdir -p "$DATA_ROOT/raw" "$DATA_ROOT/unified" "$DATA_ROOT/weights/baseline_source"

for sp in train val test; do
  zip="$DATA_ROOT/raw/${sp}.zip"
  if [[ -f "$zip" && $(stat -c%s "$zip" 2>/dev/null || stat -f%z "$zip") -gt 1000000 ]]; then
    echo "skip download $sp.zip (already present)"
  else
    echo "=== downloading ${sp}.zip ==="
    wget -c "${ZENODO}/${sp}.zip?download=1" -O "$zip"
  fi
  out="$DATA_ROOT/unified/$sp"
  mkdir -p "$out"
  if [[ -d "$out/images" && $(find "$out/images" -maxdepth 1 -type f 2>/dev/null | wc -l) -gt 10 ]]; then
    echo "skip unzip $sp (images already present)"
  else
    echo "=== extracting $sp ==="
    unzip -q -o "$zip" -d "$out"
    # flatten nested split folder if Zenodo zip has train/train/images
    if [[ -d "$out/$sp/images" ]]; then
      mv "$out/$sp"/* "$out/" 2>/dev/null || true
      rmdir "$out/$sp" 2>/dev/null || true
    fi
  fi
  n=$(find "$out/images" -maxdepth 1 -type f 2>/dev/null | wc -l)
  echo "  $sp images: $n"
done

if [[ -f "$DATA_ROOT/weights/baseline_source/best_source_v8s.pt" ]]; then
  echo "OK  best_source_v8s.pt present"
else
  echo "MISSING  $DATA_ROOT/weights/baseline_source/best_source_v8s.pt"
  echo "  scp from Colab Drive or your laptop before running UDA/SSP scripts."
fi

echo "REPORT setup | data_root = $DATA_ROOT | status = done"
