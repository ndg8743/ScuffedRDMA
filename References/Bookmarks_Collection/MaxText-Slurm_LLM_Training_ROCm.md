# MaxText-Slurm: Production-Grade LLM Training with Built-In Observability

**Source URL:** https://rocm.blogs.amd.com/software-tools-optimization/maxtext-slurm/README.html

**Date Fetched:** 2026-04-12

## Overview

MaxText-Slurm is an open-source launch system and observability platform designed to streamline large language model training on AMD GPU clusters managed by Slurm. The tool addresses operational challenges that standard training frameworks don't handle—from multi-node coordination to real-time system diagnostics.

## Core Capabilities

**Unified Launch System**
The platform simplifies complex distributed training into single-command workflows. Users can launch an 8-node training run with `submit.sh 70b -N 8`, where model names automatically resolve to configuration files. Training arguments are appended after `--`.

**Three-Tier Architecture**
The system uses independently swappable layers:
- **Orchestration** (scheduler management)
- **Container** (environment isolation and GPU passthrough)
- **Training** (framework configuration)

Each tier communicates through environment variables, enabling future support for Kubernetes and other schedulers.

## Observability Stack

**Zero-Overhead Monitoring**
Setting `RAY=1` activates comprehensive observability. The system isolates training in a subprocess to prevent contention with Ray's monitoring threads, achieving "no measurable steady-state overhead on training steps."

**Three Live Dashboards**
- Ray Dashboard (actor status, stack traces)
- Prometheus (GPU thermals, power, network metrics)
- TensorBoard (training loss curves)

**Unified Metrics Store**
All metrics—GPU hardware, host performance, network, and training scalars—feed into a single Prometheus time-series database on persistent storage. This enables correlation across system layers to identify root causes.

## Diagnostic Capabilities

**Plugin-Based Extensibility**
New metric sources can be added by dropping shell scripts into the utils directory; no configuration changes needed. Three plugins ship by default for GPU, host, and training metrics.

**Post-Run Analysis**
Each job creates structured output including Prometheus TSDB, Ray logs, and core dumps, enabling offline diagnosis without cluster access.

**AI-Assisted Diagnosis**
An agentic skills framework enables AI agents to autonomously diagnose failures by querying the unified TSDB and correlating symptoms across domains—for example, identifying RCCL deadlocks by comparing GPU utilization against power consumption.

## Practical Example

During a 24-node training run that hung at step 3,841, the system's metrics revealed all GPUs reporting 100% utilization but drawing only standby power (~300W versus ~900W during training), indicating "spinning in the RCCL busy-wait loop" rather than performing useful work.

## Getting Started

```
submit.sh 70b -N 1              # Basic run
RAY=1 submit.sh 70b -N 1        # With observability
```

The project is available at github.com/AMD-AGI/maxtext-slurm.
