const VLLM_BASE_URL = process.env.VLLM_URL || 'http://vllm-decompile.default.svc:8000';

class VLLMClient {
  constructor(baseUrl = VLLM_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async healthCheck() {
    try {
      const res = await fetch(`${this.baseUrl}/health`);
      return res.ok;
    } catch {
      return false;
    }
  }

  formatPrompt(code, optimizationLevel = 'O0', inputType = 'pseudo') {
    const prefix = inputType === 'assembly'
      ? '# This is the assembly code with optimization level ' + optimizationLevel + ':\n'
      : '# This is the decompiled pseudo code with optimization level ' + optimizationLevel + ':\n';

    return `${prefix}${code}\n# What is the source code?`;
  }

  async decompile(code, { optimizationLevel = 'O0', inputType = 'pseudo', stream = false } = {}) {
    const prompt = this.formatPrompt(code, optimizationLevel, inputType);

    const body = {
      model: '/models/llm4decompile-22b-v2',
      prompt,
      max_tokens: 2048,
      temperature: 0.0,
      stream,
    };

    const res = await fetch(`${this.baseUrl}/v1/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const err = await res.text();
      throw new Error(`vLLM error (${res.status}): ${err}`);
    }

    if (stream) {
      return res.body;
    }

    const data = await res.json();
    return data.choices?.[0]?.text?.trim() || '';
  }

  async decompileStream(code, options = {}) {
    const prompt = this.formatPrompt(code, options.optimizationLevel, options.inputType);

    const body = {
      model: '/models/llm4decompile-22b-v2',
      prompt,
      max_tokens: 2048,
      temperature: 0.0,
      stream: true,
    };

    const res = await fetch(`${this.baseUrl}/v1/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const err = await res.text();
      throw new Error(`vLLM error (${res.status}): ${err}`);
    }

    return res.body;
  }
}

module.exports = { VLLMClient };
