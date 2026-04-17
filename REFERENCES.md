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

### Distributed Inference & Transport

[4] Kwon, W., Li, Z., Zhuang, S., Sheng, Y., Zheng, L., Yu, C. H., ... & Stoica, I. (2023). **Efficient Memory Management for Large Language Model Serving with PagedAttention**. *SOSP 2023*. https://arxiv.org/abs/2309.06180
- vLLM's PagedAttention paper

[4a] Chen, X. et al. (2025). **TransferEngine: Bridging Common NICs to Uniform Point-to-Point RDMA for LLM Systems**. *arXiv:2510.27656*. https://arxiv.org/abs/2510.27656
- One-sided WriteImm RDMA across multiple NICs per GPU; comparison baseline for libscuffedrdma's WFA/PMP layer

[4b] Mao, C., Zhou, Y., Zhang, L., Cui, Y., Chen, Y., & Xu, P. (2025). **Previewing UCCL-EP: Flexible and Efficient Expert Parallelism for Cloud and Beyond**. https://arxiv.org/abs/2501.xxxxx
- MoE expert-parallelism communication layer; TransferEngine reports substantially higher latency than its own approach

[4c] Zhou, S. (1987). **Performance Studies of Dynamic Load Balancing in Distributed Systems**. Ph.D. dissertation, UC Berkeley, Tech. Rep. UCB/CSD-87-376.
- Origin of the load-index abstraction used by LSF/LIM, Symphony/ELIM, and the WFA classifier design here

[4d] IBM Research (2025). **Accelerating AI inference with IBM Storage Scale**. https://research.ibm.com/blog/accelerating-ai-inference-with-ibm-storage-scale
- GPFS-backed KV cache offloading for vLLM/llm-d; reports 8–12× TTFT improvement vs recomputation. Comparison point for ScuffedRDMA's cross-node KV transfer numbers.

[4e] Hsu, V. (2026). **Accelerating NVIDIA Dynamo with IBM Storage Scale and BlueField-4 Inference Context Memory Storage Platform**. IBM Community, Jan. 5, 2026. https://community.ibm.com/community/user/blogs/vincent-hsu/2026/01/05/accelerating-nvidia-dynamo-with-ibm-storage-scale
- Four-tier KV memory hierarchy (G1 GPU / G2 CPU / G3 local NVMe / G4 shared network). Storage Scale unifies G3+G4 through a global namespace with locality-aware placement. BlueField-4 offloads RDMA network + storage paths from CPU; DOCA + NIXL provide the software integration.

[4g] Hsu, A., Ngo, K., Zhu, Y., Stoica, R., Margalit, G., Tarasov, V., & Kieran, M. (2026). **Rethinking LLM Inference Economics: KV Cache Reuse with llm-d, LMCache, and IBM Storage Scale**. IBM Community, Feb. 6, 2026. https://community.ibm.com/community/user/blogs/anthony-hsu/2026/02/06/rethinking-llm-inference-economics
- Reports TTFT and inference cost each reduced by >10× at high KV reuse rates, measured on a 70B model on 4× H100 with 128k context (~320 KB per KV entry) using LMCache externalisation to Storage Scale at ~8 GB/s sustained.

[4h] MIT sandook team. (2026). **sandook: Aggregated NVMe Block Device with Read/Write Workload Isolation**. GitHub / NSDI 2026. https://github.com/mit-sandook/sandook
- Aggregates multiple NVMe SSDs into a unified block device with dynamic read/write workload isolation and SSD-latency-model-driven scheduling. Candidate substrate for a GPFS-analog KV cache tier on commodity hardware: exposes standard Linux block-device semantics, so anything that consumes GPFS's NSD-over-RDMA interface can layer on top. Worth reading `blk_dev/` and `scheduler/control_plane/` for the workload-isolation mechanism that pairs with the hot/cold QP split in libscuffedrdma.

