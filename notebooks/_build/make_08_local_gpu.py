from nbtools import build

params = '''MODE = "local"            # "gpu": one machine with an NVIDIA GPU (desktop under WSL2, or server 1 / server 2 alone)
                          # "local": no GPU; every GPU cell reports what it would run and skips
RESULTS_SUBDIR = "local_gpu"
MODEL = "ibm-granite/granite-3.3-2b-instruct"
GPU_UTIL_EACH = 0.40      # two vLLM instances share one GPU (prefill + decode); 2 x 0.40 fits a 16 GB card with Granite 3.3-2B
MAX_MODEL_LEN = 4096
VLLM_EXTRA = "--enforce-eager"   # no CUDA graphs: less memory, slower; drop it on a 24 GB+ card
PROVIDER = "shm"          # both instances on one host: shm (RDM). "tcp" with EP_TYPE="msg" also works;
                          # on a node with an RDMA NIC (server 3's ConnectX-4) "verbs" + "msg" loops back through the NIC (untested)
EP_TYPE = "rdm"
PROMPT_LENS = "128,512,1024,2048,3072"
N_REQ = 10                # requests per prompt length in the TTFT sweep
RUN_VLLM = True
RUN_SCUFFEDQUANT = True
NIXL_BACKENDS = ""        # "UCX,LIBFABRIC" to add NixlConnector baselines; needs `setup_gpu_env.sh --nixl`
STARTUP_TIMEOUT_S = 900'''

