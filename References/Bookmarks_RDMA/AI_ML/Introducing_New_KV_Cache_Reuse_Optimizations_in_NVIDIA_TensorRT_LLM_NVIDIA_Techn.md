# Introducing New KV Cache Reuse Optimizations in NVIDIA TensorRT-LLM | NVIDIA Technical Blog

- **Source:** https://developer.nvidia.com/blog/introducing-new-kv-cache-reuse-optimizations-in-nvidia-tensorrt-llm/
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

Language models generate text by predicting the next token, given all the previous tokens including the input text tokens. Key and value elements of the previous tokens are used as historical context in LLM serving for generation of the next set of tokens. Caching these key and value elements from previous tokens avoids expensive recomputation and effectively leads to higher throughput. However, key-value (KV) cache grows linearly with the size of the language model, number of batched requests, and sequence context lengths, leading to growing memory requirements.

[NVIDIA TensorRT-LLM](https://developer.nvidia.com/tensorrt#inference) provides several KV cache optimizations to manage the challenging balance between growing memory size and preventing expensive recomputation. TensorRT-LLM is an open-source library that provides state-of-the-art inference support for numerous popular [large language models (LLMs)](https://www.nvidia.com/en-us/glossary/large-language-models/) on NVIDIA GPUs. TensorRT-LLM KV caching includes several optimizations, such as support for [paged KV cache](https://github.com/NVIDIA/TensorRT-LLM/blob/b171e879563ff0ba4eb35b94cf0e59a471e13d80/docs/source/advanced/gpt-attention.md#paged-kv-cache), [quantized KV cache](https://github.com/NVIDIA/TensorRT-LLM/blob/b171e879563ff0ba4eb35b94cf0e59a471e13d80/docs/source/advanced/gpt-attention.md#int8fp8-kv-caches),  [circular buffer KV cache](https://github.com/NVIDIA/TensorRT-LLM/blob/b171e879563ff0ba4eb35b94cf0e59a471e13d80/docs/source/advanced/gpt-attention.md#sliding-window-attention-cyclic-rolling-buffer-kv-cache), and [KV cache reuse](https://github.com/NVIDIA/TensorRT-LLM/blob/b171e879563ff0ba4eb35b94cf0e59a471e13d80/docs/source/advanced/kv-cache-reuse.md).

In this post, we dive deeper into two new high-level features that have been introduced into TensorRT-LLM. These features enable more fine-grained control over the KV cache, and provide visibility into TensorRT-LLM KV cache for use in upstream applications like KV cache aware routing.

## Priority-based KV cache eviction

When an LLM request has completed, the KV cache blocks associated with these requests are stored. Given the bounded size of the KV cache, some cached blocks may need to be evicted to make room for new sequences. By default, eviction follows a least recently used (LRU) policy.

Priority-based eviction is a new feature of the TensorRT-LLM [Executor API](https://nvidia.github.io/TensorRT-LLM/advanced/executor.html) that enables users to influence how blocks are selected for eviction. Users can specify two attributes that guide block eviction: priority and duration. The priority value sets the relative retention priority (how important it is to retain that block in the cache), and the duration value sets how long this priority level should apply for.

```
struct TokenRangeRetentionConfig {
    # The beginning of this range
    start: int
    # The end of the range. Set to null to extend to end of sequence
    end: optional<int>   
    # The priority level assigned to the range. 0->100  
    priority: int
    # The duration this priority should apply for
    duration: optional<int> 
}
# Optional parameter to executor request
struct KvCacheRetentionConfig {
    # List of priority assignments in context
    ranges: list<TokenRangeRetentionConfig>
    # Priority assigned to decode tokens
    decode_priority: optional<int>
    # Duration the decode priority applies for
    decode_duration: optional<int> 
}
```
The priority based-eviction API enables an LLM deployer to use knowledge about their workload to improve reuse opportunities by persisting blocks that are likely to be reused. For example, the deployer may want blocks corresponding to a system prompt to stay in the cache as long as possible, or blocks that might be involved in a latency-critical request should persist with higher priority than others (Figure 1).

For each request, you can specify a priority and duration value for discrete ranges of tokens in the input context, along with a priority and duration for blocks allocated during the decode phase. The priority level of a range of tokens applies until the duration has passed after no period of reuse, or until the blocks corresponding to these ranges have been evicted.

When choosing blocks to be evicted, TensorRT-LLM considers the priority levels of tokens within the block. For example, a request with a 500- token system prompt can set the token range \[0, 500) to the maximum priority. This way, the cache blocks corresponding to these tokens will only be evicted if absolutely necessary. Alternatively, if you know that blocks will never be reused, you can set the blocks of this request to the lowest priority to ensure that they are evicted first, before other blocks.

This new implementation also biases toward blocks further from the root, which leads to a small performance improvement, even when not setting priority levels. Our internal benchmarks show priority-based eviction increasing cache hit rate by around 20% and varies based on the workload.

```
# Priority-based eviction usage examples
#Example 1: One-off request
KvCacheRetentionConfig(
    [TokenRangeRetentionConfig(start=0, end=null, priority=0)],
    decode_priority=0
)
#Example 2: High Priority system prompt
KvCacheRetentionConfig(
    [TokenRangeRetentionConfig(start=0, end=1000, priority=100)]
)
#Example 3: Retain context blocks for 30 seconds, and decode blocks for 10 seconds
KvCacheRetentionConfig(
    [TokenRangeRetentionConfig(start=0, end=null, priority=100, duration=30s)],
    decode_priority=100, decode_duration=10s)
```
## KV cache event API

In large-scale LLM-powered applications, deployers often provision multiple serving instances of a model to distribute incoming requests. This raises the question, which instance should process new requests? Requests are often routed to balance load to ensure efficient utilization and quick processing of any request. The size of the KV cache on any instance represents the capacity to grow and accept new work.

However, load-based routing may not be optimal. If a moderately loaded instance has already computed and cached the keys and values for a new request, routing the request to this instance might still be preferred to optimize for cache reuse. The KV cache event API enables request routing systems to track which instances have cached or evicted blocks, enabling more intelligent reuse and greater performance.

The TensorRT-LLM [Executor API](https://nvidia.github.io/TensorRT-LLM/advanced/executor.html) now exposes a means of tracking updates to the KV cache.

```
struct KVCacheEvent {
    event_id: long // Auto-incrementing event id
    data: variant<CreatedData, StoredData, RemovedData, UpdatedData>
}
struct StoredBlockData {
    blockHash: id // Unique identifier for the block.
    tokens: list<Token>
    loraId: id
    cacheLevel: int // The cache level of the block (0 or 1, primary or secondary)
    priority: int // The priority level of this block
}
struct StoredData {
    parentHash: optional<id> // The parent of the sequence of blocks that was stored.
    blocks: list<StoredBlockData> // The list of stored blocks
}
struct RemovedData {
    blockHashes: list<id> // The hashes of blocks that were removed
}
# Set the max size of the internal event buffer. Defaults to 0 (no events)
kv_cache_config = KvCacheConfig(event_buffer_max_size=16384)
executor_config = ExecutorConfig(kv_cache_config)
executor = Executor(executor_config)
# Get an event manager
eventManager = executor.getKvCacheEventManager()
# Wait for new events. Once it returns, it implicitly clears the internal queue of events. Optionally provide a timeout value. If there's no events within this timeout, it returns an empty list.
events = eventManager.getLatestEvents()
```
When a cache block is stored for reuse, removed, or updated, an event is emitted. These events can be consumed in real time by an application to get an eventually consistent view of the current state of the TensorRT-LLM KV cache. This is especially useful for tracking KV cache reuse opportunities. It can be used on the scale of a single executor to anticipate which requests will have more reuse, or aggregated across many executors to make KV-aware routing and scheduling decisions (Figure 2).

With the introduction of priority-based eviction and event-aware routing for KV cache reuse and management, TensorRT-LLM provides you with levers that enable fine-grained control of the KV cache so you can use the knowledge of your workloads to optimize KV cache management.

## Summary

[NVIDIA TensorRT-LLM](https://nvidia.github.io/TensorRT-LLM/) provides several optimizations to efficiently deploy your generative AI applications across NVIDIA-accelerated infrastructure anywhere, including cloud, data center, and workstations. These optimizations lead to significant speedups and better cache reuse on the same hardware. This ultimately enables using fewer resources to serve the same workload, reducing energy costs, and improving total cost of ownership.