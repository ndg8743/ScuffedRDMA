# Intelligent Semantic Routing — production-stack

- **Source:** https://docs.vllm.ai/projects/production-stack/en/latest/use_cases/semantic-router-integration.html#step-2-deploy-vllm-semantic-router
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

# Intelligent Semantic Routing[#](#intelligent-semantic-routing)

This use case demonstrates how to integrate the vLLM Semantic Router with the vLLM Production Stack to create an intelligent Mixture-of-Models (MoM) system. The Semantic Router operates as an Envoy External Processor that semantically routes OpenAI API-compatible requests to the most suitable backend model using BERT-based or decoder-only LoRA classification, prompt guard, and semantic caching, improving both quality and cost efficiency.

## What is vLLM Semantic Router?[#](#what-is-vllm-semantic-router)

The vLLM Semantic Router provides:

- **Auto-selection of models**: Routes math, creative writing, code, and general queries to the best-fit models
- **Security & privacy**: PII detection, prompt guard, and safe routing for sensitive prompts
- **Performance optimizations**: Semantic cache and better tool selection to cut latency and tokens
- **Architecture**: Tight Envoy ExtProc integration with dual Go and Rust implementations
- **Monitoring**: Console, Grafana dashboards, Prometheus metrics, and tracing for full visibility

