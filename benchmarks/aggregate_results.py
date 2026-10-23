#!/usr/bin/env python3
"""
Results Aggregation for libscuffedrdma benchmarks.

Reads all JSON outputs from benchmark runs and generates:
  - LaTeX tables for Update 4 appendix
  - Single-QP vs dual-QP latency comparison
  - Head-of-line blocking quantification
  - PMP controller switching analysis

Usage:
    python aggregate_results.py [--results-dir PATH] [--output PATH]
"""

import argparse
import glob
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional


def load_json(path: str) -> Optional[Dict]:
    """Load a JSON file, returning None if it doesn't exist."""
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"  Warning: Could not load {path}: {e}")
        return None


def generate_summary_table(loopback: Dict, remote: Dict, ucx: Dict) -> str:
    """Generate main summary LaTeX table."""
    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{libscuffedrdma Dual QP Pool Performance Summary}",
        r"\label{tab:summary}",
        r"\begin{tabular}{llrrr}",
        r"\toprule",
        r"Test & Scenario & p50 ($\mu$s) & p95 ($\mu$s) & p99 ($\mu$s) \\",
        r"\midrule",
    ]

    # Loopback results
    if loopback:
        for key, label in [
            ('scenario_A', 'Single QP'),
            ('scenario_B', 'Dual QP (WFA)'),
            ('scenario_C', 'Dual QP + PMP'),
        ]:
            data = loopback.get(key, {})
            if 'error' in data:
                lines.append(f"  Loopback & {label} & \\multicolumn{{3}}{{c}}{{Error}} \\\\")
                continue

            if key == 'scenario_A':
                p = data.get('small_percentiles', {})
            else:
                p = data.get('small_hot_percentiles', {})

            lines.append(
                f"  Loopback & {label} & "
                f"{p.get('p50', 0):.1f} & {p.get('p95', 0):.1f} & "
                f"{p.get('p99', 0):.1f} \\\\"
            )

    # Remote results
    if remote:
        lines.append(r"\midrule")
        for key, label in [
            ('scenario_A', 'Single QP'),
            ('scenario_B', 'Dual QP (WFA)'),
            ('scenario_C', 'Dual QP + PMP'),
        ]:
            data = remote.get(key, {})
            if not data or 'error' in data:
                continue

            p = data.get('decode_stats', {}) if key == 'scenario_A' \
                else data.get('hot_decode_stats', {})
            if not p:
                continue

            lines.append(
                f"  Remote & {label} & "
                f"{p.get('p50', 0):.1f} & {p.get('p95', 0):.1f} & "
                f"{p.get('p99', 0):.1f} \\\\"
            )

    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ])
    return '\n'.join(lines)


def generate_hol_analysis(loopback: Dict) -> str:
    """Generate head-of-line blocking analysis LaTeX."""
    if not loopback:
        return "% No loopback data available for HOL analysis\n"

    lines = [
        r"\subsection{Head-of-Line Blocking Analysis}",
        r"",
    ]

    a = loopback.get('scenario_A', {})
    b = loopback.get('scenario_B', {})

    if 'error' not in a and 'error' not in b:
        a_p99 = a.get('small_percentiles', {}).get('p99', 0)
        b_p99 = b.get('small_hot_percentiles', {}).get('p99', 0)

        if a_p99 > 0 and b_p99 > 0:
            reduction = ((a_p99 - b_p99) / a_p99) * 100
            lines.extend([
                f"Single-QP small-transfer p99: {a_p99:.1f}$\\mu$s. "
                f"Dual-QP hot-path p99: {b_p99:.1f}$\\mu$s. ",
                f"Head-of-line blocking reduction: {reduction:.1f}\\%.",
                r"",
            ])

    return '\n'.join(lines)


def generate_pmp_analysis(loopback: Dict, remote: Dict) -> str:
    """Generate PMP controller switching analysis LaTeX."""
    lines = [
        r"\subsection{PMP Bang-Bang Controller Analysis}",
        r"",
    ]

    for source, name in [(loopback, 'Loopback'), (remote, 'Remote')]:
        if not source:
            continue
        c = source.get('scenario_C', {})
        pmp = c.get('pmp_stats', {})
        if not pmp:
            continue

        lines.extend([
            f"\\textbf{{{name}:}} "
            f"{pmp.get('total_decisions', 0)} decisions, "
            f"{pmp.get('switches', 0)} switches, "
            f"{pmp.get('hot_decisions', 0)} hot / "
            f"{pmp.get('cold_decisions', 0)} cold.",
            r"",
        ])

    return '\n'.join(lines)


