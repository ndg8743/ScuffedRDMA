# Explanations and proofs

One page per section of the [README walkthrough](../../README.md#the-thesis-section-by-section). Each page starts with the section's animation, defines its terms, derives the math, proves the claims that can be proven, and ends with a table that marks every claim as proven, measured, an approximation, or still open.

| # | Page | What is proven or derived |
|---|---|---|
| 1 | [What moves: network and storage](01-traffic.md) | KV bytes per token, per request; wire time with RoCEv2 overhead; GPU memory capacity; spill vs recompute |
| 2 | [Head-of-line blocking](02-head-of-line-blocking.md) | FIFO worst case; Pollaczek–Khinchine and Cobham formulas; one queue vs priority vs packet interleaving |
| 3 | [Where industry stands](03-industry.md) | evidence for each of the five problems |
| 4 | [The dual pool on libfabric](04-dual-pool.md) | why separate endpoints and CQs; busy-poll vs wait objects; why one harness isolates the library |
| 5 | [FabricBlobChannel](05-blob-channel.md) | slot safety invariant; staging-buffer safety; notification ordering; reassembly; Little's-law throughput bound |
| 6 | [Completion signaling](06-completion-signaling.md) | the ordering guarantee each mechanism relies on, and when it fails |
| 7 | [ScuffedRdmaConnector](07-connector.md) | keying and collision bound; lost layer → recompute, not wrong output; bounded wait; staging cost |
| 8 | [WFA classifier](08-wfa-classifier.md) | static phase detector never sees decode; softmax gradient; unique optimum of training |
| 9 | [Rule-Node Expression Trees](09-policy-trees.md) | safe short-circuiting; highest-priority rule owns each field; linear cost |
| 10 | [PMP controller](10-pmp-controller.md) | bang-bang from Pontryagin's principle; costate ≈ queue depth; the cμ rule; a sign issue in the code |
| 11 | [scuffedQuant](11-scuffedquant.md) | orthogonal rotation; coordinate variance; Lloyd–Max conditions; unbiased sketch; 1/√m error; 64-byte format |
| 12 | [NVMe storage tier](12-storage-tier.md) | O_DIRECT alignment; no double allocation; CRC32 guarantees; coalescing model vs measured data |

Each page's formulas are also the **Math** cell of the notebook that checks them ([`notebooks/`](../../notebooks/), see the README's notebook table), and the notebooks save their figures to [`docs/figures/`](../figures/).

Conventions: KiB/MiB are powers of two; MB/s and Gb/s are powers of ten. "Measured" numbers name their results file; everything else is arithmetic, a model with stated assumptions, or labeled illustrative.