[4f] Red Hat Developer (2025). **llm-d: Kubernetes-native distributed inferencing**. https://developers.redhat.com/articles/2025/05/20/llm-d-kubernetes-native-distributed-inferencing
- Source of the scorer framework (LoadAware, SessionAffinity, NoHitLRU, ActiveRequest) that the WFA classifier's decomposition mirrors

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
cat: /Users/nathan/Library/Application Support/Claude/local-agent-mode-sessions/fbcb8dd1-969b-401e-997b-314ef04669fc/effca977-6e52-43f1-9212-4083464144d3/local_dc70203d-8f65-40c1-a712-401c97773bf2/NEW_REFERENCES_APPENDIX.md: No such file or directory

---

## Bookmark Collection (Chrome RDMA Folder)

*Papers, articles, and documentation collected from Chrome bookmarks on 2026-03-11. Files stored in `References/Bookmarks_Collection/`.*

### RDMA Core & Networking

[B1] RoCE Initiative. (2016). **SoftRoCE Paper**. *RoCE Initiative*.
- File: `SoftRoCE_Paper_-_RoCE_Initiative_2016.pdf`
- https://www.roceinitiative.org/wp-content/uploads/2016/11/SoftRoCE_Paper_FINAL.pdf

[B2] IBM. (2024). **RDMA over Converged Ethernet**. *IBM Documentation*.
- File: `RDMA_over_Converged_Ethernet_-_IBM.md`
- https://www.ibm.com/docs/en/i/7.4.0?topic=concepts-rdma-over-converged-ethernet

[B3] Red Hat. (2024). **Configuring the Core RDMA Subsystem**. *Red Hat Enterprise Linux 9 Documentation*.
- File: `Configuring_Core_RDMA_Subsystem_-_Red_Hat.md`
- https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/configuring_infiniband_and_rdma_networks/configuring-the-core-rdma-subsystem_configuring-infiniband-and-rdma-networks

[B4] Intelligent Visibility. (2024). **RDMA for Storage Ethernet: RoCE vs. iWARP Guide**.
- File: `RDMA_for_Storage_Ethernet_RoCE_vs_iWARP.md`
- https://intelligentvisibility.com/rdma-roce-iwarp-guide

[B5] IBM. (2024). **RDMA Tuning**. *IBM Storage Scale Documentation*.
- File: `RDMA_Tuning_-_IBM_Storage_Scale.md`
- https://www.ibm.com/docs/en/storage-scale/6.0.0?topic=administering-rdma-tuning

[B6] IBM. (2024). **rdma_cm Operations**. *IBM AIX Documentation*.
- File: `rdma_cm_-_IBM_AIX.md`
- https://www.ibm.com/docs/en/aix/7.3.0?topic=operations-rdma-cm

[B7] IBM. (2024). **Connection Manager (CM) ID Operations**. *IBM AIX Documentation*.
- File: `Connection_Manager_CM_ID_Operations_-_IBM.md`
- https://www.ibm.com/docs/en/aix/7.3.0?topic=verbs-connection-manager-cm-id-operations

[B8] IBM. (2024). **Planning for 100 Gbps Adapter**. *IBM Storage Scale System*.
- File: `Planning_100Gbps_Adapter_-_IBM.md`
- https://www.ibm.com/docs/en/storage-scale-system/5141-AF8?topic=network-planning-100-gbps-adapter

[B9] Schmaustech. (2025). **RDMA: Shared, Hostdevice, Legacy SR-IOV**.
- File: `SCHMAUSTECH_RDMA_Shared_Hostdevice_SRIOV.md`
- https://schmaustech.blogspot.com/2025/01/rdma-shared-hostdevice-legacy-sriov.html

[B10] IOL UNH. (2024). **Manual RDMA Testing Using the OFA FSDP Cluster**.
- File: `Manual_RDMA_Testing_OFA_FSDP_Cluster.md`
- https://www.iol.unh.edu/blog/2024/09/17/manual-rdma-testing-using-ofa-fsdp-cluster

[B11] Pansolusi. (2024). **RDMA, RoCE Test in Network with MPI Tools**.
- File: `RDMA_RoCE_Test_MPI_Tools_-_Pansolusi.md`
- https://tech.pansolusi.com/2024/10/31/rdma-roce-test-in-network-with-mpi-tools/

