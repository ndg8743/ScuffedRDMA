# KV Cache Compression and Its Infra Problems

- **Source:** https://research.nvidia.com/labs/eai/blogs/kv-cache-compression-and-its-infra-problems/
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

# KV Cache Compression and Its Infra Problems

Consider serving OpenClaw on a local GPU with a capable reasoning model. The agent picks up a simple task — read a handful of documents, write a weekly report — and crashes halfway through. Not because the task is hard, but because the GPU ran out of memory.

This blog examines KV cache compression through an infrastructure lens: not only what the algorithms do, but whether they can actually run in production. An entire field is devoted to compressing the KV cache so that long inference fits in GPU memory; most of it works in the lab, much less in real deployment. The gap comes down to two infrastructure problems that papers almost never discuss. This post surveys the field's main ideas, traces where they collide with these problems, and shows how a geometric property hidden beneath RoPE has recently been used to resolve both.

**two collisions with production infrastructure**. Existing methods need

**historical attention scores**, but the

**FlashAttention kernel never writes those scores**into GPU memory. And paged attention reclaims memory only when

**a block holds no KV at all**— yet after token eviction the survivors leave almost every block partially occupied, so the

**"freed" memory never actually comes back**.

## 1. Background: The KV Cache and Memory Exhaustion in Long Inference

When a Transformer generates a token, it computes a *query*, a *key*, and a *value* vector; the new query attends over all previous keys and values to read the model's own history. The KV cache is what makes this affordable: each token's K and V are computed once and saved, and every later step reuses them instead of recomputing — O(n) work per step instead of O(n²). But nothing ever shrinks it: every generated token appends new K and V rows across all layers and heads.

The arithmetic ends badly. Qwen3-32B with 4-bit quantized weights — a configuration people actually deploy — crashes with an out-of-memory error on a 24 GB GPU after roughly 24,000 generated tokens, short of the 32K-token traces reasoning models routinely produce on hard problems (Figure 1).

Compression is possible because attention is sparse. A small fraction of tokens collect the overwhelming majority of attention weight; a token that never gets attended to could, in principle, be deleted from the cache without changing the model's outputs. The question is: which tokens are safe to delete, and when?

## 2. The Existing Methods — and Two Infrastructure Problems

