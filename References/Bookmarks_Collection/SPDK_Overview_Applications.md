# An Overview of SPDK Applications

**Source URL:** https://spdk.io/doc/app_overview.html
**Date accessed:** 2026-03-11

## Document Summary

This technical documentation covers the Storage Performance Development Kit (SPDK), a development kit providing libraries and header files for application development, along with several included applications.

## Key Applications

SPDK includes several major target applications:
- iSCSI Target
- NVMe over Fabrics Target
- vhost Target
- SPDK Target (unified application combining the three above)

The document notes that "there are also a number of tools and examples in the `examples` directory." All targets share a common framework based on subsystems with unified initialization and teardown paths.

## Configuration Overview

### Command Line Parameters

SPDK applications support numerous command-line flags. Notable parameters include:

- **CPU mask** (`-m`): Controls which processors the application uses, defaulting to `0x1`
- **Memory size** (`-s`): Specifies hugepage memory reservation with binary prefixes (e.g., 1G)
- **Config file** (`-c`): JSON RPC configuration file for application setup
- **RPC socket** (`-r`): Sets listening address, defaulting to `/var/tmp/spdk.sock`

### Special Modes

**Deferred Initialization**: The `--wait-for-rpc` parameter pauses initialization at the STARTUP state, allowing configuration via RPC commands before entering RUNTIME state.

**Multi-process Mode**: When `--shm-id` is specified, multiple application instances can share memory and NVMe devices, with the first instance acting as primary.

### CPU Mask Formats

CPU masks accept hexadecimal notation (with or without "0x" prefix) or comma-separated CPU lists with range support using hyphens.
