# Update 1: Hardware Setup

Dated January 2026 in the tex; the folder's history is all from 2026-01-31 (`b2ca1fe` initial commit, then `afb193e`, `2ec302a`, `11ed2b6` fixing the cost table) with a rename in `7841ac0` (2026-02-14). This update is the testbed: why commodity Ethernet with a dual-port QSFP card plus DAC is the target, what was bought and at what price, the custom X99 BIOS for Resizable BAR and Above 4G Decoding, the FPGA option for a DIY PCIe RDMA card, and a cost comparison against DGX/AWS/Lambda/Mac Studio. No experiments; it sets up the two servers 3 and 4 that later carry the hardware RoCEv2 and GPUDirect work.

## Research

RDMA and InfiniBand fundamentals
- Arch Wiki, InfiniBand: setup and verbs tooling. [InfiniBand_Setup_Guide.md](../../References/Bookmarks_RDMA/thesis_refs/InfiniBand_Setup_Guide.md), https://wiki.archlinux.org/title/InfiniBand
- Tesla TTPoe: lossy, PFC-free transport from Dojo; later a third transport in `middleware/ttpoe_transport.py`. [TTPoe_Time_Triggered_Protocol_over_Ethernet.md](../../References/Bookmarks_RDMA/thesis_refs/TTPoe_Time_Triggered_Protocol_over_Ethernet.md), [Tesla_TTPoE_Hot_Chips_2024.pdf](../../References/Bookmarks_Collection/Tesla_TTPoE_Hot_Chips_2024.pdf)

vLLM and inference frameworks
- Anatomy of vLLM: engine, scheduler and KV manager internals. [Anatomy_of_vLLM.md](../../References/Bookmarks_Collection/Anatomy_of_vLLM.md)
- vLLM forum, GPUDirect RDMA not outperforming standard RDMA in pipeline parallel: early evidence that the transport, not raw bandwidth, decides the outcome. [vLLM_GPUDirect_RDMA_Discussion.md](../../References/Bookmarks_Collection/vLLM_GPUDirect_RDMA_Discussion.md)
- r/LocalLLaMA vLLM vs TensorRT-LLM thread and the Exo distributed inference demo: motivation, not cited as evidence. No local copy.

Videos (no local copies; YouTube links in the tex)
- "Everything You Wanted to Know About RDMA But Were Too Proud to Ask" (listed as "Distributed LLM Inference Overview"); the slide deck is at [Everything-You-Wanted-to-Know-About-RDMA-But-Were-Too-Proud-to-Ask-Final v2.pdf](<../../References/Everything-You-Wanted-to-Know-About-RDMA-But-Were-Too-Proud-to-Ask-Final v2.pdf>).
- Apple RDMA over Thunderbolt for Mac clusters: a side interest, never pursued here.

Hardware
- r/LocalLLaMA InfiniBand vs PCIe thread: PCIe 3.0 x8 bandwidth ceiling for a 3090-class card.
- Community list of cheapest VRAM per dollar: the case for 2x V100 32 GB.
- [x99-udp4-rebar](https://github.com/ndg8743/x99-udp4-rebar): the custom BIOS.

## Work done

- Server 3 (Windows): Ryzen 9 7950X, 192 GB DDR5-5200, RTX 5070 Ti 16 GB, ConnectX-4 100GbE.
- Server 4 (Proxmox): X99 UD4P, Xeon E5-2697A v4, 128 GB DDR4 ECC, 2x Tesla V100 32 GB, ConnectX-4 100GbE.
- Custom BIOS flashed on server 4 for Resizable BAR and 4G decoding.
- Photos and price screenshots in this folder.

The tex records the hardware total as about $3,532. That is a purchase record, not a result.

## Next steps as written, status today

Update 1 has no Next Steps section. Two open items are written into the text:

| Item | Status | Evidence |
|---|---|---|
| PCIe extender or higher-wattage PSU so both V100s boot | done (implied) | Backlog draft `Update8-InfrastructureRDMATesting` runs both V100s and the ConnectX-4 on server 4. |
| GPUDirect RDMA on servers 3 and 4 | open | Same draft: `nvidia-peermem` fails because the PVE kernel lacks `CONFIG_INFINIBAND_PEER_MEM`; a kernel rebuild was started. README still lists server 4 GPUDirect as pending. |

The hardware RoCEv2 bring-up that followed this update (ConnectX-4 switched from IB to Ethernet with `mstconfig`, 50.62 Gb/s `ib_write_bw` loopback limited by PCIe 3.0 x8, 0.71 us `ib_write_lat`) is in the backlog draft [`Drafts/updates-todo/Update8-InfrastructureRDMATesting`](../Drafts/updates-todo/README.md), not in a numbered update.

## Run it

- [`notebooks/00_environment_check.ipynb`](../../notebooks/00_environment_check.ipynb) on server 3 / server 4: confirms the ConnectX-4 shows up as a RoCEv2 device, lists libfabric providers, checks `nvidia-peermem`.
- [`notebooks/03_libfabric_vs_libibverbs.ipynb`](../../notebooks/03_libfabric_vs_libibverbs.ipynb) with servers 3 and 4 as the pair: the only place in the lab with hardware RoCEv2, so the only place where hot/cold QP isolation is done by the NIC rather than the rxe kernel thread.
- [`scripts/setup_softroce_tower2.sh`](../../scripts/setup_softroce_tower2.sh) for SoftRoCE on server 4.

## Corrections

- The FPGA paragraph lists servers 1 and 2 and the Hydra cluster as "home towers". Servers 1 and 2 are the lab machines and Hydra is the lab cluster; the home machines are servers 3 and 4.
- The cost table's "Est. tok/s (70B)" column (about 18 tok/s for the homelab, etc.) is an estimate, not a measurement. Do not cite it as a result.
- "100Gbit networking" on servers 3 and 4 is the link, not an RDMA path: Update 3 lists server 3's RDMA as TCP/gRPC fallback because it runs Windows. Hardware RoCEv2 between servers 3 and 4 needs server 3 booted into Linux.