[B12] IBM. (2024). **IBM Redbooks: RDMA (redp4493)**. *IBM Redpapers*.
- File: `IBM_Redbooks_RDMA_redp4493.pdf`
- https://www.redbooks.ibm.com/redpapers/pdfs/redp4493.pdf

### InfiniBand & RoCE Specifications

[B13] InfiniBand Trade Association. (2021). **New InfiniBand and RoCE Specification: Memory Placement Extensions**.
- File: `New_InfiniBand_RoCE_Memory_Placement_Extensions.md`
- https://www.infinibandta.org/new-infiniband-and-roce-specification-introduces-memory-placement-extensions-to-significantly-reduce-persistent-memory-latency/

[B14] Ultra Ethernet Consortium. (2023). **UEC 1.0 Overview**.
- File: `UEC_1.0_Overview_Ultra_Ethernet_Consortium.pdf`
- https://ultraethernet.org/wp-content/uploads/sites/20/2023/10/23.07.12-UEC-1.0-Overview-FINAL-WITH-LOGO.pdf

[B15] Open MPI. (2024). **InfiniBand / RoCE Support**.
- File: `InfiniBand_RoCE_Support_-_Open_MPI.md`
- https://docs.open-mpi.org/en/main/tuning-apps/networking/ib-and-roce.html

[B16] MVAPICH. (2024). **MVAPICH Overview: High Performance MPI**.
- File: `MVAPICH_Overview.md`
- https://mvapich.cse.ohio-state.edu/overview/

### GPUDirect RDMA & GPU Networking

[B17] NVIDIA. (2024). **GPUDirect RDMA Documentation**.
- File: `GPUDirect_RDMA_Documentation_-_NVIDIA.md`
- https://docs.nvidia.com/cuda/gpudirect-rdma/#how-gpudirect-rdma-works

[B18] Red Hat. (2025). **Accelerate Model Training on OpenShift AI with NVIDIA GPUDirect RDMA**.
- File: `GPUDirect_RDMA_OpenShift_AI_-_Red_Hat.md`
- https://developers.redhat.com/articles/2025/04/29/accelerate-model-training-openshift-ai-nvidia-gpudirect-rdma

[B19] IBM. (2024). **GPU Direct Storage**. *IBM Scale Container Native*.
- File: `GPU_Direct_Storage_-_IBM.md`
- https://www.ibm.com/docs/en/scalecontainernative/6.0.0?topic=planning-gpu-direct-storage

[B20] IBM. (2024). **GPUDirect Storage Support for IBM Storage Scale**.
- File: `GPUDirect_Storage_IBM_Storage_Scale.md`
- https://www.ibm.com/docs/en/storage-scale/5.2.3?topic=architecture-gpudirect-storage-support-storage-scale

[B21] AMD. (2024). **GPU-enabled Message Passing Interface**. *AMD Instinct Documentation*.
- File: `GPU_enabled_MPI_-_AMD.md`
- https://instinct.docs.amd.com/projects/gpu-cluster-networking/en/latest/how-to/gpu-enabled-mpi.html

### RDMA Research Papers

[B22] Olteanu, V. et al. (2022). **NSDI '22 Paper**. *USENIX*.
- File: `USENIX_NSDI22_Olteanu.pdf`
- https://www.usenix.org/system/files/nsdi22-paper-olteanu.pdf

[B23] ArXiv. (2025). **Predictive Load Balancing for RDMA Traffic**. *arXiv:2506.08132*.
- File: `Predictive_Load_Balancing_for_RDMA_Traffic_2506.08132.pdf`
- https://arxiv.org/abs/2506.08132

[B24] Guo, Z. et al. (2023). **RecoNIC: RDMA-enabled Compute Offloading on SmartNIC**. *arXiv:2312.06207*.
- File: `RecoNIC_RDMA_Compute_Offloading_SmartNIC_2312.06207.pdf`
- https://arxiv.org/abs/2312.06207

[B25] MDPI Electronics. (2024). **A High-Performance FPGA-Based RoCE v2 RDMA Packet Parser and Generator**.
- File: `FPGA_RoCEv2_RDMA_Packet_Parser_-_MDPI.md` (stub - manual download needed)
- https://www.mdpi.com/2079-9292/13/20/4107

