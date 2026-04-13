# hipFile - AMD Infinity Storage Library

**Source URL:** https://github.com/ROCm/hipFile  
**Date Fetched:** 2026-04-12

## Overview

The **hipFile** repository is an AMD Infinity Storage library that supports IO directly to the GPU. This repository has been deprecated and moved to [ROCm/rocm-systems](https://github.com/ROCm/rocm-systems).

## Key Information

**Status**: This is an early-access technology preview, and production workloads are not recommended.

**License**: MIT

**Current Branch**: develop_deprecated (221 commits)

## Main Features & Support

The repository includes support for:

### HIPIFY Integration
The `amd-develop` branch of ROCm/HIPIFY contains hipFile support, though these changes haven't reached a public release yet. A cuFile to hipFile API mapping is available for reference.

### FIO Support
A fork of the fio project exists at ROCm/fio with a dedicated hipFile branch that includes a libhipfile engine. Unofficial releases are packaged separately.

## Installation

Detailed build and installation instructions, along with hardware and compiler compatibility information, are documented in the INSTALL.md file.

## Project Statistics

- **Stars**: 22
- **Forks**: 7
- **Code Composition**: Primarily C++ (88.3%), with CMake (7.8%) and C (2.1%)

## Note

Users are directed to use the rocm-systems repository for continued development.
