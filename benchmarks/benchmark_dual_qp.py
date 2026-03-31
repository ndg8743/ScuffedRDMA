#!/usr/bin/env python3
"""
Dual QP Pool Loopback Benchmark.

Two DualQPPools on the same rxe0 device, connected in-process.
Measures head-of-line blocking elimination.

Scenarios:
  A) Baseline: all traffic on single hot QP (mixed 256B + 1MB)
  B) Dual QP: small on hot, large on cold (WFA classifier)
  C) Dual QP + PMP: bang-bang controller manages routing

Usage:
    python benchmark_dual_qp.py [--iterations N] [--output PATH]
"""

import argparse
import json
import os
import sys
import time
import statistics
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from middleware.rdma_tensor_cache.dual_qp_pool import (
    DualQPPool, QueueSelection, QueueStats, RegisteredBuffer,
)
from middleware.rdma_tensor_cache.wfa_classifier import WFAClassifier
from middleware.rdma_tensor_cache.pmp_controller import PMPController

SMALL_SIZE = 256
LARGE_SIZE = 1048576


def make_loopback_pair(n_hot=2, n_cold=2):
    """Create two connected DualQPPools on rxe0."""
    p1 = DualQPPool(device_name="rxe0", n_hot=n_hot, n_cold=n_cold)
    p2 = DualQPPool(device_name="rxe0", n_hot=n_hot, n_cold=n_cold)
    p1.open()
    p2.open()
    i1 = p1.get_local_info()
    i2 = p2.get_local_info()
    p1.connect_all(i2)
    p2.connect_all(i1)
    return p1, p2