[B26] DatenLord. (2024). **blue-rdma Design Introduction (III) — Packet Processing**.
- File: `blue-rdma_Design_Packet_Processing_-_DatenLord.md` (stub - manual download needed)
- https://medium.com/@datenlord/blue-rdma-design-introduction-iii-packet-processing-ec14f463effd

[B27] Hale, K. C. & Dinda, P. A. (2016). **Enabling Hybrid Parallel Runtimes Through Kernel and Virtualization Support**. *VEE '16*.
- File: `Enabling_Hybrid_Parallel_Runtimes_-_Hale_2016.md`
- https://www.halek.co/publication/hale-2016-hrthvm/

[B28] DiVA Portal. (2024). **RDMA Thesis**.
- File: `DiVA_Portal_RDMA_Thesis.pdf`
- https://www.diva-portal.org/smash/get/diva2:1789103/FULLTEXT01.pdf

[B29] CERN. (2022). **ATLAS DAQ Proceedings**.
- File: `CERN_ATLAS_DAQ_PROC_2022.pdf`
- https://cds.cern.ch/record/2838102/files/ATL-DAQ-PROC-2022-020.pdf

[B30] Tong et al. (2022). **THU CSNet WiFi Paper**. *WoWMoM 2022*.
- File: `Tong_WoWMoM22_THU_CSNet.pdf`
- https://www.thucsnet.com/wp-content/papers/tong_wowmom22.pdf

### UCX & Transport Middleware

[B31] OpenUCX. (2024). **UCX: Unified Communication X Introduction**.
- File: `UCX_Unified_Communication_X_Introduction.md`
- https://openucx.org/introduction/

[B32] SPDK. (2024). **SPDK: An Overview of Applications**.
- File: `SPDK_Overview_Applications.md`
- https://spdk.io/doc/app_overview.html

[B33] Proxmox Forum. (2024). **SR-IOV vs DPDK+OVS vs vBridges**.
- File: `SR-IOV_vs_DPDK_OVS_vBridges_-_Proxmox.md`
- https://forum.proxmox.com/threads/sr-iov-vs-dpdk-ovs-vs-vbridges.116005/

### LLM Inference & Distributed Systems

[B34] AIBrix. (2025). **DeepSeek-R1 671B Multi-host Deployment in AIBrix**.
- File: `DeepSeek-R1_Multi-host_Deployment_AIBrix.md`
- https://aibrix.github.io/posts/2025-03-10-deepseek-r1/

[B35] ArXiv. (2025). **Insights into DeepSeek-V3: Scaling Challenges and Reflections on Hardware**. *arXiv:2505.09343*.
- File: `DeepSeek-V3_Scaling_Challenges_Hardware_2505.09343.pdf`
- https://arxiv.org/abs/2505.09343

[B36] ArXiv. (2025). **Triton-distributed: Programming Overlapping Kernels on Distributed AI Systems**. *arXiv:2504.19442*.
- File: `Triton-distributed_Overlapping_Kernels_2504.19442.pdf`
- https://arxiv.org/abs/2504.19442

[B37] ArXiv. (2025). **Zorse: Optimizing LLM Training Efficiency on Heterogeneous GPU Clusters**. *arXiv:2507.10392*.
- File: `Zorse_LLM_Training_Heterogeneous_GPU_2507.10392.pdf`
- https://arxiv.org/abs/2507.10392

[B38] ArXiv. (2025). **ATLAHS: An Application-centric Network Simulator for AI, HPC, and Distributed Storage**. *arXiv:2505.08936*.
- File: `ATLAHS_Network_Simulator_AI_HPC_2505.08936.pdf`
- https://arxiv.org/abs/2505.08936

[B39] Red Hat. (2025). **Demystifying llm-d and vLLM: The Race to Production**.
- File: `Demystifying_llm-d_vLLM_-_Red_Hat.md`
- https://www.redhat.com/en/blog/demystifying-llm-d-and-vllm-race-production

[B40] BentoML. (2025). **The Shift to Distributed LLM Inference: 3 Key Technologies**.
- File: `Shift_to_Distributed_LLM_Inference_-_BentoML.md`
- https://www.bentoml.com/blog/the-shift-to-distributed-llm-inference

