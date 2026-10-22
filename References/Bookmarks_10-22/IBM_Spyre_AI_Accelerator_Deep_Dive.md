# IBM's Spyre AI Accelerator Deep Dive (Gavin Bonshor, More Than Moore)

- **Source:** https://morethanmoore.substack.com/p/ibms-spyre-ai-accelerator-deep-dive
- **Bookmarked:** 2026-10-05 (Chrome, Bookmarks bar > RDMA > 10-22)
- **Retrieved:** 2026-10-22
- **Note:** Substack serves a JS shell to scripts, so this is a structured summary of the article (based on IBM's ISSCC 2026 disclosure), not a verbatim copy. Read the original for full text and figures.

---

## Positioning
- 75 W single-slot PCIe Gen5 x16 inference card for IBM Z (z17, LinuxONE 5) and Power11. Not a GPU; compared against NVIDIA L4/T4 class.
- Targets low-latency encoder inference (BERT-class fraud scoring) plus decoder/generative support.

## Silicon
- 5 nm, 330 mm², 25.6B transistors. 32 active AI cores (8×4 grid) + 2 spares, bidirectional ring bus, 64 MB on-chip SRAM.
- Each core: two corelets, 2 MB L1 each, 8×8 SIMD-systolic array; FP32 vector units for activation/normalization.
- Peak: 98 FP16 / 157 FP8 / 315 INT8 / 629 INT4 TOPS (IBM figures).

## Memory and host
- 128 GB LPDDR5 (16 ch × 6.4 Gbps), 204 GB/s, SECDED ECC. LPDDR5 over HBM due to 75 W budget.
- 64 GB/s each direction to host.

## Card-to-card RDMA (relevant to this thesis)
- On-card RDMA engine moves data card-to-card over PCIe through a PCIe switch without host CPU involvement, 64 GB/s with CRC.
- IBM's Granite-3.3-8B data: near-linear scaling to 4 cards, continued gains to 8; TTFT and ITL both improve.
- No KV-cache placement or paging details in the article.

## Power management
- 0.55 V AI core array, 0.75 V SRAM; 7T cell library chosen over 6T at that voltage.
- Dual-loop controller (fast peak-current inner loop, software outer loop on average current): ~25% inference throughput over single-loop at same budget, 7 to 32% on encoders.

## Scale
- Up to 48 cards per z17 I/O tray, 192 per system; 16 per Power11 system.
