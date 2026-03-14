const express = require('express');
const https = require('https');
const fs = require('fs');
const path = require('path');

const router = express.Router();

// K8s API config — uses in-cluster service account
const K8S_HOST = process.env.KUBERNETES_SERVICE_HOST;
const K8S_PORT = process.env.KUBERNETES_SERVICE_PORT;
const NAMESPACE = 'hydra-infra';
const DEPLOYMENT = 'vllm-decompile';

function getToken() {
  return fs.readFileSync('/var/run/secrets/kubernetes.io/serviceaccount/token', 'utf8');
}

function getCaCert() {
  return fs.readFileSync('/var/run/secrets/kubernetes.io/serviceaccount/ca.crt');
}

function k8sRequest(method, urlPath, body) {
  return new Promise((resolve, reject) => {
    if (!K8S_HOST) {
      return reject(new Error('Not running in a Kubernetes cluster'));
    }

    const options = {
      hostname: K8S_HOST,
      port: K8S_PORT,
      path: urlPath,
      method,
      headers: {
        Authorization: `Bearer ${getToken()}`,
        'Content-Type': method === 'PATCH' ? 'application/strategic-merge-patch+json' : 'application/json',
      },
      ca: getCaCert(),
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => (data += chunk));
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, body: JSON.parse(data) });
        } catch {
          resolve({ status: res.statusCode, body: data });
        }
      });
    });

    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

// GET /api/model — get vLLM deployment status
router.get('/', async (req, res) => {
  try {
    const result = await k8sRequest(
      'GET',
      `/apis/apps/v1/namespaces/${NAMESPACE}/deployments/${DEPLOYMENT}`
    );

    if (result.status !== 200) {
      return res.status(502).json({ error: 'Failed to query deployment', details: result.body });
    }

    const deploy = result.body;
    const replicas = deploy.spec?.replicas || 0;
    const ready = deploy.status?.readyReplicas || 0;
    const available = deploy.status?.availableReplicas || 0;

    // Check pod status for more detail
    const podsResult = await k8sRequest(
      'GET',
      `/api/v1/namespaces/${NAMESPACE}/pods?labelSelector=app=vllm-decompile`
    );

    let podStatus = 'Unknown';
    let podMessage = '';
    if (podsResult.status === 200 && podsResult.body.items?.length > 0) {
      const pod = podsResult.body.items[0];
      podStatus = pod.status?.phase || 'Unknown';
      const conditions = pod.status?.conditions || [];
      const scheduled = conditions.find((c) => c.type === 'PodScheduled');
      if (scheduled && scheduled.status === 'False') {
        podStatus = 'Unschedulable';
        podMessage = scheduled.message || 'Insufficient resources';
      }
    }

    res.json({
      replicas,
      ready,
      available,
      podStatus,
      podMessage,
      state:
        replicas === 0
          ? 'stopped'
          : ready > 0
            ? 'running'
            : podStatus === 'Unschedulable'
              ? 'unschedulable'
              : 'starting',
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/model/load — scale vLLM to 1 replica
router.post('/load', async (req, res) => {
  try {
    const result = await k8sRequest(
      'PATCH',
      `/apis/apps/v1/namespaces/${NAMESPACE}/deployments/${DEPLOYMENT}`,
      { spec: { replicas: 1 } }
    );

    if (result.status >= 200 && result.status < 300) {
      res.json({ message: 'Model loading started', replicas: 1 });
    } else {
      res.status(502).json({ error: 'Failed to scale deployment', details: result.body });
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/model/unload — scale vLLM to 0 replicas
router.post('/unload', async (req, res) => {
  try {
    const result = await k8sRequest(
      'PATCH',
      `/apis/apps/v1/namespaces/${NAMESPACE}/deployments/${DEPLOYMENT}`,
      { spec: { replicas: 0 } }
    );

    if (result.status >= 200 && result.status < 300) {
      res.json({ message: 'Model unloaded', replicas: 0 });
    } else {
      res.status(502).json({ error: 'Failed to scale deployment', details: result.body });
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
