#!/usr/bin/env bash
# Run all four per-architecture benchmarks. Tags output JSON by hostname
# so Chimera and Cerberus runs land in distinct files under
# benchmarks/results/test_arch/.

set -e
cd "$(dirname "$0")"

python bench_transformer.py       "$@"
python bench_mamba3.py            "$@"
python bench_granite4_hybrid.py   "$@"
python bench_granite4_moe.py      "$@"

echo
echo "Wrote:"
ls -1 "$(dirname "$0")/../results/test_arch/$(hostname -s)"*.json 2>/dev/null || \
  ls -1 "$(dirname "$0")/../results/test_arch/"*.json
