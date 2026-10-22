# MegaTrain: Full Precision Training of 100B+ Parameter Large Language Models on a Single GPU

- **Source:** https://arxiviq.substack.com/p/megatrain-full-precision-training
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > Papers > Papers)
- **Retrieved:** 2026-10-22


---

**Authors:** *Zhengqing Yuan, Hanchi Sun, Lichao Sun, Yanfang Ye*

**Paper:** [https://arxiv.org/abs/2604.05091](https://arxiv.org/abs/2604.05091)

**Code:** [https://github.com/DLYuanGod/MegaTrain](https://github.com/DLYuanGod/MegaTrain)

**Model:** N/A

# TL;DR

**WHAT was done?** The authors introduce **MegaTrain**, a memory-centric training framework designed to execute full-precision training and fine-tuning of large language models exceeding 100 billion parameters on a single GPU. By completely inverting the traditional GPU-centric execution paradigm, MegaTrain delegates the storage of all persistent model states (parameters, gradients, and optimizer moments) to the host CPU memory and utilizes the GPU solely as a transient, stateless compute cache.

**WHY it matters?** This work fundamentally challenges the assumption that large language model (LLM) training limits are strictly governed by GPU VRAM capacity. By utilizing a pipelined double-buffered data transfer schedule and a stateless template-binding model, MegaTrain breaks the GPU memory wall and scales training capacity linearly with host memory. This democratizes post-training, instruction-tuning, and long-context alignment of 100B+ models, moving these workloads from massive distributed clusters to single commodity workstation nodes.

# Details

### The VRAM Capacity Bottleneck in Post-Training Scaling

The development lifecycle of large language models has increasingly shifted from massive, compute-bound pre-training phases to highly localized, memory-bound post-training phases, such as instruction tuning, domain adaptation, and alignment. While these post-training tasks require relatively light compute resources, they are severely bottlenecked by the physical memory footprint of the models. Standard mixed-precision training requires massive allocations to store weights, gradients, and optimizer states. Traditional GPU-centric frameworks, including [PyTorch FSDP](https://arxiv.org/abs/2304.11277) and heterogeneous offloading baselines like [ZeRO-Offload](https://arxiv.org/abs/2101.06840), attempt to bypass physical VRAM limits by migrating inactive states to host CPU memory.

However, these existing systems treat the GPU as the primary authoritative store and CPU memory merely as a spill buffer. As a result, they suffer from severe PCIe transfer overheads, high synchronization latency, and memory fragmentation, which leads to catastrophic throughput degradation or out-of-memory (OOM) errors when scaling beyond 30 billion parameters on single devices. MegaTrain addresses this bottleneck by inverting this hierarchy, treating the host memory as the primary repository and streaming parameters to the GPU on demand.