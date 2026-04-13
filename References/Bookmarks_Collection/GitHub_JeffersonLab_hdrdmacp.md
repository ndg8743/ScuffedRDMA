# hdrdmacp - Jefferson Lab RDMA File Transfer Utility

**Source URL:** https://github.com/JeffersonLab/hdrdmacp  
**Date Fetched:** 2026-04-12

## Project Overview

RDMA client/server utility for high-speed file transfers over InfiniBand. The hdrdmacp tool enables efficient copying of large files between computers connected via InfiniBand using RDMA technology. It was developed for the Data Acquisition system at Jefferson Lab to handle transfers of massive datasets (approximately 20GB files).

## Basic Usage

**Server mode** (destination machine):
```
hdrdmacp -s
```

**Client mode** (source machine):
```
hdrdmacp file.dat my.server.host:/path/to/dest/filename
```

## Key Limitations

1. Unidirectional transfers only (client to server)
2. Requires complete destination filename, not just directory paths
3. Large default buffer sizes optimized for memory-rich systems

## Build Instructions

The compilation requires InfiniBand libraries:
```
c++ -o hdrdmacp *.cc -libverbs -lz
```

## Notable Features

- Supports multiple simultaneous server connections
- Optional checksum calculation (Adler32)
- Automatic parent directory creation with `-P` flag
- Configurable memory allocation and buffer management
- Customizable TCP and RDMA port assignments

## Implementation

The codebase consists of C++ source files totaling approximately 99.6% of the repository.
