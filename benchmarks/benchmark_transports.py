#!/usr/bin/env python3
"""
ScuffedRDMA Transport Benchmark Suite

Unified benchmarking tool for comparing TCP, Soft-RoCE, and TTPoe transports
in distributed LLM inference scenarios.

Usage:
    python benchmark_transports.py [OPTIONS]

Options:
    --transport TYPE    Transport to benchmark (tcp, roce, ttpoe, all)
    --model NAME        Model name for vLLM testing
    --iterations N      Number of benchmark iterations
    --output PATH       Output directory for results
    --latex             Generate LaTeX tables

Environment:
    SCUFFED_TRANSPORT   Default transport selection
    VLLM_URL            vLLM API endpoint
"""

import argparse
import json
import os
import sys
import time
import statistics
import subprocess
import psutil
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add middleware to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from middleware import TransportSelector, TransportMetrics, NCCLConfig
except ImportError:
    TransportSelector = None


@dataclass
class BenchmarkResult:
    """Results from a single benchmark iteration."""
    iteration: int
    tokens: int
    time_sec: float
    tokens_per_sec: float
    ttft_ms: float = 0.0
    cpu_percent: float = 0.0


@dataclass
class TransportBenchmark:
    """Complete benchmark results for a transport."""
    transport: str
    model: str
    iterations: int
    results: List[BenchmarkResult] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # Aggregated metrics
    avg_tokens_per_sec: float = 0.0
    std_tokens_per_sec: float = 0.0
    avg_ttft_ms: float = 0.0
    avg_cpu_percent: float = 0.0
    total_tokens: int = 0
    total_time_sec: float = 0.0

    def calculate_aggregates(self):
        """Calculate aggregate statistics from results."""
        if not self.results:
            return

        tps_values = [r.tokens_per_sec for r in self.results if r.tokens_per_sec > 0]
        ttft_values = [r.ttft_ms for r in self.results if r.ttft_ms > 0]
        cpu_values = [r.cpu_percent for r in self.results if r.cpu_percent > 0]

        if tps_values:
            self.avg_tokens_per_sec = statistics.mean(tps_values)
            self.std_tokens_per_sec = statistics.stdev(tps_values) if len(tps_values) > 1 else 0.0

        if ttft_values:
            self.avg_ttft_ms = statistics.mean(ttft_values)

        if cpu_values:
            self.avg_cpu_percent = statistics.mean(cpu_values)

        self.total_tokens = sum(r.tokens for r in self.results)
        self.total_time_sec = sum(r.time_sec for r in self.results)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        self.calculate_aggregates()
        return {
            'transport': self.transport,
            'model': self.model,
            'iterations': self.iterations,
            'timestamp': self.timestamp,
            'results': [asdict(r) for r in self.results],
            'summary': {
                'avg_tokens_per_sec': round(self.avg_tokens_per_sec, 2),
                'std_tokens_per_sec': round(self.std_tokens_per_sec, 2),
                'avg_ttft_ms': round(self.avg_ttft_ms, 1),
                'avg_cpu_percent': round(self.avg_cpu_percent, 1),
                'total_tokens': self.total_tokens,
                'total_time_sec': round(self.total_time_sec, 3),
            }
        }


