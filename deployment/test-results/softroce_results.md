# Soft-RoCE results (Feb 2, 2026)

Chimera (192.168.1.150, Aquantia 10G enp71s0) to Cerberus (192.168.1.242, Intel X710 10G eno2np1). Both with `rxe0`.

## ib_write_bw

| Link | BW avg |
|------|--------|
| WiFi (wlp227s0) | 0.28 Gb/s |
| 10G Ethernet | 0.92 Gb/s |

## ib_write_lat (2-byte, 1000 iters, 10G)

```
min      130.21 us
avg      189.61 us
99%      207.14 us
99.9%    219.66 us
```

Software RDMA is CPU-bound and adds kernel overhead. 10GbE Soft-RoCE is usable for development; hardware RoCE on ConnectX would be ~2 us range.

## Reproduce

```bash
sudo modprobe rdma_rxe
sudo rdma link add rxe0 type rxe netdev <interface>

# server
ib_write_bw -d rxe0 --report_gbits
ib_write_lat -d rxe0

# client
ib_write_bw -d rxe0 --report_gbits <server_ip>
ib_write_lat -d rxe0 <server_ip>
```

Firewall: `sudo ufw allow from 192.168.1.0/24 to any port 4791 proto udp comment 'RoCEv2'`.
