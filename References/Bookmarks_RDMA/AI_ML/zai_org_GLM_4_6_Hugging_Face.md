# zai-org/GLM-4.6 · Hugging Face

- **Source:** https://huggingface.co/zai-org/GLM-4.6
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

[2 items • Updated  •  54](/collections/zai-org/glm-46)

### Instructions to use zai-org/GLM-4.6 with libraries, inference providers, notebooks, and local apps. Follow these links to get started.

- Libraries
-  [Transformers](/zai-org/GLM-4.6?library=transformers) How to use zai-org/GLM-4.6 with Transformers: ```
# Use a pipeline as a high-level helper
from transformers import pipeline
pipe = pipeline("text-generation", model="zai-org/GLM-4.6")
messages = [
    {"role": "user", "content": "Who are you?"},
]
pipe(messages)
```
```
# pip install -U transformers accelerate
# Load model directly
from transformers import AutoTokenizer, AutoModelForCausalLM
tokenizer = AutoTokenizer.from_pretrained("zai-org/GLM-4.6")
model = AutoModelForCausalLM.from_pretrained("zai-org/GLM-4.6", device_map="auto")
messages = [
    {"role": "user", "content": "Who are you?"},
]
inputs = tokenizer.apply_chat_template(
	messages,
	add_generation_prompt=True,
	tokenize=True,
	return_dict=True,
	return_tensors="pt",
).to(model.device)
outputs = model.generate(**inputs, max_new_tokens=256)
print(tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:]))
```
- Inference
-  [HuggingChat](/chat/models/zai-org/GLM-4.6)
- Notebooks
-  [Google Colab](/zai-org/GLM-4.6/colab)
-  [Kaggle](/zai-org/GLM-4.6/kaggle)
- Local Apps [Settings](/settings/local-apps)
-  [vLLM](/zai-org/GLM-4.6?local-app=vllm) How to use zai-org/GLM-4.6 with vLLM: ##### Install from pip and serve model```
# Install vLLM from pip:
pip install vllm
# Start the vLLM server:
vllm serve "zai-org/GLM-4.6"
# Call the server using curl (OpenAI-compatible API):
curl -X POST "http://localhost:8000/v1/chat/completions" \
	-H "Content-Type: application/json" \
	--data '{
		"model": "zai-org/GLM-4.6",
		"messages": [
			{
				"role": "user",
				"content": "What is the capital of France?"
			}
		]
	}'
```
##### Use Docker docker model run hf.co/zai-org/GLM-4.6
-  [SGLang](/zai-org/GLM-4.6?local-app=sglang) How to use zai-org/GLM-4.6 with SGLang: ##### Install from pip and serve model```
# Install SGLang from pip:
pip install sglang
# Start the SGLang server:
python3 -m sglang.launch_server \
    --model-path "zai-org/GLM-4.6" \
    --host 0.0.0.0 \
    --port 30000
# Call the server using curl (OpenAI-compatible API):
curl -X POST "http://localhost:30000/v1/chat/completions" \
	-H "Content-Type: application/json" \
	--data '{
		"model": "zai-org/GLM-4.6",
		"messages": [
			{
				"role": "user",
				"content": "What is the capital of France?"
			}
		]
	}'
```
##### Use Docker images```
docker run --gpus all \
    --shm-size 32g \
    -p 30000:30000 \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    --env "HF_TOKEN=<secret>" \
    --ipc=host \
    lmsysorg/sglang:latest \
    python3 -m sglang.launch_server \
        --model-path "zai-org/GLM-4.6" \
        --host 0.0.0.0 \
        --port 30000
# Call the server using curl (OpenAI-compatible API):
curl -X POST "http://localhost:30000/v1/chat/completions" \
	-H "Content-Type: application/json" \
	--data '{
		"model": "zai-org/GLM-4.6",
		"messages": [
			{
				"role": "user",
				"content": "What is the capital of France?"
			}
		]
	}'