[B41] Caldwell, S. (2025). **Pretraining at Home: 20B Tokens from 222 Hours to 12**.
- File: `Pretraining_at_Home_20B_Tokens_-_Caldwell.md`
- https://hackbot.dad/writing/pretraining-at-home/

### Attention & GPU Kernels

[B42] ArXiv. (2025). **Hardware-Efficient Attention for Fast Decoding**. *arXiv:2505.21487*.
- File: `Hardware-Efficient_Attention_Fast_Decoding_2505.21487.pdf`
- https://arxiv.org/abs/2505.21487

[B43] ArXiv. (2025). **Categorical Foundations for CuTe Layouts**. *arXiv:2601.05972*.
- File: `Categorical_Foundations_CuTe_Layouts_2601.05972.pdf`
- https://arxiv.org/abs/2601.05972

[B44] ArXiv. (2026). **K-Search: LLM Kernel Generation via Co-Evolving Intrinsic World Model**. *arXiv:2602.19128*.
- File: `K-Search_LLM_Kernel_Generation_2602.19128.pdf`
- https://arxiv.org/abs/2602.19128

[B45] Dremov, A. (2025). **Understanding Flash Attention: Writing Triton Kernel Code**.
- File: `Understanding_Flash_Attention_Triton_-_Dremov.md`
- https://alexdremov.me/understanding-flash-attention-writing-the-algorithm-from-scratch-in-triton/

[B46] AmineDiro. (2025). **Reimplementing FlashAttention for Performance**.
- File: `Reimplementing_FlashAttention_-_AmineDiro.md`
- https://aminediro.com/posts/flash_attn/

[B47] NVIDIA. (2024). **Accelerating Transformers with NVIDIA cuDNN 9**.
- File: `Accelerating_Transformers_cuDNN_9_-_NVIDIA.md`
- https://developer.nvidia.com/blog/accelerating-transformers-with-nvidia-cudnn-9/

[B48] Gau-Nernst. (2025). **tcgen05 for Dummies**.
- File: `tcgen05_for_Dummies_-_Gau_Nernst.md`
- https://gau-nernst.github.io/tcgen05/

[B49] Gau-Nernst. (2025). **My First Multi-GPU Kernel: Writing All-to-All for AMD MI300X**.
- File: `Multi-GPU_Kernel_All-to-All_AMD_MI300X_-_Gau_Nernst.md`
- https://gau-nernst.github.io/amd-a2a/

[B50] SHI Labs. (2025). **Distributed GEMM: CUTLASS-native Tensor Parallelism**.
- File: `Distributed_GEMM_CUTLASS_Tensor_Parallelism_-_SHI_Labs.md` (stub - manual download needed)
- https://blog.shi-labs.com/distributed-gemm-88be6a481e2b

### GPU Architecture & Hardware

[B51] NVIDIA. (2025). **Inside the NVIDIA Rubin Platform: Six New Chips, One AI Supercomputer**.
- File: `Inside_NVIDIA_Rubin_Platform.md`
- https://developer.nvidia.com/blog/inside-the-nvidia-rubin-platform-six-new-chips-one-ai-supercomputer/

[B52] NVIDIA. (2024). **Beating SOTA Inference with GPUNet**.
- File: `Beating_SOTA_Inference_GPUNet_-_NVIDIA.md`
- https://developer.nvidia.com/blog/beating-sota-inference-performance-on-nvidia-gpus-with-gpunet/

[B53] Tom's Hardware. (2025). **GPUs Can Now Use PCIe-attached Memory via Panmnesia CXL IP**.
- File: `GPUs_PCIe_Memory_CXL_Panmnesia_-_Toms_Hardware.md`
- https://www.tomshardware.com/pc-components/gpus/gpus-get-a-boost-from-pcie-attached-memory-that-boosts-capacity-and-delivers-double-digit-nanosecond-latency-ssds-can-also-be-used-to-expand-gpu-memory-capacity-via-panmnesias-cxl-ip

