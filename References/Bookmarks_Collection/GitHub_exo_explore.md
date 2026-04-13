# EXO: Distributed AI Inference

## Project Overview

EXO is an open-source framework that connects all your devices into an AI cluster to run frontier AI models locally. Maintained by exo labs, it enables distributed inference across multiple devices with automatic discovery and topology-aware optimization.

## Key Features

The project highlights several capabilities:

- **Automatic Device Discovery**: Devices running EXO detect each other without manual configuration
- **RDMA over Thunderbolt 5**: Achieves "99% reduction in latency between devices" on compatible hardware
- **Topology-Aware Auto Parallel**: Dynamically determines optimal model distribution based on device resources and network metrics
- **Tensor Parallelism**: Supports model sharding for performance scaling (claimed 1.8x speedup on 2 devices, 3.2x on 4)
- **MLX Integration**: Uses MLX as the inference backend with distributed communication support
- **Multi-API Compatibility**: Compatible with OpenAI Chat Completions, Claude Messages, OpenAI Responses, and Ollama APIs
- **Custom Model Support**: Load models from HuggingFace hub

## Getting Started

### Installation Methods

**macOS**: Install Xcode, Homebrew, uv, Node.js, Rust, and macmon. Clone the repository, build the dashboard, then run `uv run exo`.

**Linux**: Install uv, Node.js (18+), and Rust. The same build process applies, though "exo runs on CPU on Linux" currently.

A standalone macOS app is available requiring "macOS Tahoe 26.2 or later."

## API Usage

EXO provides REST endpoints for model management and inference:

- Preview placements: `GET /instance/previews?model_id=...`
- Create instances: `POST /instance`
- Chat completions: `POST /v1/chat/completions`
- Model operations: `GET/POST /models`

The dashboard runs at `http://localhost:52415`.

## Repository Stats

- 43.5K stars, 3K forks
- 2,270 commits
- Apache 2.0 licensed
- Active development with 131 open issues

---

**Source**: https://github.com/exo-explore/exo
