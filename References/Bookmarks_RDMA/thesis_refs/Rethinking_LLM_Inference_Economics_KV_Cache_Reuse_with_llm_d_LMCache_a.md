# Rethinking LLM Inference Economics: KV Cache Reuse with llm-d, LMCache, and IBM Storage Scale

- **Source:** https://community.ibm.com/community/user/blogs/anthony-hsu/2026/02/06/rethinking-llm-inference-economics
- **Cited in:** REFERENCES.md [4g]
- **Retrieved:** 2026-10-22

---

# File and Object Storage

# File and Object Storage

Software-defined storage for building a global AI, HPC and analytics data platform

## Rethinking LLM Inference Economics with llm-d, LMCache, and IBM Storage Scale

Authors: [@Anthony Hsu](https://community.ibm.com/community/user/people/anthony-hsu) [@Khanh Ngo](https://community.ibm.com/community/user/profile?UserKey=010bf7e6-51f9-4752-9807-52e8d583d65a) [@Yue Zhu](https://community.ibm.com/community/user/people/yue-zhu) @Radu Stoica [@Guy Margalit](https://community.ibm.com/community/user/people/guy-margalit) [@Vasily Tarasov](https://community.ibm.com/community/user/people/vasily-tarasov) [@Michael Kieran](https://community.ibm.com/community/user/people/michael-kieran)

AI systems are like a forgetful grandparent: conversations go best when you gently remind them of earlier moments and context. In practice, this is exactly how today’s AI models “think.” They don't actually "remember" the beginning of your chat while they are typing the end. Every time you send a new message, the AI has to re-read the entire conversation history from scratch to understand the context. The longer the conversation, the more work the model has to redo—over and over again.

As LLMs move from experimentation into production, this repeated recomputation is becoming a serious problem. Inference—not training—is now the dominant cost driver. Users expect instant responses, workloads are increasingly interactive, and GPU capacity remains both scarce and expensive.

At the center of this challenge is a simple reality: most LLM inference systems repeatedly recompute work they have already done.

This is where Key-Value (KV) caching changes the story.

KV caching allows a model to reuse previously computed attention state instead of rereading the entire conversation from scratch. When that cached state can be shared, persisted, and reused across requests, inference becomes both faster and dramatically cheaper.

In this blog, we explore how combining llm-d, LMCache, and IBM Storage Scale fundamentally changes the economics of LLM inference. By enabling high rates of KV cache reuse across requests, this architecture delivers substantial gains in both latency and cost efficiency—even under conservative assumptions.

## Why KV Cache Reuse Changes Everything

Transformer-based LLMs rely on KV caches to store intermediate attention state during inference. These caches allow the model to avoid recomputing attention over tokens it has already processed, dramatically reducing compute for long prompts and multi-turn interactions.

In practice, however, many deployments fail to fully capitalize on this capability:

- KV caches are often confined to a single process or GPU
- Cache reuse is limited to short-lived sessions
- Memory pressure forces aggressive eviction
- Reuse cannot extend across nodes or restarts

As a result, systems repeatedly pay the full cost of prefill computation—even when prompts share substantial common prefixes.

This pattern is especially common in:

- Retrieval-augmented generation (RAG)
- Conversational agents
- Tool-using LLM workflows
- Enterprise copilots with shared context

LMCache externalizes KV caches so they can be reused across requests, and llm-d coordinates reuse at the inference layer. When IBM Storage Scale is used as the backing store, KV reuse becomes persistent, distributed, and economically viable at scale.

The key insight is straightforward: **every reused token is GPU compute you don’t have to pay for again**.

## System Architecture

To evaluate the impact of KV cache reuse, we modeled a controlled inference setup designed to isolate the cost and performance effects of reuse alone.

The system consists of:

- RedHat llm-d as the inference orchestrator
- LMCache managing KV cache reuse
- IBM Storage Scale as the cache backend
- NVIDIA H100 GPUs as the compute substrate

The workload assumes a single user issuing a single query at a time, intentionally excluding concurrency effects to avoid overstating gains. Each request serves approximately the same total number of tokens, while the **prefix reuse rate** varies from 0% to 100%.

Key assumptions include:

- Fixed total token count per request
- Increasing reuse corresponds to fewer tokens requiring prefill computation
- GPU, CPU, and hardware amortization costs are explicitly modeled
- Storage and network costs are treated conservatively

This approach allows us to directly observe how increasing KV reuse impacts:

- Time-to-First-Token (TTFT)
- Prefill throughput
- Cost per million tokens served
- Performance per dollar spent

The measurements were taken using a 70B-parameter instruction-tuned model in the LLaMA-class of architectures. The conclusions do not depend on this specific model and are expected to hold for other large decoder-only transformer models with comparable attention mechanisms.

## Cost Model and Methodology

To quantify the economic impact of KV cache reuse, we constructed a simplified but conservative cost model designed to capture the dominant contributors to inference cost while avoiding speculative assumptions.

The intent of this model is not to reproduce exact cloud billing statements, but to enable **relative comparison** across storage backends under identical workloads.

### Hardware Cost Assumptions

The evaluated system consists of:

- Four NVIDIA H100 GPUs
- A single CPU host with networking
- A shared storage backend used for KV cache persistence

GPU pricing is derived from publicly available H100 pricing and normalized to per-second cost. CPU and server costs are modeled as fixed infrastructure overhead amortized over system lifetime.

Storage costs are modeled explicitly for IBM Storage Scale and held constant across scenarios to isolate the effect of cache reuse and retrieval latency rather than capacity pricing.

### DRAM-Based KV Cache Cost Modeling

To estimate the cost of a DRAM-resident KV cache, we assume a representative KV working set size derived from published LLM trace studies and long-context inference behavior.

For a 70B-class model with a maximum context length of 128K tokens, each KV entry occupies approximately 320 KB. At scale, this translates to a KV cache footprint on the order of tens of gigabytes per active context and many terabytes for shared, reusable working sets.

DRAM pricing is conservatively estimated at approximately $1,000 per 128 GB module, consistent with current enterprise server configurations. Under these assumptions, a 100 TB DRAM-resident KV cache would cost on the order of $780,000, excluding additional server and networking overhead.

This highlights a key limitation of DRAM-only KV caching: while it offers low latency, its cost scales linearly with cache size and quickly dominates system capital expenditure.

### Storage-Backed KV Cache Assumptions

For storage-backed KV caching, IBM Storage Scale is modeled as a shared, high-throughput backend with sufficient bandwidth to support KV reuse without becoming the dominant latency bottleneck.

Tiered storage costs beyond the active KV working set are held constant across all scenarios. This ensures that differences in measured cost and performance arise from reuse efficiency and access latency, rather than differences in total stored capacity.

### Latency and Throughput Modeling

TTFT is modeled as the sum of:

- Fixed inference overhead
- Residual prefill computation for non-reused tokens
- KV cache retrieval time, parameterized by storage throughput

A lower bound on TTFT is established by assuming an infinitely fast CPU and storage subsystem, providing a reference point for the best achievable latency under full reuse.

## Results: Performance and Cost Under Realistic Reuse

### Latency Improves Alongside Cost

Reducing inference cost is only valuable if user experience is preserved—or improved. In practice, KV cache reuse delivers substantial latency benefits.

**Figure 1** compares TTFT across storage backends as KV cache reuse increases. As reuse grows, TTFT decreases steadily, reflecting the elimination of large prefill passes. At high reuse rates, TTFT improves by more than an order of magnitude relative to the no-reuse baseline.

The figure also shows that latency improvement is strongly dependent on the storage backend. While all systems benefit from reuse, average-throughput storage delivers only modest TTFT reductions. In contrast, IBM Storage Scale achieves substantially larger improvements, approaching DRAM-level latency at high reuse rates while preserving shared, distributed access.

As a result, KV reuse backed by Storage Scale produces latency that is:

- Lower overall
- More predictable across requests
- Less sensitive to prompt length and context size

These properties are especially important for interactive applications operating under strict service-level objectives.

Figure 1 is derived from a simplified performance model that isolates the effect of KV cache reuse and storage throughput on TTFT. The baseline corresponds to a system with **no KV cache reuse**, where every request performs a full prefill pass on the GPU and no KV data is written to or read from the filesystem. In this configuration, TTFT is dominated entirely by GPU compute and remains constant regardless of filesystem bandwidth.

For storage-backed configurations, increasing KV reuse reduces the amount of GPU prefill work and shifts the critical path toward retrieving cached KV state. The observed TTFT therefore depends on how quickly the storage backend can deliver KV data.

The “average storage” curve assumes an effective throughput of **8 GB/s**. While general-purpose storage systems may advertise higher peak bandwidths, latency-sensitive and highly concurrent workloads such as KV cache reuse rarely achieve those peaks in practice. Protocol overhead, metadata operations, network contention, and non-sequential access patterns typically reduce sustained, application-visible throughput to a range of **5–10 GB/s**. An effective throughput of 8 GB/s was chosen as a realistic midpoint within this range to represent typical storage behavior under load.

IBM Storage Scale is modeled with substantially higher sustained throughput, allowing KV retrieval to remain off the critical path even at high reuse rates. DRAM represents a lower bound on latency, where KV access time is negligible relative to GPU execution.

## Cost per Token Drops Dramatically

While latency improvements are compelling on their own, they are only part of the story. KV cache reuse also delivers dramatic cost reductions.

This effect is shown in **Figure 2**, which plots the cost per 100 million tokens as a function of KV cache reuse across storage backends. As reuse increases, the amount of GPU work required during the prefill phase decreases proportionally, shifting cost from expensive GPU compute to data retrieval.


Across the evaluated configurations, moving from no reuse to full reuse reduces cost by more than an order of magnitude. Even partial reuse produces meaningful savings, with cost declining smoothly as reuse increases.

The figure further highlights an important tradeoff. Although DRAM-backed caching provides the lowest absolute latency, its cost scales directly with the KV cache working set size and remains higher than storage-backed approaches under the evaluated assumptions. IBM Storage Scale achieves a more favorable balance, delivering near-DRAM latency improvements while maintaining the lowest cost per token across reuse levels.

The implication is clear: **Storage Scale enables latency gains from reuse without the prohibitive cost of DRAM-resident KV caches**.

## Why IBM Storage Scale Is Well-Suited for Distributed KVCache

Large-scale KV caching places unique demands on the underlying storage system. Unlike traditional model artifacts or static datasets, KV caches are latency-sensitive, highly concurrent, and accessed repeatedly across distributed inference workers. IBM Storage Scale is particularly well-suited to serve as a KV cache backend because it was designed from the ground up to support these exact characteristics.

### Built for High-Throughput, Low-Latency Access

IBM Storage Scale is the result of decades of investment in high-performance computing (HPC) workloads, where sustained throughput and predictable low latency are critical. These same properties are essential for KV cache reuse, where inference performance depends on the ability to rapidly retrieve cached attention states without introducing bottlenecks.

Rather than treating cached data as cold or infrequently accessed, Storage Scale is optimized for continuous, high-rate access patterns—making it a natural fit for serving reusable KV tensors at scale.

### Shared, Distributed Data Access by Design

KV cache reuse is most powerful when cached prefixes can be shared across GPUs, nodes, and processes. IBM Storage Scale is a distributed filesystem that provides a **single, shared namespace** with consistent performance under high concurrency.

This shared access model allows KV caches generated by one inference worker to be reused by others, regardless of where subsequent requests are scheduled. As a result, cache reuse becomes a system-wide capability rather than a node-local optimization.

### Seamless Support for Multi-Tier Storage

As LLM context windows and token volumes continue to grow, KV caches naturally expand in size and retention requirements. Managing this growth efficiently requires a storage system that can span multiple tiers without forcing manual data movement or architectural changes.

IBM Storage Scale is designed to manage data across tiers seamlessly—from high-performance local storage to lower-cost capacity tiers, including object storage and tape. This allows frequently reused KV data to remain close to compute while older or less active cache entries can be retained economically.

By decoupling cache capacity from GPU memory and supporting tiered storage transparently, Storage Scale enables long-lived KV reuse without constraining inference concurrency or model size.

## What This Means for Real Deployments

In real enterprise deployments, high prefix reuse is not an edge case—it is the common case. Retrieval-augmented generation pipelines repeatedly inject the same retrieved context, agents operate over shared instructions, and copilots maintain persistent conversational state.

Under these conditions, the combination of llm-d, LMCache, and IBM Storage Scale enables:

- Significantly lower inference cost at scale
- Substantially improved end-user responsiveness
- More efficient utilization of expensive GPU resources
- A predictable and sustainable cost model as workloads grow

Rather than scaling GPU fleets linearly with demand, organizations can scale **reuse**, extracting dramatically more value from the same hardware footprint while maintaining low latency.

## Conclusion: Changing the Inference Cost Curve

LLM inference efficiency is no longer just a model problem—it is a systems problem.

By treating KV cache reuse as a first-class architectural concern, and by backing that reuse with a high-performance distributed file system like IBM Storage Scale, organizations can fundamentally alter the economics of inference.

The combination of llm-d, LMCache, and IBM Storage Scale demonstrates that better performance and lower cost are not competing goals. With the right architecture, they reinforce each other.

As LLM workloads continue to grow, systems that maximize reuse will define the next generation of cost-efficient, scalable AI infrastructure.

## Permalink