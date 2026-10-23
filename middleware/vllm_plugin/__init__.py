"""
Out-of-tree vLLM KV connector for libscuffedrdma (ScuffedRdmaConnector).

Importing this package does not import vLLM. The vLLM subclass lives in
middleware.vllm_plugin.connector and is loaded by vLLM via
kv_connector_module_path. See README.md for launch commands.
"""

from .core import ConnectorConfig, CoreMetadata, ReqMeta, SchedulerSide, WorkerSide  # noqa: F401
from .kv_codec import decode_kv, encode_kv  # noqa: F401
from .kv_layout import block_axis, put_blocks, take_blocks  # noqa: F401

CONNECTOR_NAME = "ScuffedRdmaConnector"
CONNECTOR_MODULE = "middleware.vllm_plugin.connector"
