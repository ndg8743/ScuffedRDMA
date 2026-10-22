# mlx-community/GLM-4.5-Air-3bit · Hugging Face

- **Source:** https://huggingface.co/mlx-community/GLM-4.5-Air-3bit
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

### Instructions to use mlx-community/GLM-4.5-Air-3bit with libraries, inference providers, notebooks, and local apps. Follow these links to get started.

- Libraries
-  [MLX](/mlx-community/GLM-4.5-Air-3bit?library=mlx) How to use mlx-community/GLM-4.5-Air-3bit with MLX: ```
# Make sure mlx-lm is installed
# pip install --upgrade mlx-lm
# Generate text with mlx-lm
from mlx_lm import load, generate
model, tokenizer = load("mlx-community/GLM-4.5-Air-3bit")
prompt = "Write a story about Einstein"
messages = [{"role": "user", "content": prompt}]
prompt = tokenizer.apply_chat_template(
    messages, add_generation_prompt=True
)
text = generate(model, tokenizer, prompt=prompt, verbose=True)
```
- Notebooks
-  [Google Colab](/mlx-community/GLM-4.5-Air-3bit/colab)
-  [Kaggle](/mlx-community/GLM-4.5-Air-3bit/kaggle)
- Local Apps [Settings](/settings/local-apps)
-  [LM Studio](lmstudio://open_from_hf?model=mlx-community/GLM-4.5-Air-3bit) 
-  [Pi](/mlx-community/GLM-4.5-Air-3bit?local-app=pi) How to use mlx-community/GLM-4.5-Air-3bit with Pi: ##### Start the MLX server \# Install MLX LM: uv tool install mlx-lm # Start a local OpenAI-compatible server: mlx\_lm.server --model "mlx-community/GLM-4.5-Air-3bit" ##### Configure the model in Pi```
# Install Pi:
npm install -g @earendil-works/pi-coding-agent
# Add to ~/.pi/agent/models.json:
{
  "providers": {
    "mlx-lm": {
      "baseUrl": "http://localhost:8080/v1",
      "api": "openai-completions",
      "apiKey": "none",
      "models": [
        {
          "id": "mlx-community/GLM-4.5-Air-3bit"
        }
      ]
    }
  }
}
```
##### Run Pi \# Start Pi in your project directory: pi
-  [MLX LM](/mlx-community/GLM-4.5-Air-3bit?local-app=mlx-lm) How to use mlx-community/GLM-4.5-Air-3bit with MLX LM: ##### Generate or start a chat session \# Install MLX LM uv tool install mlx-lm # Interactive chat REPL mlx\_lm.chat --model "mlx-community/GLM-4.5-Air-3bit" ##### Run an OpenAI-compatible server```
# Install MLX LM
uv tool install mlx-lm
# Start the server
mlx_lm.server --model "mlx-community/GLM-4.5-Air-3bit"
# Calling the OpenAI-compatible server with curl
curl -X POST "http://localhost:8000/v1/chat/completions" \
   -H "Content-Type: application/json" \
   --data '{
     "model": "mlx-community/GLM-4.5-Air-3bit",
     "messages": [
       {"role": "user", "content": "Hello"}
     ]
   }'
```
-  [Hermes Agent](/mlx-community/GLM-4.5-Air-3bit?local-app=hermes-agent) How to use mlx-community/GLM-4.5-Air-3bit with Hermes Agent: ##### Start the MLX server \# Install MLX LM: uv tool install mlx-lm # Start a local OpenAI-compatible server: mlx\_lm.server --model "mlx-community/GLM-4.5-Air-3bit" ##### Configure Hermes \# Install Hermes: curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash hermes setup # Point Hermes at the local server: hermes config set model.provider custom hermes config set model.base\_url http://127.0.0.1:8080/v1 hermes config set model.default mlx-community/GLM-4.5-Air-3bit ##### Run Hermes hermes
-  [Atomic Chat](atomic-chat://models/huggingface/mlx-community/GLM-4.5-Air-3bit) 
-  [OpenClaw](/mlx-community/GLM-4.5-Air-3bit?local-app=openclaw) How to use mlx-community/GLM-4.5-Air-3bit with OpenClaw: ##### Start the MLX server \# Install MLX LM: uv tool install mlx-lm # Start a local OpenAI-compatible server: mlx\_lm.server --model "mlx-community/GLM-4.5-Air-3bit" ##### Configure OpenClaw \# Install OpenClaw: npm install -g openclaw@latest # Register the local server and set it as the default model: openclaw onboard --non-interactive --mode local \ --auth-choice custom-api-key \ --custom-base-url http://127.0.0.1:8080/v1 \ --custom-model-id "mlx-community/GLM-4.5-Air-3bit" \ --custom-provider-id mlx-lm \ --custom-compatibility openai \ --custom-text-input \ --accept-risk \ --skip-health ##### Run OpenClaw openclaw agent --local --agent main --message "Hello from Hugging Face"

# 
		
	
	
		mlx-community/GLM-4.5-Air-3bit

This model [mlx-community/GLM-4.5-Air-3bit](https://huggingface.co/mlx-community/GLM-4.5-Air-3bit) was
converted to MLX format from [zai-org/GLM-4.5-Air](https://huggingface.co/zai-org/GLM-4.5-Air)
using mlx-lm version **0.26.1**.

## 
		
	
	
		Use with mlx

```
pip install mlx-lm
```
```
from mlx_lm import load, generate
model, tokenizer = load("mlx-community/GLM-4.5-Air-3bit")
prompt = "hello"
if tokenizer.chat_template is not None:
    messages = [{"role": "user", "content": prompt}]
    prompt = tokenizer.apply_chat_template(
        messages, add_generation_prompt=True
    )
response = generate(model, tokenizer, prompt=prompt, verbose=True)
```
- Downloads last month
- 506

Model size

107B params

Tensor type

U32 ·BF16 ·F32 ·

Hardware compatibility

[Log In](/login)to add your hardware

3-bit

## Model tree for mlx-community/GLM-4.5-Air-3bit 

Base model

[zai-org/GLM-4.5-Air](/zai-org/GLM-4.5-Air)