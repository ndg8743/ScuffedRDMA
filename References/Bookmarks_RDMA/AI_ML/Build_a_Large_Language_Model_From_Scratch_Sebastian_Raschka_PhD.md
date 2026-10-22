# Build a Large Language Model (From Scratch) | Sebastian Raschka, PhD

- **Source:** https://sebastianraschka.com/llms-from-scratch/
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

# Build a Large Language Model (From Scratch)

Book companion hub

If you want to understand LLMs beyond API calls, the best way is to
        build one from the ground up. *Build a Large Language Model (From Scratch)* walks
        through text embedding, attention, GPT-style model architecture components, pretraining, and
        finetuning in Python and PyTorch.

Also: [Amazon book](https://amzn.to/4fqvn0D) · [Manning course](https://www.manning.com/livevideo/master-and-build-large-language-models)

## Study Guide

### Start with the chapter

Read the chapter first so the implementation has context. I recommend doing a first read-through pass without coding at first.

[Open book page](https://mng.bz/M96o)

### Use video as an optional second pass

Use the video course after reading if you want the same implementation ideas explained in a different format.

[Open video playlist](https://www.youtube.com/playlist?list=PLTKMiZHVd_2IIEsoJrWACkIxLRdfMlw11)

### Build alongside the book chapter

Retype and run the code after reading each chapter for the best (but most time-intensive) learning experience. Otherwise, execute the notebooks cell by cell and edit small parts when you want to explore an idea. (I have some more tips on reading books [here](/blog/2025/reading-books.html), if you are interested)

[Open code repository](https://github.com/rasbt/LLMs-from-scratch)

### Use the exercises as the check

Try the exercises at the end of each chapter before looking at the solutions. The exercises help self-check whether you understood the chapter implementation.

## Feedback

See [book page](/books/#build-a-large-language-model-from-scratch) for more testimonials.

"If you want to become a top-tier ML / AI Engineer, you need to understand what's going on under the hood."


"I got a serious closeup look at what goes on inside an LLM."


"This is the best technical book I have ever studied by a large margin."


"Ultimate hands on guide to build foundational models. This is the book you want to buy if you want to go deep."


## Chapter Map

| Chapter 1 | High-level orientation to LLMs and the model-building path. | [Open Chapter 1 code](https://github.com/rasbt/LLMs-from-scratch/tree/main/ch01) | 
| Chapter 2 | Text data, text embedding, byte pair encoding, and input-target construction. | [Open Chapter 2 code](https://github.com/rasbt/LLMs-from-scratch/tree/main/ch02) | 
| Chapter 3 | Self-attention, causal attention, multi-head attention, and transformer blocks. | [Open Chapter 3 code](https://github.com/rasbt/LLMs-from-scratch/tree/main/ch03) | 
| Chapter 4 | GPT model implementation plus modern architecture concept guides. | [Open local concept guides](/llms-from-scratch/ch04/) | 
| Chapter 5 | Pretraining, loss functions, text generation, sampling, and model loading. | [Open Chapter 5 code](https://github.com/rasbt/LLMs-from-scratch/tree/main/ch05) | 
| Chapter 6 | Classification finetuning and using a pretrained LLM for a supervised task. | [Open Chapter 6 code](https://github.com/rasbt/LLMs-from-scratch/tree/main/ch06) | 
| Chapter 7 | Instruction finetuning, prompt formatting, and instruction-following behavior. | [Open Chapter 7 code](https://github.com/rasbt/LLMs-from-scratch/tree/main/ch07) | 
| Appendix A | Introduction to PyTorch, including notebook code and distributed training notes. | [Open Appendix A code](https://github.com/rasbt/LLMs-from-scratch/tree/main/appendix-A) | 
| Appendix B | References and further reading for the main chapters. | [Open Appendix B resources](https://github.com/rasbt/LLMs-from-scratch/tree/main/appendix-B) | 
| Appendix C | Exercise solutions for checking the chapter implementations. | [Open Appendix C solutions](https://github.com/rasbt/LLMs-from-scratch/tree/main/appendix-C) | 
| Appendix D | Training-loop additions such as learning-rate schedules and other practical refinements. | [Open Appendix D code](https://github.com/rasbt/LLMs-from-scratch/tree/main/appendix-D) | 
| Appendix E | Parameter-efficient finetuning with LoRA. | [Open Appendix E code](https://github.com/rasbt/LLMs-from-scratch/tree/main/appendix-E) | 

## Architecture Concept Guides

The book covers the core implementation path through text embedding, attention,
      GPT-style model architecture components, pretraining, and finetuning. The concept guides below are
      advanced follow-up material for connecting those basics to current model
      architectures, memory use, and serving tradeoffs. **They are best read
      after completing the book.**

### A Visual Guide to Attention Variants in Modern LLMs

Use this article for a visual pass through MHA, MQA, GQA, MLA, sparse attention, sliding-window attention, and hybrid designs.

[Read the article](https://magazine.sebastianraschka.com/p/visual-attention-variants)

### MoE and SwiGLU

Use these guides to connect sparse expert routing and gated feed-forward layers to model capacity and inference cost.

[Open MoE explainer](/llm-architecture-gallery/moe/)

### The Big LLM Architecture Comparison

Use this guide to compare current decoder-style LLM architectures, including normalization, position handling, attention choices, and MoE layers.

[Read the guide](https://magazine.sebastianraschka.com/p/the-big-llm-architecture-comparison)

## Related From-Scratch Articles

These articles are optional follow-up reads for specific implementation details.
      **They are best read after completing the book.**

### Self-Attention from Scratch

A compact standalone implementation of the core mechanism behind transformer LLMs.

[Read the article](/blog/2023/self-attention-from-scratch.html)

### BPE Tokenizer from Scratch

A practical implementation of byte pair encoding, one of the first pieces to understand before LLM training.

[Read the article](/blog/2025/bpe-from-scratch.html)

### KV Cache from Scratch

A focused explanation of the inference cache that makes autoregressive generation efficient.

[Read the article](https://magazine.sebastianraschka.com/p/coding-the-kv-cache-in-llms)

### Qwen from Scratch

A bridge from the book's baseline implementation to a modern open-weight model family.

[Read the article](https://magazine.sebastianraschka.com/p/qwen3-from-scratch)

### LoRA and DoRA from Scratch

A code-oriented path into parameter-efficient adaptation after you understand the base model.

[Read the article](https://magazine.sebastianraschka.com/p/lora-and-dora-from-scratch)

### LLM Evaluation from Scratch

Benchmarks, verifiers, leaderboards, and LLM judges as practical tools for checking model behavior.

[Read the article](https://magazine.sebastianraschka.com/p/llm-evaluation-4-approaches)

## Where to Go Next

After finishing the book, these are the next places I would go. Continue with reasoning methods, or use the gallery to compare current model architectures more broadly.

### Build a Reasoning Model (From Scratch)

Continue here after the LLM basics if you want inference-time scaling, reinforcement learning, and distillation.

[Open reasoning hub](/reasoning-from-scratch/)

### LLM Architecture Gallery

Compare architecture figures, attention mechanisms, decoder types, and implementation links across model families.

[Open gallery](/llm-architecture-gallery/)