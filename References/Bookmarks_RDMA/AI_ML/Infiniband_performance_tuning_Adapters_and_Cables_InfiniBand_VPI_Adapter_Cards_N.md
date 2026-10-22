# Infiniband performance tuning - Adapters and Cables / InfiniBand/VPI Adapter Cards - NVIDIA Developer Forums

- **Source:** https://forums.developer.nvidia.com/t/infiniband-performance-tuning/207467
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

Hello,

I am trying to tune the setup I have to improve the performance of the infiniband network to the maximum possible. The current setup is as follows.

1 Dell T3600 quad core, 3.6GHz node

1 Supermicro dual quad core, 2.4GHz node

40Gbps dual port QDR cards in both the machines. Cards report up and running at 4X QDR on both the machines.

1 Mellanox IS5022 switch

I have used the following document to mount a ramdisk from the supermicro box on the dell box and then tune the various parameters as suggested by mellanox for maximum performance.

HowTo Configure NFS over RDMA (RoCE) *[https://community.mellanox.com/s/article/howto-configure-nfs-over-rdma--roce-x](https://community.mellanox.com/s/article/howto-configure-nfs-over-rdma--roce-x)*

Performance Tuning for Mellanox Adapters *[https://community.mellanox.com/s/article/performance-tuning-for-mellanox-adapters](https://community.mellanox.com/s/article/performance-tuning-for-mellanox-adapters)*

The following are the performance numbers that I am getting after all the tuning.

I am using perftest-3.2 to run a ib\_write\_bw test to test the network.

On the server side,

./ib\_write\_bw -F -a -i 2 --report\_gbits


- Waiting for client to connect… \*



RDMA\_Write BW Test

Dual-port : OFF Device : mlx4\_0

Number of qps : 1 Transport type : IB

Connection type : RC Using SRQ : OFF

CQ Moderation : 100

Mtu : 2048\[B\]

Link type : IB

Max inline data : 0\[B\]

rdma\_cm QPs : OFF

Data ex. method : Ethernet


local address: LID 0x3e QPN 0x0220 PSN 0x5f2422 RKey 0x011102 VAddr 0x007f4c1dd87000

remote address: LID 0x40 QPN 0x022f PSN 0x1afac0 RKey 0xa80993cc VAddr 0x007f197680b000


[#bytes](/tag/bytes) [#iterations](/tag/iterations) BW peak\[Gb/sec\] BW average\[Gb/sec\] MsgRate\[Mpps\]

8388608 5000 28.75 28.75 0.000428


On the client side,

./ib\_write\_bw -F -a --report\_gbits 192.168.20.253


RDMA\_Write BW Test

Dual-port : OFF Device : mlx4\_0

Number of qps : 1 Transport type : IB

Connection type : RC Using SRQ : OFF

TX depth : 128

CQ Moderation : 100

Mtu : 2048\[B\]

Link type : IB

Max inline data : 0\[B\]

rdma\_cm QPs : OFF

Data ex. method : Ethernet


local address: LID 0x40 QPN 0x022f PSN 0x1afac0 RKey 0xa80993cc VAddr 0x007f197680b000

remote address: LID 0x3e QPN 0x0220 PSN 0x5f2422 RKey 0x011102 VAddr 0x007f4c1dd87000


[#bytes](/tag/bytes) [#iterations](/tag/iterations) BW peak\[Gb/sec\] BW average\[Gb/sec\] MsgRate\[Mpps\]

2 5000 0.16 0.13 8.331405

4 5000 0.32 0.31 9.757306

8 5000 0.64 0.62 9.765456

16 5000 1.28 1.26 9.861474

32 5000 2.55 2.48 9.689547

64 5000 5.12 4.95 9.670853

128 5000 10.10 9.55 9.324976

256 5000 20.21 17.22 8.407847

512 5000 26.72 24.94 6.088563

1024 5000 28.61 28.53 3.482441

2048 5000 28.60 28.49 1.738749

4096 5000 28.56 28.56 0.871647

8192 5000 28.75 28.75 0.438630

16384 5000 28.74 28.74 0.219247

32768 5000 28.74 28.74 0.109631

65536 5000 28.74 28.74 0.054817

131072 5000 28.75 28.75 0.027418

262144 5000 28.75 28.75 0.013707

524288 5000 28.75 28.75 0.006855

1048576 5000 28.75 28.75 0.003427

2097152 5000 28.75 28.75 0.001714

4194304 5000 28.75 28.75 0.000857

8388608 5000 28.75 28.75 0.000428


In order to test it further, I copied a 5GB file from a ramdisk to the mounted ramdisk on supermicro and timed the copy.

time cp /mnt/ramdiskDEV/myrandomfile /mnt/ramdiskNAS

real 0m3.931s

user 0m0.004s

sys 0m2.748s

It looks like the copy is occurring at 10.17Gbps which seems quite low compared to the 40Gbps hardware and also with respect to 28.75 Gbps being reported by perftest. What am I missing here and how can I improve the performance of the infiniband network?

Any help is greatly appreciated!!

Thanks

Krishna