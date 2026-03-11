# Inside the NVIDIA Rubin Platform: Six New Chips, One AI Supercomputer

**Source URL:** https://developer.nvidia.com/blog/inside-the-nvidia-rubin-platform-six-new-chips-one-ai-supercomputer/
**Date accessed:** 2026-03-11

---

**Author:** Kyle Aubrey, Director of Technical Marketing at NVIDIA
**Published:** January 5, 2026

## Overview

This comprehensive technical article explores NVIDIA's Rubin platform, designed specifically for next-generation AI factories that require continuous intelligence production at scale. The platform represents "extreme co-design" where GPUs, CPUs, networking, and infrastructure are architected as an integrated system rather than optimized independently.

## Key Platform Breakthroughs

The Rubin platform delivers five major advances:

1. **Sixth-generation NVLink** providing 3.6 TB/s scale-up bandwidth
2. **Vera CPU** with custom Olympus cores optimized for data movement
3. **Rubin GPU Transformer Engine** for transformer-era AI workloads
4. **Third-generation confidential computing** enabling rack-scale trusted execution
5. **Second-generation RAS engine** supporting zero-downtime self-testing

## Six Core Chips

**Vera CPU:** Features 88 custom Olympus cores with Spatial Multithreading, delivering up to 1.2 TB/s memory bandwidth and 1.8 TB/s NVLink-C2C coherent connectivity with GPUs.

**Rubin GPU:** Provides 50 PFLOPS NVFP4 inference performance and 35 PFLOPS training performance, with 22 TB/s HBM4 memory bandwidth and 3.6 TB/s NVLink bandwidth per GPU.

**NVLink 6 Switch:** Enables all-to-all topology across 72 GPUs with in-network compute acceleration for collective operations.

**ConnectX-9:** Delivers 800 Gb/s per port with programmable endpoint control for bursty AI traffic management.

**BlueField-4 DPU:** Integrates 64-core Grace CPU with ConnectX-9 networking to power infrastructure services, storage acceleration, and security operations.

**Spectrum-6 Ethernet Switch:** Provides 102.4 Tb/s total bandwidth using co-packaged photonics for efficient scale-out connectivity.

## System Architecture

The **Vera Rubin NVL72** operates as a rack-scale accelerator delivering:
- 200 petaFLOPS NVFP4 performance per tray
- 14.4 TB/s NVLink 6 bandwidth
- 2 TB fast memory across the system
- Fully liquid-cooled design

## Performance Gains

Compared to prior generations, Rubin achieves:
- Up to 5x higher inference throughput
- 3.5x improved training performance
- 2.8x greater memory bandwidth
- 2x increased NVLink bandwidth

## AI Factory Requirements

The platform addresses three scaling laws driving modern AI:
- Pre-training scaling where models learn foundational knowledge
- Post-training scaling enabling reasoning capabilities
- Test-time scaling where models generate more tokens during inference

## Software and Operations

The architecture supports cloud-scale operations through BlueField-4-based infrastructure services, including **ICMS** (Inference Context Memory Storage) for managing distributed KV cache across AI pods, improving efficiency for long-context agentic workloads.
