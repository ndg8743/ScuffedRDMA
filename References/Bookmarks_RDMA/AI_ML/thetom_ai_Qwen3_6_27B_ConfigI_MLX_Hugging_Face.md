# thetom-ai/Qwen3.6-27B-ConfigI-MLX · Hugging Face

- **Source:** https://huggingface.co/thetom-ai/Qwen3.6-27B-ConfigI-MLX
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

### Instructions to use thetom-ai/Qwen3.6-27B-ConfigI-MLX with libraries, inference providers, notebooks, and local apps. Follow these links to get started.

- Libraries
-  [MLX](/thetom-ai/Qwen3.6-27B-ConfigI-MLX?library=mlx) How to use thetom-ai/Qwen3.6-27B-ConfigI-MLX with MLX: ```
# Make sure mlx-lm is installed
# pip install --upgrade mlx-lm
# Generate text with mlx-lm
from mlx_lm import load, generate
model, tokenizer = load("thetom-ai/Qwen3.6-27B-ConfigI-MLX")
prompt = "Write a story about Einstein"
messages = [{"role": "user", "content": prompt}]
prompt = tokenizer.apply_chat_template(
    messages, add_generation_prompt=True
)
text = generate(model, tokenizer, prompt=prompt, verbose=True)
```
- Notebooks
-  [Google Colab](/thetom-ai/Qwen3.6-27B-ConfigI-MLX/colab)
-  [Kaggle](/thetom-ai/Qwen3.6-27B-ConfigI-MLX/kaggle)
- Local Apps [Settings](/settings/local-apps)
-  [LM Studio](lmstudio://open_from_hf?model=thetom-ai/Qwen3.6-27B-ConfigI-MLX) 
-  [Pi](/thetom-ai/Qwen3.6-27B-ConfigI-MLX?local-app=pi) How to use thetom-ai/Qwen3.6-27B-ConfigI-MLX with Pi: ##### Start the MLX server \# Install MLX LM: uv tool install mlx-lm # Start a local OpenAI-compatible server: mlx\_lm.server --model "thetom-ai/Qwen3.6-27B-ConfigI-MLX" ##### Configure the model in Pi```
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
          "id": "thetom-ai/Qwen3.6-27B-ConfigI-MLX"
        }
      ]
    }
  }
}
```
##### Run Pi \# Start Pi in your project directory: pi
-  [MLX LM](/thetom-ai/Qwen3.6-27B-ConfigI-MLX?local-app=mlx-lm) How to use thetom-ai/Qwen3.6-27B-ConfigI-MLX with MLX LM: ##### Generate or start a chat session \# Install MLX LM uv tool install mlx-lm # Interactive chat REPL mlx\_lm.chat --model "thetom-ai/Qwen3.6-27B-ConfigI-MLX" ##### Run an OpenAI-compatible server```
# Install MLX LM
uv tool install mlx-lm
# Start the server
mlx_lm.server --model "thetom-ai/Qwen3.6-27B-ConfigI-MLX"
# Calling the OpenAI-compatible server with curl
curl -X POST "http://localhost:8000/v1/chat/completions" \
   -H "Content-Type: application/json" \
   --data '{
     "model": "thetom-ai/Qwen3.6-27B-ConfigI-MLX",
     "messages": [
       {"role": "user", "content": "Hello"}
     ]
   }'
