const express = require('express');
const { VLLMClient } = require('../lib/vllm-client');

const router = express.Router();
const vllm = new VLLMClient();

router.get('/', async (req, res) => {
  const modelHealthy = await vllm.healthCheck();
  res.json({
    status: 'ok',
    model: {
      name: 'llm4decompile-22b-v2',
      healthy: modelHealthy,
      url: process.env.VLLM_URL || 'http://vllm-decompile.default.svc:8000',
    },
    uptime: process.uptime(),
  });
});

module.exports = router;