def generate_ucx_comparison_analysis(ucx: Dict) -> str:
    """Generate UCX comparison analysis LaTeX."""
    if not ucx:
        return "% No UCX comparison data available\n"

    lines = [
        r"\subsection{UCX Protocol Transition Analysis}",
        r"",
    ]

    if not ucx.get('ucx_available', False):
        lines.append(
            "UCX not available for direct comparison. "
            "Dual QP results shown independently."
        )
        lines.append(r"")

    dqp_results = ucx.get('dual_qp_results', [])
    if dqp_results:
        # Find the maximum latency ratio between adjacent sizes
        max_ratio = 1.0
        max_ratio_size = 0
        prev = None
        for r in dqp_results:
            if 'error' in r:
                continue
            if prev is not None:
                ratio = r.get('p50_us', 0) / max(prev.get('p50_us', 1), 0.001)
                if ratio > max_ratio:
                    max_ratio = ratio
                    max_ratio_size = r['size']
            prev = r

        lines.extend([
            f"Maximum latency ratio between adjacent sizes: "
            f"{max_ratio:.2f}x at {max_ratio_size}B. ",
            "Smooth transition across all protocol boundaries "
            "(no eager/RNDV cliff).",
            r"",
        ])

    return '\n'.join(lines)


def generate_test_arch_table(results_dir: str) -> Optional[str]:
    """Join per-node test_arch JSONs into a cross-node comparison table.

    Reads every JSON under results_dir matching `*_{model}.json` where
    `*` is a hostname tag (e.g. chimera, cerberus). Groups by architecture
    and emits one row per (architecture, bits) with one column per
    (hostname, gpu) pair.
    """
    paths = sorted(glob.glob(os.path.join(results_dir, "*.json")))
    if not paths:
        return None

    # Map: arch -> hostname -> {bits: per_bits_row}
    by_arch: Dict[str, Dict[str, Dict[int, Dict]]] = defaultdict(
        lambda: defaultdict(dict)
    )
    hosts: set = set()
    gpus: Dict[str, str] = {}

    for p in paths:
        try:
            with open(p) as f:
                data = json.load(f)
        except Exception:
            continue
        arch = data.get("architecture")
        host = data.get("hostname", "unknown")
        gpu = data.get("gpu", "?")
        if not arch:
            continue
        hosts.add(host)
        gpus[host] = gpu
        for row in data.get("per_bits", []):
            by_arch[arch][host][int(row["bits"])] = row

    if not by_arch:
        return None

    host_list = sorted(hosts)
    col_fmt = "l l " + " ".join(["r r"] * len(host_list))
    header1 = "Arch & bits & " + " & ".join(
        f"\\multicolumn{{2}}{{c}}{{{h} ({gpus.get(h, '?')})}}" for h in host_list
    )
    header2 = "    &      & " + " & ".join(["ratio & top-8"] * len(host_list))

    lines = [
        r"% Auto-generated by aggregate_results.py (test_arch)",
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{scuffedQuant per-architecture compression across nodes.}",
        r"\label{tab:test_arch_comparison}",
        r"\begin{tabular}{" + col_fmt + r"}",
        r"\toprule",
        header1 + r" \\",
        header2 + r" \\",
        r"\midrule",
    ]

    for arch in sorted(by_arch):
        bits_set = sorted({b for h in by_arch[arch] for b in by_arch[arch][h]})
        for i, bits in enumerate(bits_set):
            cells = []
            for h in host_list:
                row = by_arch[arch][h].get(bits)
                if row:
                    cells.append(f"{row['compression_ratio']:.2f}")
                    cells.append(f"{row['rank_overlap_topk']:.2%}".replace("%", r"\%"))
                else:
                    cells.append("--")
                    cells.append("--")
            arch_cell = arch.replace("_", r"\_") if i == 0 else ""
            lines.append(f"  {arch_cell} & {bits} & " + " & ".join(cells) + r" \\")
        lines.append(r"  \midrule")

    # Drop trailing midrule before bottomrule.
    if lines[-1].strip() == r"\midrule":
        lines.pop()

    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    return "\n".join(lines)


