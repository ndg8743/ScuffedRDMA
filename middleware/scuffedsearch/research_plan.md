# ScuffedSearch: RDMA Research Automation Plan

## Rules
1. **Only modify `optimize.py`** — `prepare.py` is immutable
2. **One change at a time** — isolate variables for clear attribution
3. **Git commit every experiment** — reproducibility is mandatory
4. **Time budget**: each experiment should complete within 5 minutes
5. **Score threshold**: KEEP if score improves by >1%, else DISCARD

## Metrics (from prepare.py)
- **Throughput** (Gbps): sustained transfer bandwidth
- **Latency** (μs): median round-trip time
- **Bandwidth efficiency**: throughput / link_bandwidth
- **Score**: geometric mean of throughput_efficiency × latency_factor

## Optimization Axes
1. **Batch size**: number of tensors per batch (1–256)
2. **QP depth**: send/recv queue depth (1–128)
3. **Prefetch depth**: layers to prefetch ahead (0–10)
4. **Wire format**: FP32 / FP16 / BF16 / INT8
5. **Transport mode**: TCP / SoftRoCE / Hardware RoCE
6. **Buffer pool**: pre-registered buffers (1–32)
7. **Inline threshold**: bytes for inline sends (0–512)
8. **Congestion window**: outstanding RDMA ops (1–128)

## Experiment Log

| # | Date | Change | Score Before | Score After | Outcome |
|---|------|--------|-------------|-------------|---------|
| 1 | — | Baseline (default params) | — | — | — |
