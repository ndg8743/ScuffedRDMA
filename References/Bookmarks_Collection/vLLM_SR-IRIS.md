# vLLM Semantic Router v0.1 Iris: The First Major Release

**Source URL:** https://vllm.ai/blog/vllm-sr-iris
**Date Accessed:** 2026-03-11

**Published:** January 5, 2026
**Author:** vLLM Semantic Router Team

## Overview

vLLM Semantic Router serves as "System Level Intelligence" for Mixture-of-Models (MoM) infrastructure. The platform functions as an intermediary between users and LLM models, making intelligent routing decisions based on signals extracted from requests and responses.

## Key Features in v0.1 Iris

### Architecture: Signal-Decision Plugin Chain
The system evolved from a static 14-category approach to a flexible architecture that extracts six signal types:
- Domain signals (MMLU-trained classification)
- Keyword signals (regex-based pattern matching)
- Embedding signals (semantic similarity)
- Factual signals (hallucination detection)
- Feedback signals (user satisfaction metrics)
- Preference signals (personalization)

### Performance: Modular LoRA Architecture
Through collaboration with Hugging Face's Candle team, the platform reduced computational overhead by sharing base model computation across classification tasks using Low-Rank Adaptation.

### Safety: HaluGate Detection
A three-stage hallucination pipeline identifies problematic responses through sentinel classification, token-level detection, and NLI-based explanation.

### Ecosystem Integration
Compatible with vLLM Production Stack, NVIDIA Dynamo, Kubernetes-native solutions, and API gateways including Envoy and Istio.

### MoM Model Family
Specialized models for domain classification, PII detection, jailbreak protection, hallucination detection, tool management, and feedback analysis.

## Installation & Deployment

Local setup: `pip install vllm-sr`
Kubernetes: `helm install semantic-router oci://ghcr.io/vllm-project/charts/semantic-router`

## v0.2 Roadmap

Planned enhancements include advanced signal extraction, ML-based model selection algorithms, multi-turn RL-driven optimization, and improved safety mechanisms.