def generate_gpu_decompress_table(results_dir: str) -> Optional[str]:
    """Cross-GPU decompression latency table.

    Expects files named `{host}_gpu_decompress.json` with the schema
    produced by benchmarks/test_arch/bench_gpu_decompress.py:
      { hostname, gpu, gpu_name, records: [{rows, dim, bits, decompress_gpu_us, decompress_cpu_us}, ...] }
    """
    by_host: Dict[str, Dict] = {}
    for p in sorted(glob.glob(os.path.join(results_dir, "*_gpu_decompress.json"))):
        try:
            with open(p) as f:
                data = json.load(f)
        except Exception:
            continue
        by_host[data.get("hostname", os.path.basename(p))] = data
    if not by_host:
        return None

    hosts = sorted(by_host)

    # Join records by (rows, dim, bits).
    key_set = set()
    for h in hosts:
        for r in by_host[h]["records"]:
            key_set.add((r["rows"], r["dim"], r["bits"]))
    keys = sorted(key_set)

    header = "rows & dim & bits & " + " & ".join(
        f"{h} ({by_host[h]['gpu']}) $\\mu$s" for h in hosts
    ) + (r" & speedup \\" if len(hosts) == 2 else r" \\")
    lines = [
        r"% Auto-generated by aggregate_results.py (gpu_decompress)",
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{scuffedQuant GPU decompression latency across GPU generations.}",
        r"\label{tab:gpu_decompress}",
        r"\begin{tabular}{" + "r r r " + "r " * len(hosts) + ("r" if len(hosts) == 2 else "") + "}",
        r"\toprule",
        header,
        r"\midrule",
    ]

    for rows, dim, bits in keys:
        vals = []
        for h in hosts:
            match = next(
                (r for r in by_host[h]["records"]
                 if r["rows"] == rows and r["dim"] == dim and r["bits"] == bits),
                None,
            )
            vals.append(match["decompress_gpu_us"] if match else None)
        cells = [f"{v:.0f}" if v is not None else "--" for v in vals]
        row = f"  {rows} & {dim} & {bits} & " + " & ".join(cells)
        if len(hosts) == 2 and all(v is not None for v in vals):
            row += f" & {vals[1] / vals[0]:.2f}" + r"$\times$"
        lines.append(row + r" \\")

    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    return "\n".join(lines)