```
-  [Docker Model Runner](/zai-org/GLM-4.6?local-app=docker-model-runner) How to use zai-org/GLM-4.6 with Docker Model Runner: docker model run hf.co/zai-org/GLM-4.6

# 
		
	
	
		GLM-4.6

👋 Join our [Discord](https://discord.gg/QR7SARHRxK) community.
    

📖 Check out the GLM-4.6 [technical blog](https://z.ai/blog/glm-4.6), [technical report(GLM-4.5)](https://arxiv.org/abs/2508.06471), and [Zhipu AI technical documentation](https://zhipu-ai.feishu.cn/wiki/Gv3swM0Yci7w7Zke9E0crhU7n7D).
    

📍 Use GLM-4.6 API services on [Z.ai API Platform.](https://docs.z.ai/guides/llm/glm-4.6) 
    

👉 One click to [GLM-4.6](https://chat.z.ai).

## 
		
	
	
		Model Introduction

Compared with GLM-4.5, **GLM-4.6**  brings several key improvements:

- **Longer context window:** The context window has been expanded from 128K to 200K tokens, enabling the model to handle more complex agentic tasks.
- **Superior coding performance:** The model achieves higher scores on code benchmarks and demonstrates better real-world performance in applications such as Claude Code、Cline、Roo Code and Kilo Code, including improvements in generating visually polished front-end pages.
- **Advanced reasoning:** GLM-4.6 shows a clear improvement in reasoning performance and supports tool use during inference, leading to stronger overall capability.
- **More capable agents:** GLM-4.6 exhibits stronger performance in tool using and search-based agents, and integrates more effectively within agent frameworks.
- **Refined writing:** Better aligns with human preferences in style and readability, and performs more naturally in role-playing scenarios.

We evaluated GLM-4.6 across eight public benchmarks covering agents, reasoning, and coding. Results show clear gains over GLM-4.5, with GLM-4.6 also holding competitive advantages over leading domestic and international models such as **DeepSeek-V3.1-Terminus** and **Claude Sonnet 4**.

## 
		
	
	
		Inference

**Both GLM-4.5 and GLM-4.6 use the same inference method.**

you can check our [github](https://github.com/zai-org/GLM-4.5) for more detail.

## 
		
	
	
		Recommended Evaluation Parameters

For general evaluations, we recommend using a **sampling temperature of 1.0**.

For **code-related evaluation tasks** (such as LCB), it is further recommended to set:

- `top_p = 0.95`
- `top_k = 40`

## 
		
	
	
		Evaluation

- Downloads last month
- 21,039

## Model tree for zai-org/GLM-4.6 

## Spaces using zai-org/GLM-4.6 100

## Collection including zai-org/GLM-4.6

## Paper for zai-org/GLM-4.6

   [Paper • 2508.06471 • Published  •  217](/papers/2508.06471) 

## Evaluation results 

- [ScaleAI/SWE-bench\_Pro](/datasets/ScaleAI/SWE-bench_Pro) · SWE Bench Pro [View evaluation results](/zai-org/GLM-4.6/discussions/34) [leaderboard](/datasets/ScaleAI/SWE-bench_Pro?eval_result=zai-org/GLM-4.6&leaderboard_task_id=SWE_Bench_Pro) 9.67
- [mercor/apex-agents](/datasets/mercor/apex-agents) · Apex Agents [View evaluation results](/zai-org/GLM-4.6/discussions/36) [leaderboard](/datasets/mercor/apex-agents?eval_result=zai-org/GLM-4.6&leaderboard_task_id=apex-agents) 4<sup>\*</sup>
- [harborframework/terminal-bench-2.0](/datasets/harborframework/terminal-bench-2.0) · Terminalbench 2 [View evaluation results](/zai-org/GLM-4.6/discussions/33) [leaderboard](/datasets/harborframework/terminal-bench-2.0?eval_result=zai-org/GLM-4.6&leaderboard_task_id=terminalbench_2) 24.5<sup>\*</sup>