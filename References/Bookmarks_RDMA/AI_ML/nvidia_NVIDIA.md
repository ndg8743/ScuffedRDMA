# nvidia (NVIDIA)

- **Source:** https://huggingface.co/nvidia
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

[NVIDIA Kumo Relational Outperforms Supervised Machine Learning on Relational Data, No Training Required    •  17](/blog/nvidia/kumo-relational)

### AI & ML interests

None defined yet.

### Recent Activity

[View all activity](/organizations/nvidia/activity/all)

### Papers

[Joints, Camera, Action! Co-Generating 3D Motion and Video for Arbitrary Rigs](/papers/2610.28632)

[ACCRUE: Continual Off-Policy Reinforcement Learning for Robot Foundation Models](/papers/2610.18596)

[View all Papers](/nvidia/papers)

### Articles



































































































This is NVIDIA's home for open model weights, datasets, and interactive demos. Everything here is designed to give developers and researchers production-ready starting points for Generative AI, Physical AI, and agentic workflows – backed by the same research that powers NVIDIA's enterprise AI platform.

## **The Nemotron Family: Digital Intelligence**

The Nemotron family is NVIDIA's lineup of purpose-built foundation models spanning language, reasoning, vision, retrieval, speech, and safety. Each model targets a specific performance profile - from ultra-efficient edge inference to heavyweight multi-turn agent orchestration - and ships with open weights, open datasets, and reproducible training recipes.

### **Language & Reasoning (Nemotron 3)**

The core language model lineup, engineered for advanced reasoning and agentic tasks across a range of model sizes and deployment targets.

- [**Nemotron 3.5 Lightning**](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16)**:** A highly efficient small language model (SLM) built on a hybrid Mamba-2 + Transformer MoE architecture (30B total / 3B active parameters), and Multi-Token Prediction (MTP) layers. Optimized for long-running autonomous agents, sub-agent workhorse deployments, and efficient local inference on a single H100 or DGX Spark (GB10). Features a 1M-token context window, reasoning ON/OFF modes, and a suite of speculative-decoding drafters — DSpark, DFlash, and MTP — for faster generation. Served via vLLM, SGLang, TRT-LLM, Ollama, llama.cpp, and more.
- [**Nemotron 3.5 Super VL:**](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-NVFP4) This vision-language model features 120 billion total parameters with 12 billion active parameters per forward pass. It combines a hybrid Mamba-Transformer Mixture-of-Experts (MoE) architecture with a C-RADIO vision encoder to process text, images, and video. For efficient inference, it incorporates Multi-Token Prediction (MTP) for speculative decoding and NVFP4 quantization refined through quantization-aware distillation. Designed for agentic coding, tool use, and document and video understanding, it supports a context window of up to 1 million tokens.
- [**Nemotron 3 Ultra:**](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-NVFP4) A frontier-scale large language model (550B total / 55B active parameters) utilizing a hybrid LatentMoE architecture with MTP layers. Designed for the most demanding workloads, it delivers strong agentic, reasoning, and conversational capabilities for complex multi-step agents, long-context analysis, and high-stakes reasoning over code, math, and science.

### **Safety & Content Moderation**

Models purpose-built for enterprise-grade safety and alignment workflows.

