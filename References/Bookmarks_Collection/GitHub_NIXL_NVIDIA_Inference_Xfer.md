# NVIDIA Inference Xfer Library (NIXL)

**Source URL:** https://github.com/ai-dynamo/nixl  
**Date Fetched:** 2026-04-12

## Overview

NIXL is a specialized library designed to accelerate point-to-point communications in AI inference frameworks such as NVIDIA Dynamo while abstracting various memory and storage types through modular plugins.

## Key Features

- **Memory Abstraction**: Supports CPU and GPU memory
- **Storage Options**: File, block, and object store support
- **Modular Architecture**: Plugin-based design for extensibility
- **Multi-language Support**: C++, Python, and Rust bindings

## Platform Support

Linux is the only supported OS, specifically tested on Ubuntu (22.04/24.04) and Fedora. macOS and Windows are not currently supported.

## Installation Methods

**Quick Install via PyPI:**
- For CUDA 12: `pip install nixl[cu12]`
- For CUDA 13: `pip install nixl[cu13]`

**From Source:** Requires CMake, build-essential, Python development tools, and UCX 1.20.x dependencies.

## Core Dependencies

- UCX (version 1.20.x)
- GDRCopy (optional, for maximum performance)
- ETCD (optional, for distributed metadata coordination)
- CUDA toolkit

## Build Process

The project uses Meson build system with commands like `meson setup <build_dir>` followed by `ninja` and `ninja install`. Various build options customize features like documentation generation and plugin selection.

## Documentation

Comprehensive guides cover:
- Architecture overview
- Python API usage
- Backend development
- Telemetry
- Benchmarking tools (nixlbench and kvbench)
