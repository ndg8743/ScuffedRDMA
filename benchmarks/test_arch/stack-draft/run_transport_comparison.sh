#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
echo "=== ScuffedRDMA P2P benchmark ==="
python bench_scuffedrdma_p2p.py "$@"
echo ""
echo "=== UCCL P2P benchmark ==="
python bench_uccl_p2p.py "$@"
echo ""
echo "=== Results ==="
python bench_compare.py
