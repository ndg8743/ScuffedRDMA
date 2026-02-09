#!/bin/bash
# Automated benchmark across all transports

for transport in tcp roce ttpoe; do
    ./start_cluster.sh --transport=$transport
    sleep 120  # Wait for model load

    python benchmarks/benchmark_transports.py \
        --transport=$transport \
        --iterations=5 \
        --output=$OUTPUT_DIR

    ./start_cluster.sh --stop
done
