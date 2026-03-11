const express = require('express');
const { VLLMClient } = require('../lib/vllm-client');

const router = express.Router();
const vllm = new VLLMClient();

// POST /api/decompile — non-streaming
router.post('/', async (req, res) => {
  try {
    const { code, optimizationLevel, inputType } = req.body;

    if (!code || !code.trim()) {
      return res.status(400).json({ error: 'No code provided' });
    }

    const result = await vllm.decompile(code, { optimizationLevel, inputType });
    res.json({ result, model: 'llm4decompile-22b-v2' });
  } catch (err) {
    console.error('Decompile error:', err.message);
    res.status(502).json({ error: err.message });
  }
});

// POST /api/decompile/stream — SSE streaming
router.post('/stream', async (req, res) => {
  try {
    const { code, optimizationLevel, inputType } = req.body;

    if (!code || !code.trim()) {
      return res.status(400).json({ error: 'No code provided' });
    }

    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');

    const stream = await vllm.decompileStream(code, { optimizationLevel, inputType });
    const reader = stream.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n').filter(l => l.startsWith('data: '));

      for (const line of lines) {
        const data = line.slice(6);
        if (data === '[DONE]') {
          res.write('data: [DONE]\n\n');
        } else {
          try {
            const parsed = JSON.parse(data);
            const text = parsed.choices?.[0]?.text || '';
            if (text) {
              res.write(`data: ${JSON.stringify({ text })}\n\n`);
            }
          } catch {
            // skip malformed chunks
          }
        }
      }
    }

    res.end();
  } catch (err) {
    console.error('Stream error:', err.message);
    if (!res.headersSent) {
      res.status(502).json({ error: err.message });
    } else {
      res.end();
    }
  }
});

module.exports = router;