The field launched in 2023 from one observation: attention is highly non-uniform. Models devote a disproportionate share of attention weight to the very first tokens — "attention sinks," not semantically important but always present (StreamingLLM [\[2\]](#ref-2)) — while roughly 20% of tokens collect 80% of the total weight, "heavy hitters" that tend to stay important over time (H2O [\[3\]](#ref-3); Scissorhands [\[4\]](#ref-4)). The standard recipe followed (Figure 2): always keep the sinks, always keep a sliding window of recent tokens, and keep a budget of heavy hitters from the middle. On long-document tasks — question answering, summarization, code retrieval — the recipe works well.

The recipe leaves its key question open: how does a method know which middle tokens are the heavy hitters? The answer that defines the largest category of compression methods is to read the model's own **historical attention scores**. Every decode step computes attention over the whole history anyway, and those scores are a running record of which cached tokens the model actually uses. H2O [\[3\]](#ref-3) is the canonical example: it maintains, for every cached token, a cumulative sum of the attention that token has received across all decode steps so far, and after each step it evicts the lowest-scoring token to hold the cache at a fixed budget (Figure 3).

SnapKV [\[6\]](#ref-6) is the most influential refinement of the same idea. Instead of accumulating scores continuously, it scores once (Figure 4): the most recent W tokens of the prompt form an "observation window," and the attention they pay to the full history decides — at the end of prefill, once and for all — which tokens stay. This removes the per-step bookkeeping and avoids cumulative scoring's bias toward tokens that have simply been around longer. The category has many further variants on the same ingredients: Scissorhands [\[4\]](#ref-4) and TOVA [\[5\]](#ref-5) swap the decode-time scoring signal; PyramidKV [\[7\]](#ref-7) and Ada-KV [\[8\]](#ref-8) split the one-shot budget per layer and per head.

But the observation window cannot be made large. Because RoPE — the rotation that encodes each token's position into its query vector — orients every query by its position, only the most recent queries, empirically about 25, reflect where the model is actually attending. So any piece of information that draws no attention during one phase of the reasoning process gets evicted — even if later reasoning depends on it.

This entire category — whether it scores continuously like H2O or once like SnapKV — rests on observing attention scores; among the methods above, only StreamingLLM's fixed sink-plus-recency rule needs none. That shared requirement, not the quality of any particular heuristic, collides with production infrastructure in two ways.

**Infrastructure Problem 1: FlashAttention does not expose attention scores.**Production inference runs on FlashAttention, which tiles the attention computation through SRAM (the GPU's small, fast on-chip memory) and never materializes the N×N score matrix in HBM (the GPU's main memory). That is what makes it fast — and it means the scores eviction methods want to observe are never written anywhere compression code can read them. This hits hardest where the method needs the

**full attention history**. H2O-style cumulative scoring requires the attention scores of

**every decode step**— the running sums cannot be updated without observing each step's scores as they are computed. The reference H2O implementation resolves the conflict by

**falling back to eager attention**,

**materializing the full score matrix**and

**abandoning FlashAttention**outright.

**Infrastructure Problem 2: Repeated token eviction cannot actually free GPU memory in production systems.**Production serving systems like vLLM manage the KV cache with

*paged attention*: GPU memory is divided into fixed-size physical blocks, each holding KV data for about 16 tokens, and a block can be freed only when it is completely empty. Repeated decode-time eviction

**scatters survivors across blocks**(Figure 5). Evicting 14,400 of 16,000 tokens leaves 1,600 survivors spread over the roughly 1,000 blocks originally allocated;

**almost every block keeps at least one survivor**, so the

**allocator reclaims almost nothing**. R-KV

[\[10\]](#ref-10)— the strongest prior evictor designed specifically for reasoning models — reports 90% memory savings, but those savings were measured with

**pre-allocated contiguous tensors, not in vLLM**, and its own Appendix D acknowledges that integrating with paged attention "presents a non-trivial challenge and may require further investigation." Quest

[\[9\]](#ref-9)sidesteps the block-reclamation problem by

**keeping the full cache**and only selecting which pages each query reads, so

**KV memory still grows with context length**.

## 3. A System Solution to the Two Infrastructure Problems

The way out starts from a different question. Instead of "which tokens received high attention recently?", ask: "does the geometry of the model's learned representation space predict that a token will be important?" The distinction changes what information a method needs at runtime — and therefore what infrastructure it requires. TriAttention [\[1\]](#ref-1) is the method built on this question.

### Solution to Problem 1: No Attention Scores Needed — Pre-RoPE Geometry

TriAttention's answer to Problem 1 is to never need attention scores in the first place. It decides which KV entries to keep from the geometry of the model's learned representation space — no attention score is ever observed at runtime, so the records FlashAttention refuses to write are records the method never asks for. Problem 1 is not worked around; it simply does not apply.

The mechanism rests on a stable geometric property of the model's learned Q/K vectors — Figure 6 walks through it step by step.

### Solution to Problem 2: Forward-Packing Compaction

A score by itself frees nothing. In paged memory, a block can only be returned to the allocator once *every* slot in it is dead — eviction scores merely mark tokens, so the survivors must be physically consolidated until whole blocks actually empty out. TriAttention runs this consolidation roughly every 128 decoded tokens, and there are two ways to do it. The order-preserving repack (Figure 7) slides every survivor forward so the cache stays in original token order: no extra position bookkeeping, and the changes to an inference engine like vLLM stay minimal. The hole-filling variant (Figure 8) instead drops the newest survivors straight into the slots vacated by eviction: far less data movement per compaction, at the cost of a scrambled physical order that must then be tracked explicitly. Both variants live in the TriAttention codebase (the hole-filling one since v0.1.0) and remain maintained. The two figures below play the same round of decoding through each strategy.

### Results

The table below shows accuracy on competition math, where KV cache compression matters most. For AIME 2024 and AIME 2025 the KV budget is 2,048 tokens — one-sixteenth of what a full 32K-token trace would otherwise cache; for MATH500 it is 512. All methods run at the same budget.

| Method | AIME 2024 | AIME 2025 | MATH 500 | 
|---|---|---|---|
| Full Attention (no compression) | 57.1% | 40.8% | 69.6% | 
| SnapKV [\[6\]](#ref-6) | 34.6% | 20.0% | 49.2% | 
| R-KV [\[10\]](#ref-10) | 25.4% | 17.5% | 46.4% | 
| TriAttention [\[1\]](#ref-1) | **42.1%** | **32.9%** | **56.0%** | 

The accuracy gap is large. At budget 2,048, TriAttention nearly doubles R-KV's AIME 2025 accuracy (32.9% vs. 17.5%). At a slightly larger budget of 3,072 tokens, it matches the full-attention baseline (40.8%) while delivering **2.5× higher throughput** (563 vs. 223 tokens/second) and **10.7× KV memory reduction**. Code is available at [github.com/WeianMao/triattention](https://github.com/WeianMao/triattention).

## 4. KV Cache Infra in Video Generation

The memory pressure of long inference reappears in video generation — at larger scale. A video model's tokens are spatial patches rather than words, and an *autoregressive* generator caches KV entries for every frame produced so far, exactly the way an LLM caches past tokens; within seconds of 480p video, the cache outgrows the model’s own weights [\[11\]](#ref-11). The video community has pursued the same two tracks as text — quantization and token eviction — and it has learned the lesson this blog keeps returning to: the algorithmic idea is half the work, and the demons live in the infrastructure details. Each of the three systems below earns its gains there.

On the quantization track, Quant VideoGen [\[11\]](#ref-11) pushes the cache down to 2 bits per element. The enabler is a property specific to video: adjacent frames are nearly identical, so the cache is full of near-duplicate tokens; grouping those tokens and storing each one’s small residual from its group average instead of full-precision K and V tensors makes the data quantization-friendly, and progressively refining and quantizing the residuals yields up to 7× memory compression — no retraining, and less than 4% latency overhead. LongLive 2.0 [\[13\]](#ref-13) takes the same track to production scale, quantizing both weights and KV cache to NVFP4 (4-bit) on a 5B-parameter generator for **1.84× throughput** at negligible quality cost — and its detail worth dwelling on is the fused **parallel dequantization** kernel (Figure 10). Storing the cache in 4 bits means every block must be dequantized before each attention step, and the naive approach launches one GPU kernel per block. Dequantization, however, is embarrassingly parallel in principle — every 4-bit value can be decoded independently of all the others — and the per-block loop hides that parallelism behind a queue of small sequential launches; the fused kernel instead issues one launch whose threads map one-to-one onto every packed pair of FP4 values across the whole cache window, presenting the entire workload to the GPU at once. In practice, this keeps the overall quantization/dequantization overhead below 2%.

On the eviction track, §3's system solution carries over directly: TriAttention's trigonometric scoring [\[1\]](#ref-1) has been applied to LongLive [\[12\]](#ref-12), a real-time video generator built on Wan2.1-T2V-1.3B. Each KV entry corresponds to spatial patches from one frame, and the scoring decides which frames to evict — no attention scores observed, nothing for the serving stack to fight — cutting the cache by 50% with negligible quality drop; the integration ships in the TriAttention repository.

Both domains are converging on the same insight: good compression is not primarily about finding the right scoring heuristic. It is about understanding why a signal has the structure it has — and exploiting that structure at the kernel level.

## 5. Closing Thoughts

From 2023 to 2025 the field's framing was: find the right heuristic for which tokens matter — heavy hitters, sinks plus recency, observation windows, redundancy. All reasonable hypotheses. But these methods run into two walls. Methods that select tokens by observed attention hit the first: FlashAttention never exposes the scores they need. Methods that evict repeatedly during decode hit the second: eviction frees no GPU memory when the allocator works in whole blocks and the survivors stay scattered. A method that cannot clear the second wall saves compute but not memory — the scarcer resource during long inference.

TriAttention clears both walls by changing the question: score tokens from the model's stable pre-RoPE geometry rather than from observed attention, and physically consolidate survivors into a dense prefix so that tail blocks are actually freed. The result is a method that reduces the physical memory footprint of the KV cache in production paged-attention deployment — and, because pre-RoPE geometry predicts a token's importance at any distance rather than through a \~25-query observation window, sustains accuracy at compression ratios where observation-window methods collapse.

One open question remains. TriAttention uses a uniform KV budget across heads, yet the per-head distance-preference curves it computes already classify heads by behavior — local, sink, range-specific. The natural next step is to allocate budget in proportion to a head's complexity. Whether the pre-RoPE insight generalizes further — to model interpretability, to dynamic sparse attention, to other modalities — is an open problem worth exploring.

## References

1. **TriAttention: Efficient Long Reasoning with Trigonometric KV Compression.** Mao W., Lin X., Huang W., Xie Y., Fu T., Zhuang B., Han S., Chen Y. *ICML*, 2026. [github.com/WeianMao/triattention](https://github.com/WeianMao/triattention)
2. **Efficient Streaming Language Models with Attention Sinks.** Xiao G., Tian Y., Chen B., Han S., Lewis M. *ICLR*, 2024. [arXiv:2309.17453](https://arxiv.org/abs/2309.17453)
3. **H2O: Heavy-Hitter Oracle for Efficient Generative Inference of Large Language Models.** Zhang Z., Sheng Y., Zhou T., Chen T., Zheng L., Cai R., Song Z., Tian Y., Ré C., Barrett C., Wang Z., Chen B. *NeurIPS*, 2023. [arXiv:2306.14048](https://arxiv.org/abs/2306.14048)
4. **Scissorhands: Exploiting the Persistence of Importance Hypothesis for LLM KV Cache Compression at Test Time.** Liu Z., Desai A., Liao F., Wang W., Xie V., Xu Z., Kyrillidis A., Shrivastava A. *NeurIPS*, 2023. [arXiv:2305.17118](https://arxiv.org/abs/2305.17118)
5. **Transformers are Multi-State RNNs.** Oren M., Hassid M., Yarden N., Adi Y., Schwartz R. *EMNLP*, 2024. [arXiv:2401.06104](https://arxiv.org/abs/2401.06104) (TOVA)
6. **SnapKV: LLM Knows What You Are Looking for Before Generation.** Li Y., Huang Y., Yang B., Venkitesh B., Locatelli A., Ye H., Cai T., Lewis P., Chen D. *NeurIPS*, 2024. [arXiv:2404.14469](https://arxiv.org/abs/2404.14469)
7. **PyramidKV: Dynamic KV Cache Compression based on Pyramidal Information Funneling.** Cai Z., Zhang Y., Gao B., Liu Y., Li Y., Liu T., Lu K., Xiong W., Dong Y., Hu J., Xiao W. *arXiv preprint*, 2024. [arXiv:2406.02069](https://arxiv.org/abs/2406.02069)
8. **Ada-KV: Optimizing KV Cache Eviction by Adaptive Budget Allocation for Efficient LLM Inference.** Feng Y., Lv J., Cao Y., Xie X., Zhou S.K. *NeurIPS*, 2025. [arXiv:2407.11550](https://arxiv.org/abs/2407.11550)
9. **Quest: Query-Aware Sparsity for Efficient Long-Context LLM Inference.** Tang J., Zhao Y., Zhu K., Xiao G., Kasikci B., Han S. *ICML*, 2024. [arXiv:2406.10774](https://arxiv.org/abs/2406.10774)
10. **R-KV: Redundancy-aware KV Cache Compression for Reasoning Models.** Cai Z., Xiao W., Sun H., Luo C., Zhang Y., et al. *NeurIPS*, 2025. [arXiv:2505.24133](https://arxiv.org/abs/2505.24133)
11. **Quant VideoGen: Auto-Regressive Long Video Generation via 2-Bit KV-Cache Quantization.** Xi H., Yang S., Zhao Y., Li M., Cai H., et al., Han S., Keutzer K. *ICML*, 2026. [arXiv:2602.02958](https://arxiv.org/abs/2602.02958)
12. **LongLive: Real-time Interactive Long Video Generation.** Yang S., Huang W., Chu R., Xiao Y., Zhao Y., et al., Han S., Chen Y. *ICLR*, 2026. [arXiv:2509.22622](https://arxiv.org/abs/2509.22622)
13. **LongLive 2.0: An NVFP4 Parallel Infrastructure for Long Video Generation.** Chen Y., Wang L., Huang W., Yang S., Zhang B., Xiao Y., Chu R., Mao W., Hu Q., Liu S., Zhao Y., Mao H., Chen Y.-C., Xie E., Qi X., Han S. *arXiv preprint*, 2026. [arXiv:2605.18739](https://arxiv.org/abs/2605.18739)