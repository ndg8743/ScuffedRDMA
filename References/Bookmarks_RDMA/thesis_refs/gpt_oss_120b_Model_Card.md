# gpt-oss-120b Model Card

- **Source:** https://huggingface.co/openai/gpt-oss-120b
- **Cited in:** REFERENCES.md [18]
- **Retrieved:** 2026-10-22

---

[Open-weight models designed for powerful reasoning, agentic tasks, and versatile developer use cases. • 2 items • Updated  •  483](/collections/openai/gpt-oss)

### Instructions to use openai/gpt-oss-120b with libraries, inference providers, notebooks, and local apps. Follow these links to get started.

- Libraries
-  [Transformers](/openai/gpt-oss-120b?library=transformers) How to use openai/gpt-oss-120b with Transformers: ```
# Use a pipeline as a high-level helper
from transformers import pipeline
pipe = pipeline("text-generation", model="openai/gpt-oss-120b")
messages = [
    {"role": "user", "content": "Who are you?"},
]
pipe(messages)
```
```
# pip install -U transformers accelerate
# Load model directly
from transformers import AutoTokenizer, AutoModelForCausalLM
tokenizer = AutoTokenizer.from_pretrained("openai/gpt-oss-120b")
model = AutoModelForCausalLM.from_pretrained("openai/gpt-oss-120b", device_map="auto")
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
-  [HuggingChat](/chat/models/openai/gpt-oss-120b)
- Notebooks
-  [Google Colab](/openai/gpt-oss-120b/colab)
-  [Kaggle](/openai/gpt-oss-120b/kaggle)
-  [AMD Developer Cloud](/openai/gpt-oss-120b/amd)
- Local Apps [Settings](/settings/local-apps)
-  [vLLM](/openai/gpt-oss-120b?local-app=vllm) How to use openai/gpt-oss-120b with vLLM: ##### Install from pip and serve model```
# Install vLLM from pip:
pip install vllm
# Start the vLLM server:
vllm serve "openai/gpt-oss-120b"
# Call the server using curl (OpenAI-compatible API):
curl -X POST "http://localhost:8000/v1/chat/completions" \
	-H "Content-Type: application/json" \
	--data '{
		"model": "openai/gpt-oss-120b",
		"messages": [
			{
				"role": "user",
				"content": "What is the capital of France?"
			}
		]
	}'
```
##### Use Docker docker model run hf.co/openai/gpt-oss-120b
-  [SGLang](/openai/gpt-oss-120b?local-app=sglang) How to use openai/gpt-oss-120b with SGLang: ##### Install from pip and serve model```
# Install SGLang from pip:
pip install sglang
# Start the SGLang server:
python3 -m sglang.launch_server \
    --model-path "openai/gpt-oss-120b" \
    --host 0.0.0.0 \
    --port 30000
# Call the server using curl (OpenAI-compatible API):
curl -X POST "http://localhost:30000/v1/chat/completions" \
	-H "Content-Type: application/json" \
	--data '{
		"model": "openai/gpt-oss-120b",
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
        --model-path "openai/gpt-oss-120b" \
        --host 0.0.0.0 \
        --port 30000
# Call the server using curl (OpenAI-compatible API):
curl -X POST "http://localhost:30000/v1/chat/completions" \
	-H "Content-Type: application/json" \
	--data '{
		"model": "openai/gpt-oss-120b",
		"messages": [
			{
				"role": "user",
				"content": "What is the capital of France?"
			}
		]
	}'
