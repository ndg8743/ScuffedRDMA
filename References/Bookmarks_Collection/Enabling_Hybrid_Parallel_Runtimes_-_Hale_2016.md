# Enabling Hybrid Parallel Runtimes Through Kernel and Virtualization Support

**Source URL:** https://www.halek.co/publication/hale-2016-hrthvm/
**Date accessed:** 2026-03-11

**Authors:** Kyle C. Hale, Peter A. Dinda

**Published:** July 2016 (VEE '16)

**Institution:** Oregon State University

## Overview

This research introduces the hybrid runtime (HRT) model, which combines a parallel runtime system and applications into a specialized OS kernel operating in kernel mode with full hardware privileges.

## Key Components

**Nautilus Aerokernel**
A kernel framework designed for HRTs on x64 and Xeon Phi platforms. According to the abstract, "Aerokernel primitives...can operate much faster, up to two orders of magnitude faster, than related primitives in Linux." The framework also provides consistent performance with lower variance.

**Hybrid Virtual Machine (HVM)**
An extension to the Palacios virtual machine monitor enabling a single VM to simultaneously run traditional OS stacks alongside HRTs with specialized hardware access. The system allows HRT bootstrapping comparable to Linux process startup times and function invocation with latencies approaching native function calls.

## Technical Achievements

The researchers created prototype HRTs, including implementations based on the Legion runtime system, with accompanying application benchmarks demonstrating practical effectiveness.

## Research Tags

parallelism, operating systems, runtime systems
