# Flash-KMeans - Fast and Memory-Efficient K-Means Clustering

**Source URL:** https://github.com/svg-project/flash-kmeans  
**Date Fetched:** 2026-04-12

## Overview

Flash-KMeans is a GPU-accelerated K-Means implementation using Triton kernels, designed for fast and memory-efficient clustering. The project provides IO-aware batched K-Means clustering implemented with Triton GPU kernels and serves as the official K-Means implementation for Sparse VideoGen2.

## Key Features

**Performance**: Benchmarks on NVIDIA H200 GPUs with FP16 precision demonstrate significant speedups compared to alternatives like fast_pytorch_kmeans and fastkmeans implementations.

**Multi-GPU Support**: Automatically scales across available GPUs when processing large datasets that exceed single-GPU memory capacity.

**Flexible APIs**: Offers both low-level functions and interfaces resembling faiss/sklearn for user convenience.

## Installation & Usage

Installation is straightforward via pip or from source. Basic usage involves importing the clustering function and specifying parameters like number of clusters and convergence tolerance.

## Benchmarking Results

Testing reveals advantages across various configurations with different cluster counts, data point quantities, and batch sizes. The implementation handles datasets scaling from 256K to 268M data points through streaming from CPU memory.

## Citation

The authors request citation of their arXiv paper (2603.09229) on Flash-KMeans and the related Sparse VideoGen2 work (2505.18875) for academic use.
