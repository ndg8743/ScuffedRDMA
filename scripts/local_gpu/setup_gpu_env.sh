#!/usr/bin/env bash
# One-time setup for the single-GPU run (notebook 08) on a desktop GPU.
# Works on Ubuntu under WSL2 (Windows desktop) or native Ubuntu / Debian.
#
#   bash scripts/local_gpu/setup_gpu_env.sh            # full setup, build, tests
#   bash scripts/local_gpu/setup_gpu_env.sh --check    # only report what is installed
#
# Options (flags or env):
#   --skip-apt       SKIP_APT=1       do not apt install system packages
#   --skip-tests     SKIP_TESTS=1     do not run pytest at the end
#   --nixl           INSTALL_NIXL=1   also pip install nixl (UCX + LIBFABRIC backends) for the baseline runs
#   --venv PATH      VENV=PATH        virtualenv location (default ~/scuffed)
#   --backend NAME   TORCH_BACKEND=   auto | cu128 | cu129 | cu130 (default auto: picked from the driver)
#   --dry-run        DRY_RUN=1        print the commands, run nothing
#
# CUDA under WSL2 comes from the Windows NVIDIA driver. Do not install a Linux NVIDIA driver inside WSL.
# torch and vLLM wheels bundle the CUDA runtime, so no CUDA toolkit is needed for anything here.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV="${VENV:-$HOME/scuffed}"
TORCH_BACKEND="${TORCH_BACKEND:-auto}"
SKIP_APT="${SKIP_APT:-0}" SKIP_TESTS="${SKIP_TESTS:-0}" INSTALL_NIXL="${INSTALL_NIXL:-0}" DRY_RUN="${DRY_RUN:-0}"
CHECK_ONLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-apt) SKIP_APT=1 ;;
    --skip-tests) SKIP_TESTS=1 ;;
    --nixl) INSTALL_NIXL=1 ;;
    --venv) VENV="$2"; shift ;;
    --backend) TORCH_BACKEND="$2"; shift ;;
    --dry-run) DRY_RUN=1 ;;
    --check) CHECK_ONLY=1 ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

