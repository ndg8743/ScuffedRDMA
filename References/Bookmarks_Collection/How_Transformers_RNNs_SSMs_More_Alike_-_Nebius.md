# How Transformers, RNNs and SSMs are More Alike Than You Think

**Source URL:** https://nebius.com/blog/posts/mixers-are-rnns
**Date accessed:** 2026-03-11

---

**Author:** Stanislav Fedotov
**Published:** August 21, 2024
**Reading Time:** 10 minutes

## Overview

This technical article explores surprising mathematical connections between three major neural network architectures used in large language models: Transformers, Recurrent Neural Networks (RNNs), and State Space Models (SSMs).

## Key Concepts Explained

### Linearized Attention

The article demonstrates how removing the softmax function from standard attention mechanisms creates "linearized attention," which enables recurrent computation. By introducing a kernel function φ, the mechanism becomes: "the complexity of multiplying M on a vector is O(RL) for some constant (and not very large) R."

This approach provides dual benefits: linear inference complexity and parallel training capability, similar to traditional RNNs.

### Masked Self-Attention Mechanics

Standard transformer attention applies an attention mask preventing future token access. The author breaks down this process: multiplying query-key products, normalizing, masking, applying softmax, then combining with values.

### Structured Matrix Multiplication

The article presents a four-step algorithm for efficiently computing attention outputs with special matrix masks. This involves creating 3D tensors from keys and values, then strategically multiplying structured matrices to maintain computational efficiency.

### State Space Models Connection

SSMs represent sequential relationships as: "h_t = A_t h_{t-1} + B_t x_t" and "y_t = C_t h_t + D_t x_t." The breakthrough insight is that semiseparable matrices from SSMs can function as attention masks with O(rL) complexity instead of O(L²).

### State Space Duality

The Mamba 2 paper's central finding reveals masked attention can be rewritten as: "Mu = (G⊗CB)u" where G acts as the mask, C as queries, B as transposed keys, and u as values. This demonstrates SSMs and attention mechanisms are mathematically equivalent under specific conditions.

## Practical Implications

Hybrid architectures like Jamba, Samba, and Griffin combine these insights for improved efficiency. These models achieve "significantly more time- and memory-efficient" performance than pure transformers while maintaining comparable capabilities.

## Limitations Noted

Linearized attention-based models experience training instability and reduced performance compared to standard attention, suggesting information bottlenecks in the d×d matrix representation versus adaptable L×L alternatives.