[B54] Tom's Hardware. (2025). **Faulty Nvidia H100 GPUs and HBM3 Memory During LLama 3 Training**.
- File: `Faulty_H100_GPUs_HBM3_LLama3_Training_-_Toms_Hardware.md`
- https://www.tomshardware.com/tech-industry/artificial-intelligence/faulty-nvidia-h100-gpus-and-hbm3-memory-caused-half-of-the-failures-during-llama-3-training-one-failure-every-three-hours-for-metas-16384-gpu-training-cluster

[B55] SemiAnalysis. (2025). **NVIDIA Tensor Core Evolution: From Volta to Blackwell**.
- File: `NVIDIA_Tensor_Core_Volta_to_Blackwell.md`
- https://newsletter.semianalysis.com/p/nvidia-tensor-core-evolution-from-volta-to-blackwell

### Quantization & Precision

[B56] Rouhani, B. D. et al. (2023). **Microscaling Data Formats for Deep Learning**. *arXiv:2310.10537*.
- File: `Microscaling_Data_Formats_for_Deep_Learning_2310.10537.pdf`
- https://arxiv.org/abs/2310.10537

[B57] Hugging Face. (2025). **INT4 vs FP4: The Future of 4-Bit Quantization**.
- File: `INT4_vs_FP4_4-Bit_Quantization.md`
- https://huggingface.co/blog/onekq/nvfp4-int4

[B58] NVIDIA. (2024). **Train With Mixed Precision**.
- File: `Train_With_Mixed_Precision_-_NVIDIA.md`
- https://docs.nvidia.com/deeplearning/performance/mixed-precision-training/index.html

### Memory & KV Cache

[B59] WEKA. (2025). **WEKA Breaks the AI Memory Barrier with Augmented Memory Grid on NeuralMesh**.
- File: `WEKA_Augmented_Memory_Grid_NeuralMesh.md`
- https://www.weka.io/company/weka-newsroom/press-releases/weka-breaks-the-ai-memory-barrier-with-augmented-memory-grid/

[B60] WEKA. (2025). **NVIDIA Shared KV Cache: WEKA Adoption Roadmap to ICMS**.
- File: `NVIDIA_Shared_KV_Cache_WEKA_Roadmap.md`
- https://www.weka.io/blog/ai-ml/nvidia-is-defining-the-future-of-shared-kv-cache-weka-provides-the-adoption-roadmap/

[B61] IBM Research. (2025). **How Memory Augmentation Can Improve LLMs**.
- File: `How_Memory_Augmentation_Improves_LLMs_-_IBM.md`
- https://research.ibm.com/blog/memory-augmented-LLMs

### Parallel Computing & Systems

[B62] Nebius. (2025). **How Transformers, RNNs and SSMs Are More Alike Than You Think**.
- File: `How_Transformers_RNNs_SSMs_More_Alike_-_Nebius.md`
- https://nebius.com/blog/posts/mixers-are-rnns

[B63] Fleury, R. (2025). **Multi-Core By Default**. *Digital Grove*.
- File: `Multi-Core_By_Default_-_Ryan_Fleury.md`
- https://www.rfleury.com/p/multi-core-by-default

[B64] GCC Wiki. (2024). **Offloading**.
- File: `GCC_Offloading_Wiki.md`
- https://gcc.gnu.org/wiki/Offloading

[B65] ArXiv. (2025). **Rethinking Allocations in Post-Moore Clouds**. *arXiv:2501.11185*.
- File: `Rethinking_Allocations_Post-Moore_Clouds_2501.11185.pdf`
- https://arxiv.org/abs/2501.11185

[B66] Priakhin. (2022). **Stanford Legion Retreat: Native GPU DMA System**.
- File: `Stanford_Legion_Retreat_GPU_DMA_Priakhin_2022.pdf`
- https://theory.stanford.edu/~aiken/LegionRetreat22/slides/priakhin.pdf

[B67] RAND Corporation. (2025). **RAND Report RRA4591-1**.
- File: `RAND_RRA4591-1_Report.pdf`
- https://www.rand.org/content/dam/rand/pubs/research_reports/RRA4500/RRA4591-1/RAND_RRA4591-1.pdf

### vLLM & Inference Serving

[B68] vLLM. (2025). **vLLM Now Supports gpt-oss**.
- File: `vLLM_Supports_gpt-oss.md`
- https://blog.vllm.ai/2025/08/05/gpt-oss.html

