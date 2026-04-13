# scripts

Operational scripts for bringing up the two-tower RDMA testbed and running transport benchmarks against a vLLM cluster.

## Active scripts

### `setup_softroce_tower2.sh`
Configures SoftRoCE (rxe) on top of a ConnectX-4 100GbE interface on Tower 2 (Proxmox host with 2x V100). Loads kernel modules, creates the `rxe0` device, applies MTU/ring-buffer/sysctl tuning, and installs a systemd unit so the config survives reboot. Run as root with the NIC interface name as the first arg.

### `load_ttpoe.sh`
Wrapper around the Tesla TTPoe kernel modules (`modttpoe`, `modttpip`). Subcommands: `load`, `unload`, `status`, `build`, `test`, `peer`. Expects source at `/opt/ttpoe` by default. Used when running the TTPoe transport path end-to-end.

### `start_cluster.sh`
Brings the Chimera (head) and Cerberus (worker) nodes up with vLLM via docker compose. Picks NCCL env vars per transport (`tcp`, `roce`, `hwroce`, `ttpoe`, `auto`) and waits for the `:8000/v1/models` endpoint. `--stop` tears it down. This is the entry point for all cluster-level work.

### `benchmark_all.sh`
Loops over a comma-separated list of transports, calls `start_cluster.sh` for each, fires `--iterations` completion requests at the vLLM endpoint, and writes per-transport JSON plus a `summary.json`, `comparison.csv`, and optional LaTeX table. Current defaults target Llama-4-Scout-17B.

## Stale / obsolete

The `.ps1` PowerShell scripts and `mlxup_output.txt` were one-shot Windows-side tooling for a Tower 1 Windows box that is no longer in the loop. The Windows tower was retired when Tower 1 moved to Linux and Mellanox firmware flashing was done off that host. Candidates for deletion:

- `check_mlx.ps1`
- `diag_mlx.ps1`
- `mlxup_silent.ps1`
- `run_mlxup.ps1`
- `run_mlxup_update.ps1`
- `setup_mlx_tower1.ps1`
- `mlxup_output.txt` (captured output from one of the above)

All six `.ps1` files landed in a single commit (`a5476c7`) and have not been touched since. Keep only if the Windows flashing workflow is expected to come back.
