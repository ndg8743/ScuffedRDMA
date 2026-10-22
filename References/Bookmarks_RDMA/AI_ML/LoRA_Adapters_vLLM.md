# LoRA Adapters - vLLM

- **Source:** https://docs.vllm.ai/en/latest/features/lora/
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

# LoRA Adapters[¶](#lora-adapters)

This document shows you how to use [LoRA adapters](https://arxiv.org/abs/2106.09685) with vLLM on top of a base model.

LoRA adapters can be used with any vLLM model that implements [SupportsLoRA](../../api/vllm/model_executor/models/interfaces/#vllm.model_executor.models.interfaces.SupportsLoRA).

Adapters can be efficiently served on a per-request basis with minimal overhead. First we download the adapter(s) and save them locally with

Then we instantiate the base model and pass in the `enable_lora=True` flag:

We can now submit the prompts and call `llm.generate` with the `lora_request` parameter. The first parameter
of [`LoRARequest`](../../api/vllm/lora/request/#vllm.lora.request.LoRARequest) is a human identifiable name, the second parameter is a globally unique ID for the adapter and
the third parameter is the path to the LoRA adapter.

## Code

Check out  [examples/features/lora/multilora\_offline.py](https://github.com/vllm-project/vllm/blob/main/examples/features/lora/multilora_offline.py) for an example of how to use LoRA adapters with the async engine and how to use more advanced configuration options.

## Serving LoRA Adapters[¶](#serving-lora-adapters)

LoRA adapted models can also be served with the Open-AI compatible vLLM server. To do so, we use
`--lora-modules {name}={path} {name}={path}` to specify each LoRA module when we kick off the server:

The server entrypoint accepts all other LoRA configuration parameters (`max_loras`, `max_lora_rank`, `max_cpu_loras`,
etc.), which will apply to all forthcoming requests. Upon querying the `/models` endpoint, we should see our LoRA along
with its base model (if `jq` is not installed, you can follow [this guide](https://jqlang.org/download/) to install it.):

## Command

Requests can specify the LoRA adapter as if it were any other model via the `model` request parameter. The requests will be
processed according to the server-wide LoRA configuration (i.e. in parallel with base model requests, and potentially other
LoRA adapter requests if they were provided and `max_loras` is set high enough).

The following is an example request

## Dynamically serving LoRA Adapters[¶](#dynamically-serving-lora-adapters)

In addition to serving LoRA adapters at server startup, the vLLM server supports dynamically configuring LoRA adapters at runtime through dedicated API endpoints and plugins. This feature can be particularly useful when the flexibility to change models on-the-fly is needed.

Warning

This feature comes with security risks. It should not be used in production unless it is an isolated, fully trusted environment.

To enable dynamic LoRA configuration, ensure that the environment variable `VLLM_ALLOW_RUNTIME_LORA_UPDATING`
is set to `True`.

### Using API Endpoints[¶](#using-api-endpoints)

Loading a LoRA Adapter:

To dynamically load a LoRA adapter, send a POST request to the `/v1/load_lora_adapter` endpoint with the necessary
details of the adapter to be loaded. The request payload should include the name and path to the LoRA adapter.

Example request to load a LoRA adapter:

Upon a successful request, the API will respond with a `200 OK` status code from `vllm serve`, and `curl` returns the response body: `Success: LoRA adapter 'sql_adapter' added successfully`. If an error occurs, such as if the adapter
cannot be found or loaded, an appropriate error message will be returned.

Unloading a LoRA Adapter:

To unload a LoRA adapter that has been previously loaded, send a POST request to the `/v1/unload_lora_adapter` endpoint
with the name or ID of the adapter to be unloaded.

Upon a successful request, the API responds with a `200 OK` status code from `vllm serve`, and `curl` returns the response body: `Success: LoRA adapter 'sql_adapter' removed successfully`.

Example request to unload a LoRA adapter:

### Using Plugins[¶](#using-plugins)

Alternatively, you can use the LoRAResolver plugin to dynamically load LoRA adapters. LoRAResolver plugins enable you to load LoRA adapters from both local and remote sources such as local file system and S3. On every request, when there's a new model name that hasn't been loaded yet, the LoRAResolver will try to resolve and load the corresponding LoRA adapter.

You can set up multiple LoRAResolver plugins if you want to load LoRA adapters from different sources. For example, you might have one resolver for local files and another for S3 storage. vLLM will load the first LoRA adapter that it finds.

You can either install existing plugins or implement your own. By default, vLLM comes with a [resolver plugin to load LoRA adapters from a local directory, as well as a resolver plugin to load LoRA adapters from repositories on Hugging Face Hub](https://github.com/vllm-project/vllm/tree/main/vllm/plugins/lora_resolvers)
To enable either of these resolvers, you must `set VLLM_ALLOW_RUNTIME_LORA_UPDATING` to True.

- To leverage a local directory, set `VLLM_PLUGINS` to include `lora_filesystem_resolver` and set `VLLM_LORA_RESOLVER_CACHE_DIR` to a local directory. When vLLM receives a request using a LoRA adapter `foobar`,
it will first look in the local directory for a directory `foobar`, and attempt to load the contents of that directory as a LoRA adapter. If successful, the request will complete as normal and that adapter will then be available for normal use on the server.
- To leverage repositories on Hugging Face Hub, set `VLLM_PLUGINS` to include `lora_hf_hub_resolver` and set `VLLM_LORA_RESOLVER_HF_REPO_LIST` to a comma separated list of repository IDs on Hugging Face Hub. When vLLM receives a request for the LoRA adapter `my/repo/subpath`, it will download the adapter at the `subpath` of `my/repo` if it exists and contains an `adapter_config.json`, then build a request to the cached dir for the adapter, similar to the `lora_filesystem_resolver`. Please note that enabling remote downloads is insecure and not intended for use in production environments.

Alternatively, follow these example steps to implement your own plugin:

1. Implement the LoRAResolver interface. ## Example of a simple S3 LoRAResolver implementation2. Register [`LoRAResolver`](../../api/vllm/lora/resolver/#vllm.lora.resolver.LoRAResolver) plugin.
For more details, refer to the [vLLM's Plugins System](../../design/plugin_system/).

### In-Place LoRA Reloading[¶](#in-place-lora-reloading)

When dynamically loading LoRA adapters, you may need to replace an existing adapter with updated weights while keeping the same name. The `load_inplace` parameter enables this functionality. This commonly occurs in asynchronous reinforcement learning setups, where adapters are continuously updated and swapped in without interrupting ongoing inference.

When `load_inplace=True`, vLLM will replace the existing adapter with the new one.

Example request to load or replace a LoRA adapter with the same name:

## New format for `--lora-modules`[¶](#new-format-for-lora-modules)

In the previous version, users would provide LoRA modules via the following format, either as a key-value pair or in JSON format. For example:

This would only include the `name` and `path` for each LoRA module, but did not provide a way to specify a `base_model_name`.
Now, you can specify a base\_model\_name alongside the name and path using JSON format. For example:

To provide the backward compatibility support, you can still use the old key-value format (name=path), but the `base_model_name` will remain unspecified in that case.

## Mixing 2D and 3D MoE LoRA Adapters[¶](#mixing-2d-and-3d-moe-lora-adapters)

To serve 2D-format(based on `megatron`) and 3D-format (based on `peft`) adapters from the same engine instance, start the server with `--enable-mixed-moe-lora-format`
and declare the layout of each adapter explicitly via the `is_3d_lora_weight` field.

Server startup (static modules):

Dynamic load via `/v1/load_lora_adapter`:

You must know your adapter's layout

Under `--enable-mixed-moe-lora-format`, vLLM trusts whatever
`is_3d_lora_weight` the caller declares. Loading checks reject fused 3D
expert weights routed to a 2D wrapper without the required flags, but
do not validate every layout mismatch. A wrong declaration can still
cause loading failures or incorrect outputs. Confirm the layout before serving:

- **2D (per-expert, megatron-style)** → set `is_3d_lora_weight: false`.
  Adapter keys look like `...experts.{idx}.gate_proj.lora_A.weight`, `...experts.{idx}.up_proj.lora_A.weight`, `...experts.{idx}.down_proj.lora_A.weight` — one set per expert.
- **3D (fused, peft-style)** → set `is_3d_lora_weight: true`.
  Adapter keys look like `...experts.gate_up_proj.lora_A.weight`, `...experts.down_proj.lora_A.weight` — a single tensor that stacks
  all experts on the leading dim.

When `--enable-mixed-moe-lora-format` is **not** set, `is_3d_lora_weight`
is ignored: vLLM picks the wrapper from the base model's
`is_3d_moe_weight` and the adapter is required to match. The field is
also ignored for non-MoE models.

For a model using a 2D MoE wrapper (such as Qwen3-MoE), loading fused 3D
expert adapter weights requires both `enable_mixed_moe_lora_format=True`
on the engine and `is_3d_lora_weight=True` on the request. Otherwise, adapter
loading raises a `ValueError` naming these settings before activation.

## LoRA model lineage in model card[¶](#lora-model-lineage-in-model-card)

The new format of `--lora-modules` is mainly to support the display of parent model information in the model card. Here's an explanation of how your current response supports this:

- The `parent` field of LoRA model `sql-lora` now links to its base model `meta-llama/Llama-3.2-3B-Instruct`. This correctly reflects the hierarchical relationship between the base model and the LoRA adapter.
- The `root` field points to the artifact location of the lora adapter.

## Command output

## LoRA Support for Tower and Connector of Multi-Modal Model[¶](#lora-support-for-tower-and-connector-of-multi-modal-model)

Currently, vLLM experimentally supports LoRA for the Tower and Connector components of multi-modal models. To enable this feature, you need to implement the corresponding token helper functions for the tower and connector. For more details on the rationale behind this approach, please refer to  [PR 26674](https://github.com/vllm-project/vllm/pull/26674). We welcome contributions to extend LoRA support to additional models' tower and connector. Please refer to  [Issue 31479](https://github.com/vllm-project/vllm/issues/31479) to check the current model support status.

## Default LoRA Models For Multimodal Models[¶](#default-lora-models-for-multimodal-models)

Some models, e.g., [Granite Speech](https://huggingface.co/ibm-granite/granite-speech-3.3-8b) and [Phi-4-multimodal-instruct](https://huggingface.co/microsoft/Phi-4-multimodal-instruct) multimodal, contain LoRA adapter(s) that are expected to always be applied when a given modality is present. This can be a bit tedious to manage with the above approaches, as it requires the user to send the [`LoRARequest`](../../api/vllm/lora/request/#vllm.lora.request.LoRARequest) (offline) or to filter requests between the base model and LoRA model (server) depending on the content of the request's multimodal data.

To this end, we allow registration of default multimodal LoRAs to handle this automatically, where users can map each modality to a LoRA adapter to automatically apply it when the corresponding inputs are present. Note that currently, we only allow one LoRA per prompt; if several modalities are provided, each of which are registered to a given modality, none of them will be applied.

## Example usage for offline inference

You can also pass a json dictionary of `--default-mm-loras` mapping modalities to LoRA model IDs. For example, when starting the server:

Note: Default multimodal LoRAs are currently only available for `.generate` and chat completions.

## Sequence-Classification LoRA Adapters[¶](#sequence-classification-lora-adapters)

vLLM supports PEFT sequence-classification adapters that save a complete, single-layer linear classification head through `modules_to_save`. The saved module must be named `score` or `classifier`.

See  [classification\_with\_lora\_offline.py](https://github.com/vllm-project/vllm/blob/main/examples/pooling/classify/classification_with_lora_offline.py) for an offline classification example using a LoRA adapter.

To batch adapters with different `num_labels`, set the maximum number of labels:

The equivalent [`LLM`](../../api/vllm/entrypoints/llm/#vllm.entrypoints.llm.LLM) argument is `max_lora_cls_labels`. It defaults to the base model's `num_labels`, and each request returns its adapter's number of labels.

A classification head stored as float32 is converted to the runtime head dtype when it is loaded.

## Token-Classification LoRA Adapters[¶](#token-classification-lora-adapters)

For token-classification models that support LoRA, use `pooling_task="token_classify"` with `LLM.encode`.

Classification heads support LoRA A/B weights (matching the base head's output size) or `modules_to_save=["classifier"]`. Full heads follow the [sequence-classification configuration](#sequence-classification-lora-adapters) above, including `max_lora_cls_labels` for different label counts.

## Using Tips[¶](#using-tips)

### Configuring `max_lora_rank`[¶](#configuring-max_lora_rank)

The `--max-lora-rank` parameter controls the maximum rank allowed for LoRA adapters. This setting affects memory allocation and performance:

- **Set it to the maximum rank** among all LoRA adapters you plan to use
- **Avoid setting it too high** - using a value much larger than needed wastes memory and can cause performance issues

For example, if your LoRA adapters have ranks \[16, 32, 64\], use `--max-lora-rank 64` rather than 256

### Restricting LoRA to Specific Modules[¶](#restricting-lora-to-specific-modules)

The `--lora-target-modules` parameter allows you to restrict which model modules have LoRA applied at deployment time. This is useful for performance tuning when you only need LoRA on specific layers:

When `--lora-target-modules` is not specified, LoRA will be applied to all supported modules in the model. This parameter accepts module suffixes (the last component of the module name), such as `o_proj`, `qkv_proj`, `gate_proj`, etc.