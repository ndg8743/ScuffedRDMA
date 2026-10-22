# NVIDIA TensorRT Model Optimizer - vLLM

- **Source:** https://docs.vllm.ai/en/v0.11.0/features/quantization/modelopt.html
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

# NVIDIA TensorRT Model Optimizer[¶](#nvidia-tensorrt-model-optimizer)

The [NVIDIA TensorRT Model Optimizer](https://github.com/NVIDIA/TensorRT-Model-Optimizer) is a library designed to optimize models for inference with NVIDIA GPUs. It includes tools for Post-Training Quantization (PTQ) and Quantization Aware Training (QAT) of Large Language Models (LLMs), Vision Language Models (VLMs), and diffusion models.

We recommend installing the library with:

## Quantizing HuggingFace Models with PTQ[¶](#quantizing-huggingface-models-with-ptq)

You can quantize HuggingFace models using the example scripts provided in the TensorRT Model Optimizer repository. The primary script for LLM PTQ is typically found within the `examples/llm_ptq` directory.

Below is an example showing how to quantize a model using modelopt's PTQ API:

## Code

After the model is quantized, you can export it to a quantized checkpoint using the export API:

The quantized checkpoint can then be deployed with vLLM. As an example, the following code shows how to deploy `nvidia/Llama-3.1-8B-Instruct-FP8`, which is the FP8 quantized checkpoint derived from `meta-llama/Llama-3.1-8B-Instruct`, using vLLM:

## Code