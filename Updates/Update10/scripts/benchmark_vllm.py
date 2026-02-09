"""vLLM gpt-oss-120b benchmark script."""
from openai import OpenAI
import time

client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")

for i in range(5):
    start = time.perf_counter()
    response = client.completions.create(
        model="openai/gpt-oss-120b",
        prompt="Explain RDMA networking in 100 words.",
        max_tokens=100
    )
    elapsed = time.perf_counter() - start
    tokens = response.usage.completion_tokens
    print(f"Iteration {i+1}: {tokens} tokens in {elapsed:.3f}s "
          f"= {tokens/elapsed:.2f} tok/s")
