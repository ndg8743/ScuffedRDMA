# KernelBlaster - CUDA Optimization Framework

**Source URL:** https://github.com/NVlabs/KernelBlaster  
**Date Fetched:** 2026-04-12

## Overview

KernelBlaster is an open-source framework from NVIDIA Labs that optimizes CUDA code using memory-augmented in-context reinforcement learning. The system achieves significant performance improvements by combining profiling feedback, a persistent optimization knowledge base, and intelligent exploration strategies.

## Key Achievements

The framework demonstrates impressive speedups compared to PyTorch baselines:
- 1.43x on KernelBench Level 1
- 2.50x on Level 2
- 1.50x on Level 3

## Core Innovation

Rather than treating each kernel optimization as an isolated task, KernelBlaster maintains a persistent optimization database that learns from previous attempts. This approach prevents repeated mistakes and enables the agent to make progressively smarter optimization choices.

## Methodology

The system operates through a cycle of:
1. Loading CUDA kernels
2. Profiling candidates
3. Retrieving relevant optimization patterns
4. Generating new code candidates
5. Evaluating results
6. Updating strategy

This reinforcement learning-style loop improves over time as the knowledge base grows.

## Technical Structure

The codebase includes:
- Input kernels from KernelBench-CUDA dataset (Levels 1-3)
- Optimization agents and profiling utilities
- Workflow orchestration and GPU server infrastructure
- A structured knowledge base tracking performance patterns

## Getting Started

Users can build a Docker container, set environment variables (including OpenAI API key), and execute optimization runs via provided scripts. The framework outputs optimized kernels and maintains detailed trajectory artifacts.

## Citation

Published as: "KernelBlaster: Continual Cross-Task CUDA Optimization via Memory-Augmented In-Context Reinforcement Learning" (arXiv:2602.14293)
