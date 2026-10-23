"""Parameter cell shared by notebooks 01-03."""

PARAMS = '''MODE = "local"            # "local": smoke runs on this machine (tcp / tcp;ofi_rxm / shm providers)
                          # "cluster": this host is the client, the server runs on PEER over ssh
PEER = "cerberus"         # ssh host for the server side (cluster mode)
PEER_IP = "192.168.1.242" # server address on the RDMA netdev; default taken from benchmark_dual_qp_remote.py, check it
REMOTE_REPO = None        # repo path on PEER if it differs from this host
DOMAIN = "rxe0"           # RDMA device / libfabric domain on both nodes
SV_GID_INDEX = None       # set if the auto-picked GID (first IPv4-mapped) is wrong, e.g. "1"
HOT_CPU = None            # pin the hot loop (cluster: pick a core away from the NIC IRQs)
COLD_CPU = None           # pin the cold stream thread
ITERS = None              # None: 2000 local, 20000 cluster
'''

COMMON = '''from benchmarks.fabric import runner
import pandas as pd
import matplotlib.pyplot as plt
pd.set_option("display.width", 200); pd.set_option("display.max_columns", 30)
CLUSTER = MODE == "cluster"
N = ITERS or (20000 if CLUSTER else 2000)
W = max(100, N // 20)
PAIR = dict(peer=PEER, peer_ip=PEER_IP, remote_repo=REMOTE_REPO) if CLUSTER else {}
ENV = {"SV_GID_INDEX": str(SV_GID_INDEX)} if SV_GID_INDEX is not None else {}
STACKS = runner.stacks(MODE)
if CLUSTER:
    for st in STACKS:
        if st["tool"] == "sf_bench":
            st["args"] += ["-d", DOMAIN]
        else:
            ENV.setdefault("SV_IB_PORT", "1")
PIN = (["--hot-cpu", str(HOT_CPU)] if HOT_CPU is not None else []) + (["--cold-cpu", str(COLD_CPU)] if COLD_CPU is not None else [])
print(runner.build(remote=PEER if CLUSTER else None, remote_repo=REMOTE_REPO))
for st in STACKS: print(st["label"], st["tool"], st["args"])'''
