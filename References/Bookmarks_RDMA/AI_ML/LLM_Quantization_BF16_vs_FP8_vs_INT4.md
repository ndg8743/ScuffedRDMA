# LLM Quantization: BF16 vs FP8 vs INT4

- **Source:** https://research.aimultiple.com/llm-quantization/
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

We benchmarked Qwen3-32B at 4 precision levels (BF16, FP8, GPTQ-Int8, GPTQ-Int4) on a single NVIDIA H100 80GB GPU. Each configuration was evaluated on 2 benchmarks (\~12.2K questions) covering knowledge and code generation, plus 2,000+ inference runs to measure throughput. Int4 is 2.7x faster than BF16 while losing less than 2 points on MMLU-Pro, but code generation (HumanEval) drops 8 points.

## Quantization benchmark results

**MMLU-Pro** tests broad reasoning across 14 domains (\~12K questions, 5-shot). This is the harder version of MMLU with 10-choice questions instead of 4.

**HumanEval** tests code generation (164 problems, pass@1). The model writes Python functions that run against unit tests. This is the only benchmark where the output is executed, not just scored.

**Throughput** is output tokens per second at batch size 1.

**Model size** is GPU memory consumed by weights alone, measured after loading.

### MMLU-Pro breakdown by category

Engineering and law show the largest drops at Int4. Math stays stable across all precisions.

### Memory capacity and concurrency

GPU monitoring tools like nvidia-smi report near-full utilization regardless of model size because vLLM pre-allocates all available memory. The real question is how that memory splits between model weights and KV cache, because KV cache determines how many users you can serve concurrently.

Max users is the memory-bound ceiling before OOM: total token capacity divided by context length per user. This is the theoretical maximum. In practice, scheduling overhead reduces it slightly.

This has direct implications for reasoning models. DeepSeek-R1 and Qwen-QwQ generate thousands of internal “thought” tokens (often 2K-5K) before producing a final answer. On BF16, a single reasoning request could consume the entire 17K token capacity, blocking a second user. On Int4, the 193K capacity fits multiple concurrent reasoning sessions.

## Key findings

### FP8 loses no measurable accuracy

FP8 scores 69.64% on MMLU-Pro vs 70.24% for BF16, a 0.6 point difference across 12,000 questions. On HumanEval, both FP8 and BF16 score identically at 39.02%. FP8 gives you 1.5x throughput and cuts your model size in half for a 0.6 point cost.

GPTQ-Int8 scores 70.32% on MMLU-Pro but drops 1.8 points on HumanEval (37.20%). If code generation matters, FP8 is the safer pick.

### Int4 degrades code generation more than knowledge

MMLU-Pro drops 1.6 points at Int4 (70.24% to 68.66%). HumanEval drops 8 points (39.02% to 31.10%). Code generation requires precise token predictions where small weight errors compound across function bodies.

### The real win is concurrency, not speed

Int4 is 2.7x faster than BF16. But the larger effect is on memory. BF16 leaves only 4.4 GB for KV cache, enough for about 4 concurrent users at 4K context. Int4 frees up 47.3 GB, enough for 47 users, a 12x increase in serving capacity from the same GPU.

### Math scores hold across all precisions

Math scores barely move: 81.87% at BF16, 81.87% at FP8, 81.87% at Int8, 80.24% at Int4. Engineering (49.64% to 43.45%) and law (43.05% to 40.60%) are more sensitive.