[B69] Cadence. (2024). **ONFI 5.2: What's New in Open NAND Flash Interface**.
- File: `ONFI_5.2_NAND_Flash_Interface_-_Cadence.md`
- https://community.cadence.com/cadence_blogs_8/b/fv/posts/onfi-5-2-what-s-new-in-open-nand-flash-interface-s-latest-5-2-standard

[B70] ArXiv. (2025). **When to Reason: Semantic Router for vLLM**. *arXiv:2510.08731*.
- File: `When_to_Reason_Semantic_Router_vLLM_2510.08731.pdf`
- https://arxiv.org/abs/2510.08731

[B71] Softwarefrontier. (2025). **Mastering CUDA and High-Performance Computing, Part III**.
- File: `Mastering_CUDA_HPC_Part_III.md`
- https://softwarefrontier.substack.com/p/mastering-cuda-and-high-performance-204

[B72] IBM Community. (2026). **NVIDIA AI Blueprints on IBM Fusion**.
- File: `NVIDIA_AI_Blueprints_IBM_Fusion.md`
- https://community.ibm.com/community/user/blogs/patrick-fay/2026/03/04/nvidia-ai-blueprints-on-ibm-fusion-ai-recipes

[B73] Xilinx. (2024). **PCIe Peer-to-Peer (P2P) — XRT Documentation**.
- File: `PCIe_Peer-to-Peer_P2P_-_XRT.md`
- https://xilinx.github.io/XRT/master/html/p2p.html

### Papers from Repo References (Newly Downloaded)

[B74] Dao, T. et al. (2022). **FlashAttention: Fast and Memory-Efficient Exact Attention**. *NeurIPS 2022*. *arXiv:2205.14135*.
- File: `FlashAttention_IO-Aware_2205.14135.pdf`

[B75] Dao, T. (2023). **FlashAttention-2: Faster Attention with Better Parallelism**. *arXiv:2307.08691*.
- File: `FlashAttention-2_Faster_Attention_2307.08691.pdf`

[B76] Kwon, W. et al. (2023). **Efficient Memory Management for LLM Serving with PagedAttention**. *SOSP 2023*. *arXiv:2309.06180*.
- File: `PagedAttention_Efficient_LLM_Serving_2309.06180.pdf`

[B77] Zheng, L. et al. (2023). **Judging LLM-as-a-Judge with MT-Bench**. *arXiv:2306.05685*.
- File: `MT-Bench_Judging_LLM-as-Judge_2306.05685.pdf`

[B78] Tesla. (2024). **TTPoE at Hot Chips 2024: Replacing TCP for Low Latency**.
- File: `Tesla_TTPoE_Hot_Chips_2024.pdf`

[B79] Shah, A. et al. (2023). **NSDI '23 Paper**. *USENIX*.
- File: `USENIX_NSDI23_Shah.pdf`

[B80] Jiang, Y. et al. (2020). **OSDI '20 Paper**. *USENIX*.
- File: `USENIX_OSDI20_Jiang.pdf`

[B81] Ghobadi, M. et al. (2024). **Cassini**. *NSDI 2024*.
- File: `Cassini_NSDI_2024_Ghobadi.pdf`

[B82] Shailesh, M. (2019). **SRoCE: Software RoCE**.
- File: `SRoCE_Mani_Shailesh.pdf`

[B83] Drepper, U. (2007). **What Every Programmer Should Know About Memory**.
- File: `Drepper_What_Every_Programmer_Should_Know_About_Memory.pdf`

[B84] MIT. (2024). **MIT LCS TR-785**.
- File: `MIT_LCS_TR-785.pdf`

[B85] Guo, Z. et al. (2010). **GPU Communication Optimization**. *IPDPS 2010*.
- File: `Rice_Guo_IPDPS_2010.pdf`

[B86] Kaplan, J. et al. (2020). **Scaling Laws for Neural Language Models**. *arXiv:2010.16248*.
- File: `Scaling_Laws_Neural_LMs_2010.16248.pdf`

### Additional Repo Articles (Newly Downloaded)