Learn more: [vLLM Semantic Router](https://vllm-semantic-router.com)

## Benefits of Integration[#](#benefits-of-integration)

The vLLM Production Stack provides deployment capabilities that spin up vLLM servers with traffic routing to different models, service discovery and fault tolerance through the Kubernetes API, and support for round-robin, session-based, prefix-aware, KV-aware and disaggregated-prefill routing with LMCache native support.

The Semantic Router adds a system-intelligence layer that:

- Classifies each user request
- Selects the most suitable model from a pool
- Injects domain-specific system prompts
- Performs semantic caching
- Enforces enterprise-grade security checks such as PII and jailbreak detection

By combining these two systems, you obtain a unified inference stack where semantic routing ensures that each request is answered by the best possible model, while Production-Stack routing maximizes infrastructure and inference efficiency with rich metrics.

## Table of Contents[#](#table-of-contents)

## Prerequisites[#](#prerequisites)

- kubectl
- Helm
- A Kubernetes cluster (kind, minikube, GKE, etc.)
- Completion of [Prerequisite](../getting_started/prerequisite.html) and [Quick Start](../getting_started/quickstart.html)

## Step 1: Deploy the vLLM Production Stack[#](#step-1-deploy-the-vllm-production-stack)

Deploy the vLLM Production Stack using the provided Helm values file:

```
helm repo add vllm-production-stack https://vllm-project.github.io/production-stack
helm install vllm-stack vllm-production-stack/vllm-stack -f https://github.com/vllm-project/production-stack/blob/main/tutorials/assets/values-23-SR.yaml
```
The sample values file configures:

- **Model**: Qwen/Qwen3-8B with 2 replicas
- **Router**: Round-robin routing logic with session key support
- **Resources**: 8 CPU, 16Gi memory, 1 GPU per instance

Identify the ClusterIP and port of your router Service:

```
kubectl get svc vllm-router-service
# Note the router service ClusterIP and port (e.g., 10.97.254.122:80)
```
## Step 2: Deploy vLLM Semantic Router[#](#step-2-deploy-vllm-semantic-router)

Follow the official [Install in Kubernetes](https://vllm-semantic-router.com/docs/installation/k8s/ai-gateway) guide with the updated configuration.

Deploy vLLM Semantic Router using Helm:

```
# Deploy vLLM Semantic Router with custom values from GHCR OCI registry
# (Optional) If you use a registry mirror/proxy, append: --set global.imageRegistry=<your-registry>
helm install semantic-router oci://ghcr.io/vllm-project/charts/semantic-router \
  --version v0.0.0-latest \
  --namespace vllm-semantic-router-system \
  --create-namespace \
  -f https://raw.githubusercontent.com/vllm-project/semantic-router/refs/heads/main/deploy/kubernetes/ai-gateway/semantic-router-values/values.yaml
kubectl wait --for=condition=Available deployment/semantic-router \
  -n vllm-semantic-router-system --timeout=600s
# Install Envoy Gateway
helm upgrade -i eg oci://docker.io/envoyproxy/gateway-helm \
  --version v0.0.0-latest \
  --namespace envoy-gateway-system \
  --create-namespace \
  -f https://raw.githubusercontent.com/envoyproxy/ai-gateway/main/manifests/envoy-gateway-values.yaml
# Install Envoy AI Gateway
helm upgrade -i aieg oci://docker.io/envoyproxy/ai-gateway-helm \
  --version v0.0.0-latest \
  --namespace envoy-ai-gateway-system \
  --create-namespace
# Install Envoy AI Gateway CRDs
helm upgrade -i aieg-crd oci://docker.io/envoyproxy/ai-gateway-crds-helm \
  --version v0.0.0-latest \
  --namespace envoy-ai-gateway-system
# Wait for AI Gateway to be ready
kubectl wait --timeout=300s -n envoy-ai-gateway-system \
  deployment/ai-gateway-controller --for=condition=Available
```
Note

The values file contains the configuration for the semantic router including domain classification, LoRA routing, and plugin settings. You can download and customize it from the [semantic-router-values](https://raw.githubusercontent.com/vllm-project/semantic-router/refs/heads/main/deploy/kubernetes/ai-gateway/semantic-router-values/values.yaml) to match your vLLM Production Stack setup.

Create LLM Demo Backends and AI Gateway Routes:

```
# Apply LLM demo backends
kubectl apply -f https://raw.githubusercontent.com/vllm-project/semantic-router/refs/heads/main/deploy/kubernetes/ai-gateway/aigw-resources/base-model.yaml
# Apply AI Gateway routes
kubectl apply -f https://raw.githubusercontent.com/vllm-project/semantic-router/refs/heads/main/deploy/kubernetes/ai-gateway/aigw-resources/gwapi-resources.yaml
```
## Step 3: Test the Deployment[#](#step-3-test-the-deployment)

Port-forward to the Envoy service:

```
export ENVOY_SERVICE=$(kubectl get svc -n envoy-gateway-system \
  --selector=gateway.envoyproxy.io/owning-gateway-namespace=default,gateway.envoyproxy.io/owning-gateway-name=semantic-router \
  -o jsonpath='{.items[0].metadata.name}')
kubectl port-forward -n envoy-gateway-system svc/$ENVOY_SERVICE 8080:80
```
Send a chat completions request:

```
curl -i -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MoM",
    "messages": [
      {"role": "user", "content": "What is the derivative of f(x) = x^3?"}
    ]
  }'
```
The semantic router will analyze the request, identify it as a math query, and route it to the appropriate model through the vLLM Production Stack router.

## Troubleshooting[#](#troubleshooting)

- **Gateway not accessible**: Check the Gateway and Envoy service status
- **Semantic router not responding**: Check pod status and logs with `kubectl logs -n vllm-semantic-router-system`
- **Error codes returned**: Check the production stack router logs with `kubectl logs`

## Conclusion[#](#conclusion)

In this use case, we’ve demonstrated how to:

1. Deploy vLLM Production Stack with a router service
2. Integrate vLLM Semantic Router with the production stack
3. Configure Envoy Gateway and AI Gateway for intelligent routing
4. Test the end-to-end semantic routing functionality

This integration provides a powerful combination of semantic intelligence and production-grade infrastructure, enabling efficient, secure, and intelligent model routing for diverse workloads.

Note

**Preview Version**: This guide is based on the preview version of vLLM Semantic Router integration. The deployment steps, configuration options, and API interfaces may change in future releases as the feature evolves. Please refer to the latest documentation for updates.