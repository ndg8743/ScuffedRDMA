# LMCache

- **Source:** https://lmcache.ai/
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML > LLM Inference)
- **Retrieved:** 2026-10-22


---

## GitHub Stars

## Contributors

## PyPI downloads

## Community members

## 1.3K+

## Building the Foundation of AI Memory Tensor with KV Cache Infrastructure

LMCache pioneers KV cache infrastructure for LLM inference, turning KV cache into AI-native memory that can be stored, compressed, searched, and reused across your entire cluster

## Could AI dream with an electric LMCache?

- INTEGRATIONS

## Compatibility

Supports major inference engines, hardware platforms, and pluggable external storage backends.

- INFERENCE engines

- Storage vendors

- MAINSTREAM ORCHESTRATORS

- GPU VENDORS

- Inference providers

- Research Ideas

- INTEGRATIONS

## Compatibility

Supports major inference engines, hardware platforms, and pluggable external storage backends.

- MAINSTREAM ORCHESTRATORS

- INFERENCE engines

- Storage vendors

- Inference providers

- GPU VENDORS

- Research Ideas

- ARCHITECTURE

## Supported **Deployment**   Patterns

No architectural changes required. Choose the deployment mode that matches your setup.

## In-Process

Simplest integration.

LMCache runs inside the inference engine process.

## Serving 

Engine

## 1

## KV

Library

## Serving 

Engine

## 2

## KV

Library

## Serving 

Engine

## N

## KV

Library

## LMCache Multiprocess

Run LMCache as a standalone server, separate from the inference engine. The engine handles model execution, while LMCache manages KV cache storage, reuse, and recovery across workers, providing process isolation and cache that survives worker restarts or failures.

## Serving 

Engine

## 1

## Serving 

Engine

## 2

## Serving 

Engine

## N

## LMCache Server

MP mode is the **recommended** deployment path and the focus of future LMCache development.

- HOW IT WORKS

## LMCache **Capabilities**  

## Store

## Compress

## Move

## Observe

- ECOSYSTEM

## Broad Ecosystem **Collaboration**  

LMCache is used in production by infrastructure teams, cloud providers, and open-source projects worldwide.

## Nvidia

## Dynamo integrates seamlessly with popular inference engines like vLLM and open source tools like LMCache, enabling efficient cache reuse, reduced recomputation, and better support for long-context and high-concurrency workloads.

## Google Cloud

## For Google Kubernetes Engine users, LMCache’s tiered storage solution improves inference performance by using node-local storage, especially for long system prompts that generate large KV Caches.

## AMD

## When integrated with vLLM, LMCache delivers 3–10× improvements on AMD Instinct MI300X GPUs for a wide range of community models, including Qwen3, Llama3, and Qwen-VL.

## CoreWeave

## Together, LMCache and CoreWeave AI Object Storage form a tightly integrated system: LMCache handles cache serialization and coordination, while CoreWeave AI Object Storage provides the distributed performance backbone that makes external caching seamless.

## Redis

## LMCache reduces redundant computation by caching and reusing key-value (KV) pairs for repeated token chunks. Redis provides the real-time infrastructure to store and retrieve those chunks at scale. Together, they enable faster inference.

## PyTorch Foundation

## LMCache is the first and most efficient open source Key-Value caching solution.

## Tensormesh

## Every improvement to LMCache's architecture means more efficient caching, faster inference, and lower bills for teams running AI workloads at scale.

## Nvidia

## Dynamo integrates seamlessly with popular inference engines like vLLM and open source tools like LMCache, enabling efficient cache reuse, reduced recomputation, and better support for long-context and high-concurrency workloads.

## Google Cloud

## For Google Kubernetes Engine users, LMCache’s tiered storage solution improves inference performance by using node-local storage, especially for long system prompts that generate large KV Caches.

## AMD

## When integrated with vLLM, LMCache delivers 3–10× improvements on AMD Instinct MI300X GPUs for a wide range of community models, including Qwen3, Llama3, and Qwen-VL.

## CoreWeave

## Together, LMCache and CoreWeave AI Object Storage form a tightly integrated system: LMCache handles cache serialization and coordination, while CoreWeave AI Object Storage provides the distributed performance backbone that makes external caching seamless.

## Redis

## LMCache reduces redundant computation by caching and reusing key-value (KV) pairs for repeated token chunks. Redis provides the real-time infrastructure to store and retrieve those chunks at scale. Together, they enable faster inference.

## PyTorch Foundation

## LMCache is the first and most efficient open source Key-Value caching solution.

## Tensormesh

## Every improvement to LMCache’s architecture means more efficient caching, faster inference, and lower bills for teams running AI workloads at scale.

- RESEARCH

## Built on Best **Research** 

- EXPLORE

## Resources

Practical guides, community tools, and everything you need to deploy, contribute to, and stay current with LMCache.

## Recipes

## Contribution Guidelines

## Fresh from the Community

## Tools

## Get Started

## Dive In

## Join the community

Slack, GitHub, Office Hours