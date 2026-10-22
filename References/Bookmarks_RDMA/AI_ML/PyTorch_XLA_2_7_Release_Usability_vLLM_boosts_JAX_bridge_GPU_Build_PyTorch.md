# PyTorch/XLA 2.7 Release Usability, vLLM boosts, JAX bridge, GPU Build – PyTorch

- **Source:** https://pytorch.org/blog/pytorch-xla-2-7-release-usability-vllm-boosts-jax-bridge-gpu-build/
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

PyTorch/XLA is a Python package that uses the XLA deep learning compiler to enable PyTorch deep learning workloads on various hardware backends, including Google Cloud TPUs, GPUs, and AWS Inferentia/Trainium. The PyTorch/XLA team has been working hard to bring new capabilities to researchers and developers using TPUs/GPUs and XLA backends. In this update, we’ve made many additions and improvements to the framework. Some of the notable highlights are:

- Usability improvements

- Experimental bridge with JAX operations

- A new Pallas-based kernel for ragged paged attention, enabling further optimizations on [vLLM TPU](https://docs.vllm.ai/en/v0.5.5/getting_started/tpu-installation.html)

These features, bug fixes, and other details are outlined in the [release notes](https://github.com/pytorch/xla/releases). Let’s now delve into the highlights in detail!

## Usability Improvements

Developers are now able to better target areas of code that they want to measure the performance of by marking the exact regions of code that they would like to profile. An example of this is:

server = xp.start\_server(8001)
xp.start\_trace(profiling\_dir)
# Run some computation
...
xp.stop\_trace()

PyTorch/XLA 2.7 also introduces an API to query the number of cached compilation graphs, aiding in the detection of unexpected compilations during production inference or training. An additional enhancement optimizes host-to-device transfers by avoiding unnecessary tensor copying, thus improving performance.

## JAX Bridge in PyTorch/XLA (Prototype)

We’re experimenting with integrating **JAX operations directly into PyTorch/XLA graphs** as a way to enable a bridge between the frameworks — this method enables users to call JAX functions inside PyTorch models running with XLA.

As a use case, we’ve explored calling \`jax.experimental.shard\_alike\` from PyTorch/XLA. This function improves sharding propagation in certain code patterns like scan, and we’ve integrated it as part of the GSPMD (Generalized SPMD) workflow in the compiler. This tool is utilized in [torchprime](https://github.com/AI-Hypercomputer/torchprime) to enable support for the [SplashAttention Pallas kernel](https://github.com/AI-Hypercomputer/torchprime/blob/b123c0cc157c28f32a0f6588f19e2d352d2a3617/torchprime/torch_xla_models/experimental/custom_kernel.py).

import torch\_xla.core.xla\_builder as xb
# Native function written in JAX
def jax\_function(...):
  import jax
  ...
  return ...
res = xb.call\_jax(...) \</pre?

## **Ragged Paged Attention Pallas Kernel**

Efficient attention for variable-length sequences is critical for scaling large language models, and the new **Pallas kernel for ragged paged attention** brings a major performance and usability upgrade to [vLLM TPU](https://docs.vllm.ai/en/v0.5.5/getting_started/tpu-installation.html).

This update introduces a custom kernel implemented using the [**Pallas**](https://docs.jax.dev/en/latest/pallas/index.html) custom kernel language and is lowered to Mosaic for TPU. It supports **ragged (variable-length)** input sequences and implements a **paged attention** pattern. Below are the key features:

- Supports mixed prefill and decode operations to increase inference throughput (e.g., up to a 5x speedup compared to the padded Multi-Queries Paged Attention implementation for llama-3-8b).
- No GMM (Grouped Matmul) Metadata required! We calculate the metadata on the fly in the kernel. This can increase performance by 10%.
- Provides a CUDA Flash Attention equivalent with Paged Attention support and a similar interface.

We are continuously collaborating with the **vLLM community** to further optimize performance, expand kernel coverage, and streamline TPU inference at scale.

## **GPU Build is Back**

The GPU build was paused in the PyTorch/XLA 2.6 release, but we’ve now re-enabled **GPU Continuous Integration (CI)** in version 2.7. The current release includes GPU builds with **CUDA 12.6**, marking an important step forward for GPU support.

While CUDA support is still considered **experimental** in this release, we plan to expand coverage to additional CUDA versions in upcoming releases.

## **Get Involved**

Please check out the latest changes on [GitHub](https://github.com/pytorch/xla). As always, we’re actively seeking feedback and contributions from the community.