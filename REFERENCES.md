# References

Comprehensive bibliography for the ScuffedRDMA thesis project.

## Core Papers

### Quantization & Data Formats

[1] Rouhani, B. D., Zhao, R., More, A., Hall, M., Khodamoradi, A., Deng, S., ... & Micikevicius, P. (2023). **Microscaling Data Formats for Deep Learning**. *arXiv preprint arXiv:2310.10537*. https://arxiv.org/abs/2310.10537
- Introduces MXFP4 quantization used by gpt-oss
- Enables 4x reduction in model size and bandwidth

### Attention Mechanisms

[2] Dao, T., Fu, D. Y., Ermon, S., Rudra, A., & Ré, C. (2022). **FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness**. *NeurIPS 2022*. https://arxiv.org/abs/2205.14135

[3] Dao, T. (2023). **FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning**. *arXiv preprint arXiv:2307.08691*. https://arxiv.org/abs/2307.08691

### Distributed Inference

[4] Kwon, W., Li, Z., Zhuang, S., Sheng, Y., Zheng, L., Yu, C. H., ... & Stoica, I. (2023). **Efficient Memory Management for Large Language Model Serving with PagedAttention**. *SOSP 2023*. https://arxiv.org/abs/2309.06180
- vLLM's PagedAttention paper

[5] Zheng, L., Chiang, W. L., Sheng, Y., Li, Z., Kwon, W., Zhuang, S., ... & Stoica, I. (2023). **Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena**. *arXiv preprint arXiv:2306.05685*. https://arxiv.org/abs/2306.05685

## Technical Documentation

### RDMA & Networking

[6] Mellanox Technologies. (2024). **NVIDIA MLNX_OFED Documentation**. https://docs.nvidia.com/networking/display/MLNXOFEDv24010331/
- MOFED installation and configuration

[7] NVIDIA. (2024). **GPUDirect RDMA Documentation**. https://docs.nvidia.com/cuda/gpudirect-rdma/index.html
- Direct GPU-NIC communication

[8] Linux RDMA. (2024). **rdma-core Documentation**. https://github.com/linux-rdma/rdma-core
- Soft-RoCE and RDMA userspace libraries

[9] Linux RDMA. (2024). **perftest - RDMA Performance Tests**. https://github.com/linux-rdma/perftest
- ib_write_bw, ib_write_lat benchmarking tools

### Tesla TTPoe

[10] Tesla, Inc. (2024). **TTPoe: Time-Triggered Protocol over Ethernet**. https://github.com/teslamotors/ttpoe
- Low-latency transport from Dojo supercomputer

[11] Tesla. (2024). **TTPoE at Hot Chips 2024: Replacing TCP for Low Latency Applications**. *Hot Chips 2024*. https://hc2024.hotchips.org/assets/program/conference/day2/17_HC2024_Tesla_TTPoE_v5.pdf

### vLLM & Inference

[12] vLLM Project. (2025). **Anatomy of vLLM**. https://blog.vllm.ai/2025/09/05/anatomy-of-vllm.html

[13] vLLM Project. (2025). **gpt-oss on vLLM**. https://blog.vllm.ai/2025/08/05/gpt-oss.html
- gpt-oss model support with MXFP4

[14] vLLM Project. (2026). **Disaggregated Prefilling Documentation**. https://docs.vllm.ai/en/latest/features/disagg_prefill/

[15] FlashInfer. (2025). **FlashInfer: Kernel Library for LLM Serving**. https://github.com/flashinfer-ai/flashinfer
- MXFP4 MoE kernel optimization

### LLM Models

[16] Meta AI. (2025). **Llama 4: The Beginning of a New Era of Natively Multimodal AI**. https://ai.meta.com/blog/llama-4-multimodal-intelligence/

[17] Meta AI. (2025). **Llama 4 Scout 17B-16E-Instruct**. https://huggingface.co/meta-llama/Llama-4-Scout-17B-16E-Instruct
- 109B total params, 17B active, MoE architecture

[18] OpenAI. (2025). **gpt-oss-120b Model Card**. https://huggingface.co/openai/gpt-oss-120b
- 116.8B parameters, MXFP4 quantization

### NCCL & Collective Communication

[19] NVIDIA. (2024). **NCCL Documentation**. https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/index.html

[20] NVIDIA. (2024). **NCCL Environment Variables**. https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/env.html
- NCCL_IB_HCA, NCCL_NET_GDR_LEVEL configuration

## GitHub Issues & Discussions

[21] vLLM. (2026). **Issue #22279: FlashAttention 3 fails on Blackwell GPUs**. https://github.com/vllm-project/vllm/issues/22279
- Lazy import fix for RTX 5090

[22] vLLM. (2025). **GPUDirect RDMA vs Standard RDMA Benchmarking Discussion**. https://discuss.vllm.ai/t/vllm-benchmarking-why-is-gpudirect-rdma-not-outperforming-standard-rdma-in-a-pipeline-parallel-setup/1377

## Industry Standards

[23] Ultra Ethernet Consortium. (2025). **UEC 1.0 Specification**. https://ultraethernet.org/
- Next-generation AI networking standard

[24] Open Compute Project. (2025). **OCP Falcon Networking Specification**. https://github.com/opencomputeproject/OCP-NET-Falcon

## Additional Resources

[25] Arch Linux Wiki. (2024). **InfiniBand Setup Guide**. https://wiki.archlinux.org/title/InfiniBand

[26] RDMA-Rust. (2025). **Sideway: Rust RDMA Library**. https://github.com/RDMA-Rust/sideway

[27] Shailesh, M. (2019). **rdma-tas: RDMA over TAS/DPDK**. https://github.com/mani-shailesh/rdma-tas
- EuroSys 2019 paper implementation

---

## Citation Format (BibTeX)

```bibtex
@article{rouhani2023microscaling,
  title={Microscaling Data Formats for Deep Learning},
  author={Rouhani, Bita Darvish and Zhao, Ritchie and More, Ankit and Hall, Mathew and others},
  journal={arXiv preprint arXiv:2310.10537},
  year={2023}
}

@inproceedings{kwon2023efficient,
  title={Efficient Memory Management for Large Language Model Serving with PagedAttention},
  author={Kwon, Woosuk and Li, Zhuohan and Zhuang, Siyuan and others},
  booktitle={SOSP},
  year={2023}
}

@article{dao2023flashattention2,
  title={FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning},
  author={Dao, Tri},
  journal={arXiv preprint arXiv:2307.08691},
  year={2023}
}
```
