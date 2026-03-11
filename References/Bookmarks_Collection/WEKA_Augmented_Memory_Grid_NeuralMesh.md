# WEKA Breaks The AI Memory Barrier With Augmented Memory Grid on NeuralMesh

**Source URL:** https://www.weka.io/company/weka-newsroom/press-releases/weka-breaks-the-ai-memory-barrier-with-augmented-memory-grid/
**Date accessed:** 2026-03-11

---

**Publication Date:** November 18, 2025
**Location:** ST. LOUIS, MO and CAMPBELL, CA

## Key Announcement

WEKA unveiled Augmented Memory Grid, a breakthrough memory extension technology for its NeuralMesh platform. The solution has been validated on Oracle Cloud Infrastructure and addresses a critical constraint in AI inference: GPU memory limitations.

## Technical Capabilities

The technology delivers impressive performance metrics:
- **1000x increase** in key-value cache capacity compared to traditional GPU memory constraints
- **20x improvement** in time-to-first-token when processing extended 128,000-token sequences
- **High I/O performance**: 7.5M read and 1.0M write operations per second in eight-node clusters

## How It Works

Augmented Memory Grid creates a high-speed connection between GPU high-bandwidth memory and flash-based storage. Using RDMA and NVIDIA's GPUDirect Storage technology, the system maintains near-memory performance while dramatically expanding accessible cache capacity. This eliminates redundant token recomputation that typically wastes GPU cycles.

## Business Impact

The advancement fundamentally reshapes inference economics by enabling:
- Higher GPU tenant density in cloud environments
- Reduced idle GPU cycles
- Improved power efficiency
- New business models for long-context AI applications

## Partnerships

Oracle Cloud Infrastructure provided the validation platform, leveraging its bare-metal GPU infrastructure with RDMA networking. WEKA integrated deeply with NVIDIA technologies including GPUDirect Storage and Dynamo, plus open-sourced a plugin for NVIDIA's Inference Transfer Library.
