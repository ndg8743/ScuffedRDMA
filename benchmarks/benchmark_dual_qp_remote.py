#!/usr/bin/env python3
"""
Cross-Node Dual QP Pool Benchmark (Chimera <-> Cerberus).

Server/client pattern for benchmarking over real 10GbE.
Simulates KV cache transfer: 32 layers, 32 heads, 128 head_dim, seq_len=512.

Usage:
    # On cerberus (server):
    python benchmark_dual_qp_remote.py --role server --port 19877

    # On chimera (client):
    python benchmark_dual_qp_remote.py --role client --host 192.168.1.242 --port 19877
"""

import argparse
import json
import os
import socket
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from middleware.rdma_tensor_cache.dual_qp_pool import (
    DualQPPool, QueueSelection, RegisteredBuffer,
)
from middleware.rdma_tensor_cache.wfa_classifier import WFAClassifier
from middleware.rdma_tensor_cache.pmp_controller import PMPController


# KV cache simulation parameters
NUM_LAYERS = 32
NUM_HEADS = 32
HEAD_DIM = 128
SEQ_LEN = 512

# Per-layer KV cache size: 2 (K+V) * num_heads * seq_len * head_dim * 2 (FP16)
KV_LAYER_SIZE = 2 * NUM_HEADS * SEQ_LEN * HEAD_DIM * 2  # = 8MB per layer
TOKEN_SIZE = NUM_HEADS * HEAD_DIM * 2  # = 8KB per token

OOB_PORT = 19877


def exchange_qp_info_server(port: int, local_info: dict) -> dict:
    """TCP server for QP info exchange."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', port))
    sock.listen(1)
    print(f"  Waiting for client on port {port}...")
    conn, addr = sock.accept()
    print(f"  Client connected from {addr}")

    # Serialize gid
    info_to_send = _serialize_info(local_info)
    data = json.dumps(info_to_send).encode()
    conn.sendall(len(data).to_bytes(4, 'big') + data)

    size = int.from_bytes(conn.recv(4), 'big')
    remote_data = _deserialize_info(json.loads(conn.recv(size).decode()))

    conn.close()
    sock.close()
    return remote_data


def exchange_qp_info_client(host: str, port: int, local_info: dict) -> dict:
    """TCP client for QP info exchange."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(30)
    print(f"  Connecting to {host}:{port}...")
    sock.connect((host, port))

    # Receive server info
    size = int.from_bytes(sock.recv(4), 'big')
    remote_data = _deserialize_info(json.loads(sock.recv(size).decode()))

    # Send client info
    info_to_send = _serialize_info(local_info)
    data = json.dumps(info_to_send).encode()
    sock.sendall(len(data).to_bytes(4, 'big') + data)

    sock.close()
    return remote_data


def _serialize_info(info: dict) -> dict:
    """Make QP info JSON-serializable (GID object -> string)."""
    result = {}
    for k, v in info.items():
        if hasattr(v, 'gid'):  # pyverbs GID object
            result[k] = str(v)
        elif isinstance(v, list):
            result[k] = v
        else:
            result[k] = v
    return result


def _deserialize_info(info: dict) -> dict:
    """Reconstruct GID object from serialized info."""
    from pyverbs.addr import GID
    result = dict(info)
    if 'gid' in result and isinstance(result['gid'], str):
        result['gid'] = GID(result['gid'])
    return result


