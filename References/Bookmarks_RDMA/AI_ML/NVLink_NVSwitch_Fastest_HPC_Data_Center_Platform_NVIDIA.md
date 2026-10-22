# NVLink & NVSwitch: Fastest HPC Data Center Platform | NVIDIA

- **Source:** https://www.nvidia.com/en-us/data-center/nvlink/
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

Scale-up networking fabric with high-bandwidth GPU-to-GPU communications for AI training, inference, and other demanding rack-scale GPU-accelerated workloads.

Reaching the highest performance for the latest AI models requires seamless, high-throughput GPU-to-GPU communications across the entire server rack. With low latency, massive networking bandwidth, and all-to-all connectivity, the sixth-generation NVIDIA NVLink™ and NVLink Switch are designed to accelerate training and inference for faster reasoning and agentic AI workloads.

The sixth-generation NVLink enables 3 TB/s of bandwidth per GPU for the [NVIDIA Vera Rubin platform](https://www.nvidia.com/en-us/data-center/technologies/rubin/)—1.7x more bandwidth than the previous generation and 12x the bandwidth of PCIe Gen6. Rack-scale architectures like [NVIDIA Vera Rubin NVL72](https://www.nvidia.com/en-us/data-center/vera-rubin-nvl72/) connect 72 GPUs in an all-to-all topology for a total of 216 TB/s, providing massive bandwidth for the all-to-all communications needed for training and inference of leading mixture-of-experts model architectures. NVLink 6 Switch also introduces new management and resiliency features designed to maximize system uptime, including control plane resilience, the ability to run with a partially populated rack, and hot-swapping of switch trays.

Sixth-generation NVIDIA NVLink in NVIDIA Vera Rubin increases GPU-to-GPU communication bandwidth by 1.7x compared to the previous generation for faster training and inference with the latest AI model architectures.

NVLink is a 3 TB/s bidirectional, direct GPU-to-GPU interconnect that scales multi-GPU input and output (IO) within a server. The NVIDIA NVLink Switch chips connect multiple NVLinks to provide all-to-all GPU communication at full NVLink speed across the entire rack.

To enable high-speed, collective operations, each NVLink Switch has engines for NVIDIA Scalable Hierarchical Aggregation and Reduction Protocol (SHARP)™ for in-network reductions and multicast acceleration.

With NVLink Switch, NVLink connections can be extended across nodes to create a seamless, high-bandwidth, multi-node GPU cluster—effectively forming a data-center-sized GPU. NVIDIA NVLink Switch enables 216 TB/s of GPU bandwidth in one NVIDIA Vera Rubin NVL72 for large model parallelism. Multi-server clusters with NVLink scale GPU communications in balance with the increased computing, so NVIDIA Vera Rubin NVL72 can support 9x the GPU count versus a single eight-GPU system.

NVIDIA NVLink™ Fusion delivers industry-leading AI scale-up and scale-out performance with NVIDIA technology plus semi-custom ASICs or CPUs, enabling hyperscalers to build an ASIC hybrid AI infrastructure with NVIDIA NVLink technology and rack-scale architecture.

The NVLink Switch chip in Vera Rubin NVL72 enables 72 fully connected GPUs in a non-blocking compute fabric. The NVLink Switch interconnects every GPU pair at an incredible 3 TB/s. It supports full all-to-all communication. The 72 GPUs in Vera Rubin NVL72 can be used as a single high-performance accelerator with up to 3.6 exaFLOPS of AI compute power.

NVLink and NVLink Switch are essential building blocks of the complete NVIDIA data center solution that incorporates hardware, networking, software, libraries, and optimized AI models and applications from the NVIDIA AI Enterprise software suite and the NVIDIA NGC™ catalog. The most powerful end-to-end AI and HPC platform, it allows researchers to deliver real-world results and deploy solutions into production, driving unprecedented acceleration at every scale.

|  | Fourth Generation | Fifth Generation | Sixth Generation | 
|---|---|---|---|
| NVLink Bandwidth per GPU | 900 GB/s | 1,800 GB/s | 3,000 GB/s | 
| Maximum Number of Links per GPU | 18 | 18 | 36 | 
| Supported NVIDIA Architectures/Platforms | NVIDIA Hopper™ | NVIDIA Blackwell | NVIDIA Vera Rubin | 

|  | NVLink 4 Switch | NVLink 5 Switch | NVLink 6 Switch | 
|---|---|---|---|
| NVLink GPU Domains | 8 | 8 \| 72 | 8 \| 72 | 
| NVLink Switch GPU-to-GPU Bandwidth | 900 GB/s | 1,800 GB/s | 3,000 GB/s | 
| Total Aggregate Bandwidth | 7.2 TB/s | 130 TB/s (NVL72) | 216 TB/s (NVL72) | 
| Supported NVIDIA Architectures/Platforms | NVIDIA Hopper | NVIDIA Blackwell | NVIDIA Vera Rubin | 

Built to accelerate the next generation of agentic AI, NVIDIA Blackwell Ultra delivers breakthrough inference performance with dramatically lower cost. Cloud providers such as Microsoft, CoreWeave, and Oracle Cloud Infrastructure are deploying NVIDIA GB300 NVL72 systems at scale for low-latency and long-context use cases, such as agentic coding and coding assistants.

This is enabled by deep co-design across NVIDIA Blackwell, NVLink™, and NVLink Switch for scale-out; NVFP4 for low-precision accuracy; and NVIDIA Dynamo and TensorRT™ LLM for speed and flexibility—as well as development with community frameworks SGLang, vLLM, and more.

Learn more about the NVIDIA Vera Rubin Platform.