#!/usr/bin/env python3
"""ScuffedRDMA P2P latency benchmark across message sizes."""
import argparse, json, socket, sys, time
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from common import save_json, detect_node
from middleware.rdma_tensor_cache.dual_qp_pool import DualQPPool, RegisteredBuffer

SIZES = [64, 1024, 4096, 65536, 262144, 1048576, 4194304]
OOB_PORT = 19878


def _recv_exact(sock, n):
    buf = b''
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("socket closed")
        buf += chunk
    return buf


def _serialize_info(info):
    return {k: str(v) if hasattr(v, 'gid') else v for k, v in info.items()}


def _deserialize_info(info):
    from pyverbs.addr import GID
    result = dict(info)
    if 'gid' in result and isinstance(result['gid'], str):
        result['gid'] = GID(result['gid'])
    return result


def exchange_server(port, local_info):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', port))
    sock.listen(1)
    print(f"Waiting for client on :{port}")
    conn, addr = sock.accept()
    print(f"Client connected: {addr}")
    data = json.dumps(_serialize_info(local_info)).encode()
    conn.sendall(len(data).to_bytes(4, 'big') + data)
    sz = int.from_bytes(_recv_exact(conn, 4), 'big')
    remote = _deserialize_info(json.loads(_recv_exact(conn, sz)))
    conn.close(); sock.close()
    return remote


def exchange_client(host, port, local_info):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(30)
    print(f"Connecting to {host}:{port}")
    sock.connect((host, port))
    sz = int.from_bytes(_recv_exact(sock, 4), 'big')
    remote = _deserialize_info(json.loads(_recv_exact(sock, sz)))
    data = json.dumps(_serialize_info(local_info)).encode()
    sock.sendall(len(data).to_bytes(4, 'big') + data)
    sock.close()
    return remote


def percentiles(lats):
    s = sorted(lats)
    n = len(s)
    return {
        'p50': s[n // 2],
        'p95': s[int(n * 0.95)],
        'p99': s[int(n * 0.99)],
        'mean': sum(s) / n,
        'count': n,
    }


def bench_write(pool, send_buf, recv_buf, size, iterations):
    lats = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        pool.post_write_hot(send_buf, recv_buf.addr, recv_buf.rkey, size)
        lats.append((time.perf_counter() - t0) * 1e6)
    return percentiles(lats)


def main():
    ap = argparse.ArgumentParser(description='ScuffedRDMA P2P benchmark')
    ap.add_argument('--role', required=True, choices=['server', 'client'])
    ap.add_argument('--host', default='192.168.1.242')
    ap.add_argument('--port', type=int, default=OOB_PORT)
    ap.add_argument('--device', default='rxe0')
    ap.add_argument('--gid-index', type=int, default=2)
    ap.add_argument('--iterations', type=int, default=50)
    args = ap.parse_args()

    pool = DualQPPool(device_name=args.device, gid_index=args.gid_index, n_hot=2, n_cold=2)
    pool.open()

    local_info = pool.get_local_info()
    if args.role == 'server':
        remote_info = exchange_server(args.port, local_info)
    else:
        remote_info = exchange_client(args.host, args.port, local_info)
    pool.connect_all(remote_info)

    max_sz = max(SIZES)
    send_buf = pool.register_buffer('send', max_sz)
    recv_buf = pool.register_buffer('recv', max_sz)
    send_buf.write(b'\xAA' * min(4096, max_sz))

    results = {'type': 'scuffedrdma_p2p', 'role': args.role, 'device': args.device, 'sizes': {}}

    if args.role == 'server':
        for sz in SIZES:
            stats = bench_write(pool, send_buf, recv_buf, sz, args.iterations)
            results['sizes'][str(sz)] = stats
            print(f"  {sz:>8} B  p50={stats['p50']:.1f} p95={stats['p95']:.1f} p99={stats['p99']:.1f} us")
        save_json(results, 'scuffedrdma_p2p')
    else:
        print("Client passive. Press Enter when server finishes.")
        try:
            input()
        except EOFError:
            time.sleep(120)

    pool.close()
    print("Done.")


if __name__ == '__main__':
    main()