[B87] vLLM. (2025). **Anatomy of vLLM**.
- File: `Anatomy_of_vLLM.md`
- https://blog.vllm.ai/2025/09/05/anatomy-of-vllm.html

[B88] LMCache. (2025). **LMCache + vLLM v1 + NIXL**.
- File: `LMCache_vLLM_NIXL.md`
- https://blog.lmcache.ai/2025-04-11-lmcache-vllmv1-nixl/

[B89] Chips and Cheese. (2024). **Tesla's TTPoe at Hot Chips 2024**.
- File: `Tesla_TTPoe_Chips_and_Cheese.md`
- https://chipsandcheese.com/p/teslas-ttpoe-at-hot-chips-2024-replacing-tcp-for-low-latency-applications

[B90] Linux NFS Wiki. (2024). **NFS over SoftRoCE Setup**.
- File: `NFS_over_SoftRoCE_Setup.md`
- https://linux-nfs.org/wiki/index.php/NFS_over_SoftRoCE_setup

[B91] LMAX Exchange. (2011). **The LMAX Disruptor**.
- File: `LMAX_Disruptor.md`
- https://lmax-exchange.github.io/disruptor/disruptor.html

[B92] Lei Chat. (2025). **Triton Compiler Development Tips**.
- File: `Triton_Compiler_Development_Tips.md`
- https://www.lei.chat/posts/triton-compiler-development-tips/

[B93] IBM Research. (2025). **Accelerating AI Inference with IBM Storage Scale**.
- File: `IBM_Accelerating_AI_Inference_Storage_Scale.md`
- https://research.ibm.com/blog/accelerating-ai-inference-with-ibm-storage-scale

[B94] vLLM. (2026). **vLLM SR-IRIS: Semantic Router**.
- File: `vLLM_SR-IRIS.md`
- https://blog.vllm.ai/2026/01/05/vllm-sr-iris.html

[B95] llm-d. (2025). **llm-d Architecture**.
- File: `llm-d_Architecture.md`
- https://llm-d.ai/docs/architecture

[B96] AMD ROCm. (2025). **vLLM MoE Guide**.
- File: `ROCm_vLLM_MoE_Guide.md`
- https://rocm.blogs.amd.com/software-tools-optimization/vllm-moe-guide/README.html

[B97] Level1Techs. (2024). **QAT HowTo on Linux, SR-IOV and Proxmox 8**.
- File: `QAT_SRIOV_Proxmox_Level1Techs.md`
- https://forum.level1techs.com/t/qat-howto-on-linux-and-sriov-and-proxmox-8/205786

[B98] vLLM. (2025). **Disaggregated Prefilling Documentation**.
- File: `Disaggregated_Prefill_vLLM.md`
- https://docs.vllm.ai/en/latest/features/disagg_prefill/

[B99] NVIDIA. (2024). **NCCL RDMA SHARP Plugins — HPC-X**.
- File: `NCCL_RDMA_SHARP_Plugins_HPC-X.md`
- https://docs.nvidia.com/networking/display/hpcxv2200/nccl-rdma-sharp+plugins


## Multi-Node Multi-GPU Communication

[MG1] Kraus, J. (2022). **Multi-GPU Programming for Earth Scientists**. NVIDIA DevTech Compute, CISL/UCAR presentation (82 slides). https://www.cisl.ucar.edu/sites/default/files/2022-07/Multi%20Node%20Multi%20GPU%20Programming.pdf
- Covers NCCL, NVSHMEM, CUDA-aware MPI, GPUDirect (P2P + RDMA), UCX architecture
- Key comparison: GPUDirect RDMA 4.27us latency vs CUDA-aware MPI 24.56us vs regular MPI 25.64us (JUWELS Booster, A100)
- NVSHMEM GPU-initiated communication eliminates offload latencies vs CPU-initiated (slides 6-7)
- UCX NUMA-aware NIC binding with GPU affinity (slide 27, relevant to our PR #10669)
- Performance: GPUDirect RDMA ~24 GB/s at 4MB vs ~15 GB/s without GDR (slides 38-39)
- File: `References/Multi_Node_Multi_GPU_Programming_Kraus_2022.pdf`
