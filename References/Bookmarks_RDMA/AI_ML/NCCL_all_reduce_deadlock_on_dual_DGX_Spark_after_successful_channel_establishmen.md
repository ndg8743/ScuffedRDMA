# NCCL all-reduce deadlock on dual DGX Spark after successful channel establishment — affects both vLLM and TRT-LLM - DGX Spark / GB10 User Forum / DGX Spark / GB10 - NVIDIA Developer Forums

- **Source:** https://forums.developer.nvidia.com/t/nccl-all-reduce-deadlock-on-dual-dgx-spark-after-successful-channel-establishment-affects-both-vllm-and-trt-llm/366127/3
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

[helm](https://forums.developer.nvidia.com/u/helm)
                  
                
              
              
                  
                  
              3
              
            
            
              Salut aniculescu and thank you for your response.

We followed the NCCL stacked-sparks playbook exactly as directed. N1 and N2 in the below refer to Spark 1 and Spark 2.  Here’s what happened:

## 

1. Built NCCL v2.28.9-1 from source on both nodes per the playbook (`make -j src.build NVCC_GENCODE="-gencode=arch=compute_121,code=sm_121"`). **Note:** This required patching `/usr/local/cuda/include/crt/math_functions.h` on both nodes — the shipping DGX OS (Ubuntu 25.10, kernel 6.17.0-1014-nvidia) has a glibc `rsqrt` exception specification that is incompatible with CUDA 13.0’s `math_functions.h`. Without patching lines 629 and 653 to add `noexcept`, the NCCL build fails with:

```
/usr/include/aarch64-linux-gnu/bits/mathcalls.h(206): error: exception specification 
is incompatible with that of previous function "rsqrt"
```

1. Built nccl-tests with `make MPI=1` on both nodes — successful.
2. Verified CX7 connectivity: `enp1s0f0np0` UP on both nodes, IPs 192.168.200.1/24 and 192.168.200.2/24, ping \< 1ms, passwordless SSH working (`ssh 192.168.200.2 hostname` returns “N2” correctly).
3. Ran the playbook’s cross-node test exactly as specified:

```
export UCX_NET_DEVICES=enp1s0f0np0
export NCCL_SOCKET_IFNAME=enp1s0f0np0
export OMPI_MCA_btl_tcp_if_include=enp1s0f0np0
mpirun -np 2 -H 192.168.200.1:1,192.168.200.2:1 \
  --mca plm_rsh_agent "ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no" \
  -x LD_LIBRARY_PATH=$LD_LIBRARY_PATH \
  $HOME/nccl-tests/build/all_reduce_perf -b 8 -e 128M -f 2 -g 1
```

## 

The nccl-tests binary fails with:

```
Invalid number of GPUs: 2 requested but only 1 were found.
```

We isolated the issue to OpenMPI itself. Running `mpirun -np 2 -H 192.168.200.1:1,192.168.200.2:1 hostname` returns:

```
N1
N1
```

Both MPI ranks execute on N1 despite SSH to 192.168.200.2 completing successfully (`ssh 192.168.200.2 hostname` returns “N2” correctly from the same shell). We tested with:

- `-H` flag and `--host` flag — same result
- `--hostfile` with explicit `slots=1` — same result
- `--map-by :OVERSUBSCRIBE` — same result
- With and without `--mca plm_rsh_agent` — same result
- Both GPUs free (Ollama stopped on both nodes) — same result

OpenMPI version: 5.0.8 (shipping with DGX OS).

## 

**Issue 1: NCCL build fails on shipping DGX OS.** The CUDA 13.0 `math_functions.h` header is incompatible with Ubuntu 25.10’s glibc math headers. The playbook’s build command fails out of the box. A manual header patch is required.

**Issue 2: OpenMPI 5.0.8 cannot distribute MPI ranks across DGX Spark nodes via CX7 IP addresses.** This blocks the NCCL playbook’s cross-node test entirely, and is likely the root cause of the TP deadlocks we reported in the original post — if MPI can’t distribute processes correctly, the NCCL all-reduce will deadlock because both ranks try to use the same single GPU.

## 

- 2x DGX Spark (GB10), driver 580.126.09, CUDA 13.0
- DGX OS: Ubuntu 25.10, kernel 6.17.0-1014-nvidia
- ConnectX-7 DAC: Amphenol (NVIDIA-shipped with the Sparks)
- CX7 interface: `enp1s0f0np0`, MTU 9000

## 

1. Is there a known fix for OpenMPI 5.0.8 cross-node process distribution on DGX Spark?
2. Is the CUDA header incompatibility with Ubuntu 25.10’s glibc a known issue?
3. Can NVIDIA provide a confirmed working software configuration (OpenMPI version, DGX OS version, CUDA version) for the stacked-sparks NCCL playbook?

Mulțumesc!