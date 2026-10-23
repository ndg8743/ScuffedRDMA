"""libfabric transport for libscuffedrdma (see README.md in this folder)."""
from .channel import BlobChannel, TcpBlobChannel  # noqa: F401


def __getattr__(name):
    # lazy: importing middleware.fabric must not require the C library
    if name in ("FabricPool", "FabricBlobChannel", "FabricError", "build"):
        from . import pool
        return getattr(pool, name)
    raise AttributeError(name)