say()  { printf '\n== %s\n' "$*"; }
warn() { printf 'WARN: %s\n' "$*" >&2; }
die()  { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
run()  { echo "+ $*"; [[ "$DRY_RUN" == 1 ]] || "$@"; }

SUDO=""; [[ $EUID -ne 0 ]] && SUDO="sudo"
IS_WSL=0; grep -qi microsoft /proc/version 2>/dev/null && IS_WSL=1

# ---------------------------------------------------------------- 1. driver
say "GPU driver"
[[ $IS_WSL == 1 ]] && echo "WSL2 detected" && export PATH="$PATH:/usr/lib/wsl/lib"
if ! command -v nvidia-smi >/dev/null 2>&1; then
  if [[ $IS_WSL == 1 ]]; then
    die "nvidia-smi not found in WSL. Install or update the NVIDIA driver on Windows (Game Ready or Studio),
       then run 'wsl --shutdown' in PowerShell and reopen Ubuntu. /usr/lib/wsl/lib/nvidia-smi should then exist."
  fi
  die "nvidia-smi not found. Install the NVIDIA driver (ubuntu-drivers install), reboot, rerun."
fi
nvidia-smi --query-gpu=name,driver_version,memory.total,compute_cap --format=csv,noheader 2>/dev/null \
  || nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
DRV_CUDA="$(nvidia-smi 2>/dev/null | sed -n 's/.*CUDA Version: *\([0-9.]*\).*/\1/p' | head -1)"
echo "driver supports CUDA ${DRV_CUDA:-unknown}"
if [[ -n "$DRV_CUDA" ]]; then
  maj="${DRV_CUDA%%.*}"; min="${DRV_CUDA#*.}"; min="${min%%.*}"
  (( maj < 12 )) && die "driver supports CUDA $DRV_CUDA; vLLM needs 12.x. Update the NVIDIA driver."
  (( maj == 12 && min < 8 )) && warn "driver supports CUDA $DRV_CUDA; RTX 50-series (sm_120) needs 12.8+. Update the driver if torch reports the arch missing."
fi
case "$ROOT" in /mnt/[a-z]/*) warn "repo is on the Windows filesystem ($ROOT); builds and model loads are much slower there. Clone into ~ inside WSL." ;; esac

if [[ $CHECK_ONLY == 1 ]]; then
  say "check only"
  for t in gcc make fi_info python3 ibv_devices; do printf '%-12s %s\n' "$t" "$(command -v $t || echo missing)"; done
  [[ -x "$VENV/bin/python" ]] && "$VENV/bin/python" - <<'PY' || echo "venv $VENV: missing or broken"
import importlib
for m in ("torch", "vllm", "nixl", "jupyterlab", "pandas"):
    try:
        mod = importlib.import_module(m); print(f"{m:12s} {getattr(mod, '__version__', 'ok')}")
    except Exception as e:
        print(f"{m:12s} missing ({type(e).__name__})")
import torch
if torch.cuda.is_available():
    p = torch.cuda.get_device_properties(0)
    print("cuda", torch.version.cuda, p.name, f"sm_{p.major}{p.minor}", "in arch list:", f"sm_{p.major}{p.minor}" in torch.cuda.get_arch_list())
else:
    print("torch.cuda.is_available() = False")
PY
  exit 0
fi

# ---------------------------------------------------------------- 2. system packages
if [[ "$SKIP_APT" != 1 ]]; then
  say "system packages (libfabric, rdma-core, compiler)"
  command -v apt-get >/dev/null || die "no apt-get; install gcc make libfabric-dev libibverbs-dev python3-venv by hand and rerun with --skip-apt"
  run $SUDO apt-get update -y
  run $SUDO env DEBIAN_FRONTEND=noninteractive apt-get install -y \
    build-essential pkg-config git python3-venv python3-dev \
    libfabric-dev libfabric-bin libibverbs-dev rdma-core ibverbs-utils
fi
if [[ "$DRY_RUN" != 1 ]]; then
  command -v fi_info >/dev/null && { echo "libfabric providers on this box:"; fi_info -l 2>/dev/null | grep -E '^(shm|tcp|verbs|udp|sockets)' | tr '\n' ' '; echo; } \
    || warn "fi_info missing; libfabric-bin did not install"
fi

# ---------------------------------------------------------------- 3. python env with CUDA torch + vLLM
say "virtualenv $VENV"
[[ -x "$VENV/bin/python" ]] || run python3 -m venv "$VENV"
PY="$VENV/bin/python"
run "$PY" -m pip install -q -U pip uv
# vLLM pins its own torch; --torch-backend picks the matching CUDA wheel index (cu128 / cu129 / cu130).
run "$VENV/bin/uv" pip install --python "$PY" -U vllm --torch-backend="$TORCH_BACKEND"
run "$VENV/bin/uv" pip install --python "$PY" -U jupyterlab ipykernel nbformat nbclient pandas matplotlib transformers pytest numpy
if [[ "$INSTALL_NIXL" == 1 ]]; then
  run "$VENV/bin/uv" pip install --python "$PY" -U nixl || warn "nixl install failed; the NIXL baseline cells will skip"
fi
# prebuilt kernels so the first vllm serve does not compile for minutes (newer vLLM only)
[[ -x "$VENV/bin/vllm" ]] && { run "$VENV/bin/vllm" download-kernels || warn "vllm download-kernels not available in this vLLM; first start compiles kernels"; }

# ---------------------------------------------------------------- 4. verify CUDA from torch
say "CUDA from torch"
if [[ "$DRY_RUN" != 1 ]]; then
"$PY" - <<'PY'
import sys, torch
print("torch", torch.__version__, "cuda", torch.version.cuda)
if not torch.cuda.is_available():
    sys.exit("torch.cuda.is_available() is False. Check nvidia-smi works, then rerun with --backend cu128 (or cu130).")
p = torch.cuda.get_device_properties(0)
sm = f"sm_{p.major}{p.minor}"
print(f"{p.name}  {sm}  {p.total_memory / 2**30:.1f} GiB")
if sm not in torch.cuda.get_arch_list():
    print(f"WARN: {sm} not in this torch build's arch list {torch.cuda.get_arch_list()}; "
          "RTX 50-series needs a CUDA 12.8+ wheel: rerun with --backend cu128 or cu130")
a = torch.randn(1024, 1024, device="cuda", dtype=torch.bfloat16)
b = (a @ a.T).float().sum().item()
torch.cuda.synchronize()
print("bf16 matmul on GPU ok", round(b, 1))
import vllm; print("vllm", vllm.__version__)
PY
fi

# ---------------------------------------------------------------- 5. native builds
say "native builds"
for d in middleware/libscuffedfabric middleware/libscuffedverbs middleware/nccl_plugin; do
  run make -C "$ROOT/$d" || warn "build failed in $d"
done

# ---------------------------------------------------------------- 6. jupyter kernel
say "jupyter kernel 'scuffed'"
run "$PY" -m ipykernel install --user --name scuffed --display-name "scuffed (CUDA)"

# ---------------------------------------------------------------- 7. tests
if [[ "$SKIP_TESTS" != 1 ]]; then
  VSRC="$("$PY" -c 'import vllm, pathlib; print(pathlib.Path(vllm.__file__).parent.parent)' 2>/dev/null || true)"
  say "pytest -m gpu (KV layout, codec, connector loopback with caches on cuda:0)"
  (cd "$ROOT" && run env VLLM_SRC="$VSRC" "$PY" -m pytest -q -p no:cacheprovider -m gpu -rs) || warn "gpu tests failed"
  say "full suite"
  (cd "$ROOT" && run env VLLM_SRC="$VSRC" "$PY" -m pytest -q -p no:cacheprovider -rs) || warn "some tests failed"
fi

say "done"
cat <<EOF
Next:
  . $VENV/bin/activate && cd $ROOT && jupyter lab notebooks/08_local_gpu.ipynb
  pick the "scuffed (CUDA)" kernel, set MODE = "gpu" in the first cell, Run All.
  Results land in results/local_gpu/. On a 16 GB card keep GPU_UTIL_EACH = 0.40 and --enforce-eager.
EOF
