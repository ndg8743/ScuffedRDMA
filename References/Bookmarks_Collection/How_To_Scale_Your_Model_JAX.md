# How to Scale Your Model
**Source URL:** https://jax-ml.github.io/scaling-book/
**Date Fetched:** 2026-04-12

## Overview

This comprehensive book, published February 4, 2025, by Jacob Austin and ten co-authors at Google DeepMind, demystifies large language model scaling across hardware systems.

## Core Purpose

The authors state the book aims to help readers understand "how TPUs (and GPUs) work and how they communicate with each other, how LLMs run on real hardware." The resource targets researchers who need practical knowledge about efficiently deploying massive models.

## Key Topics Covered

The twelve-chapter structure addresses:

- **Foundational concepts**: Roofline analysis, TPU architecture, and matrix operations across distributed systems
- **Transformer mechanics**: Parameter counting, computational requirements for both training and inference
- **Parallelization strategies**: Data, tensor, pipeline, and expert parallelism techniques
- **Practical applications**: Tutorials using LLaMA 3 as a real-world example
- **Implementation guidance**: JAX programming and performance profiling

## Target Audience

Readers should possess baseline familiarity with Transformers and LLMs, though the book builds from foundational concepts. The authors acknowledge this represents essential knowledge for contemporary AI research: "doing cutting-edge research will be inextricably tied to an understanding of how to efficiently scale models."

## Citation Format

For academic reference: Austin et al., "How to Scale Your Model", Google DeepMind, 2025.