```
-  [Docker Model Runner](/openai/gpt-oss-120b?local-app=docker-model-runner) How to use openai/gpt-oss-120b with Docker Model Runner: docker model run hf.co/openai/gpt-oss-120b


[**Try gpt-oss**](https://gpt-oss.com) ·
  [**Guides**](https://cookbook.openai.com/topic/gpt-oss) ·
  [**Model card**](https://arxiv.org/abs/2508.10925) ·
  **OpenAI blog**

Welcome to the gpt-oss series, [OpenAI’s open-weight models](https://openai.com/open-models) designed for powerful reasoning, agentic tasks, and versatile developer use cases.

We’re releasing two flavors of these open models:

- `gpt-oss-120b` — for production, general purpose, high reasoning use cases that fit into a single 80GB GPU (like NVIDIA H100 or AMD MI300X) (117B parameters with 5.1B active parameters)
- `gpt-oss-20b` — for lower latency, and local or specialized use cases (21B parameters with 3.6B active parameters)

Both models were trained on our [harmony response format](https://github.com/openai/harmony) and should only be used with the harmony format as it will not work correctly otherwise.

This model card is dedicated to the larger `gpt-oss-120b` model. Check out [`gpt-oss-20b`](https://huggingface.co/openai/gpt-oss-20b) for the smaller model.


# 
		
	
	
		Highlights

- **Permissive Apache 2.0 license:** Build freely without copyleft restrictions or patent risk—ideal for experimentation, customization, and commercial deployment.
- **Configurable reasoning effort:** Easily adjust the reasoning effort (low, medium, high) based on your specific use case and latency needs.
- **Full chain-of-thought:** Gain complete access to the model’s reasoning process, facilitating easier debugging and increased trust in outputs. It’s not intended to be shown to end users.
- **Fine-tunable:** Fully customize models to your specific use case through parameter fine-tuning.
- **Agentic capabilities:** Use the models’ native capabilities for function calling, [web browsing](https://github.com/openai/gpt-oss/tree/main?tab=readme-ov-file#browser), [Python code execution](https://github.com/openai/gpt-oss/tree/main?tab=readme-ov-file#python), and Structured Outputs.
- **MXFP4 quantization:** The models were post-trained with MXFP4 quantization of the MoE weights, making `gpt-oss-120b` run on a single 80GB GPU (like NVIDIA H100 or AMD MI300X) and the `gpt-oss-20b` model run within 16GB of memory. All evals were performed with the same MXFP4 quantization.

# 
		
	
	
		Inference examples

## 
		
	
	
		Transformers

You can use `gpt-oss-120b` and `gpt-oss-20b` with Transformers. If you use the Transformers chat template, it will automatically apply the [harmony response format](https://github.com/openai/harmony). If you use `model.generate` directly, you need to apply the harmony format manually using the chat template or use our [openai-harmony](https://github.com/openai/harmony) package.

To get started, install the necessary dependencies to setup your environment:

```
pip install -U transformers kernels torch 
```
Once, setup you can proceed to run the model by running the snippet below:

```
from transformers import pipeline
import torch
model_id = "openai/gpt-oss-120b"
pipe = pipeline(
    "text-generation",
    model=model_id,
    torch_dtype="auto",
    device_map="auto",
)
messages = [
    {"role": "user", "content": "Explain quantum mechanics clearly and concisely."},
]
outputs = pipe(
    messages,
    max_new_tokens=256,
)
print(outputs[0]["generated_text"][-1])
```
Alternatively, you can run the model via [`Transformers Serve`](https://huggingface.co/docs/transformers/main/serving) to spin up a OpenAI-compatible webserver:

```
transformers serve
transformers chat localhost:8000 --model-name-or-path openai/gpt-oss-120b
```
[Learn more about how to use gpt-oss with Transformers.](https://cookbook.openai.com/articles/gpt-oss/run-transformers)

## 
		
	
	
		vLLM

vLLM recommends using [uv](https://docs.astral.sh/uv/) for Python dependency management. You can use vLLM to spin up an OpenAI-compatible webserver. The following command will automatically download the model and start the server.

```
uv pip install --pre vllm==0.10.1+gptoss \
    --extra-index-url https://wheels.vllm.ai/gpt-oss/ \
    --extra-index-url https://download.pytorch.org/whl/nightly/cu128 \
    --index-strategy unsafe-best-match