- [**Nemotron 3.5 Content Safety:**](https://huggingface.co/nvidia/Nemotron-3.5-Content-Safety) A multimodal, multilingual small language model (4B parameters) designed to act as a robust content-safety moderator. It supports standard taxonomy safety classification as well as custom-policy enforcement with reasoning traces for text and image inputs.

### **Speech & Multimodal**

NVIDIA provides a broad set of specialized multimodal foundations that integrate seamlessly with the Nemotron ecosystem — spanning speech recognition, multilingual translation, vision-language understanding, and real-time voice AI. These models are optimized for both cloud and edge deployment.

#### *Speech Recognition & Translation ([Nemotron Speech](https://huggingface.co/collections/nvidia/nemotron-speech))*

State-of-the-art, production-ready speech models from the NVIDIA NeMo Speech research team for ASR, TTS, speaker diarization, and speech-to-speech.

- [**Parakeet**](https://huggingface.co/collections/nvidia/parakeet-659711f49d1469e51546e021)**:** A family of FastConformer-based ASR (Automatic Speech Recognition) models achieving state-of-the-art WER (Word Error Rate). The latest [parakeet-tdt-0.6b-v3](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3) extends support to 25 European languages with automatic language detection, while the [1.1B English variant](https://huggingface.co/nvidia/parakeet-rnnt-1.1b) delivers maximum transcription accuracy.
- [**Canary**](https://huggingface.co/nvidia/canary-1b-v2)**:** Multilingual and multitask speech models capable of simultaneous translation and transcription across 25 languages, trained on NVIDIA's Granary dataset.
- [**Nemotron Speech Streaming**](https://huggingface.co/nvidia/nemotron-speech-streaming-en-0.6b)**:** A cache-aware streaming ASR model with native punctuation and capitalization, offering configurable chunk sizes (80ms–1120ms) for low-latency voice agent pipelines.
- [**Nemotron 3.5 ASR Streaming 0.6B:**](https://huggingface.co/nvidia/nemotron-3.5-asr-streaming-0.6b) A highly accurate, low-latency streaming automatic speech recognition (ASR) model capable of fast, real-time transcription across multiple languages, optimized for efficient voice AI pipelines.
- [**Parakeet Realtime EOU**](https://huggingface.co/nvidia/parakeet_realtime_eou_120m-v1)**:** A lightweight 120M-parameter streaming ASR model with built-in end-of-utterance detection at 80–160ms latency, purpose-built for voice AI agent turn-taking.
- [**Multitalker Parakeet**](https://huggingface.co/nvidia/multitalker-parakeet-streaming-0.6b-v1)**:** Streaming multi-speaker ASR using speaker kernel injection - handles fully overlapped speech without requiring speaker enrollment audio.

#### *Vision & Document Intelligence*

Vision-language models that bring multimodal understanding to documents, images, and video - from OCR and chart parsing to visual Q&A.

- [**Nemotron Parse:**](https://huggingface.co/nvidia/NVIDIA-Nemotron-Parse-v1.2) A general-purpose document parsing model that overcomes the shortcomings of traditional OCR technologies by deeply understanding complex layouts. It seamlessly extracts structured formatting, tables (as Markdown/LaTeX), bounding-boxes, and semantic classes from highly unstructured PDFs and images.
- **Nemotron 3 Omni:** A unified multimodal large language model that seamlessly ingests video, audio, image, and text to support enterprise-grade Q&A, transcription, and document intelligence workflows, effectively handling complex reasoning across rich media.

### **Nemotron RAG**

A complete, modular retrieval-augmented generation stack — from document ingestion through semantic search to precision reranking — designed for production pipelines that handle text, images, and complex multimodal documents.

- **Extract:** Models for  ingesting and extracting structured information from  multimodal sources, including charts, tables, and scanned documents (e.g. [Nemotron Parse v1.2](https://huggingface.co/nvidia/NVIDIA-Nemotron-Parse-v1.2), [Nemotron OCR and Object Detection](https://huggingface.co/collections/nvidia/nemotron-ocr-and-object-detection)).
- **Embed:** Multimodal embedding models that map  text, images, or audio into shared semantic  vectors spaces for search and retrieval (e.g. [Llama Nemotron Embed VL 1B v2](https://huggingface.co/nvidia/llama-nemotron-embed-vl-1b-v2)).
- **Rerank:** Cross-encoder reranking  models that rescore retrieved candidates using deeper relevance modeling (e.g. [Llama Nemotron Rerank VL 1B v2](https://huggingface.co/nvidia/llama-nemotron-rerank-vl-1b-v2)).


## **Community Collaborations**

NVIDIA releases optimized and aligned versions of leading community architectures, leveraging proprietary alignment techniques (SteerLM, RLHF, RPO) and open datasets like HelpSteer2 to push open models further.

- [**Llama-3.1-Nemotron**](https://huggingface.co/collections/nvidia/llama-nemotron)**:** A diverse family of models where Llama 3.1 architectures are fine-tuned using NVIDIA's **HelpSteer2** datasets to improve helpfulness and instruction adherence. Includes [Ultra (253B)](https://huggingface.co/nvidia/Llama-3_1-Nemotron-Ultra-253B-v1), [Super (49B)](https://huggingface.co/nvidia/Llama-3.3-Nemotron-Super-49B-v1), and [Nano (8B)](https://huggingface.co/nvidia/Llama-3.1-Nemotron-Nano-8B-v1) variants.
- **Mistral-NeMo:** A 12B parameter model built in collaboration with Mistral AI, offering a high performance-to-size ratio and an expanded 128k context window.

## **Physical AI**

### **NVIDIA Cosmos**

[NVIDIA Cosmos](https://huggingface.co/collections/nvidia/cosmos3) is an open platform of World Foundation Models (WFMs), training recipes, optimization practices, and data curation tools — purpose-built to understand, simulate, and reason about the physical world for robotics, autonomous vehicles, and physical AI.

At its center is **Cosmos 3**, the first fully open *omni-model* for physical AI. Built on a Mixture-of-Transformers (MoT) architecture, a single model pairs an autoregressive reasoner with a diffusion generator — reasoning *before* it generates — to unify vision reasoning, world generation, and action prediction across text, image, video, ambient sound, and action in one forward pass.

One model replaces a stack of pipelines, serving as a vision-language model, video generator, forward/inverse dynamics model, or robot policy without architectural changes:

- **[Cosmos 3 Super](https://huggingface.co/nvidia/Cosmos3-Super)**: The 32B-class omni-model (32B reasoner + 32B generator) for large-scale synthetic data generation (SDG) and research. Runs on NVIDIA Hopper and Blackwell GPUs.
- **[Cosmos 3 Nano](https://huggingface.co/nvidia/Cosmos3-Nano)**: The 8B-class omni-model (8B reasoner + 8B generator) optimized for efficient inference on workstation-grade compute like the RTX PRO 6000.
- **[Cosmos 3 Edge](https://huggingface.co/nvidia/Cosmos3-Edge)**: The 4B-class omni-model (2B reasoner + 2B generator) optimized for real-time robotic policy and visual reasoning on the edge.

Supporting the models across the platform:

- **[Cosmos Framework](https://github.com/NVIDIA/Cosmos-Framework)**: An end-to-end framework for training and serving WFMs — inference, post-training scripts, and agent skills.
- **Open SDG datasets**: Synthetic data spanning robot simulation, physics interaction, spatial reasoning, human motion, autonomous driving, and warehouse safety — released to help the community train and evaluate WFMs.

**Get started:** [Cosmos 3 collection](https://huggingface.co/collections/nvidia/cosmos3) · [GitHub](https://github.com/nvidia/Cosmos) · [NIM microservices](https://build.nvidia.com/models?q=cosmos) · [Cookbook](https://nvidia-cosmos.github.io/cosmos-cookbook/) · [Technical report](https://research.nvidia.com/labs/cosmos-lab/cosmos3/technical-report.pdf)

### **NVIDIA GR00T**

[GR00T N1.5 VLA](https://arxiv.org/pdf/2503.14734): NVIDIA's open foundation model for humanoid robot reasoning and control. Combines an Eagle-based vision-language backbone with a diffusion transformer (DiT) action head for language-conditioned manipulation across diverse embodiments. [We have integrated GR00T N1.5 into LeRobot](https://huggingface.co/docs/lerobot/groot) for policy post-training learning and deployment.

### **IsaacLab-Arena**

[IsaacLab-Arena](https://github.com/isaac-sim/IsaacLab-Arena): An open-source framework for large-scale, GPU-accelerated robot policy evaluation in simulation built over top of IsaacLab. Provides modular APIs for task curation, automated diversification, and parallel benchmarking across embodiments and environments. [We have integrated IsaacLab-Arena into LeRobot](https://huggingface.co/docs/lerobot/envhub_isaaclab_arena) for scalable closed-loop policy evaluation and benchmarking along with datasets and 250+ scenes from our partner [Lightwheel AI](https://www.lightwheel.ai/), on HuggingfaceHub.

# **Nemotron Datasets**

Every model NVIDIA ships rests on a data layer — and that data shapes how the model reasons, what it knows, and where it can be safely deployed. Nemotron Datasets are the open version of that foundation: web-scale pretraining corpora, alignment and reasoning data, multimodal grounding, and embodied AI simulation, released under permissive licenses with the training recipes and evaluation frameworks that produced them. Beyond Nemotron, NVIDIA's broader open data catalog spans 200+ releases across Physical AI and robotics, autonomous vehicles, biology and drug discovery, retrieval and evaluation benchmarks, and sovereign AI. Use the table below to find the right starting point for what you're trying to build.

## **Which dataset collection should I use?**

| If you want to... | Use this Collection | Start with these datasets | 
|---|---|---|
| **FOUNDATION** |  |  | 
| Pre-train a base model | [**Nemotron Pre-Training Collection**](https://huggingface.co/collections/nvidia/nemotron-pre-training-datasets) | [Nemotron-Pretraining-Legal-v1](https://huggingface.co/datasets/nvidia/Nemotron-Pretraining-Legal-v1), [Nemotron-Pretraining-Specialized-v1.2](https://huggingface.co/datasets/nvidia/Nemotron-Pretraining-Specialized-v1.2),[Nemotron-Pretraining-Code-v3](https://huggingface.co/datasets/nvidia/Nemotron-Pretraining-Code-v3) | 
| **BUILD A CAPABILITY** |  |  | 
| Math reasoning, proofs, and quantitative problem-solving | [**Nemotron Math & Reasoning Collection**](https://huggingface.co/collections/nvidia/nemotron-math-and-reasoning) | Nemotron-SFT-Math-v3, Nemotron-Math-v2, AceReason-Math, Nemotron-CC-Math-v1 | 
| Code generation, debugging, and SWE workflows | [**Nemotron Code & SWE Collection**](https://huggingface.co/collections/nvidia/nemotron-code-and-swe) | Nemotron-SFT-Competitive-Programming-v2, Nemotron-SFT-SWE-v2, Nemotron-CC-Code-v1 | 
| Helpful, multi-turn, instruction-following chat | [**Nemotron Chat & Instruction Collection**](https://huggingface.co/collections/nvidia/nemotron-chat-and-instruction-following) | Nemotron-SFT-Instruction-Following-Chat-v2, Nemotron-RL-instruction\_following | 
| Agentic and tool-use behavior | [**Nemotron Agentic Collection**](https://huggingface.co/collections/nvidia/nemotron-agentic-and-tool-use) | Nemotron-SFT-Agentic-v2, Nemotron-RL-Agentic-Function-Calling-Pivot-v1 | 
| Safety, refusals, and content moderation | [**Nemotron Safety Collection**](https://huggingface.co/collections/nvidia/nemotron-safety-and-content-moderation) | Aegis-AI-Content-Safety-Dataset-2.0, Nemotron-Safety-Guard-Dataset-v3, Nemotron-PII | 
| Image and document understanding | [**Nemotron Vision-Language Collection**](https://huggingface.co/collections/nvidia/nemotron-vision-language) | Nemotron-VLM-Dataset-v2, Llama-Nemotron-VLM-Dataset-v1 | 
| **TRAINING STAGES** |  |  | 
| RL data with verifiable rewards (math, code, agentic, instruction) | [**Nemotron Reinforcement Learning Collection**](https://huggingface.co/collections/nvidia/nemotron-reinforcement-learning) | Nemotron-RL-math-OpenMathReasoning, Nemotron-RL-coding-competitive\_coding, Nemotron-RL-Agentic-Function-Calling-Pivot-v1 | 
| Train a reward model | [**Nemotron Reward Modeling Collection**](https://huggingface.co/collections/nvidia/nemotron-reward-modeling) | HelpSteer3, HelpSteer2, Nemotron-RLHF-GenRM-v1 | 
| Full post-training recipe (SFT + RL blend) | [**Nemotron Post-Training Blends Collection**](https://huggingface.co/collections/nvidia/nemotron-post-training-datasets) | Llama-Nemotron-Post-Training-Dataset, Nemotron-Post-Training-Dataset-v2, Nemotron-Cascade-2-SFT-Data | 
| Evaluate model performance | **Nemotron Eval & Benchmark Collection** | SPEED-bench | 
| **SPECIALIZED & SOVEREIGN** |  |  | 
| Multilingual or domain-specific (e.g. finance) capability | [**Nemotron Supervised Fine-Tuning Collection**](https://huggingface.co/collections/nvidia/nemotron-supervised-fine-tuning) | Nemotron-SFT-Multilingual-v1, Nemotron-SpecializedDomains-Finance-v1 | 
| Diverse synthetic personas grounded in real population distributions | [**Nemotron Personas Collection**](https://huggingface.co/collections/nvidia/nemotron-personas) | Nemotron-Personas-USA / India / Japan / Brazil / France / Singapore / El Salvador / Vietnam |