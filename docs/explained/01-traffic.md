# 1. What moves: network and storage

[← back to the README section](../../README.md#1-what-moves-network-and-storage)

![How the KV cache works](../media/01_kvcache.gif)

![KV traffic and spill](../media/01_traffic.gif)

Section 0 explains what the KV cache is and why it can be moved at all. The rest derives every number in the animations from the model shape and the link rate, so each one can be checked by hand. It covers the KV size per token, the per-request total, the wire time (with and without RoCE packet overhead), how much of it fits in GPU memory, and when spilling to NVMe is cheaper than recomputing.

---

## 0. How the KV cache works

**Attention, one step.** At each layer a token $`i`$ has three vectors made from its hidden state $`x_i`$: a query $`q_i = W_Q x_i`$, a key $`k_i = W_K x_i`$ and a value $`v_i = W_V x_i`$. When token $`t`$ is generated, its output at that layer is

```math
s_i = \frac{\langle q_t, k_i \rangle}{\sqrt{d}}, \qquad \alpha_i = \frac{e^{s_i}}{\sum_{j \le t} e^{s_j}}, \qquad o_t = \sum_{i \le t} \alpha_i\, v_i \qquad (i = 1, \dots, t).
```

The scores say how much each earlier token matters to this one; the weights $`\alpha_i`$ are positive and sum to 1; the output is a weighted average of the values. In the animation the new query is closest to the key of "cat", so "cat" gets weight 0.85.

**Claim: caching K and V is exact, not an approximation.** Once $`k_i`$ and $`v_i`$ are computed, later tokens never change them.

*Proof.* By induction over layers. At the first layer, $`x_i`$ is the embedding of token $`i`$, which depends only on token $`i`$. Suppose that at layer $`\ell`$ every $`x_i`$ depends only on tokens $`1..i`$. Then $`k_i`$, $`v_i`$ and $`q_i`$ depend only on tokens $`1..i`$. The causal mask restricts the sum for $`o_i`$ to $`j \le i`$, so $`o_i`$ also depends only on tokens $`1..i`$. The residual add, the normalization and the MLP act on each position separately, so the layer-$`\ell{+}1`$ input $`x_i`$ depends only on tokens $`1..i`$ as well. So no later token can change $`k_i`$ or $`v_i`$ at any layer. $`\square`$

That is why the cache can be computed on one server and used on another: it is a pure function of the prompt and the weights.

**What the cache saves.** Without it, step $`t`$ recomputes $`k_i, v_i`$ for all $`t`$ tokens, so generating $`T`$ tokens costs $`\sum_{t=1}^{T} t = T(T+1)/2`$ projections per layer. With it, each token's $`k, v`$ is computed once: $`T`$ projections. The attention sum itself still touches all $`t`$ cached rows at every step.

**Why decode is limited by memory bandwidth.** Per decode step, per layer, with $`h_q`$ query heads sharing $`h_{kv}`$ KV heads (group size $`g = h_q/h_{kv}`$) and $`s`$ bytes per element:

```math
\text{FLOPs} \approx \underbrace{2td}_{q\cdot k} + \underbrace{2td}_{\alpha \cdot v} \text{ per query head} = 4\,t\,d\,h_q, \qquad \text{bytes read} = 2\,t\,h_{kv}\,d\,s, \qquad \frac{\text{FLOPs}}{\text{byte}} = \frac{2g}{s}.
```

In bf16 that is $`g`$ FLOPs per byte, independent of the context length. GPUs can do far more arithmetic per byte of memory traffic than that, so decode waits on reading the cache. Prefill processes the whole prompt in one pass, reuses each loaded K and V across many queries, and is limited by arithmetic instead. Different bottlenecks are the reason to run the two phases on different servers, and then the cache has to cross the network (§1 onward).

**Paged blocks.** vLLM stores the cache in fixed-size blocks of $`B`$ tokens ($`B = 16`$ is the usual CUDA default and what the tests here use) and keeps a per-request block table from logical block number to physical block, like page tables in virtual memory. A request of $`T`$ tokens uses $`\lceil T/B \rceil`$ blocks per layer, and only the last one can be partly empty, so the memory wasted per request is under $`B`$ tokens' worth: at most $`15 \times 80\text{ KiB} = 1200\text{ KiB}`$ for Granite 3.3-2B. Blocks do not need to be contiguous, which is why the connector gathers a request's blocks (`kv_layout.take_blocks`) before sending and scatters them on arrival (README section 7).

## 1. How big is the KV cache?

In each attention layer, every token produces one key vector and one value vector per **KV head**. With grouped-query attention several query heads share one KV head, so the count that matters is the number of KV heads $`h_{kv}`$, not the number of query heads.

```math
\text{bytes per token per layer} = \underbrace{2}_{K \text{ and } V} \times h_{kv} \times d_{\text{head}} \times \underbrace{s}_{\text{bytes per element}} .
```

For Granite 3.3-2B (`config.json`: 40 layers, 8 KV heads, head_dim 64; bf16 so $`s = 2`$):

```math
2 \times 8 \times 64 \times 2 = 2048 \text{ B} = 2 \text{ KiB per token per layer.}
```

Per token across all layers: $`2 \text{ KiB} \times 40 = 80 \text{ KiB}`$.

For a prompt of $`T`$ tokens:

| | formula | $`T = 2048`$ |
|---|---|---|
| one layer | $`2\text{ KiB} \times T`$ | 4 MiB |
| whole request | $`80\text{ KiB} \times T`$ | 160 MiB |

## 2. How long does it take on the wire?

**Payload only.** 160 MiB is $`160 \times 2^{20} \times 8 = 1{,}342{,}177{,}280`$ bits. At $`10^{10}`$ bit/s that is **134.2 ms**. That is a lower bound: no protocol could do better on this link.

**With RoCEv2 packet overhead.** Each RoCEv2 packet carries, besides payload: Ethernet header 14 B + FCS 4 B, preamble and start delimiter 8 B, inter-frame gap 12 B, IPv4 20 B, UDP 8 B, InfiniBand base transport header 12 B, invariant CRC 4 B. That is 82 B per packet (plus a 16 B RDMA extended header on the first packet of each write). With path MTU $`P`$ the efficiency is $`P/(P + 82)`$:

| RoCE path MTU | efficiency | 160 MiB takes |
|---|---|---|
| 4096 B (jumbo Ethernet frames) | 98.0% | 137 ms |
| 1024 B (default 1500 B Ethernet MTU) | 92.6% | 145 ms |

So most of the per-request transfer time is unavoidable serialization; the protocol adds a few percent. The open question is not the bulk transfer time but what *else* is stuck behind it (section 2 of the README).

## 3. What else is on the link at the same time

While one request's 160 MiB streams, other requests are still running, and they need small messages:

| message | typical size | source |
|---|---|---|
| connector `__done__` marker | under 100 B | `wait_for_save` |
| flow-control credit | 8 B | `FabricBlobChannel` (section 5) |
| token ids, scheduler metadata | tens of bytes | the serving loop |
| decode KV delta | $`2\text{ KiB} \times b \times L`$ for $`b`$ new tokens | per decode step |

The ratio is the problem: a 4 MiB layer is $`2^{19}`$ times larger than an 8-byte credit. With one FIFO queue (README section 2), every small message pays for the bulk in front of it.

## 4. Does it fit in GPU memory?

On the decode server, vLLM reserves a fraction $`g`$ of GPU memory (`--gpu-memory-utilization`), puts the weights in it, and uses the rest for KV blocks. With $`M`$ bytes of GPU memory and $`W`$ bytes of weights, the KV budget is $`gM - W`$ (minus activation workspace, ignored here). The number of 2,048-token requests whose KV fits at once is

```math
N_{\max} = \left\lfloor \frac{gM - W}{160 \text{ MiB}} \right\rfloor .
```

Example with stated assumptions: a 24 GB card, $`g = 0.85`$, and roughly 5 GB of bf16 weights gives $`(20.4 - 5)\text{ GB} / 160\text{ MiB} \approx 91`$ concurrent requests at 2K tokens. Double the context and it halves. Once the budget is full, vLLM has to evict something.

## 5. When spilling to NVMe beats recomputing

Evicted KV can be dropped (recompute it later with another prefill) or written to NVMe (read it back later). Per layer of a 2K-token request (4 MiB):

- **Read back** costs about $`4 \text{ MiB} / R_{\text{read}}`$. With the measured NVMe read rate on server 2 (1.7 to 2.2 GB/s, README section 12) that is about 2 ms.
- **Recompute** costs one layer of prefill for 2,048 tokens. That is roughly $`2 \times P_{\text{layer}} \times T`$ FLOPs, where $`P_{\text{layer}}`$ is the layer's parameter count, plus attention, which grows with $`T^2`$. It depends on the GPU, so it has to be measured, not assumed.

So spilling pays off when $`\text{bytes}/R_{\text{read}} < t_{\text{recompute}}`$. Recompute cost grows faster than linearly with context, while read-back grows linearly, so long prompts favor spilling. Where the crossover sits on our hardware is something the storage experiments measure (notebook 07), not something this page claims.

## 6. Status

| Number | Kind |
|---|---|
| 2 KiB per token per layer, 160 MiB per 2K request | arithmetic from the model config |
| 134 ms, 137 ms, 145 ms | arithmetic from line rate and header sizes |
| 91 concurrent requests | arithmetic with an assumed weight size |
| NVMe read 1.7–2.2 GB/s | measured (server 2) |
| Recompute vs spill crossover | not measured yet |

## References

1. W. Kwon, Z. Li, S. Zhuang, Y. Sheng, L. Zheng, C. H. Yu, J. E. Gonzalez, H. Zhang, I. Stoica. "Efficient Memory Management for Large Language Model Serving with PagedAttention." *Proc. 29th ACM Symposium on Operating Systems Principles (SOSP)*, 2023. [arXiv:2309.06180](https://arxiv.org/abs/2309.06180). *Used for: paged KV blocks, block tables and the last-block waste bound (§0), and how vLLM budgets GPU memory for KV (§4).*
2. IBM. *granite-3.3-2b-instruct* model card and `config.json` (40 layers, 8 KV heads, head_dim 64). [huggingface.co/ibm-granite/granite-3.3-2b-instruct](https://huggingface.co/ibm-granite/granite-3.3-2b-instruct). *Used for: the KV shape (§1).*
3. InfiniBand Trade Association. *Supplement to InfiniBand Architecture Specification Volume 1, Release 1.2.1, Annex A17: RoCEv2*, 2014. [infinibandta.org](https://www.infinibandta.org/ibta-specification/). *Used for: RoCEv2 encapsulation (IP/UDP + BTH + ICRC) in §2.*
4. IEEE. *IEEE Std 802.3-2022, IEEE Standard for Ethernet*: Clause 3 (MAC frame: header, FCS) and Clause 4 (preamble, start delimiter, inter-packet gap). *Used for: the 38 B of Ethernet framing per packet in §2.*
5. Update 6 (`Updates/Update6-StorageTier/`) and `benchmarks/results/test_arch/chimera_storage_spill.json`. *Used for: the measured NVMe read rates in §5.*

6. A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, L. Jones, A. N. Gomez, Ł. Kaiser, I. Polosukhin. "Attention Is All You Need." *Advances in Neural Information Processing Systems 30 (NeurIPS)*, 2017. [arXiv:1706.03762](https://arxiv.org/abs/1706.03762). *Used for: scaled dot-product attention and the causal mask (§0).*
7. J. Ainslie, J. Lee-Thorp, M. de Jong, Y. Zemlyanskiy, F. Lebrón, S. Sanghai. "GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints." *Proc. EMNLP*, 2023. [arXiv:2305.13245](https://arxiv.org/abs/2305.13245). *Used for: query heads sharing KV heads (§0, §1).*
8. R. Pope, S. Douglas, A. Chowdhery, J. Devlin, J. Bradbury, A. Levskaya, J. Heek, K. Xiao, S. Agrawal, J. Dean. "Efficiently Scaling Transformer Inference." *Proc. MLSys*, 2023. [arXiv:2211.05102](https://arxiv.org/abs/2211.05102). *Used for: decode being memory-bandwidth-bound and prefill compute-bound (§0).*
9. P. Patel, E. Choukse, C. Zhang, A. Shah, Í. Goiri, S. Maleki, R. Bianchini. "Splitwise: Efficient Generative LLM Inference Using Phase Splitting." *Proc. ISCA*, 2024. [arXiv:2311.18677](https://arxiv.org/abs/2311.18677). *Used for: running prefill and decode on different machines (§0).*