vllm serve openai/gpt-oss-120b
```
[Learn more about how to use gpt-oss with vLLM.](https://cookbook.openai.com/articles/gpt-oss/run-vllm)

## 
		
	
	
		PyTorch / Triton

To learn about how to use this model with PyTorch and Triton, check out our [reference implementations in the gpt-oss repository](https://github.com/openai/gpt-oss?tab=readme-ov-file#reference-pytorch-implementation).

## 
		
	
	
		Ollama

If you are trying to run gpt-oss on consumer hardware, you can use Ollama by running the following commands after [installing Ollama](https://ollama.com/download).

```
# gpt-oss-120b
ollama pull gpt-oss:120b
ollama run gpt-oss:120b
```
[Learn more about how to use gpt-oss with Ollama.](https://cookbook.openai.com/articles/gpt-oss/run-locally-ollama)

#### 
		
	
	
		LM Studio

If you are using [LM Studio](https://lmstudio.ai/) you can use the following commands to download.

```
# gpt-oss-120b
lms get openai/gpt-oss-120b
```
Check out our [awesome list](https://github.com/openai/gpt-oss/blob/main/awesome-gpt-oss.md) for a broader collection of gpt-oss resources and inference partners.

# 
		
	
	
		Download the model

You can download the model weights from the [Hugging Face Hub](https://huggingface.co/collections/openai/gpt-oss-68911959590a1634ba11c7a4) directly from Hugging Face CLI:

```
# gpt-oss-120b
huggingface-cli download openai/gpt-oss-120b --include "original/*" --local-dir gpt-oss-120b/
pip install gpt-oss
python -m gpt_oss.chat model/
```
# 
		
	
	
		Reasoning levels

You can adjust the reasoning level that suits your task across three levels:

- **Low:** Fast responses for general dialogue.
- **Medium:** Balanced speed and detail.
- **High:** Deep and detailed analysis.

The reasoning level can be set in the system prompts, e.g., "Reasoning: high".

# 
		
	
	
		Tool use

The gpt-oss models are excellent for:

- Web browsing (using built-in browsing tools)
- Function calling with defined schemas
- Agentic operations like browser tasks

# 
		
	
	
		Fine-tuning

Both gpt-oss models can be fine-tuned for a variety of specialized use cases.

This larger model `gpt-oss-120b` can be fine-tuned on a single H100 node, whereas the smaller [`gpt-oss-20b`](https://huggingface.co/openai/gpt-oss-20b) can even be fine-tuned on consumer hardware.

# 
		
	
	
		Citation

```
@misc{openai2025gptoss120bgptoss20bmodel,
      title={gpt-oss-120b & gpt-oss-20b Model Card}, 
      author={OpenAI},
      year={2025},
      eprint={2508.10925},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2508.10925}, 
}
```
- Downloads last month
- 2,964,075

## Model tree for openai/gpt-oss-120b 

## Spaces using openai/gpt-oss-120b 100

## Collection including openai/gpt-oss-120b

## Paper for openai/gpt-oss-120b

## Evaluation results 

- [Idavidrein/gpqa](/datasets/Idavidrein/gpqa) · Diamond [leaderboard](/datasets/Idavidrein/gpqa?eval_result=openai/gpt-oss-120b&leaderboard_task_id=diamond) 
- GPQA Diamond[View evaluation results](/openai/gpt-oss-120b/discussions/221) [source](https://huggingface.co/datasets/evaleval/EEE_datastore/blob/192329fb7d6b15b7b0936a1a58ae862aa7e8ba24/flat/objects/5d/3e/5d3e8832-c770-4796-957b-dfaefbd3bb2a.json) 80.81<sup>\*</sup>
- Reasoning: medium, With tools[View evaluation results](/openai/gpt-oss-120b/discussions/183) <sup>\*</sup>
- Reasoning: medium[View evaluation results](/openai/gpt-oss-120b/discussions/182) <sup>\*</sup>
- [ScaleAI/SWE-bench\_Pro](/datasets/ScaleAI/SWE-bench_Pro) · SWE Bench Pro [View evaluation results](/openai/gpt-oss-120b/discussions/177) [leaderboard](/datasets/ScaleAI/SWE-bench_Pro?eval_result=openai/gpt-oss-120b&leaderboard_task_id=SWE_Bench_Pro) 16.2
- [SWE-bench/SWE-bench\_Verified](/datasets/SWE-bench/SWE-bench_Verified) · Swe Bench Resolved [leaderboard](/datasets/SWE-bench/SWE-bench_Verified?eval_result=openai/gpt-oss-120b&leaderboard_task_id=swe_bench_%_resolved)