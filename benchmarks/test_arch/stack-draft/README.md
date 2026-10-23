# test_arch benchmarks

Transport-layer P2P latency comparison: ScuffedRDMA vs UCCL.

## Scripts

- `common.py` -- shared harness, result saving, node detection
- `bench_scuffedrdma_p2p.py` -- RDMA write latency across message sizes (64B--4MB)
- `bench_uccl_p2p.py` -- UCCL benchmark wrapper (requires UCCL built + torchrun)
- `bench_compare.py` -- print summary of all saved results
- `run_transport_comparison.sh` -- runs all benchmarks in sequence

## Usage

ScuffedRDMA (two terminals, two nodes):

    # server (cerberus)
    python bench_scuffedrdma_p2p.py --role server --device rxe0

    # client (chimera)
    python bench_scuffedrdma_p2p.py --role client --host 192.168.1.242 --device rxe0

Or run everything:

    bash run_transport_comparison.sh --role server --device rxe0

## Prerequisites

- pyverbs, numpy
- SoftROCE (rxe0) or real RDMA NIC configured
- UCCL built for UCCL benchmarks (`cd uccl && bash build.sh cu12 p2p --install`)

## Output

JSON results saved to `benchmarks/results/test_arch/`.
