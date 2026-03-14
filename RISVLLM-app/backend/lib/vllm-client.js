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

  // Exact prompt format from LLM4Decompile training:
  // https://github.com/albertan017/LLM4Decompile/blob/main/ghidra/demo.py
  formatPrompt(code) {
    return `# This is the assembly code:\n${code.trim()}\n# What is the source code?\n`;
  }

  async decompile(code, { stream = false } = {}) {
    const prompt = this.formatPrompt(code);

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

  async decompileStream(code) {
    const prompt = this.formatPrompt(code);

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