class TransportBenchmarker:
    """
    Benchmark runner for transport comparison.

    Supports three benchmark modes:
    1. Raw transport (direct socket/RDMA performance)
    2. NCCL collective operations
    3. vLLM inference (end-to-end)
    """

    # Test prompts for vLLM benchmarking
    PROMPTS = [
        "Explain RDMA networking and its benefits for distributed AI inference in 100 words.",
        "Describe how tensor parallelism works in large language model inference.",
        "What are the key differences between TCP and RDMA for data center networking?",
    ]

    def __init__(self,
                 model: str = "meta-llama/Llama-4-Scout-17B-16E",
                 vllm_url: str = "http://localhost:8000/v1",
                 iterations: int = 5,
                 max_tokens: int = 100):
        """
        Initialize benchmarker.

        Args:
            model: Model name for vLLM testing
            vllm_url: vLLM API endpoint
            iterations: Number of benchmark iterations
            max_tokens: Max tokens per request
        """
        self.model = model
        self.vllm_url = vllm_url
        self.iterations = iterations
        self.max_tokens = max_tokens
        self.results: Dict[str, TransportBenchmark] = {}

    def benchmark_raw_transport(self, transport: str,
                                 host: str = "localhost",
                                 port: int = 12345,
                                 message_size: int = 4096) -> TransportMetrics:
        """
        Benchmark raw transport performance (socket-level).

        Args:
            transport: Transport type (tcp, roce, ttpoe)
            host: Remote host
            port: Remote port
            message_size: Size of test messages

        Returns:
            TransportMetrics with results
        """
        if TransportSelector is None:
            raise RuntimeError("Middleware not available")

        selector = TransportSelector(transport)
        trans = selector.get_transport()

        if not trans.is_available():
            raise RuntimeError(f"Transport {transport} not available")

        try:
            trans.connect(host, port)
            trans.reset_metrics()

            test_data = b'X' * message_size

            for i in range(self.iterations):
                # Measure send latency
                start = time.perf_counter()
                trans.send(test_data)
                response = trans.recv(message_size, timeout=5.0)
                latency = time.perf_counter() - start

                trans.metrics.update_latency(latency)

            return trans.get_metrics()

        finally:
            trans.disconnect()

    def benchmark_vllm(self, transport: str) -> TransportBenchmark:
        """
        Benchmark vLLM inference with specified transport.

        Args:
            transport: Transport type (affects NCCL configuration)

        Returns:
            TransportBenchmark with results
        """
        benchmark = TransportBenchmark(
            transport=transport,
            model=self.model,
            iterations=self.iterations
        )

        try:
            import requests
        except ImportError:
            print("requests library required for vLLM benchmarking")
            return benchmark

        # Warmup
        print(f"  Warming up {transport}...")
        try:
            requests.post(
                f"{self.vllm_url}/completions",
                json={"model": self.model, "prompt": "Hi", "max_tokens": 5},
                timeout=60
            )
        except Exception as e:
            print(f"  Warmup failed: {e}")

        print(f"  Running {self.iterations} iterations...")

        for i in range(self.iterations):
            prompt = self.PROMPTS[i % len(self.PROMPTS)]

            # Measure CPU before request
            cpu_before = psutil.cpu_percent(interval=None)

            start_time = time.perf_counter()
            first_token_time = None

            try:
                # Use streaming to measure TTFT
                response = requests.post(
                    f"{self.vllm_url}/completions",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "max_tokens": self.max_tokens,
                        "stream": True
                    },
                    stream=True,
                    timeout=300
                )

                token_count = 0
                for line in response.iter_lines():
                    if first_token_time is None:
                        first_token_time = time.perf_counter()

                    if line:
                        try:
                            # Parse SSE data
                            if line.startswith(b'data: '):
                                data = json.loads(line[6:])
                                if 'choices' in data:
                                    text = data['choices'][0].get('text', '')
                                    token_count += len(text.split())
                        except json.JSONDecodeError:
                            pass

                end_time = time.perf_counter()
                total_time = end_time - start_time
                ttft = (first_token_time - start_time) * 1000 if first_token_time else 0

                # Measure CPU after request
                cpu_after = psutil.cpu_percent(interval=None)
                cpu_usage = (cpu_before + cpu_after) / 2

                tps = token_count / total_time if total_time > 0 else 0

                result = BenchmarkResult(
                    iteration=i + 1,
                    tokens=token_count,
                    time_sec=total_time,
                    tokens_per_sec=tps,
                    ttft_ms=ttft,
                    cpu_percent=cpu_usage
                )
                benchmark.results.append(result)

                print(f"    Iter {i+1}: {token_count} tokens, {tps:.2f} tok/s, TTFT {ttft:.1f}ms")

            except Exception as e:
                print(f"    Iter {i+1}: ERROR - {e}")
                benchmark.results.append(BenchmarkResult(
                    iteration=i + 1,
                    tokens=0,
                    time_sec=0,
                    tokens_per_sec=0
                ))

        benchmark.calculate_aggregates()
        return benchmark

    def run_all(self, transports: List[str] = None) -> Dict[str, TransportBenchmark]:
        """
        Run benchmarks for all specified transports.

        Args:
            transports: List of transports to test (default: all available)

        Returns:
            Dictionary of transport name to benchmark results
        """
        if transports is None:
            transports = ['tcp', 'roce']  # Default, exclude ttpoe unless specified

        for transport in transports:
            print(f"\n{'='*60}")
            print(f"Benchmarking: {transport.upper()}")
            print('='*60)

            try:
                self.results[transport] = self.benchmark_vllm(transport)
            except Exception as e:
                print(f"  Failed: {e}")
                self.results[transport] = TransportBenchmark(
                    transport=transport,
                    model=self.model,
                    iterations=0
                )

        return self.results

    def save_results(self, output_dir: str) -> None:
        """
        Save results to JSON files.

        Args:
            output_dir: Output directory path
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save individual transport results
        for transport, benchmark in self.results.items():
            result_file = output_path / f"{transport}_results.json"
            with open(result_file, 'w') as f:
                json.dump(benchmark.to_dict(), f, indent=2)

        # Save summary
        summary = {
            'model': self.model,
            'iterations': self.iterations,
            'max_tokens': self.max_tokens,
            'timestamp': datetime.now().isoformat(),
            'results': {}
        }

        for transport, benchmark in self.results.items():
            benchmark.calculate_aggregates()
            summary['results'][transport] = {
                'avg_tokens_per_sec': benchmark.avg_tokens_per_sec,
                'std_tokens_per_sec': benchmark.std_tokens_per_sec,
                'avg_ttft_ms': benchmark.avg_ttft_ms,
                'avg_cpu_percent': benchmark.avg_cpu_percent,
            }

        summary_file = output_path / "summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\nResults saved to: {output_path}")

    def generate_latex(self, output_dir: str) -> str:
        """
        Generate LaTeX table of results.

        Args:
            output_dir: Output directory path

        Returns:
            LaTeX table string
        """
        # Transport display names and expected latencies
        display_names = {
            'tcp': ('TCP', r'$\sim$1ms'),
            'roce': ('Soft-RoCE', r'$\sim$190$\mu$s'),
            'ttpoe': ('TTPoe', r'$\sim$2$\mu$s'),
        }

        lines = [
            r'% Transport Benchmark Results',
            r'% Generated by ScuffedRDMA benchmark_transports.py',
            r'',
            r'\begin{table}[htbp]',
            r'\centering',
            r'\caption{Transport Performance Comparison for Distributed LLM Inference}',
            r'\label{tab:transport-benchmark}',
            r'\begin{tabular}{lcccc}',
            r'\toprule',
            r'\textbf{Transport} & \textbf{Tokens/s} & \textbf{Std Dev} & \textbf{TTFT (ms)} & \textbf{CPU \%} \\',
            r'\midrule',
        ]

        tcp_tps = self.results.get('tcp', TransportBenchmark('tcp', self.model, 0)).avg_tokens_per_sec

        for transport in ['tcp', 'roce', 'ttpoe']:
            if transport not in self.results:
                continue

            benchmark = self.results[transport]
            benchmark.calculate_aggregates()

            name, _ = display_names.get(transport, (transport.upper(), ''))

            # Calculate improvement vs TCP
            if transport != 'tcp' and tcp_tps > 0:
                improvement = ((benchmark.avg_tokens_per_sec - tcp_tps) / tcp_tps) * 100
                tps_str = f"{benchmark.avg_tokens_per_sec:.1f} (+{improvement:.1f}\\%)"
            else:
                tps_str = f"{benchmark.avg_tokens_per_sec:.1f}"

            line = f"{name} & {tps_str} & {benchmark.std_tokens_per_sec:.2f} & {benchmark.avg_ttft_ms:.1f} & {benchmark.avg_cpu_percent:.1f} \\\\"
            lines.append(line)

        lines.extend([
            r'\bottomrule',
            r'\end{tabular}',
            r'\end{table}',
        ])

        latex_content = '\n'.join(lines)

        # Save to file
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        latex_file = output_path / "results.tex"
        with open(latex_file, 'w') as f:
            f.write(latex_content)

        print(f"LaTeX table saved to: {latex_file}")
        return latex_content

    def print_summary(self) -> None:
        """Print summary of benchmark results."""
        print("\n" + "="*60)
        print("BENCHMARK SUMMARY")
        print("="*60)
        print(f"Model: {self.model}")
        print(f"Iterations: {self.iterations}")
        print(f"Max Tokens: {self.max_tokens}")
        print("-"*60)

        tcp_tps = 0.0
        for transport, benchmark in sorted(self.results.items()):
            benchmark.calculate_aggregates()

            if transport == 'tcp':
                tcp_tps = benchmark.avg_tokens_per_sec

            improvement = ""
            if transport != 'tcp' and tcp_tps > 0 and benchmark.avg_tokens_per_sec > 0:
                pct = ((benchmark.avg_tokens_per_sec - tcp_tps) / tcp_tps) * 100
                improvement = f" (+{pct:.1f}% vs TCP)"

            print(f"{transport.upper():10} {benchmark.avg_tokens_per_sec:>8.2f} tok/s{improvement}")

        print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description="ScuffedRDMA Transport Benchmark Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument('--transport', '-t', default='all',
                       help='Transport to benchmark (tcp, roce, ttpoe, all)')
    parser.add_argument('--model', '-m',
                       default=os.environ.get('MODEL', 'meta-llama/Llama-4-Scout-17B-16E'),
                       help='Model name for vLLM testing')
    parser.add_argument('--iterations', '-n', type=int, default=5,
                       help='Number of benchmark iterations')
    parser.add_argument('--max-tokens', type=int, default=100,
                       help='Max tokens per request')
    parser.add_argument('--output', '-o',
                       default=None,
                       help='Output directory for results')
    parser.add_argument('--vllm-url',
                       default=os.environ.get('VLLM_URL', 'http://localhost:8000/v1'),
                       help='vLLM API endpoint')
    parser.add_argument('--latex', action='store_true',
                       help='Generate LaTeX table')

    args = parser.parse_args()

    # Determine output directory
    if args.output is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.output = f"results/benchmark_{timestamp}"

    # Determine transports to test
    if args.transport == 'all':
        transports = ['tcp', 'roce']  # Exclude ttpoe by default
    else:
        transports = [t.strip() for t in args.transport.split(',')]

    # Run benchmarks
    benchmarker = TransportBenchmarker(
        model=args.model,
        vllm_url=args.vllm_url,
        iterations=args.iterations,
        max_tokens=args.max_tokens
    )

    benchmarker.run_all(transports)
    benchmarker.print_summary()
    benchmarker.save_results(args.output)

    if args.latex:
        benchmarker.generate_latex(args.output)


if __name__ == '__main__':
    main()