def percentiles(lats):
    if not lats:
        return {'p50': 0, 'p95': 0, 'p99': 0, 'mean': 0, 'count': 0}
    s = sorted(lats)
    return {
        'p50': s[len(s) // 2],
        'p95': s[int(len(s) * 0.95)],
        'p99': s[int(len(s) * 0.99)],
        'mean': statistics.mean(s),
        'count': len(s),
    }


def scenario_a(iterations):
    """All traffic on single hot QP - baseline for HOL blocking."""
    sender, receiver = make_loopback_pair(n_hot=1, n_cold=1)
    send_buf = sender.register_buffer('send', LARGE_SIZE)
    recv_buf = receiver.register_buffer('recv', LARGE_SIZE)
    send_buf.write(b'\xAA' * min(4096, SMALL_SIZE))

    small_lats, large_lats = [], []
    for i in range(iterations):
        if i % 2 == 0:
            lat = sender.post_write_hot(send_buf, recv_buf.addr,
                                        recv_buf.rkey, SMALL_SIZE)
            small_lats.append(lat)
        else:
            lat = sender.post_write_hot(send_buf, recv_buf.addr,
                                        recv_buf.rkey, LARGE_SIZE)
            large_lats.append(lat)

    result = {
        'scenario': 'A_single_qp',
        'small_percentiles': percentiles(small_lats),
        'large_percentiles': percentiles(large_lats),
        'hot_stats': sender.hot_stats.to_dict(),
    }
    sender.close()
    receiver.close()
    return result


def scenario_b(iterations):
    """Dual QP with WFA classifier."""
    sender, receiver = make_loopback_pair(n_hot=2, n_cold=2)
    send_buf = sender.register_buffer('send', LARGE_SIZE)
    recv_buf = receiver.register_buffer('recv', LARGE_SIZE)
    send_buf.write(b'\xAA' * min(4096, SMALL_SIZE))

    classifier = WFAClassifier()
    small_hot, large_cold = [], []

    for i in range(iterations):
        is_small = (i % 2 == 0)
        size = SMALL_SIZE if is_small else LARGE_SIZE
        queue = classifier.classify(f"t_{i}", size, layer_idx=i % 32)

        if queue == QueueSelection.HOT_QP:
            lat = sender.post_write_hot(send_buf, recv_buf.addr,
                                        recv_buf.rkey, size)
            if is_small:
                small_hot.append(lat)
        else:
            lat = sender.post_write_cold(send_buf, recv_buf.addr,
                                         recv_buf.rkey, size)
            if not is_small:
                large_cold.append(lat)

    result = {
        'scenario': 'B_dual_qp',
        'small_hot_percentiles': percentiles(small_hot),
        'large_cold_percentiles': percentiles(large_cold),
        'hot_stats': sender.hot_stats.to_dict(),
        'cold_stats': sender.cold_stats.to_dict(),
        'classifier_stats': classifier.get_stats(),
    }
    sender.close()
    receiver.close()
    return result


def scenario_c(iterations):
    """Dual QP + PMP bang-bang controller."""
    sender, receiver = make_loopback_pair(n_hot=2, n_cold=2)
    send_buf = sender.register_buffer('send', LARGE_SIZE)
    recv_buf = receiver.register_buffer('recv', LARGE_SIZE)
    send_buf.write(b'\xAA' * min(4096, SMALL_SIZE))

    classifier = WFAClassifier()
    controller = PMPController()
    small_hot, large_cold = [], []

    for i in range(iterations):
        is_small = (i % 2 == 0)
        size = SMALL_SIZE if is_small else LARGE_SIZE
        queue = classifier.classify(f"t_{i}", size, layer_idx=i % 32)

        hd, cd = sender.sample_queue_depths()
        pmp_queue = controller.decide(hd, cd)

        if queue == QueueSelection.HOT_QP:
            lat = sender.post_write_hot(send_buf, recv_buf.addr,
                                        recv_buf.rkey, size)
            if is_small:
                small_hot.append(lat)
        else:
            lat = sender.post_write_cold(send_buf, recv_buf.addr,
                                         recv_buf.rkey, size)
            if not is_small:
                large_cold.append(lat)

    result = {
        'scenario': 'C_dual_qp_pmp',
        'small_hot_percentiles': percentiles(small_hot),
        'large_cold_percentiles': percentiles(large_cold),
        'hot_stats': sender.hot_stats.to_dict(),
        'cold_stats': sender.cold_stats.to_dict(),
        'classifier_stats': classifier.get_stats(),
        'pmp_stats': controller.get_stats(),
    }
    sender.close()
    receiver.close()
    return result


def generate_latex_table(results):
    lines = [
        r"\begin{table}[h]",
        r"\centering",
        r"\caption{Dual QP Pool Head-of-Line Blocking (SoftRoCE Loopback)}",
        r"\label{tab:dual_qp_results}",
        r"\begin{tabular}{lrrrrr}",
        r"\toprule",
        r"Scenario & Small p50 ($\mu$s) & Small p95 ($\mu$s) & Small p99 ($\mu$s) & Ops & Bytes \\",
        r"\midrule",
    ]

    for key, label in [
        ('scenario_A', 'Single QP (baseline)'),
        ('scenario_B', 'Dual QP (WFA)'),
        ('scenario_C', 'Dual QP + PMP'),
    ]:
        data = results.get(key, {})
        if 'error' in data:
            lines.append(f"  {label} & \\multicolumn{{5}}{{c}}{{Error}} \\\\")
            continue

        p = data.get('small_percentiles', data.get('small_hot_percentiles', {}))
        stats = data.get('hot_stats', {})
        lines.append(
            f"  {label} & {p.get('p50', 0):.1f} & {p.get('p95', 0):.1f} & "
            f"{p.get('p99', 0):.1f} & {stats.get('ops_completed', 0)} & "
            f"{stats.get('bytes_transferred', 0)} \\\\"
        )

    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Dual QP Pool Loopback Benchmark')
    parser.add_argument('--iterations', type=int, default=200)
    parser.add_argument('--output', type=str,
                        default=str(Path(__file__).parent / 'results'))
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    print(f"Dual QP Pool Benchmark (in-process loopback)")
    print(f"  Iterations: {args.iterations}")
    print(f"  Small: {SMALL_SIZE}B, Large: {LARGE_SIZE}B")
    print()

    results = {}

    print("  [A] Single QP baseline...")
    try:
        results['scenario_A'] = scenario_a(args.iterations)
        p = results['scenario_A']['small_percentiles']
        print(f"      Small p50={p['p50']:.1f}  p95={p['p95']:.1f}  p99={p['p99']:.1f} us")
    except Exception as e:
        print(f"      FAILED: {e}")
        results['scenario_A'] = {'error': str(e)}

    print("  [B] Dual QP (WFA)...")
    try:
        results['scenario_B'] = scenario_b(args.iterations)
        p = results['scenario_B']['small_hot_percentiles']
        print(f"      Small-hot p50={p['p50']:.1f}  p95={p['p95']:.1f}  p99={p['p99']:.1f} us")
    except Exception as e:
        print(f"      FAILED: {e}")
        results['scenario_B'] = {'error': str(e)}

    print("  [C] Dual QP + PMP...")
    try:
        results['scenario_C'] = scenario_c(args.iterations)
        p = results['scenario_C']['small_hot_percentiles']
        print(f"      Small-hot p50={p['p50']:.1f}  p95={p['p95']:.1f}  p99={p['p99']:.1f} us")
    except Exception as e:
        print(f"      FAILED: {e}")
        results['scenario_C'] = {'error': str(e)}

    # Save
    with open(os.path.join(args.output, 'dual_qp_benchmark.json'), 'w') as f:
        json.dump(results, f, indent=2, default=str)

    latex = generate_latex_table(results)
    with open(os.path.join(args.output, 'dual_qp_table.tex'), 'w') as f:
        f.write(latex)

    print(f"\nResults saved to {args.output}/")

    # HOL blocking comparison
    a = results.get('scenario_A', {})
    b = results.get('scenario_B', {})
    if 'error' not in a and 'error' not in b:
        a99 = a['small_percentiles']['p99']
        b99 = b['small_hot_percentiles']['p99']
        if a99 > 0:
            print(f"\n  HOL blocking reduction: {((a99 - b99) / a99 * 100):.1f}%")
            print(f"  Single QP small p99: {a99:.1f} us")
            print(f"  Dual QP hot p99:     {b99:.1f} us")


if __name__ == '__main__':
    main()
