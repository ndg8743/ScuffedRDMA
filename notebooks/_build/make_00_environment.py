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
("md", "## Hardware of this machine\n\nWritten to `docs/figures/<MODE>/HARDWARE.md` so every measured figure has the machine it came from next to it."),
("code", '''import re, json as _json
def _cmd(c):
    r = subprocess.run(c, shell=True, text=True, capture_output=True); return (r.stdout or r.stderr).strip()
hw = {"host": HOST, "mode": MODE, "utc": STAMP}
hw["virtualization"] = _cmd("systemd-detect-virt 2>/dev/null || echo unknown")
hw["os"] = _cmd("grep PRETTY_NAME /etc/os-release | cut -d= -f2").strip(chr(34))
hw["kernel"] = _cmd("uname -r")
lscpu = {k.strip(): v.strip() for k, v in (l.split(":", 1) for l in _cmd("lscpu").splitlines() if ":" in l)}
hw["cpu"] = {k: lscpu.get(k) for k in ("Model name", "CPU(s)", "Thread(s) per core", "Core(s) per socket", "Socket(s)",
                                     "CPU max MHz", "Hypervisor vendor", "L1d cache", "L2 cache", "L3 cache", "NUMA node(s)") if lscpu.get(k)}
mem = {l.split()[0].rstrip(":"): int(l.split()[1]) for l in Path("/proc/meminfo").read_text().splitlines()[:3]}
hw["memory_GiB"] = round(mem.get("MemTotal", 0) / 2**20, 1)
hw["block_devices"] = chr(10).join(l for l in _cmd("lsblk -d -o NAME,SIZE,TYPE,ROTA,MODEL 2>/dev/null").splitlines() if re.search(r"\\s\\d+(\\.\\d+)?[GT]\\s", l))
hw["tmp_mount"] = _cmd("df -h /tmp | tail -1")
nics = []
for n in sorted(os.listdir("/sys/class/net")):
    if n == "lo" or n.startswith(("ifb", "veth", "docker", "br-")): continue
    spd = Path(f"/sys/class/net/{n}/speed"); st = Path(f"/sys/class/net/{n}/operstate")
    sp_ = spd.read_text().strip() if spd.exists() else "?"
    nics.append({"iface": n, "speed_Mbps": "unknown" if sp_ in ("-1", "?") else sp_, "state": st.read_text().strip() if st.exists() else "?",
                 "driver": os.path.basename(os.path.realpath(f"/sys/class/net/{n}/device/driver")) if Path(f"/sys/class/net/{n}/device/driver").exists() else "virtual"})
hw["nics"] = nics
hw["pci_net_rdma"] = _cmd("lspci 2>/dev/null | grep -iE 'ethernet|infiniband|network' ")
hw["rdma_devices"] = sorted(os.listdir("/sys/class/infiniband")) if Path("/sys/class/infiniband").is_dir() else []
hw["gpu"] = _cmd("nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>/dev/null || echo none")
hw["libfabric"] = _cmd("fi_info --version 2>/dev/null | head -1 || echo missing")
hw["libfabric_providers"] = sorted({l.strip(" :") for l in _cmd("fi_info -l 2>/dev/null").splitlines() if l and not l.startswith(" ")})
hw["rdma_core"] = _cmd("dpkg-query -W -f='${Version}' rdma-core 2>/dev/null || echo ?")
hw["python"] = sys.version.split()[0]
for mod in ("numpy", "torch", "vllm"):
    try: hw[mod] = __import__(mod).__version__
    except Exception: hw[mod] = "not installed"
hw["compiler"] = _cmd("gcc --version | head -1")
md = [f"# Hardware: `{HOST}` ({MODE} mode)", "", f"Captured {STAMP} by notebook 00. Measured figures in this directory come from this machine.", "",
      "| | |", "|---|---|",
      f"| Virtualization | {hw['virtualization']}" + (f" on {hw['cpu']['Hypervisor vendor']}" if hw['cpu'].get('Hypervisor vendor') else "") + " |", f"| OS / kernel | {hw['os']} / {hw['kernel']} |",
      f"| CPU | {hw['cpu'].get('Model name', '?')}; {hw['cpu'].get('CPU(s)', '?')} logical CPUs, {hw['cpu'].get('Core(s) per socket', '?')} cores x {hw['cpu'].get('Socket(s)', '?')} socket(s), {hw['cpu'].get('Thread(s) per core', '?')} thread(s)/core |",
      f"| Caches | L1d {hw['cpu'].get('L1d cache', '?')}, L2 {hw['cpu'].get('L2 cache', '?')}, L3 {hw['cpu'].get('L3 cache', '?')} |",
      f"| Memory | {hw['memory_GiB']} GiB |",
      f"| Block devices (>= 1 GiB; ROTA 1 = reported rotational) | {' / '.join(' '.join(l.split()) for l in hw['block_devices'].splitlines()) or '?'} |",
      f"| /tmp (local-mode results and spill) | {hw['tmp_mount']} |",
      "| NICs | " + (", ".join(n["iface"] + " (" + n["driver"] + ", " + str(n["speed_Mbps"]) + " Mb/s, " + n["state"] + ")" for n in nics) or "none") + " |",
      f"| RDMA devices | {', '.join(hw['rdma_devices']) or 'none'} |",
      f"| GPU | {hw['gpu']} |",
      f"| libfabric | {hw['libfabric']}; providers: {', '.join(hw['libfabric_providers'])} |",
      f"| rdma-core | {hw['rdma_core']} |",
      f"| Python / numpy / torch / vLLM | {hw['python']} / {hw['numpy']} / {hw['torch']} / {hw['vllm']} |",
      f"| Compiler | {hw['compiler']} |", ""]
if MODE == "local":
    md += ["Local mode is a smoke test: no RDMA device, libfabric `tcp` / `shm` providers in loopback, `/tmp` on a virtual disk instead of NVMe. Nothing measured here is a thesis result.", ""]
hwp = FIGDIR / MODE / "HARDWARE.md"; hwp.write_text(chr(10).join(md)); print("wrote", hwp.relative_to(ROOT)); print(chr(10).join(md))
info["hardware"] = hw'''),
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