[Automate a process](https://aimultiple.com/agentic-enterprise-service)

## Cost per token

Using H100 SXM pricing on RunPod ($2.69/hour) at batch size 1:

These numbers reflect single-user, real-time generation. Batch processing drops the cost further.

## LLM quantization benchmark methodology

### Environment

- **GPU:** Single NVIDIA H100 80GB HBM3 (SXM) via RunPod ($2.69/hr)
- **Software:** vLLM 0.17.0, lm-evaluation-harness 0.4.11, PyTorch 2.8.0, CUDA 12.8, Python 3.11
- **Model:** Qwen3-32B (post-trained/instruction-tuned) from HuggingFace. No fine-tuning applied.

### Accuracy evaluation

- All evaluations run via `lm-evaluation-harness` with `batch_size="auto"`.
- Each task runs in a **separate subprocess**. Model loaded fresh each time, GPU fully cleaned between tasks. This prevents OOM from memory fragmentation.
- HumanEval runs with `HF_ALLOW_CODE_EVAL=1` (code execution enabled).
- MMLU-Pro results include per-category breakdown (biology, math, physics, law, etc.).
- Qwen3’s thinking mode was not active during evaluations. lm-evaluation-harness sends raw formatted prompts without applying the model’s chat template (`apply_chat_template=False` by default), so the `<think>` token is never injected.

### Performance evaluation

- 5 rotating prompts across domains (science, coding, general knowledge)
- 10 warmup iterations (not measured), then 500 measured iterations
- Fixed output: `max_tokens=256, temperature=0.7, top_p=0.9, batch_size=1`
- Metrics: throughput (tokens/sec), GPU memory usage (GB)

### vLLM configuration per precision

All precisions use `gpu_memory_utilization=0.90, max_model_len=4096`.

### Split-process architecture

Each benchmark runs as two separate processes to prevent OOM:

1. **Step 1:** Load model, warmup, benchmark throughput, save to temp file, exit.
2. **Cleanup:** Force-kill vLLM and Ray processes, wait 10 seconds.
3. **Step 2:** Load model fresh, run each eval task in a separate subprocess, merge with step 1 metrics, save final JSON.

### Controlled variables

To eliminate external factors, the following parameters were fixed across all runs:

### Test prompts

The 5 test prompts:

1. “Explain the theory of relativity in simple terms.” (Science/Abstract)
2. “Write a Python function to find the longest palindromic substring.” (Coding)
3. “What are the main causes of climate change and their effects?” (Complex Reasoning)
4. “Describe the process of photosynthesis step by step.” (Process Description)
5. “How does a neural network learn from data?” (Technical Explanation)

### Data verification: vLLM runtime telemetry

The memory and concurrency figures in this article were derived directly from [vLLM engine initialization](https://aimultiple.com/inference-engines) logs during benchmark execution.

**BF16 initialization:**

**GPTQ-Int4 initialization:**

[Add as preferred source](https://www.google.com/preferences/source?q=aimultiple.com)

## Limitations

All tests use batch size 1. In [high-throughput scenarios](https://aimultiple.com/gpu-benchmark), the performance gap between Int4 and BF16 widens because memory bandwidth saturation becomes the dominant bottleneck.

Results are specific to the H100 SXM. Older GPUs (A100, A10) lack native FP8 support. Consumer GPUs (RTX 4090) have different memory bandwidth characteristics.

The GPTQ models (JunHowie) are community-provided quantizations. Official releases may use different calibration datasets or parameters, which can affect accuracy.

We tested GPTQ only. Other quantization methods (AWQ, BitsAndBytes NF4, GGUF, HQQ) might offer different trade-offs.

## Conclusion

For Qwen3-32B on an H100, FP8 is the default choice. You get 1.5x the throughput, half the memory footprint, and a 0.6 point accuracy cost.

Int4 makes sense when you need maximum throughput or concurrency: 2.7x speed, 12x concurrency, at the cost of 1.6 points on MMLU-Pro and 8 points on HumanEval.

Int8 sits in the middle and does not offer a clear advantage over FP8 in this setup. The throughput gain over FP8 is small (43.3 vs 37.9 tok/s) and the accuracy is comparable. FP8 is simpler because it is officially provided by the model authors and does not require a third-party quantized checkpoint.

The biggest practical impact of quantization is not speed, it is concurrency. BF16 can serve 4 users at 4K context on a single H100. Int4 can serve 47. At $2.69/hr, that brings cost per 1M tokens from $28.73 down to $10.69.

## Cite this benchmark

Pick the format that matches where you're publishing. Pasting the link version into your CMS preserves the backlink.

```
@misc{sari2026,
  author = {Sarı, Ekrem and Ermut, Sıla},
  title  = {{LLM Quantization: BF16 vs FP8 vs INT4}},
  year   = {2026},
  month  = mar,
  howpublished    = {\url{https://aimultiple.com/llm-quantization}},
  note   = {AIMultiple. Retrieved March 17, 2026}
}
```
Results and timestamps of 62 data points. Download the summary data shown in this article's charts and tables as a ZIP file containing 13 CSV files.

[Download](https://cdn.aimultiple.com/benchmark_data/article5_llm-quantization_data.zip?v=1792257187)

Want the granular data behind it? [Join Premium](https://aimultiple.com/premium)

## Changelog

2 updates
1. Updated the introduction with new benchmark results and model configurations.
2. Added HumanEval to the accuracy evaluation in the methodology section.

[View Full Profile](https://aimultiple.com/author/ekrem-sari)

She previously worked as a recruiter in project management and consulting firms. Sıla holds a Master of Science degree in Social Psychology and a Bachelor of Arts degree in International Relations.

[View Full Profile](https://aimultiple.com/author/sila-ermut)

## Be the first to comment

Your email address will not be published. All fields are required. Comments are left in their original language.