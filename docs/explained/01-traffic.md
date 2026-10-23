# 1. What moves: network and storage

[← back to the README section](../../README.md#1-what-moves-network-and-storage)

![KV traffic and spill](../media/01_traffic.gif)

This page derives every number in the animation from the model shape and the link rate, so each one can be checked by hand. It covers the KV size per token, the per-request total, the wire time (with and without RoCE packet overhead), how much of it fits in GPU memory, and when spilling to NVMe is cheaper than recomputing.

---

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

1. W. Kwon, Z. Li, S. Zhuang, Y. Sheng, L. Zheng, C. H. Yu, J. E. Gonzalez, H. Zhang, I. Stoica. "Efficient Memory Management for Large Language Model Serving with PagedAttention." *Proc. 29th ACM Symposium on Operating Systems Principles (SOSP)*, 2023. [arXiv:2309.06180](https://arxiv.org/abs/2309.06180). *Used for: paged KV blocks and how vLLM budgets GPU memory for KV (§4).*
2. IBM. *granite-3.3-2b-instruct* model card and `config.json` (40 layers, 8 KV heads, head_dim 64). [huggingface.co/ibm-granite/granite-3.3-2b-instruct](https://huggingface.co/ibm-granite/granite-3.3-2b-instruct). *Used for: the KV shape (§1).*
3. InfiniBand Trade Association. *Supplement to InfiniBand Architecture Specification Volume 1, Release 1.2.1, Annex A17: RoCEv2*, 2014. [infinibandta.org](https://www.infinibandta.org/ibta-specification/). *Used for: RoCEv2 encapsulation (IP/UDP + BTH + ICRC) in §2.*
4. IEEE. *IEEE Std 802.3-2022, IEEE Standard for Ethernet*: Clause 3 (MAC frame: header, FCS) and Clause 4 (preamble, start delimiter, inter-packet gap). *Used for: the 38 B of Ethernet framing per packet in §2.*
5. Update 6 (`Updates/Update6-StorageTier/`) and `benchmarks/results/test_arch/chimera_storage_spill.json`. *Used for: the measured NVMe read rates in §5.*
