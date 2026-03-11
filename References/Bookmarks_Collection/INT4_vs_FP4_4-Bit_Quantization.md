# INT4 vs FP4: The Future of 4-Bit Quantization

**Source URL:** https://huggingface.co/blog/onekq/nvfp4-int4

**Date Accessed:** 2026-03-11

---

**Author:** Yi Cui (@onekq)
**Published:** November 19, 2025
**Type:** Community Article

## Article Summary

This article analyzes the technical and geopolitical dynamics between INT4 and FP4 quantization formats, using Kimi K2's choice of INT4 as a case study.

## How Kimi Stole the Show

- Nvidia's Blackwell GPU launched with NVFP4 (4-bit floating-point) as a centerpiece feature
- FP4 offers technical advantages over INT4: dynamic range, better precision near zero, proper outlier handling, hardware acceleration
- However, Kimi released K2 in INT4, not FP4

## Why INT4?

Three practical reasons:

1. **Hardware constraints:** Chinese model makers lack Blackwell GPUs due to export controls; they use Ampere (A800) and Hopper (H800) which support INT4
2. **Ecosystem alignment:** Customers also run Ampere hardware; INT4 optimization makes sense for this market
3. **Hardware incompatibility:** Blackwell cannot natively run INT4 models efficiently—it only accelerates FP4

## The Nuance of Conversion

### QAT vs PTQ Trade-offs

- Models trained with QAT (Quantization-Aware Training) learn INT4-specific quantization grids during training
- Converting post-training (PTQ) from INT4 to FP4 loses the training trajectories and quantization-aware adaptations
- Result: suboptimal FP4 models

### Distribution Mismatch

- **INT4:** Uniform spacing across value ranges
- **FP4:** Exponential spacing (denser near zero where weights cluster)

Converting between formats creates alignment problems as values land between quantization levels.

## How the Future Will Unfold

1. **FP4 Will Eventually Dominate:** Technically superior, but limited access prevents immediate adoption
2. **The Ampere Renaissance:** INT4-optimized Chinese models keep older hardware (Ampere/Hopper) relevant longer—extends hardware ROI by ~2 years
3. **Challenges for Blackwell:** Without efficient INT4 inference, upgrade urgency weakens
4. **The Next Chapter:** Ecosystem fragmentation will continue; FP4 will eventually replace INT4

## Technical Insights

The article highlights a key tension: **superior hardware (Blackwell) cannot efficiently run superior models (trained on FP4)** if those models are trained on older hardware architectures due to geopolitical constraints.

This creates a self-reinforcing cycle where INT4 models keep older hardware valuable, delaying Blackwell adoption and fragmenting the AI inference ecosystem.