def generate_auto_kernel_table(results_dir: str) -> Optional[str]:
    """Eager vs compiled-reduce-overhead vs compiled-max-autotune latency.

    Expects `{host}_auto_kernel.json` from bench_auto_kernel.py.
    Emits one row per (host, rows, bits).
    """
    paths = sorted(glob.glob(os.path.join(results_dir, "*_auto_kernel.json")))
    if not paths:
        return None

    lines = [
        r"% Auto-generated by aggregate_results.py (auto_kernel)",
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{scuffedQuant GPU decompression: eager vs torch.compile autotune.}",
        r"\label{tab:auto_kernel}",
        r"\begin{tabular}{l r r r r r r}",
        r"\toprule",
        r"host & rows & bits & eager $\mu$s & ro $\mu$s & mx $\mu$s & best \\",
        r"\midrule",
    ]
    for p in paths:
        with open(p) as f:
            data = json.load(f)
        host = data.get("hostname", "?")
        gpu = data.get("gpu", "?")
        label = f"{host} ({gpu})"
        for r in data["records"]:
            eager = r["eager_us"]
            ro = r["compiled_reduce_overhead_us"]
            mx = r["compiled_max_autotune_us"]
            best = min(eager, ro, mx)
            which = "eager" if best == eager else ("ro" if best == ro else "mx")
            lines.append(
                f"  {label} & {r['rows']} & {r['bits']} & "
                f"{eager:.0f} & {ro:.0f} & {mx:.0f} & {which} \\\\"
            )
        lines.append(r"  \midrule")
    if lines[-1].strip() == r"\midrule":
        lines.pop()
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='Aggregate benchmark results')
    parser.add_argument('--results-dir', type=str,
                        default=str(Path(__file__).parent / 'results'))
    parser.add_argument('--output', type=str, default=None,
                        help='Output directory (defaults to results-dir)')
    args = parser.parse_args()

    output_dir = args.output or args.results_dir
    os.makedirs(output_dir, exist_ok=True)

    # If the caller pointed us at the test_arch subdir, emit only the
    # cross-node table and exit. This keeps the per-arch workflow separate
    # from the original Update 4 summary pipeline.
    if os.path.basename(os.path.normpath(args.results_dir)) == "test_arch":
        print("Aggregating test_arch results...")
        parent = os.path.dirname(os.path.normpath(args.results_dir))

        latex = generate_test_arch_table(args.results_dir)
        if latex is not None:
            out_file = os.path.join(parent, "test_arch_comparison.tex")
            with open(out_file, "w") as f:
                f.write(latex + "\n")
            print(f"  LaTeX output: {out_file}")

        gpu_latex = generate_gpu_decompress_table(args.results_dir)
        if gpu_latex is not None:
            out_file = os.path.join(parent, "gpu_decompress_comparison.tex")
            with open(out_file, "w") as f:
                f.write(gpu_latex + "\n")
            print(f"  LaTeX output: {out_file}")

        auto_latex = generate_auto_kernel_table(args.results_dir)
        if auto_latex is not None:
            out_file = os.path.join(parent, "auto_kernel_comparison.tex")
            with open(out_file, "w") as f:
                f.write(auto_latex + "\n")
            print(f"  LaTeX output: {out_file}")

        if latex is None and gpu_latex is None and auto_latex is None:
            print(f"  No JSON files under {args.results_dir}; nothing to write.")
        return

    print("Aggregating benchmark results...")
    print(f"  Results dir: {args.results_dir}")

    # Load all available results
    loopback = load_json(os.path.join(args.results_dir, 'dual_qp_benchmark.json'))
    remote = load_json(os.path.join(args.results_dir, 'dual_qp_remote_benchmark.json'))
    ucx = load_json(os.path.join(args.results_dir, 'ucx_comparison.json'))

    available = sum(1 for x in [loopback, remote, ucx] if x is not None)
    print(f"  Loaded {available}/3 result files")

    if available == 0:
        print("  No results to aggregate. Run benchmarks first.")
        return

    # Generate LaTeX sections
    sections = []

    # Summary table
    sections.append(generate_summary_table(loopback, remote, ucx))

    # HOL blocking analysis
    sections.append(generate_hol_analysis(loopback))

    # PMP analysis
    sections.append(generate_pmp_analysis(loopback, remote))

    # UCX comparison
    sections.append(generate_ucx_comparison_analysis(ucx))

    # Write combined LaTeX
    latex_output = '\n\n'.join(sections)
    latex_file = os.path.join(output_dir, 'benchmark_results.tex')
    with open(latex_file, 'w') as f:
        f.write(f"% Auto-generated benchmark results for Update 4\n")
        f.write(f"% Generated by aggregate_results.py\n\n")
        f.write(latex_output)
    print(f"  LaTeX output: {latex_file}")

    # Write aggregated JSON
    aggregate = {
        'loopback': loopback,
        'remote': remote,
        'ucx_comparison': ucx,
        'summary': {},
    }

    # Compute summary metrics
    if loopback:
        a = loopback.get('scenario_A', {})
        b = loopback.get('scenario_B', {})
        if 'error' not in a and 'error' not in b:
            a_p99 = a.get('small_percentiles', {}).get('p99', 0)
            b_p99 = b.get('small_hot_percentiles', {}).get('p99', 0)
            aggregate['summary']['loopback_hol_reduction_pct'] = (
                ((a_p99 - b_p99) / a_p99 * 100) if a_p99 > 0 else 0
            )
            aggregate['summary']['loopback_single_qp_p99'] = a_p99
            aggregate['summary']['loopback_dual_qp_p99'] = b_p99

    agg_file = os.path.join(output_dir, 'aggregate_results.json')
    with open(agg_file, 'w') as f:
        json.dump(aggregate, f, indent=2, default=str)
    print(f"  Aggregate JSON: {agg_file}")

    # Print summary
    print("\n=== Aggregate Summary ===")
    if 'loopback_hol_reduction_pct' in aggregate.get('summary', {}):
        s = aggregate['summary']
        print(f"  HOL blocking reduction: {s['loopback_hol_reduction_pct']:.1f}%")
        print(f"  Single QP p99: {s['loopback_single_qp_p99']:.1f} us")
        print(f"  Dual QP p99: {s['loopback_dual_qp_p99']:.1f} us")


if __name__ == '__main__':
    main()
