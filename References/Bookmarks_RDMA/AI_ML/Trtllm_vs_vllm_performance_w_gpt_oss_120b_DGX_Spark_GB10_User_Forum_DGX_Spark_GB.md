# Trtllm vs vllm performance /w gpt-oss-120b - DGX Spark / GB10 User Forum / DGX Spark / GB10 - NVIDIA Developer Forums

- **Source:** https://forums.developer.nvidia.com/t/trtllm-vs-vllm-performance-w-gpt-oss-120b/357885
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

I am doing some testing with aiperf between trtllm and vllm and seeing some significant differences in token throughput: \~ 109 tps with vLLM and \~ 30 tps with trtllm. Wanted to see if I am missing anything in my trtllm config  or is trtllm missing some GB10 optimizations that vLLM has?

Tested with trtllm 1.0.8rc6 and 1.0.8rc8. rc8 occasionally shows a CUDA invalid instruction, so I fail back to rc6. I’ve tried the configurations in the trtllm DGX Spark playbook, but it doesn’t make a difference.

docker run --rm --gpus all -e TIKTOKEN\_ENCODINGS\_BASE=/tmp/tiktoken\_encodings -v ./tiktoken\_encodings:/tmp/tiktoken\_encodings --ipc=host --network host --ulimit memlock=-1 --ulimit stack=67108864 -v \~/.cache/huggingface:/root/.cache/huggingface -p 8000:8000 [nvcr.io/nvidia/tensorrt-llm/release:1.2.0rc8](http://nvcr.io/nvidia/tensorrt-llm/release:1.2.0rc8) trtllm-serve serve openai/gpt-oss-120b --port 8000 --backend pytorch --max\_seq\_len 131072 --max\_batch\_size 16 --free\_gpu\_memory\_fraction 0.7 --trust\_remote\_code

Tested with vLLM 0.13.0 using the official vLLM 0.13.0 wheel mentioned on this forum.

            
          
          
            
            
              TRT-LLM is not on par with vLLM on the spark right now. Latest numbers for GPT-OSS-120B and others [Spark Arena - LLM Leaderboard](https://spark-arena.com/leaderboard)