cells = [
("md", """Everything in the thesis stack that a single GPU can exercise, on one machine. No RDMA device is needed:
the two vLLM instances talk through libfabric's `shm` (or `tcp`) provider, which is the same
`FabricBlobChannel` code path the verbs provider uses between server 1 and server 2.

What it checks, in order:
1. GPU, torch, vLLM versions; native builds; the full test suite including the `gpu`-marked tests.
2. The connector against the installed vLLM's `KVConnectorBase_V1` (signature check).
3. Connector data path with KV caches **on the GPU**, byte-exact, over TCP and libfabric.
4. scuffedQuant on real Granite 3.3-2B KV (per-layer top-8 overlap, mean ± std, packed sizes).
5. **vLLM disaggregated serving on one GPU**: prefill instance (`kv_producer`) and decode instance
   (`kv_consumer`) with `ScuffedRdmaConnector` and the proxy; greedy outputs compared token for token
   with a single-instance run; TTFT / ITL sweep for both.
6. GPU decompression benchmark and a libfabric loopback sanity check on this CPU.

**What these numbers are.** Same-host transfers through shared memory or loopback TCP. They show the
connector works inside real vLLM with real GPU tensors and what it costs relative to a single instance on
this machine. They are not the cross-node transport results (notebooks 01 to 03 and 06 on the lab nodes).

**Setup, once** (Ubuntu under WSL2 on the Windows desktop, or native Linux):
```
wsl --install -d Ubuntu-24.04                     # PowerShell, Windows only; CUDA comes from the Windows NVIDIA driver
git clone https://github.com/ndg8743/ScuffedRDMA ~/ScuffedRDMA && cd ~/ScuffedRDMA
bash scripts/local_gpu/setup_gpu_env.sh           # apt libfabric/rdma-core, venv with CUDA torch + vLLM, builds, tests
. ~/scuffed/bin/activate && jupyter lab notebooks/08_local_gpu.ipynb
```
Pick the "scuffed (CUDA)" kernel and set `MODE = "gpu"`. `setup_gpu_env.sh --check` reports what is installed.
RTX 50-series (SM_120) needs a vLLM build against CUDA 12.8 or newer; the first cell prints what is installed."""),
("code", '''import importlib, signal, shutil, urllib.request
info = {}
try:
    import torch
    info["torch"] = torch.__version__
    info["cuda_available"] = torch.cuda.is_available()
    if torch.cuda.is_available():
        p = torch.cuda.get_device_properties(0)
        info["gpu"] = {"name": p.name, "capability": f"{p.major}.{p.minor}", "mem_gb": round(p.total_memory / 2**30, 1),
                       "cuda": torch.version.cuda}
except Exception as e:
    info["torch"] = f"unavailable: {e}"
    info["cuda_available"] = False
try:
    import vllm
    info["vllm"] = vllm.__version__
    info["vllm_path"] = str(Path(vllm.__file__).parent.parent)
except Exception as e:
    info["vllm"] = f"unavailable: {e}"
GPU = MODE == "gpu" and info.get("cuda_available", False)
if MODE == "gpu" and not GPU:
    print("MODE='gpu' but torch sees no CUDA device; GPU cells will skip")
if shutil.which("nvidia-smi"):
    info["nvidia_smi"] = sh("nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used --format=csv", check=False).stdout
info'''),
("md", "## 1. Build and test"),
("code", '''for d in ["middleware/libscuffedfabric", "middleware/libscuffedverbs", "middleware/nccl_plugin"]:
    r = sh(f"make -C {d}", check=False)
    info[f"build:{d}"] = "ok" if r.returncode == 0 else r.stderr[-800:]
env = dict(os.environ)
if "vllm_path" in info:
    env["VLLM_SRC"] = info["vllm_path"]   # lets the connector signature test run against the installed vLLM
r = subprocess.run("python3 -m pytest -q -p no:cacheprovider -rs", shell=True, cwd=ROOT, text=True, capture_output=True, env=env)
info["pytest"] = r.stdout[-4000:]
print(r.stdout[-2500:])'''),
("md", "## 2. Connector data path with KV caches on the GPU"),
("code", '''from middleware.vllm_plugin.loopback import default_args, run_both
loop = []
if GPU:
    for transport, prov, ep in [("tcp", None, None), ("fabric", PROVIDER, EP_TYPE), ("fabric", "tcp", "msg")]:
        a = default_args(transport=transport, provider=prov, ep_type=ep, device="cuda:0",
                         prompt_lens=[128, 512, 2048], timeout=300.0)
        out = run_both(a)
        for pr, co in zip(out["producer"]["requests"], out["consumer"]["requests"]):
            loop.append({"transport": f"{transport}/{prov or '-'}/{ep or '-'}", "prompt_len": pr["prompt_len"],
                         "push_ms": pr["push_ms"], "load_ms": co["load_ms"], "match": pr["digest"] == co["digest"]})
    print("all byte-exact:", all(x["match"] for x in loop))
else:
    print("skipped (no GPU); the CPU version of this check runs in notebook 06")
import pandas as pd
pd.DataFrame(loop)'''),
("md", "## 3. scuffedQuant on real Granite 3.3-2B KV"),
("code", '''sq = {}
if GPU and RUN_SCUFFEDQUANT:
    out = RESULTS / f"{HOST}_scuffed_quant_llm.json"
    sh(f"python3 benchmarks/benchmark_scuffed_quant_llm.py --device cuda --bits 3 --qjl-dim 256 --output {out}", check=False)
    if out.exists():
        d = json.loads(out.read_text())
        ov = [l["topk_overlap"] for l in d["layers"]]
        import statistics as st
        sq = {"layers": len(ov), "top8_mean": st.mean(ov), "top8_std": st.stdev(ov), "top8_min": min(ov),
              "head_dim": d.get("head_dim"), "summary": d.get("summary")}
        from middleware.rdma_tensor_cache.scuffed_quant import ScuffedQuant
        import numpy as np
        hd = d.get("head_dim", 64)
        c = ScuffedQuant(dim=hd, bits=3, qjl_dim=256).compress(np.random.default_rng(0).standard_normal((1024, hd)).astype(np.float32))
        sq["packed_bytes_per_vector"] = c.nbytes / 1024
        sq["ratio_vs_fp16"] = hd * 2 / sq["packed_bytes_per_vector"]
else:
    print("skipped (no GPU or RUN_SCUFFEDQUANT=False)")
sq'''),
("md", """## 4. vLLM disaggregated serving on one GPU

Decode (`kv_consumer`) starts first and listens for KV; prefill (`kv_producer`) pushes each layer's KV for
each request through `FabricBlobChannel`; the proxy sends the prompt to prefill with `max_tokens=1`, then
the full request to decode. Then the same prompts go to a single instance with no connector."""),
("code", '''import time as _t
from benchmarks.vllm_disagg import run_ttft_sweep as ttft
LAUNCH = ROOT / "benchmarks" / "vllm_disagg" / "launch.sh"
LOGS = RESULTS / "logs"; LOGS.mkdir(parents=True, exist_ok=True)
procs = []
def start(name, role, extra_env):
    e = {**os.environ, "PYTHONPATH": str(ROOT), "MODEL": MODEL, "PREFILL_HOST": "127.0.0.1", "DECODE_HOST": "127.0.0.1",
         "MAX_MODEL_LEN": str(MAX_MODEL_LEN), "EXTRA_ARGS": VLLM_EXTRA, **extra_env}
    log = open(LOGS / f"{name}.log", "w")
    p = subprocess.Popen(["bash", str(LAUNCH), role], cwd=ROOT, env=e, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    procs.append((name, p)); return p
def wait_ready(url, p, timeout=STARTUP_TIMEOUT_S):
    t0 = _t.time()
    while _t.time() - t0 < timeout:
        if p.poll() is not None:
            raise RuntimeError(f"{url} exited early; see {LOGS}")
        try:
            if urllib.request.urlopen(url + "/health", timeout=2).status == 200:
                return _t.time() - t0
        except Exception:
            _t.sleep(2)
    raise TimeoutError(url)
def stop_all():
    for name, p in procs:
        if p.poll() is None:
            os.killpg(p.pid, signal.SIGTERM)
    for name, p in procs:
        try: p.wait(60)
        except Exception: os.killpg(p.pid, signal.SIGKILL)
    procs.clear(); _t.sleep(5)
PROMPTS = ["Explain head-of-line blocking in one paragraph.", "List three uses of RDMA write with immediate data.",
           "What does a KV cache store in a transformer?", "Summarize disaggregated prefill and decode."]
def run_sweep(url, label):
    res = ttft.sweep(url, MODEL, lens, n=N_REQ, max_tokens=64, warmup=2)
    res["label"] = label
    return res
def complete(url):
    outs = []
    for pr in PROMPTS:
        body = json.dumps({"model": MODEL, "prompt": pr, "max_tokens": 48, "temperature": 0}).encode()
        req = urllib.request.Request(url + "/v1/completions", body, {"Content-Type": "application/json"})
        outs.append(json.loads(urllib.request.urlopen(req, timeout=300).read())["choices"][0]["text"])
    return outs
lens = [int(x) for x in PROMPT_LENS.split(",")]
serve = {"runs": []}'''),
("code", '''if GPU and RUN_VLLM:
    try:
        common = {"CONNECTOR": "scuffed", "TRANSPORT": "fabric", "PROVIDER": PROVIDER, "EP_TYPE": EP_TYPE, "GPU_UTIL": str(GPU_UTIL_EACH)}
        dec = start("decode", "decode", {**common, "METRICS_PORT": "9465"})
        serve["decode_ready_s"] = wait_ready("http://127.0.0.1:8200", dec)
        pre = start("prefill", "prefill", {**common, "METRICS_PORT": "9464"})
        serve["prefill_ready_s"] = wait_ready("http://127.0.0.1:8100", pre)
        prx = start("proxy", "proxy", {"CONNECTOR": "scuffed", "PROXY_PORT": "8000"})
        _t.sleep(3)
        serve["disagg_text"] = complete("http://127.0.0.1:8000")
        serve["runs"].append(run_sweep("http://127.0.0.1:8000", f"scuffed-fabric-{PROVIDER}"))
        for port in (9464, 9465):
            try: serve[f"metrics_{port}"] = urllib.request.urlopen(f"http://127.0.0.1:{port}/metrics", timeout=5).read().decode()[-6000:]
            except Exception as e: serve[f"metrics_{port}"] = str(e)
    finally:
        stop_all()
else:
    print("skipped (no GPU or RUN_VLLM=False)")'''),
("code", '''if GPU and RUN_VLLM:
    try:
        one = start("single", "single", {"GPU_UTIL": str(min(0.85, 2 * GPU_UTIL_EACH)), "SINGLE_PORT": "8300"})
        serve["single_ready_s"] = wait_ready("http://127.0.0.1:8300", one)
        serve["single_text"] = complete("http://127.0.0.1:8300")
        serve["runs"].append(run_sweep("http://127.0.0.1:8300", "single-instance"))
    finally:
        stop_all()
    same = [a == b for a, b in zip(serve.get("disagg_text", []), serve.get("single_text", []))]
    serve["greedy_match"] = same
    print("greedy outputs identical (disagg vs single):", same)'''),
("md", """### NixlConnector baselines (optional)

`NIXL_BACKENDS="UCX,LIBFABRIC"` runs the same sweep through vLLM's `NixlConnector`. The LIBFABRIC backend is
the libfabric path the stock stack ships; on this machine it can only select libfabric `tcp` (its discovery
takes cxi, efa, tcp, sockets in that order), and its README lists GPUDirect RDMA as required. A failed start
is recorded with the log lines that explain it rather than retried."""),
("code", '''nixl_status = {}
for be in [b.strip().upper() for b in NIXL_BACKENDS.split(",") if b.strip()]:
    if not (GPU and RUN_VLLM):
        break
    conn = "nixl" if be == "UCX" else "nixl-libfabric"
    nx = {"CONNECTOR": conn, "GPU_UTIL": str(GPU_UTIL_EACH), "NIXL_SIDE_PORT_PREFILL": "5600",
          "NIXL_SIDE_PORT_DECODE": "5601", "NIXL_FI_PROVIDER": "tcp"}
    try:
        d2 = start(f"nixl-{be}-decode", "decode", nx); wait_ready("http://127.0.0.1:8200", d2)
        p2 = start(f"nixl-{be}-prefill", "prefill", nx); wait_ready("http://127.0.0.1:8100", p2)
        start(f"nixl-{be}-proxy", "proxy", {"CONNECTOR": "nixl", "PROXY_PORT": "8000"}); _t.sleep(3)
        serve["runs"].append(run_sweep("http://127.0.0.1:8000", f"nixl-{be.lower()}"))
        nixl_status[be] = "ok"
    except Exception as e:
        lines = []
        for side in ("decode", "prefill"):
            f = LOGS / f"nixl-{be}-{side}.log"
            if f.exists():
                lines += [l for l in f.read_text(errors="replace").splitlines()
                          if any(k in l for k in ("NIXL", "nixl", "libfabric", "LIBFABRIC", "Error", "error"))][-15:]
        nixl_status[be] = {"error": repr(e), "log": lines}
    finally:
        stop_all()
serve["nixl_status"] = nixl_status
nixl_status'''),
("code", '''rows = []
for run in serve["runs"]:
    for r in run.get("results", []):
        rows.append({"label": run.get("label"), **{k: r.get(k) for k in ("prompt_len", "n", "ok", "ttft_p50_ms", "ttft_p99_ms", "itl_p50_ms", "itl_p99_ms")}})
tt = pd.DataFrame(rows)
if not tt.empty:
    figg, ax = plt.subplots(1, 2, figsize=(11, 3.6))
    for lab, g in tt.groupby("label"):
        ax[0].plot(g.prompt_len, g.ttft_p50_ms, marker="o", label=f"{lab} p50"); ax[0].plot(g.prompt_len, g.ttft_p99_ms, ls="--", alpha=.6)
        ax[1].plot(g.prompt_len, g.itl_p50_ms, marker="o", label=lab)
    ax[0].set_xlabel("prompt tokens"); ax[0].set_ylabel("TTFT ms (dashed p99)"); ax[1].set_xlabel("prompt tokens"); ax[1].set_ylabel("ITL p50 ms")
    for a in ax: a.legend()
    figg.suptitle(f"one GPU, prefill + decode instances sharing it ({HOST})")
    fig("07_single_gpu_ttft_itl", caption="E7")
else:
    print("no TTFT rows (GPU cells skipped)")
tt'''),
("md", "## 5. GPU decompression and a libfabric loopback sanity check"),
("code", '''dec = {}
if GPU:
    out = RESULTS / f"{HOST}_gpu_decompress.json"
    r = sh(f"cd benchmarks/test_arch && python3 bench_gpu_decompress.py --dim 64 --bits 3 4 --rows 4096 32768", check=False)
    dec["stdout"] = r.stdout[-3000:]
from benchmarks.fabric import runner
fab = []
for single in (False, True):
    d = runner.try_pair("sf_bench", ["-p", "shm", "-t", "rdm", "-m", "hol", "-n", "5000", "-w", "200", "--cold-size", "1048576",
                                     "-W", "8", "--hot-cpu", "2", "--cold-cpu", "4"] + (["-s"] if single else []))
    fab.append(runner.rows_hol(d, "shm loopback " + ("single EP" if single else "dual EP")))
pd.DataFrame(fab)'''),
("code", '''save("local_gpu", {"info": info, "loopback_gpu": loop, "scuffedquant": sq, "serve": serve,
                   "ttft_rows": rows, "gpu_decompress": dec, "fabric_loopback": fab,
                   "note": "single-host: shm/loopback transfers, not cross-node transport results"})'''),
]

build("08_local_gpu.ipynb", "08 · Single-GPU end-to-end run",
      "Everything that one GPU can exercise: GPU-resident connector data path, scuffedQuant on real KV, and vLLM disaggregated serving with ScuffedRdmaConnector on one card.",
      params, cells, sections=[(7, "ScuffedRdmaConnector inside vLLM", "07-connector.md"), (11, "scuffedQuant: rotate, quantize, sketch the residual", "11-scuffedquant.md")])