```
-  [Hermes Agent](/thetom-ai/Qwen3.6-27B-ConfigI-MLX?local-app=hermes-agent) How to use thetom-ai/Qwen3.6-27B-ConfigI-MLX with Hermes Agent: ##### Start the MLX server \# Install MLX LM: uv tool install mlx-lm # Start a local OpenAI-compatible server: mlx\_lm.server --model "thetom-ai/Qwen3.6-27B-ConfigI-MLX" ##### Configure Hermes \# Install Hermes: curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash hermes setup # Point Hermes at the local server: hermes config set model.provider custom hermes config set model.base\_url http://127.0.0.1:8080/v1 hermes config set model.default thetom-ai/Qwen3.6-27B-ConfigI-MLX ##### Run Hermes hermes
-  [Atomic Chat](atomic-chat://models/huggingface/thetom-ai/Qwen3.6-27B-ConfigI-MLX) 
-  [OpenClaw](/thetom-ai/Qwen3.6-27B-ConfigI-MLX?local-app=openclaw) How to use thetom-ai/Qwen3.6-27B-ConfigI-MLX with OpenClaw: ##### Start the MLX server \# Install MLX LM: uv tool install mlx-lm # Start a local OpenAI-compatible server: mlx\_lm.server --model "thetom-ai/Qwen3.6-27B-ConfigI-MLX" ##### Configure OpenClaw \# Install OpenClaw: npm install -g openclaw@latest # Register the local server and set it as the default model: openclaw onboard --non-interactive --mode local \ --auth-choice custom-api-key \ --custom-base-url http://127.0.0.1:8080/v1 \ --custom-model-id "thetom-ai/Qwen3.6-27B-ConfigI-MLX" \ --custom-provider-id mlx-lm \ --custom-compatibility openai \ --custom-text-input \ --accept-risk \ --skip-health ##### Run OpenClaw openclaw agent --local --agent main --message "Hello from Hugging Face"

# 
		
	
	
		Qwen3.6-27B - TurboQuant+ Config-I (MLX)

**27B-parameter dense model with Config-I mixed-precision quantization.** Standard MLX format - works with stock `mlx_lm` and `mlx-swift-lm`. No custom loaders required.

Config-I quantization of [Qwen/Qwen3.6-27B](https://huggingface.co/Qwen/Qwen3.6-27B) (27B dense, 64 layers, hybrid GatedDeltaNet + full attention). The policy applies 4-bit to middle layers, protects boundary layers at 8-bit, and shields embeddings at full precision. See the [Config-I paper](https://github.com/TheTom/turboquant_plus/blob/main/docs/papers/weight-compression-tq4.md) for the policy derivation.

## 
		
	
	
		Compression

| Size | Details | 
|---|---|
| bf16 source | \~54 GB | 
| **Config-I (mixed 4/8-bit)** | **\~20 GB** | 

Note: For dense models, Config-I's primary advantage over uniform 4-bit is quality preservation at boundary layers and embeddings, not size reduction. The aggressive 2-3 bit expert compression that drives size wins on MoE models does not apply here (no experts to compress).

## 
		
	
	
		Tested with vllm-swift


[**vllm-swift**](https://github.com/TheTom/vllm-swift) is a native Swift/Metal backend for vLLM. Install with Homebrew:

```
brew tap TheTom/tap && brew install vllm-swift
```
Or from source:

```
git clone https://github.com/TheTom/vllm-swift.git && cd vllm-swift
./scripts/install.sh      # builds Swift bridge, installs plugin, creates activate.sh
source activate.sh         # sets DYLD_LIBRARY_PATH (generated by install.sh)
```
Serve this model:

```
vllm-swift download thetom-ai/Qwen3.6-27B-ConfigI-MLX
vllm-swift serve ~/models/Qwen3.6-27B-ConfigI-MLX \
    --served-model-name qwen3.6-27b \
    --max-model-len 40960 \
    --enable-auto-tool-choice --tool-call-parser hermes \
    --additional-config '{"kv_scheme": "turbo4", "kv_bits": 4}'
```
This gives you an OpenAI-compatible API at `http://localhost:8000` with tool calling support and 3.2x KV cache compression.

### 
		
	
	
		Decode Speed (M5 Max 128GB)

| Backend | Decode | 
|---|---|
| **vllm-swift (Swift/Metal)** | **23.7 tok/s** | 
| mlx-lm (Python/MLX) | 19.8 tok/s | 

vllm-swift is **+20% faster** than Python mlx-lm on single-request decode.

### 
		
	
	
		KV Cache Compression (TurboQuant)

Measured at 4K context on M5 Max 128GB via vllm-swift:

| Scheme | Compression | PPL | Decode | PPL vs fp16 | Decode vs fp16 | 
|---|---|---|---|---|---|
| none (fp16) | 1.0x | 1.16 | 22.8 tok/s | — | — | 
| turbo4 (K4V4) | 3.2x | 1.29 | 20.8 tok/s | +11% | -9% | 
| turbo4v2 (K4V2) | 3.8x | 1.34 | 20.9 tok/s | +15% | -8% | 
| turbo3v2 (K3V2) | 4.6x | 1.43 | 20.8 tok/s | +23% | -9% | 
| turbo3 (K3V3) | 4.6x | 1.46 | 20.4 tok/s | +26% | -11% | 

**Recommendation:** turbo4 symmetric (K4V4). Best PPL (+11% vs fp16) with 3.2x compression and only -9% decode cost. All schemes are usable — even turbo3 at +26% PPL is still coherent (PPL 1.46 is low).

## 
		
	
	
		Config-I Policy (Qwen3.6 Dense Adaptation)

64 layers with hybrid attention (GatedDeltaNet + full attention at every 4th layer).

| Component | Bits | Layers | Rationale | 
|---|---|---|---|
| Attention Q/K/V/O | **4-bit** | middle 60 | Standard attention compression | 
| FFN gate/up | **4-bit** | middle 60 | Read projections | 
| FFN down | **4-bit** | middle 60 | Write-back projections | 
| GDN projections | **4-bit** | middle 60 | Linear attention layers | 
| Boundary (all tensors) | **8-bit** | first 2 + last 2 | Boundary layer protection | 
| Embeddings + lm\_head | **8-bit** | - | Protected | 

## 
		
	
	
		What is Config-I?

Config-I is a tensor-role-aware weight compression policy from TurboQuant+. Through systematic A/B isolation, it was discovered that attention tensors, FFN read projections (gate/up), FFN write-back projections (down), and boundary layers have dramatically different compression sensitivity. The key insight: **compression policy matters more than compression math** - which tensors to compress, which to protect, and how aggressively.

Config-I has been validated on MiniMax M2.7 (93.5% MMLU, PPL 4.604, 12/12 NIAH) and across Qwen/Phi model families at 27-38% size reduction with +1.0-3.9% PPL. See [MiniMax M2.7 Config-I results](https://huggingface.co/thetom-ai/MiniMax-M2.7-ConfigI-MLX) for a fully benchmarked reference.

## 
		
	
	
		Compatibility

| Field | Value | 
|---|---|
| Format | MLX safetensors (standard) | 
| Runtime | `mlx_lm` (Python), `mlx-swift-lm` (Swift), `vllm-swift` | 
| Platform | Apple Silicon (M-series with 32GB+) | 
| Quantized on | 2026-04-24 | 

**No custom loader needed.** This is standard MLX per-layer quantization. Any tool that reads MLX safetensors with `config.json` quantization metadata will work.

## 
		
	
	
		Links

- [vllm-swift](https://github.com/TheTom/vllm-swift) — Native Swift/Metal backend for vLLM
- [Config-I Paper](https://github.com/TheTom/turboquant_plus/blob/main/docs/papers/weight-compression-tq4.md)
- [Getting Started Guide](https://github.com/TheTom/turboquant_plus/blob/main/docs/getting-started.md)
- [TurboQuant+ Repository](https://github.com/TheTom/turboquant_plus)
- [MiniMax M2.7 Config-I (fully benchmarked)](https://huggingface.co/thetom-ai/MiniMax-M2.7-ConfigI-MLX)

Quantized by [@thetom-ai](https://huggingface.co/thetom-ai) | [GitHub](https://github.com/TheTom) | [X](https://x.com/no_stp_on_snek) | [Sponsor](https://github.com/sponsors/TheTom)

- Downloads last month
- 31

[Log In](/login)to add your hardware

4-bit

## Model tree for thetom-ai/Qwen3.6-27B-ConfigI-MLX 

Base model

[Qwen/Qwen3.6-27B](/Qwen/Qwen3.6-27B)