#!/usr/bin/env python3
"""
UCX vs libscuffedrdma Comparison Benchmark.

Demonstrates UCX protocol transition cliffs vs smooth dual QP performance.
References UCX issues:
  - #10552: 50x latency cliff at eager->RNDV boundary on Grace Hopper
  - #10486: >32KB messages switch RDMA send->read causing degradation
  - #10532: Latency drop at eager->zcopy transition (~3000B)
  - #11091: RNDV heuristic regression in UCX 1.19

Methodology:
  1. Run ucx_perftest at message sizes crossing eager/RNDV boundaries
  2. Run equivalent workload through dual QP pool
  3. Compare latency curves to show cliff elimination

Usage:
    python benchmark_ucx_comparison.py [--output PATH]
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))


# Message sizes that cross UCX eager/RNDV boundaries
# UCX default eager threshold: ~8KB for tag, ~64KB for RMA
# RNDV threshold varies by transport
BOUNDARY_SIZES = [
    64, 128, 256, 512, 1024,       # Well within eager
    2048, 3000, 4096,              # Near zcopy transition (#10532)
    8192, 16384, 32768,            # Near eager/RNDV boundary
    49152, 65536,                  # At RNDV boundary (#10486)
    131072, 262144, 524288,        # RNDV territory
    1048576,                       # 1MB - deep RNDV
]


def check_ucx_available() -> Tuple[bool, str]:
    """Check if UCX perftest is available."""
    try:
        result = subprocess.run(
            ['ucx_perftest', '-h'],
            capture_output=True, text=True, timeout=5
        )
        return True, "ucx_perftest available"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    try:
        result = subprocess.run(
            ['ucx_info', '-v'],
            capture_output=True, text=True, timeout=5
        )
        return False, f"ucx_info available but ucx_perftest not found. UCX version: {result.stdout.strip()}"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, "UCX not installed"


def run_ucx_perftest(size: int, iterations: int = 1000,
                     transport: str = "rc_verbs") -> Optional[Dict]:
    """
    Run ucx_perftest for a given message size and return latency.

    Uses loopback mode with server/client in separate processes.
    """
    try:
        # Start server
        server_cmd = [
            'ucx_perftest',
            '-t', 'tag_lat',  # Tag matching latency
            '-s', str(size),
            '-n', str(iterations),
            '-w', '50',  # Warmup
        ]

        server_proc = subprocess.Popen(
            server_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        time.sleep(0.5)

        # Start client
        client_cmd = server_cmd + ['127.0.0.1']
        client_result = subprocess.run(
            client_cmd,
            capture_output=True, text=True, timeout=30
        )

        server_proc.terminate()
        server_proc.wait(timeout=5)

        # Parse output for latency
        for line in client_result.stdout.split('\n'):
            if 'tag_lat' in line.lower() or 'lat' in line.lower():
                parts = line.split()
                for i, part in enumerate(parts):
                    try:
                        lat = float(part)
                        if lat > 0 and lat < 1e6:
                            return {
                                'size': size,
                                'latency_us': lat,
                                'raw_output': line.strip(),
                            }
                    except ValueError:
                        continue

        return {
            'size': size,
            'latency_us': None,
            'raw_output': client_result.stdout[:200],
            'error': 'Could not parse latency',
        }

    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return {
            'size': size,
            'latency_us': None,
            'error': str(e),
        }


def run_dual_qp_benchmark(sizes: List[int], iterations_per_size: int = 100) -> List[Dict]:
    """
    Run dual QP pool benchmark at each message size.

    Uses hot QP for small messages, cold QP for large messages,
    measuring the transition to show no cliff.
    """
    from middleware.rdma_tensor_cache.dual_qp_pool import DualQPPool, QueueStats
    from middleware.rdma_tensor_cache.wfa_classifier import WFAClassifier

    results = []

    for size in sizes:
        try:
            # Create fresh pool for each size to get clean measurements
            pool = DualQPPool(device_name="rxe0", n_hot=2, n_cold=2)
            pool.open()

            # For loopback, we need two pools connected to each other
            pool2 = DualQPPool(device_name="rxe0", n_hot=2, n_cold=2)
            pool2.open()

            # Exchange info
            info1 = pool.get_local_info()
            info2 = pool2.get_local_info()
            pool.connect_all(info2)
            pool2.connect_all(info1)

            # Register buffers
            send_buf = pool.register_buffer('send', size)
            recv_buf = pool2.register_buffer('recv', size)
            send_buf.write(b'\xAA' * min(size, 4096))

            classifier = WFAClassifier()

            latencies = []
            for i in range(iterations_per_size):
                queue = classifier.classify(f"bench_{size}", size)

                if queue.value == 'hot':
                    lat = pool.post_write_hot(
                        send_buf, recv_buf.addr, recv_buf.rkey, size
                    )
                else:
                    lat = pool.post_write_cold(
                        send_buf, recv_buf.addr, recv_buf.rkey, size
                    )
                latencies.append(lat)

            pool.close()
            pool2.close()

            s = sorted(latencies)
            results.append({
                'size': size,
                'queue': classifier.classify(f"bench_{size}", size).value,
                'p50_us': s[len(s) // 2],
                'p95_us': s[int(len(s) * 0.95)],
                'p99_us': s[int(len(s) * 0.99)],
                'mean_us': sum(s) / len(s),
                'min_us': s[0],
                'max_us': s[-1],
            })
            print(f"    Size {size:>8d}B: p50={results[-1]['p50_us']:>8.1f}us  "
                  f"p99={results[-1]['p99_us']:>8.1f}us  [{results[-1]['queue']}]")

        except Exception as e:
            results.append({
                'size': size,
                'error': str(e),
            })
            print(f"    Size {size:>8d}B: ERROR - {e}")

    return results


def generate_comparison_table(ucx_results: List[Dict],
                              dual_qp_results: List[Dict]) -> str:
    """Generate LaTeX comparison table."""
    lines = [
        r"\begin{table}[h]",
        r"\centering",
        r"\caption{UCX vs libscuffedrdma Latency Across Protocol Boundaries}",
        r"\label{tab:ucx_comparison}",
        r"\begin{tabular}{rrrrr}",
        r"\toprule",
        r"Size (B) & UCX p50 ($\mu$s) & DualQP p50 ($\mu$s) & UCX p99 ($\mu$s) & DualQP p99 ($\mu$s) \\",
        r"\midrule",
    ]

    ucx_by_size = {r['size']: r for r in ucx_results}
    dqp_by_size = {r['size']: r for r in dual_qp_results}

    for size in BOUNDARY_SIZES:
        ucx = ucx_by_size.get(size, {})
        dqp = dqp_by_size.get(size, {})

        ucx_p50 = f"{ucx.get('latency_us', 'N/A')}"
        ucx_p99 = "N/A"  # ucx_perftest typically reports mean
        dqp_p50 = f"{dqp.get('p50_us', 'N/A'):.1f}" if 'p50_us' in dqp else "N/A"
        dqp_p99 = f"{dqp.get('p99_us', 'N/A'):.1f}" if 'p99_us' in dqp else "N/A"

        # Highlight rows near protocol boundaries
        marker = ""
        if size in [3000, 8192, 32768, 65536]:
            marker = r" $\dag$"

        lines.append(
            f"  {size:>8d}{marker} & {ucx_p50} & {dqp_p50} & {ucx_p99} & {dqp_p99} \\\\"
        )

    lines.extend([
        r"\bottomrule",
        r"\multicolumn{5}{l}{\footnotesize $\dag$ Near UCX protocol transition boundary (Issues \#10552, \#10486, \#10532)} \\",
        r"\end{tabular}",
        r"\end{table}",
    ])
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='UCX vs libscuffedrdma Comparison Benchmark'
    )
    parser.add_argument('--output', type=str,
                        default=str(Path(__file__).parent / 'results'))
    parser.add_argument('--iterations', type=int, default=100,
                        help='Iterations per message size')
    parser.add_argument('--skip-ucx', action='store_true',
                        help='Skip UCX benchmark (use if UCX not installed)')
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    print("UCX vs libscuffedrdma Comparison Benchmark")
    print(f"  Message sizes: {len(BOUNDARY_SIZES)} ({BOUNDARY_SIZES[0]}B - {BOUNDARY_SIZES[-1]}B)")
    print()

    # Check UCX availability
    ucx_available, ucx_msg = check_ucx_available()
    print(f"  UCX: {ucx_msg}")

    # Run UCX benchmark
    ucx_results = []
    if ucx_available and not args.skip_ucx:
        print("\n  Running UCX perftest...")
        for size in BOUNDARY_SIZES:
            result = run_ucx_perftest(size, iterations=args.iterations)
            if result:
                ucx_results.append(result)
                lat = result.get('latency_us', 'N/A')
                print(f"    Size {size:>8d}B: {lat}")
    else:
        print("\n  Skipping UCX benchmark (not available or --skip-ucx)")

    # Run dual QP benchmark
    print("\n  Running Dual QP benchmark...")
    dual_qp_results = run_dual_qp_benchmark(BOUNDARY_SIZES, args.iterations)

    # Save results
    output = {
        'ucx_available': ucx_available,
        'ucx_message': ucx_msg,
        'ucx_results': ucx_results,
        'dual_qp_results': dual_qp_results,
        'message_sizes': BOUNDARY_SIZES,
        'ucx_issues_referenced': [
            '#10552: eager->RNDV 50x latency cliff',
            '#10486: >32KB RDMA send->read switch',
            '#10532: eager->zcopy transition at ~3000B',
            '#11091: RNDV heuristic regression in 1.19',
        ],
    }

    output_file = os.path.join(args.output, 'ucx_comparison.json')
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nResults saved to {output_file}")

    # Generate LaTeX
    latex = generate_comparison_table(ucx_results, dual_qp_results)
    latex_file = os.path.join(args.output, 'ucx_comparison_table.tex')
    with open(latex_file, 'w') as f:
        f.write(latex)
    print(f"LaTeX table saved to {latex_file}")


if __name__ == '__main__':
    main()
