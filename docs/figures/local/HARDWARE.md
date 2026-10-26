# Hardware: `vm` (local mode)

Captured 20261026T181938Z by notebook 00. Measured figures in this directory come from this machine.

| | |
|---|---|
| Virtualization | docker on KVM |
| OS / kernel | Ubuntu 24.04.5 LTS / 6.18.44-fc-v153 |
| CPU | Intel(R) Xeon(R) Processor @ 2.80GHz; 2 logical CPUs, 2 cores x 1 socket(s), 1 thread(s)/core |
| Caches | L1d 64 KiB (2 instances), L2 2 MiB (2 instances), L3 33 MiB (1 instance) |
| Memory | 7.8 GiB |
| Block devices (>= 1 GiB; ROTA 1 = reported rotational) | vda 256G disk 1 |
| /tmp (local-mode results and spill) | /dev/vda        252G   19G   25G  44% / |
| NICs | eth0 (virtio_net, unknown Mb/s, up) |
| RDMA devices | none |
| GPU | none |
| libfabric | fi_info: 1.17.0; providers: net, ofi_hook_debug, ofi_hook_dmabuf_peer_mem, ofi_hook_hmem, ofi_hook_noop, ofi_hook_perf, ofi_mrail, ofi_rxd, ofi_rxm, psm, psm2, shm, sockets, tcp, udp |
| rdma-core | 50.0-2ubuntu0.2 |
| Python / numpy / torch / vLLM | 3.13.17 / 2.5.3 / 2.14.1+cpu / not installed |
| Compiler | gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0 |

Local mode is a smoke test: no RDMA device, libfabric `tcp` / `shm` providers in loopback, `/tmp` on a virtual disk instead of NVMe. Nothing measured here is a thesis result.
