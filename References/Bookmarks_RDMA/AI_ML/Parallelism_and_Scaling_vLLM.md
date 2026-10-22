# Parallelism and Scaling - vLLM

- **Source:** https://docs.vllm.ai/en/stable/serving/parallelism_scaling/#ray-cluster-setup-with-containers
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

# Parallelism and Scaling[¶](#parallelism-and-scaling)

## Distributed inference strategies for a single-model replica[¶](#distributed-inference-strategies-for-a-single-model-replica)

To choose a distributed inference strategy for a single-model replica, use the following guidelines:

- **Single GPU (no distributed inference):** if the model fits on a single GPU, distributed inference is probably unnecessary. Run inference on that GPU.
- **Single-node multi-GPU using tensor parallel inference:** if the model is too large for a single GPU but fits on a single node with multiple GPUs, use *tensor parallelism*. For example, set `tensor_parallel_size=4` when using a node with 4 GPUs.
- **Multi-node multi-GPU using tensor parallel and pipeline parallel inference:** if the model is too large for a single node, combine *tensor parallelism* with *pipeline parallelism*. Set `tensor_parallel_size` to the number of GPUs per node and `pipeline_parallel_size` to the number of nodes. For example, set `tensor_parallel_size=8` and `pipeline_parallel_size=2` when using 2 nodes with 8 GPUs per node.

Increase the number of GPUs and nodes until there is enough GPU memory for the model. Set `tensor_parallel_size` to the number of GPUs per node and `pipeline_parallel_size` to the number of nodes.

After you provision sufficient resources to fit the model, run `vllm`. Look for log messages like:

The `GPU KV cache size` line reports the total number of tokens that can be stored in the GPU KV cache at once. The `Maximum concurrency` line provides an estimate of how many requests can be served concurrently if each request requires the specified number of tokens (40,960 in the example above). The tokens-per-request number is taken from the model configuration's maximum sequence length, `ModelConfig.max_model_len`. If these numbers are lower than your throughput requirements, add more GPUs or nodes to your cluster.

Edge case: uneven GPU splits

If the model fits within a single node but the GPU count doesn't evenly divide the model size, enable pipeline parallelism, which splits the model along layers and supports uneven splits. In this scenario, set `tensor_parallel_size=1` and `pipeline_parallel_size` to the number of GPUs. Furthermore, if the GPUs on the node do not have NVLINK interconnect (e.g. L40S), leverage pipeline parallelism instead of tensor parallelism for higher throughput and lower communication overhead.

### Distributed serving of *Mixture of Experts* (*MoE*) models[¶](#distributed-serving-of-mixture-of-experts-moe-models)

It's often advantageous to exploit the inherent parallelism of experts by using a separate parallelism strategy for the expert layers. vLLM supports large-scale deployment combining Data Parallel attention with Expert or Tensor Parallel MoE layers. For more information, see [Data Parallel Deployment](../data_parallel_deployment/).

## Single-node deployment[¶](#single-node-deployment)

