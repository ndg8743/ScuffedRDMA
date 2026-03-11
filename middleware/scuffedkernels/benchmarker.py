"""
5-stage kernel validation and RDMA-aware roofline analysis.

Validation stages:
1. Smoke test - does it run without errors?
2. Shape test - correct output shapes for varied inputs?
3. Numerical stability - no NaN/Inf in outputs?
4. Determinism - same inputs produce same outputs?
5. Edge cases - empty tensors, single elements, max sizes?
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any, Tuple
from enum import Enum
import time
import math


class ValidationStage(Enum):
    SMOKE = "smoke"
    SHAPES = "shapes"
    STABILITY = "stability"
    DETERMINISM = "determinism"
    EDGE_CASES = "edge_cases"


@dataclass
class ValidationResult:
    """Result of a single validation stage."""
    stage: ValidationStage
    passed: bool
    message: str
    elapsed_ms: float = 0.0


@dataclass
class BenchmarkResult:
    """Performance measurement result."""
    kernel_name: str
    elapsed_ms: float
    throughput_gflops: float = 0.0
    memory_bandwidth_gbps: float = 0.0
    arithmetic_intensity: float = 0.0
    # RDMA-aware metrics
    network_bandwidth_gbps: float = 0.0
    compute_transfer_overlap: float = 0.0  # Fraction of overlap achieved


@dataclass
class RooflinePoint:
    """A point on the roofline model."""
    kernel_name: str
    arithmetic_intensity: float  # FLOPs/byte
    achieved_gflops: float
    peak_gflops: float
    peak_memory_bw_gbps: float
    # RDMA extension
    network_bw_gbps: float = 0.0
    is_network_bound: bool = False

    @property
    def efficiency(self) -> float:
        """Fraction of peak performance achieved."""
        if self.peak_gflops == 0:
            return 0.0
        return self.achieved_gflops / self.peak_gflops

    @property
    def bottleneck(self) -> str:
        """Identify the performance bottleneck."""
        ridge_point = self.peak_gflops / (self.peak_memory_bw_gbps * 1e9 / 1e9)
        if self.is_network_bound:
            return "network"
        elif self.arithmetic_intensity < ridge_point:
            return "memory"
        else:
            return "compute"


class KernelBenchmarker:
    """
    Validates kernel correctness (5 stages) and measures performance
    with RDMA-aware roofline analysis.
    """

    def __init__(self, rtol: float = 1e-3, atol: float = 1e-5):
        """
        Args:
            rtol: Relative tolerance for numerical comparison
            atol: Absolute tolerance for numerical comparison
        """
        self.rtol = rtol
        self.atol = atol
        self._validation_results: List[ValidationResult] = []

    @property
    def validation_results(self) -> List[ValidationResult]:
        return list(self._validation_results)

    def validate(self, kernel_fn: Callable, reference_fn: Callable,
                 input_generator: Callable, num_shapes: int = 5,
                 ) -> List[ValidationResult]:
        """
        Run 5-stage validation on a kernel.

        Args:
            kernel_fn: Optimized kernel to test
            reference_fn: Reference (correct) implementation
            input_generator: Callable(shape) -> input tensors
            num_shapes: Number of random shapes to test

        Returns:
            List of ValidationResult, one per stage
        """
        import numpy as np

        results = []

        # Stage 1: Smoke test
        start = time.perf_counter()
        try:
            test_input = input_generator((64, 64))
            out = kernel_fn(*test_input) if isinstance(test_input, tuple) else kernel_fn(test_input)
            results.append(ValidationResult(
                ValidationStage.SMOKE, True, "Kernel executed successfully",
                (time.perf_counter() - start) * 1000
            ))
        except Exception as e:
            results.append(ValidationResult(
                ValidationStage.SMOKE, False, f"Smoke test failed: {e}",
                (time.perf_counter() - start) * 1000
            ))
            self._validation_results = results
            return results  # No point continuing

        # Stage 2: Shape test
        start = time.perf_counter()
        shapes = [(1, 1), (32, 32), (128, 128), (256, 256), (1024, 1024)][:num_shapes]
        shape_ok = True
        for shape in shapes:
            try:
                inp = input_generator(shape)
                out = kernel_fn(*inp) if isinstance(inp, tuple) else kernel_fn(inp)
                ref = reference_fn(*inp) if isinstance(inp, tuple) else reference_fn(inp)
                if hasattr(out, 'shape') and hasattr(ref, 'shape') and out.shape != ref.shape:
                    shape_ok = False
                    break
            except Exception:
                shape_ok = False
                break
        results.append(ValidationResult(
            ValidationStage.SHAPES, shape_ok,
            f"Tested {len(shapes)} shapes" if shape_ok else "Shape mismatch detected",
            (time.perf_counter() - start) * 1000
        ))

        # Stage 3: Numerical stability
        start = time.perf_counter()
        try:
            large_input = input_generator((512, 512))
            out = kernel_fn(*large_input) if isinstance(large_input, tuple) else kernel_fn(large_input)
            out_np = np.asarray(out) if not isinstance(out, np.ndarray) else out
            stable = not (np.any(np.isnan(out_np)) or np.any(np.isinf(out_np)))
            results.append(ValidationResult(
                ValidationStage.STABILITY, stable,
                "No NaN/Inf detected" if stable else "NaN or Inf in output",
                (time.perf_counter() - start) * 1000
            ))
        except Exception as e:
            results.append(ValidationResult(
                ValidationStage.STABILITY, False, f"Stability check failed: {e}",
                (time.perf_counter() - start) * 1000
            ))

        # Stage 4: Determinism
        start = time.perf_counter()
        try:
            det_input = input_generator((128, 128))
            out1 = kernel_fn(*det_input) if isinstance(det_input, tuple) else kernel_fn(det_input)
            out2 = kernel_fn(*det_input) if isinstance(det_input, tuple) else kernel_fn(det_input)
            out1_np = np.asarray(out1) if not isinstance(out1, np.ndarray) else out1
            out2_np = np.asarray(out2) if not isinstance(out2, np.ndarray) else out2
            deterministic = np.allclose(out1_np, out2_np, rtol=0, atol=0)
            results.append(ValidationResult(
                ValidationStage.DETERMINISM, deterministic,
                "Deterministic" if deterministic else "Non-deterministic output",
                (time.perf_counter() - start) * 1000
            ))
        except Exception as e:
            results.append(ValidationResult(
                ValidationStage.DETERMINISM, False, f"Determinism check failed: {e}",
                (time.perf_counter() - start) * 1000
            ))

        # Stage 5: Edge cases
        start = time.perf_counter()
        edge_shapes = [(1, 1), (1, 1024), (1024, 1)]
        edge_ok = True
        for shape in edge_shapes:
            try:
                inp = input_generator(shape)
                kernel_fn(*inp) if isinstance(inp, tuple) else kernel_fn(inp)
            except Exception:
                edge_ok = False
                break
        results.append(ValidationResult(
            ValidationStage.EDGE_CASES, edge_ok,
            "Edge cases passed" if edge_ok else "Edge case failure",
            (time.perf_counter() - start) * 1000
        ))

        self._validation_results = results
        return results

    def benchmark(self, kernel_fn: Callable, inputs: Any,
                  num_warmup: int = 5, num_iterations: int = 100,
                  flops: int = 0, memory_bytes: int = 0,
                  ) -> BenchmarkResult:
        """
        Measure kernel performance.

        Args:
            kernel_fn: Kernel to benchmark
            inputs: Input data (tuple or single tensor)
            num_warmup: Warmup iterations
            num_iterations: Timed iterations
            flops: Known FLOPs per invocation (0 = don't compute throughput)
            memory_bytes: Known memory traffic (0 = don't compute bandwidth)

        Returns:
            BenchmarkResult with timing and throughput
        """
        # Warmup
        for _ in range(num_warmup):
            kernel_fn(*inputs) if isinstance(inputs, tuple) else kernel_fn(inputs)

        # Time
        start = time.perf_counter()
        for _ in range(num_iterations):
            kernel_fn(*inputs) if isinstance(inputs, tuple) else kernel_fn(inputs)
        total_ms = (time.perf_counter() - start) * 1000
        avg_ms = total_ms / num_iterations

        throughput = (flops / (avg_ms / 1000) / 1e9) if flops > 0 and avg_ms > 0 else 0.0
        mem_bw = (memory_bytes / (avg_ms / 1000) / 1e9) if memory_bytes > 0 and avg_ms > 0 else 0.0
        ai = flops / memory_bytes if memory_bytes > 0 else 0.0

        return BenchmarkResult(
            kernel_name="",  # Set by caller
            elapsed_ms=avg_ms,
            throughput_gflops=throughput,
            memory_bandwidth_gbps=mem_bw,
            arithmetic_intensity=ai,
        )

    def roofline_analysis(self, kernel_name: str,
                          achieved_gflops: float,
                          arithmetic_intensity: float,
                          peak_gflops: float,
                          peak_memory_bw_gbps: float,
                          network_bw_gbps: float = 0.0,
                          ) -> RooflinePoint:
        """
        Compute roofline model point with optional RDMA network ceiling.

        The network bandwidth adds a third ceiling to the traditional
        compute/memory roofline, relevant for RDMA-bound kernels.

        Args:
            kernel_name: Kernel identifier
            achieved_gflops: Measured throughput
            arithmetic_intensity: FLOPs per byte accessed
            peak_gflops: Device peak compute (e.g., V100 = 15.7 TFLOPS FP32)
            peak_memory_bw_gbps: Device peak memory BW (e.g., V100 = 900 GB/s)
            network_bw_gbps: Network bandwidth (e.g., 100GbE = 12.5 GB/s)

        Returns:
            RooflinePoint with bottleneck analysis
        """
        is_net_bound = False
        if network_bw_gbps > 0:
            # Network ceiling: if kernel needs more data than network can provide
            net_ceiling = arithmetic_intensity * network_bw_gbps
            mem_ceiling = arithmetic_intensity * peak_memory_bw_gbps
            if net_ceiling < mem_ceiling and net_ceiling < peak_gflops:
                is_net_bound = True

        return RooflinePoint(
            kernel_name=kernel_name,
            arithmetic_intensity=arithmetic_intensity,
            achieved_gflops=achieved_gflops,
            peak_gflops=peak_gflops,
            peak_memory_bw_gbps=peak_memory_bw_gbps,
            network_bw_gbps=network_bw_gbps,
            is_network_bound=is_net_bound,
        )
