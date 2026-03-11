const express = require('express');
const cors = require('cors');
const path = require('path');

const decompileRouter = require('./routes/decompile');
const uploadRouter = require('./routes/upload');
const healthRouter = require('./routes/health');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json({ limit: '5mb' }));

// API routes
app.use('/api/decompile', decompileRouter);
app.use('/api/upload', uploadRouter);
app.use('/api/health', healthRouter);

// Serve frontend static files
app.use(express.static(path.join(__dirname, '../frontend/dist')));

// SPA fallback
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../frontend/dist/index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`RISVLLM server running on port ${PORT}`);
  console.log(`vLLM endpoint: ${process.env.VLLM_URL || 'http://vllm-decompile.default.svc:8000'}`);
});
