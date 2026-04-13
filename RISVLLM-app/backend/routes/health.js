const express = require('express');
const { VLLMClient } = require('../lib/vllm-client');

const router = express.Router();
const vllm = new VLLMClient();

router.get('/', async (req, res) => {
  const modelHealthy = await vllm.healthCheck();
  res.json({
    status: 'ok',
    purpose: 'RISVLLM is a reverse engineering IDE that uses LLM4Decompile-22B-v2 to convert Ghidra pseudo-code and assembly into readable C source code. Paste or upload decompiled output from Ghidra, select the compiler optimization level, and the model refines it into clean, human-readable C.',
    model: {
      name: 'llm4decompile-22b-v2',
      params: '22B',
      architecture: 'MistralForCausalLM',
      precision: 'bfloat16',
      maxTokens: 4096,
      healthy: modelHealthy,
      url: process.env.VLLM_URL || 'http://vllm-decompile.hydra-infra.svc:8000',
      promptFormat: '# This is the assembly code:\\n{ghidra_pseudo_code}\\n# What is the source code?\\n',
    },
    uptime: process.uptime(),
  });
});

module.exports = router;