def run_kv_transfer_single_qp(pool: DualQPPool, recv_buf: RegisteredBuffer,
                               send_buf: RegisteredBuffer,
                               iterations: int) -> Dict:
    """Scenario A: all KV layers on single QP."""
    latencies = []

    for iteration in range(iterations):
        for layer in range(NUM_LAYERS):
            offset = 0
            # Transfer token-sized chunks (simulating decode) and
            # full-layer chunks (simulating prefill)
            if iteration % 2 == 0:
                # Prefill: full layer transfer (8MB)
                size = min(KV_LAYER_SIZE, send_buf.array.size)
                lat = pool.post_write_hot(
                    send_buf, recv_buf.addr, recv_buf.rkey, size
                )
            else:
                # Decode: single token (8KB)
                size = min(TOKEN_SIZE, send_buf.array.size)
                lat = pool.post_write_hot(
                    send_buf, recv_buf.addr, recv_buf.rkey, size
                )
            latencies.append({
                'layer': layer,
                'iteration': iteration,
                'size': size,
                'type': 'prefill' if iteration % 2 == 0 else 'decode',
                'latency_us': lat,
            })

    # Compute per-type stats
    prefill_lats = [l['latency_us'] for l in latencies if l['type'] == 'prefill']
    decode_lats = [l['latency_us'] for l in latencies if l['type'] == 'decode']

    def percentiles(lats):
        if not lats:
            return {}
        s = sorted(lats)
        return {
            'p50': s[len(s) // 2],
            'p95': s[int(len(s) * 0.95)],
            'p99': s[int(len(s) * 0.99)],
            'mean': sum(s) / len(s),
            'count': len(s),
        }

    return {
        'scenario': 'A_single_qp',
        'prefill_stats': percentiles(prefill_lats),
        'decode_stats': percentiles(decode_lats),
        'hot_stats': pool.hot_stats.to_dict(),
    }


def run_kv_transfer_dual_qp(pool: DualQPPool, recv_buf: RegisteredBuffer,
                             send_buf: RegisteredBuffer,
                             iterations: int,
                             use_pmp: bool = False) -> Dict:
    """Scenario B/C: dual QP with classifier and optional PMP."""
    classifier = WFAClassifier()
    controller = PMPController() if use_pmp else None

    latencies = []

    for iteration in range(iterations):
        for layer in range(NUM_LAYERS):
            if iteration % 2 == 0:
                size = min(KV_LAYER_SIZE, send_buf.array.size)
                transfer_type = 'prefill'
            else:
                size = min(TOKEN_SIZE, send_buf.array.size)
                transfer_type = 'decode'

            tensor_id = f"kv_L{layer}_{transfer_type}"
            queue = classifier.classify(tensor_id, size, layer_idx=layer)

            if controller is not None:
                hd, cd = pool.sample_queue_depths()
                pmp_queue = controller.decide(hd, cd)
                # Let PMP override for mid-range
                if TOKEN_SIZE < size < KV_LAYER_SIZE:
                    queue = pmp_queue

            if queue == QueueSelection.HOT_QP:
                lat = pool.post_write_hot(
                    send_buf, recv_buf.addr, recv_buf.rkey, size
                )
            else:
                lat = pool.post_write_cold(
                    send_buf, recv_buf.addr, recv_buf.rkey, size
                )

            latencies.append({
                'layer': layer,
                'iteration': iteration,
                'size': size,
                'type': transfer_type,
                'queue': queue.value,
                'latency_us': lat,
            })

    prefill_lats = [l['latency_us'] for l in latencies if l['type'] == 'prefill']
    decode_lats = [l['latency_us'] for l in latencies if l['type'] == 'decode']
    hot_decode = [l['latency_us'] for l in latencies
                  if l['type'] == 'decode' and l['queue'] == 'hot']

    def percentiles(lats):
        if not lats:
            return {}
        s = sorted(lats)
        return {
            'p50': s[len(s) // 2],
            'p95': s[int(len(s) * 0.95)],
            'p99': s[int(len(s) * 0.99)],
            'mean': sum(s) / len(s),
            'count': len(s),
        }

    scenario = 'C_dual_qp_pmp' if use_pmp else 'B_dual_qp'
    result = {
        'scenario': scenario,
        'prefill_stats': percentiles(prefill_lats),
        'decode_stats': percentiles(decode_lats),
        'hot_decode_stats': percentiles(hot_decode),
        'hot_stats': pool.hot_stats.to_dict(),
        'cold_stats': pool.cold_stats.to_dict(),
        'classifier_stats': classifier.get_stats(),
    }
    if controller:
        result['pmp_stats'] = controller.get_stats()
    return result


def main():
    parser = argparse.ArgumentParser(
        description='Cross-Node Dual QP Pool Benchmark'
    )
    parser.add_argument('--role', required=True, choices=['server', 'client'])
    parser.add_argument('--host', type=str, default='192.168.1.242',
                        help='Server host (for client mode)')
    parser.add_argument('--port', type=int, default=OOB_PORT)
    parser.add_argument('--device', type=str, default='rxe0')
    parser.add_argument('--gid-index', type=int, default=2,
                        help='GID index (2 = IPv4-mapped for cross-node)')
    parser.add_argument('--iterations', type=int, default=10,
                        help='Number of full KV cache transfer iterations')
    parser.add_argument('--output', type=str,
                        default=str(Path(__file__).parent / 'results'))
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    print(f"Cross-Node Dual QP Benchmark")
    print(f"  Role: {args.role}")
    print(f"  Device: {args.device}")
    print(f"  KV cache: {NUM_LAYERS} layers, {NUM_HEADS} heads, "
          f"{HEAD_DIM} head_dim, seq_len={SEQ_LEN}")
    print(f"  Per-layer size: {KV_LAYER_SIZE / 1024:.0f} KB")
    print(f"  Token size: {TOKEN_SIZE / 1024:.0f} KB")
    print()

    # Create pool
    pool = DualQPPool(device_name=args.device, gid_index=args.gid_index,
                       n_hot=2, n_cold=2)
    pool.open()

    local_info = pool.get_local_info()

    # Exchange QP info
    if args.role == 'server':
        remote_info = exchange_qp_info_server(args.port, local_info)
    else:
        remote_info = exchange_qp_info_client(args.host, args.port, local_info)

    pool.connect_all(remote_info)
    print("  QPs connected.")

    # Register buffers
    max_size = min(KV_LAYER_SIZE, 16 * 1024 * 1024)  # Cap at 16MB
    send_buf = pool.register_buffer('send', max_size)
    recv_buf = pool.register_buffer('recv', max_size)

    # Fill send buffer with pattern
    np.copyto(send_buf.array[:min(4096, max_size)],
              np.frombuffer(b'\xAA' * min(4096, max_size), dtype=np.uint8))

    results = {}

    if args.role == 'server':
        # Server drives transfers
        print("\n  [A] Single QP baseline...")
        results['scenario_A'] = run_kv_transfer_single_qp(
            pool, recv_buf, send_buf, args.iterations
        )
        print(f"      Decode p99: {results['scenario_A']['decode_stats'].get('p99', 'N/A'):.1f} us")

        # Reset stats
        pool.hot_stats = type(pool.hot_stats)()
        pool.cold_stats = type(pool.cold_stats)()

        print("  [B] Dual QP (WFA classifier)...")
        results['scenario_B'] = run_kv_transfer_dual_qp(
            pool, recv_buf, send_buf, args.iterations
        )
        print(f"      Hot-decode p99: {results['scenario_B']['hot_decode_stats'].get('p99', 'N/A'):.1f} us")

        pool.hot_stats = type(pool.hot_stats)()
        pool.cold_stats = type(pool.cold_stats)()

        print("  [C] Dual QP + PMP...")
        results['scenario_C'] = run_kv_transfer_dual_qp(
            pool, recv_buf, send_buf, args.iterations, use_pmp=True
        )
        print(f"      Hot-decode p99: {results['scenario_C']['hot_decode_stats'].get('p99', 'N/A'):.1f} us")

        # Save results
        output_file = os.path.join(args.output, 'dual_qp_remote_benchmark.json')
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n  Results saved to {output_file}")

    else:
        # Client: passive side, just keep pool alive
        print("  Client ready. Waiting for server transfers...")
        try:
            input("  Press Enter when server is done...")
        except EOFError:
            time.sleep(60)

    pool.close()
    print("  Done.")


if __name__ == '__main__':
    main()
