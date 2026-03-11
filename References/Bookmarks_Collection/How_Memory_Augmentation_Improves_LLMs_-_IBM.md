# How Memory Augmentation Improves Large Language Models

**Source URL:** https://research.ibm.com/blog/memory-augmented-LLMs
**Date accessed:** 2026-03-11

---

**Author:** Peter Hess
**Published:** September 24, 2024
**Topic:** AI, Generative AI

## Overview

IBM Research is developing memory augmentation strategies to address persistent limitations in large language models, particularly their struggle with long input sequences and computational inefficiency.

## Key Problems

LLMs face significant challenges: they lack long-term memory capacity, struggle with lengthy contexts, and require substantial computing resources. The self-attention mechanism underlying transformers becomes increasingly costly as input length grows. Additionally, training data becomes obsolete over time, and models can inadvertently leak sensitive information.

## Two Main Approaches

**CAMELoT** (Consolidated Associative Memory Enhanced Long Transformer) plugs into existing models to extend context handling. Drawing from neuroscience principles, it implements three properties: information compression for storage, novelty detection for new concepts, and recency-based replacement. "As the input length increases, the computational cost of self-attention grows quadratically," explains IBM scientist Rogerio Feris.

When applied to Llama 2-7b, CAMELoT reduced perplexity by up to 30% while achieving equivalent accuracy with shorter inputs.

**Larimar** adds episodic memory functioning like a "hippocampus" for contextual, updatable information. It enables rapid, gradient-free memory updates during inference for fact-checking and content editing. The system mitigates hallucinations and prevents sensitive information leakage through selective fact forgetting.

## Benefits

Both approaches avoid costly retraining while improving accuracy, enabling longer document processing, enhancing user intent understanding in chatbots, and supporting context length generalization—a model's ability to handle inputs longer than training data.
