# Offloading Support in GCC

**Source URL:** https://gcc.gnu.org/wiki/Offloading
**Date accessed:** 2026-03-11

---

## Overview

This GCC Wiki article provides comprehensive documentation on GPU offloading capabilities in the GNU Compiler Collection. The guide covers using offloading features, building offload-enabled compilers, and understanding the technical compilation and runtime processes.

## Supported Offload Targets

GCC supports two primary GPU architectures:

**AMD GPUs (Radeon/CDNA Instinct):** Includes support for multiple GPU generations—Vega 10/20 (gfx900, gfx906), CDNA1 MI100 (gfx908), CDNA2 MI200 (gfx90a), and consumer cards like gfx1030 and gfx1100. The article notes that "Fiji (gfx803) support has been removed from GCC 15, and was deprecated in GCC 14."

**NVIDIA GPUs (nvptx):** Supported through NVIDIA PTX target specification, enabling compilation for NVIDIA graphics processors.

## Key Features

The document emphasizes that "No hardware-vendor libraries (like CUDA or ROCm) are required for compilation. And when run: if the hardware library is not available and/or no suitable offload device is available, host fallback is done."

Offloading is enabled through:
- **OpenMP**: Via `-fopenmp` flag
- **OpenACC**: Via `-fopenacc` flag

## Build Requirements

Compiling GCC with offloading support requires:
- LLVM 15+ (for AMD GCN support)
- nvptx-tools (for NVIDIA support)
- Newlib library
- Standard build dependencies (GMP, mpfr, mpc, ISL)

## Distribution Support

- **openSUSE/SUSE**: Install `cross-{nvptx,amdgcn}-gcc13`
- **Debian/Ubuntu**: Install `gcc-13-offload-{nvptx,amdgcn}`
- **Fedora/RHEL**: Install `{gcc,libgomp}-offload-{nvptx,amdgcn}`

## Technical Architecture

The compilation process involves several stages:

1. Host compiler generates outlined target functions with special LTO sections
2. Address mapping tables maintain host-to-device address translation
3. The `lto-wrapper` invokes target-specific `mkoffload` tools
4. Accel compilers generate device code from intermediate representation
5. Device images are embedded in the host binary through special sections

## Runtime Process

At execution, GOMP (GNU OpenMP) plugins handle device interaction. The runtime system performs address translation using splay trees to map host addresses to target device addresses. If offload devices are unavailable, "host fallback" automatically executes code on the CPU instead.

## Notable Version Changes

- **GCC 13**: Added AMD gfx90a support
- **GCC 14**: Deprecated AMD Fiji support; added consumer GPU support
- **GCC 15**: Removed Fiji support entirely; introduced experimental generic AMD GPU support
