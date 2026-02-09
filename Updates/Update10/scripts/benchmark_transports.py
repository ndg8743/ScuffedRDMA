"""Transport benchmarker for comparing all backends."""
import time
import requests


class TransportBenchmarker:
    def benchmark_vllm(self, transport: str):
        benchmark = TransportBenchmark(transport=transport)

        for i in range(self.iterations):
            start = time.perf_counter()
            response = requests.post(
                f"{self.vllm_url}/completions",
                json={"model": self.model, "prompt": prompt})
            duration = time.perf_counter() - start

            benchmark.results.append(BenchmarkResult(
                tokens=response.json()['usage']['completion_tokens'],
                time_sec=duration,
                tokens_per_sec=tokens / duration
            ))

        return benchmark

    def generate_latex(self, output_dir: str) -> str:
        """Generate LaTeX table from results."""
        ...