vLLM supports distributed tensor-parallel and pipeline-parallel inference and serving. The implementation includes [Megatron-LM's tensor parallel algorithm](https://arxiv.org/pdf/1909.08053.pdf).

The default distributed runtimes are [Ray](https://github.com/ray-project/ray) for multi-node inference and native Python `multiprocessing` for single-node inference. You can override the defaults by setting `distributed_executor_backend` in the [`LLM`](../../api/vllm/entrypoints/llm/#vllm.entrypoints.llm.LLM) class or `--distributed-executor-backend` in the API server. Use `mp` for `multiprocessing` or `ray` for Ray.

For multi-GPU inference, set `tensor_parallel_size` in the [`LLM`](../../api/vllm/entrypoints/llm/#vllm.entrypoints.llm.LLM) class to the desired GPU count. For example, to run inference on 4 GPUs:

For multi-GPU serving, include `--tensor-parallel-size` when starting the server. For example, to run the API server on 4 GPUs:

To enable pipeline parallelism, add `--pipeline-parallel-size`. For example, to run the API server on 8 GPUs with pipeline parallelism and tensor parallelism:

## Multi-node deployment[¶](#multi-node-deployment)

If a single node lacks sufficient GPUs to hold the model, deploy vLLM across multiple nodes. Ensure that every node provides an identical execution environment, including the model path and Python packages. Using container images is recommended because they provide a convenient way to keep environments consistent and to hide host heterogeneity.

### What is Ray?[¶](#what-is-ray)

Ray is a distributed computing framework for scaling Python programs. Multi-node vLLM deployments can use Ray as the runtime engine.

vLLM uses Ray to manage the distributed execution of tasks across multiple nodes and control where execution happens.

Ray also offers high-level APIs for large-scale [offline batch inference](https://docs.ray.io/en/latest/data/working-with-llms.html) and [online serving](https://docs.ray.io/en/latest/serve/llm) that can leverage vLLM as the engine. These APIs add production-grade fault tolerance, scaling, and distributed observability to vLLM workloads.

Ray is an optional dependency. Install it explicitly before using Ray-based execution, for example:

For details, see the [Ray documentation](https://docs.ray.io/en/latest/index.html).

### Ray cluster setup with containers[¶](#ray-cluster-setup-with-containers)

The helper script  [examples/ray\_serving/run\_cluster.sh](https://github.com/vllm-project/vllm/blob/main/examples/ray_serving/run_cluster.sh) starts containers across nodes and initializes Ray. By default, the script runs Docker without administrative privileges, which prevents access to the GPU performance counters when profiling or tracing. To enable admin privileges, add the `--cap-add=CAP_SYS_ADMIN` flag to the Docker command.

Choose one node as the head node and run:

On each worker node, run:

Note that `VLLM_HOST_IP` is unique for each worker. Keep the shells running these commands open; closing any shell terminates the cluster. Ensure that all nodes can communicate with each other through their IP addresses.

Network security

For security, set `VLLM_HOST_IP` to an address on a private network segment. Traffic sent over this network is unencrypted, and the endpoints exchange data in a format that can be exploited to execute arbitrary code if an adversary gains network access. Ensure that untrusted parties cannot reach the network.

From any node, enter a container and run `ray status` and `ray list nodes` to verify that Ray finds the expected number of nodes and GPUs.

Tip

Alternatively, set up the Ray cluster using KubeRay. For more information, see [KubeRay vLLM documentation](https://docs.ray.io/en/latest/cluster/kubernetes/examples/rayserve-llm-example.html).

### Running vLLM on a Ray cluster[¶](#running-vllm-on-a-ray-cluster)

Tip

If Ray is running inside containers, run the commands in the remainder of this guide *inside the containers*, not on the host. To open a shell inside a container, connect to a node and use `docker exec -it <container_name> /bin/bash`.

Once a Ray cluster is running, use vLLM as you would in a single-node setting. All resources across the Ray cluster are visible to vLLM, so a single `vllm` command on a single node is sufficient.

The common practice is to set the tensor parallel size to the number of GPUs in each node, and the pipeline parallel size to the number of nodes. For example, if you have 16 GPUs across 2 nodes (8 GPUs per node), set the tensor parallel size to 8 and the pipeline parallel size to 2:

Alternatively, you can set `tensor_parallel_size` to the total number of GPUs in the cluster:

### Running vLLM with MultiProcessing[¶](#running-vllm-with-multiprocessing)

Besides Ray, Multi-node vLLM deployments can also use `multiprocessing` as the runtime engine. Here's an example to deploy model across 2 nodes (8 GPUs per node) with `tp_size=8` and `pp_size=2`.

Choose one node as the head node and run:

On the other worker node, run:

## Optimizing network communication for tensor parallelism[¶](#optimizing-network-communication-for-tensor-parallelism)

Efficient tensor parallelism requires fast internode communication, preferably through high-speed network adapters such as InfiniBand.
To set up the cluster to use InfiniBand, append additional arguments like `--privileged -e NCCL_IB_HCA=mlx5` to the
 [examples/ray\_serving/run\_cluster.sh](https://github.com/vllm-project/vllm/blob/main/examples/ray_serving/run_cluster.sh) helper script.
Contact your system administrator for more information about the required flags.

## Enabling GPUDirect RDMA[¶](#enabling-gpudirect-rdma)

GPUDirect RDMA (Remote Direct Memory Access) is an NVIDIA technology that allows network adapters to directly access GPU memory, bypassing the CPU and system memory. This direct access reduces latency and CPU overhead, which is beneficial for large data transfers between GPUs across nodes.

To enable GPUDirect RDMA with vLLM, configure the following settings:

- `IPC_LOCK` security context: add the `IPC_LOCK` capability to the container's security context to lock memory pages and prevent swapping to disk.
- Shared memory with `/dev/shm`: mount `/dev/shm` in the pod spec to provide shared memory for interprocess communication (IPC).

If you use Docker, set up the container as follows:

If you use Kubernetes, set up the pod spec as follows:

Confirm GPUDirect RDMA operation

To confirm your InfiniBand card is using GPUDirect RDMA, run vLLM with detailed NCCL logs: `NCCL_DEBUG=TRACE vllm serve ...`.

Then look for the NCCL version and the network used.

- If you find `[send] via NET/IB/GDRDMA` in the logs, then NCCL is using InfiniBand with GPUDirect RDMA, which *is* efficient.
- If you find `[send] via NET/Socket` in the logs, NCCL used a raw TCP socket, which *is not* efficient for cross-node tensor parallelism.

Pre-download Hugging Face models

If you use Hugging Face models, downloading the model before starting vLLM is recommended. Download the model on every node to the same path, or store the model on a distributed file system accessible by all nodes. Then pass the path to the model in place of the repository ID. Otherwise, supply a Hugging Face token by appending `-e HF_TOKEN=<TOKEN>` to `run_cluster.sh`.

## Troubleshooting distributed deployments[¶](#troubleshooting-distributed-deployments)

For information about distributed debugging, see [Troubleshooting distributed deployments](../distributed_troubleshooting/).