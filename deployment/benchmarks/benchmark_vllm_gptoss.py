#!/usr/bin/env python3
"""
vLLM gpt-oss-120b Benchmark
Tests with and without RDMA networking

Usage:
    # Without RDMA (TCP fallback)
    NCCL_NET_GDR_LEVEL=0 python benchmark_vllm_gptoss.py

    # With RDMA (Soft-RoCE)
    NCCL_IB_HCA=rxe0 python benchmark_vllm_gptoss.py
"""

import time
import os
import json
import statistics
from openai import OpenAI

# Configuration
VLLM_URL = os.getenv("VLLM_URL", "http://localhost:8000/v1")
MODEL = os.getenv("MODEL", "openai/gpt-oss-120b")
ITERATIONS = int(os.getenv("ITERATIONS", "5"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "100"))
PROMPT = "Explain RDMA (Remote Direct Memory Access) networking and its benefits for distributed AI inference in exactly 100 words."

def run_benchmark():
    client = OpenAI(base_url=VLLM_URL, api_key="dummy")

    # Check RDMA settings
    rdma_mode = "RDMA" if os.getenv("NCCL_IB_HCA") else "TCP"
    gdr_level = os.getenv("NCCL_NET_GDR_LEVEL", "auto")

    print("=" * 60)
    print(f"vLLM gpt-oss-120b Benchmark")
    print("=" * 60)
    print(f"Endpoint: {VLLM_URL}")
    print(f"Model: {MODEL}")
    print(f"Mode: {rdma_mode} (GDR_LEVEL={gdr_level})")
    print(f"Iterations: {ITERATIONS}")
    print(f"Max tokens: {MAX_TOKENS}")
    print("=" * 60)
    print()

    # Warm up
    print("Warming up...")
    try:
        client.completions.create(model=MODEL, prompt="Hi", max_tokens=5)
    except Exception as e:
        print(f"Warmup failed: {e}")
        return

    results = []
    tokens_generated = []
    ttft_list = []

    print(f"\nRunning {ITERATIONS} iterations...\n")

    for i in range(ITERATIONS):
        start_time = time.perf_counter()
        first_token_time = None

        try:
            # Use streaming to measure TTFT
            stream = client.completions.create(
                model=MODEL,
                prompt=PROMPT,
                max_tokens=MAX_TOKENS,
                stream=True
            )

            token_count = 0
            for chunk in stream:
                if first_token_time is None:
                    first_token_time = time.perf_counter()
                if chunk.choices[0].text:
                    token_count += len(chunk.choices[0].text.split())

            end_time = time.perf_counter()

            total_time = end_time - start_time
            ttft = first_token_time - start_time if first_token_time else total_time
            tps = token_count / total_time if total_time > 0 else 0

            results.append(total_time)
            tokens_generated.append(token_count)
            ttft_list.append(ttft)

            print(f"Iteration {i+1}: {token_count} tokens in {total_time:.3f}s = {tps:.2f} tok/s (TTFT: {ttft*1000:.1f}ms)")

        except Exception as e:
            print(f"Iteration {i+1}: ERROR - {e}")
            results.append(0)
            tokens_generated.append(0)
            ttft_list.append(0)

    # Calculate statistics
    valid_results = [r for r in results if r > 0]
    valid_tokens = [t for t, r in zip(tokens_generated, results) if r > 0]
    valid_ttft = [t for t in ttft_list if t > 0]

    if valid_results:
        total_tokens = sum(valid_tokens)
        total_time = sum(valid_results)
        avg_tps = total_tokens / total_time
        avg_ttft = statistics.mean(valid_ttft) * 1000  # Convert to ms

        print()
        print("=" * 60)
        print("RESULTS")
        print("=" * 60)
        print(f"Mode: {rdma_mode}")
        print(f"Total tokens: {total_tokens}")
        print(f"Total time: {total_time:.3f}s")
        print(f"Average tokens/sec: {avg_tps:.2f}")
        print(f"Average TTFT: {avg_ttft:.1f}ms")
        print(f"Std dev (time): {statistics.stdev(valid_results):.3f}s" if len(valid_results) > 1 else "")
        print("=" * 60)

        # Output JSON for comparison
        output = {
            "mode": rdma_mode,
            "model": MODEL,
            "iterations": len(valid_results),
            "total_tokens": total_tokens,
            "total_time_sec": total_time,
            "avg_tokens_per_sec": avg_tps,
            "avg_ttft_ms": avg_ttft,
            "nccl_ib_hca": os.getenv("NCCL_IB_HCA", "none"),
            "nccl_gdr_level": gdr_level
        }
        print(f"\nJSON: {json.dumps(output)}")

if __name__ == "__main__":
    run_benchmark()
