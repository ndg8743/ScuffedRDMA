from nbtools import build

params = '''MODE = "local"            # "local" or "cluster" (run on each node)
RESULTS_SUBDIR = "env"
NETDEV = None             # 10GbE interface carrying SoftRoCE, e.g. "enp1s0f0"; used only to print the rxe setup command
RUN_TESTS = True'''

cells = [
("md", """Run this first on every node. It records what the node actually has (RDMA devices, GIDs, libfabric providers,
pyverbs, compilers), builds the three native libraries, and runs the test suite. On a node with an RDMA
device the `rdma`-marked tests run too (verbs provider, `verbs;ofi_rxm`, native libibverbs loopback over rxe0)."""),
("code", '''import platform, shutil
info = {"uname": platform.uname()._asdict(), "python": sys.version, "cpus": os.cpu_count()}
for cmd in ["lscpu | head -20", "nproc", "uname -r"]:
    info[cmd] = sh(cmd, check=False).stdout'''),
("md", "## RDMA devices and GIDs"),
("code", '''ib = Path("/sys/class/infiniband")
devs = sorted(p.name for p in ib.iterdir()) if ib.is_dir() else []
info["rdma_devices"] = devs
print("RDMA devices:", devs or "none")
if not devs:
    nd = NETDEV or "<10GbE iface>"
    print(f"No device. SoftRoCE: sudo modprobe rdma_rxe && sudo rdma link add rxe0 type rxe netdev {nd}")
gids = []
for d in devs:
    for g in sorted((ib / d / "ports/1/gids").iterdir(), key=lambda p: int(p.name)):
        val = g.read_text().strip()
        if val.strip("0:") == "":
            continue
        try:
            typ = (ib / d / "ports/1/gid_attrs/types" / g.name).read_text().strip()
        except OSError:
            typ = "?"
        gids.append({"dev": d, "index": int(g.name), "gid": val, "type": typ})
info["gids"] = gids
pd_gids = __import__("pandas").DataFrame(gids) if gids else None
pd_gids'''),
("code", '''for cmd in ["ibv_devices", "ibv_devinfo -v | head -60", "rdma link show"]:
    if shutil.which(cmd.split()[0]):
        info[cmd] = sh(cmd, check=False).stdout'''),
("md", "## libfabric providers and pyverbs"),
("code", '''if shutil.which("fi_info"):
    info["fi_info_version"] = sh("fi_info --version", check=False).stdout
    info["fi_providers"] = [l.strip(" :") for l in sh("fi_info -l", check=False).stdout.split("\\n") if l and not l.startswith(" ")]
    for p in ["verbs", "verbs;ofi_rxm", "tcp", "shm"]:
        r = sh(f"fi_info -p '{p}' -c 'FI_RMA|FI_MSG' 2>/dev/null | grep -E 'provider|type|domain' | head -6", check=False)
        info[f"fi_info[{p}]"] = r.stdout
else:
    print("libfabric missing: sudo apt install libfabric-dev libfabric-bin")
try:
    import pyverbs.device as d
    info["pyverbs"] = [x.name.decode() for x in d.get_device_list()]
except Exception as e:
    info["pyverbs"] = f"unavailable: {e}"
print("pyverbs:", info["pyverbs"])'''),
("md", "## Build the native libraries"),
("code", '''for d in ["middleware/libscuffedfabric", "middleware/libscuffedverbs", "middleware/nccl_plugin"]:
    r = sh(f"make -C {d}", check=False)
    info[f"build:{d}"] = "ok" if r.returncode == 0 else r.stderr[-1500:]
    print(d, info[f"build:{d}"][:200])'''),
("md", "## Test suite"),
("code", '''if RUN_TESTS:
    r = sh("python3 -m pytest -q -p no:cacheprovider", check=False)
    info["pytest"] = r.stdout[-3000:]
    print("pytest exit", r.returncode)'''),
("code", '''save("environment", info)'''),
]

build("00_environment_check.ipynb", "00 · Environment check",
      "What this node can run: RDMA devices, GIDs, libfabric providers, pyverbs, native builds, tests.",
      params, cells)
