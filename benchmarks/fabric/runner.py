"""
Run sf_bench / sv_bench pairs from a notebook or a script.

Local mode: server and client both on this host (127.0.0.1); use the tcp,
tcp;ofi_rxm or shm providers, or verbs on rxe0 (rxe loops back to itself).

Cluster mode: this host is the client; the server is started on PEER over
ssh (key-based, as scripts/start_cluster.sh already assumes). PEER_IP is the
address on the RDMA netdev (the 10GbE port carrying rxe0), which the verbs
provider binds to. The repo must be checked out at the same path on both
nodes (REMOTE_REPO overrides).

Every result is the client's JSON with the exact server and client commands
attached, so a number can always be traced to the command that made it.
"""
from __future__ import annotations

import itertools
import json
import os
import shlex
import socket
import subprocess
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parents[2]
TOOLS = {
    "sf_bench": ROOT / "middleware" / "libscuffedfabric" / "sf_bench",
    "sv_bench": ROOT / "middleware" / "libscuffedverbs" / "sv_bench",
}
_ports = itertools.count(30000 + (os.getpid() % 300) * 30)


def build(tools: Iterable[str] = ("sf_bench", "sv_bench"), remote: Optional[str] = None,
          remote_repo: Optional[str] = None) -> Dict[str, str]:
    """make the native benches here (and on the peer when remote is given)."""
    out = {}
    for t in tools:
        d = TOOLS[t].parent
        r = subprocess.run(["make", "-C", str(d)], capture_output=True, text=True)
        out[t] = "ok" if r.returncode == 0 else r.stderr[-2000:]
        if remote:
            rr = remote_repo or str(ROOT)
            cmd = f"make -C {shlex.quote(str(Path(rr) / d.relative_to(ROOT)))}"
            r = subprocess.run(["ssh", remote, cmd], capture_output=True, text=True)
            out[f"{t}@{remote}"] = "ok" if r.returncode == 0 else r.stderr[-2000:]
    return out


def _cmd(tool: str, role: str, host: str, port: int, args: List[str], repo: Optional[Path] = None) -> List[str]:
    exe = (repo / TOOLS[tool].relative_to(ROOT)) if repo else TOOLS[tool]
    return [str(exe), "-r", role, "-H", host, "-P", str(port), *args]


def run_pair(tool: str, args: List[str], *, peer: Optional[str] = None, peer_ip: Optional[str] = None,
             remote_repo: Optional[str] = None, env: Optional[Dict[str, str]] = None,
             timeout: int = 600, port: Optional[int] = None) -> dict:
    """
    Run one benchmark. args are the shared flags (-m, -M, -p, -t, -S, ...).
    Returns the client JSON plus "server_cmd", "client_cmd", "elapsed_s".
    """
    port = port or next(_ports)
    envs = {**os.environ, **(env or {})}
    env_prefix = " ".join(f"{k}={shlex.quote(v)}" for k, v in (env or {}).items())
    t0 = time.time()
    if peer is None:
        host = "127.0.0.1"
        scmd = _cmd(tool, "server", host, port, args)
        srv = subprocess.Popen(scmd + ["-j", "/dev/null"], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                               text=True, env=envs)
        server_desc = " ".join(map(shlex.quote, scmd))
    else:
        host = peer_ip or peer
        rr = Path(remote_repo) if remote_repo else ROOT
        scmd = _cmd(tool, "server", host, port, args, repo=rr)
        remote = f"{env_prefix} {' '.join(map(shlex.quote, scmd))} -j /dev/null"
        srv = subprocess.Popen(["ssh", peer, remote], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        server_desc = f"ssh {peer} {remote}"
    ccmd = _cmd(tool, "client", host, port, args)
    try:
        cli = subprocess.run(ccmd, capture_output=True, text=True, timeout=timeout, env=envs)
        srv.wait(timeout=60)
    except subprocess.TimeoutExpired:
        srv.kill()
        raise RuntimeError(f"timeout after {timeout}s: {' '.join(ccmd)}")
    finally:
        if srv.poll() is None:
            srv.kill()
    if cli.returncode != 0:
        serr = srv.stderr.read() if srv.stderr else ""
        raise RuntimeError(f"{tool} failed ({cli.returncode}):\nclient: {cli.stderr.strip()}\nserver: {serr.strip()}")
    d = json.loads(cli.stdout)
    d["server_cmd"] = server_desc
    d["client_cmd"] = f"{env_prefix} {' '.join(map(shlex.quote, ccmd))}".strip()
    d["elapsed_s"] = round(time.time() - t0, 3)
    return d


def try_pair(tool: str, args: List[str], **kw) -> dict:
    """run_pair, but a failure becomes {"error": ...} so a sweep keeps going."""
    try:
        return run_pair(tool, args, **kw)
    except Exception as e:  # noqa: BLE001
        return {"tool": tool, "args": args, "error": str(e)[-1500:]}


def rows_sig(d: dict, label: str) -> List[dict]:
    if "error" in d:
        return [{"label": label, "error": d["error"][:200]}]
    if "skipped" in d:
        return [{"label": label, "skipped": d["skipped"]}]
    return [{"label": label, "mech": d.get("mech"), **r} for r in d.get("results", [])]


def rows_hol(d: dict, label: str) -> dict:
    if "error" in d:
        return {"label": label, "error": d["error"][:200]}
    h, c = d["hot_rtt"], d["cold"]
    return {"label": label, "single_ep": d["single_ep"], "cold_on": c["on"], "cold_size": c["size"],
            "hot_size": d.get("hot_size"), "hot_p50_us": h["p50_us"], "hot_p90_us": h["p90_us"],
            "hot_p99_us": h["p99_us"], "hot_p999_us": h["p999_us"], "hot_max_us": h["max_us"],
            "cold_MBps": c["MBps"], "n": h["n"]}


def stacks(mode: str) -> List[dict]:
    """The transport stacks compared in notebooks 01-03."""
    if mode == "cluster":
        return [
            {"label": "libibverbs RC (native)", "tool": "sv_bench", "args": []},
            {"label": "libfabric verbs MSG", "tool": "sf_bench", "args": ["-p", "verbs", "-t", "msg"]},
            {"label": "libfabric verbs;ofi_rxm RDM", "tool": "sf_bench", "args": ["-p", "verbs;ofi_rxm", "-t", "rdm"]},
        ]
    return [
        {"label": "libfabric tcp MSG (local smoke)", "tool": "sf_bench", "args": ["-p", "tcp", "-t", "msg"]},
        {"label": "libfabric tcp;ofi_rxm RDM (local smoke)", "tool": "sf_bench", "args": ["-p", "tcp;ofi_rxm", "-t", "rdm"]},
        {"label": "libfabric shm RDM (local smoke)", "tool": "sf_bench", "args": ["-p", "shm", "-t", "rdm"]},
    ]


def host() -> str:
    return socket.gethostname()
