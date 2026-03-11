# RDMA Tuning - IBM Storage Scale

**Source URL:** https://www.ibm.com/docs/en/storage-scale/6.0.0?topic=administering-rdma-tuning
**Date Accessed:** 2026-03-11

## Overview

This IBM Storage Scale documentation addresses configuration and optimization of Remote Direct Memory Access (RDMA) attributes for InfiniBand environments.

## Key Technical Content

### Page Pool Registration Issue

The documentation identifies a critical failure scenario where the GPFS daemon cannot register the page pool to InfiniBand. The recommended resolution involves adjusting Mellanox mlx4_core module parameters, specifically:
- Setting `log_mtts_per_seg` to 0 as the preferred configuration
- Increasing `log_num_mtt` values

### verbsRdmaSend Attribute

This configuration element controls whether InfiniBand RDMA or TCP handles GPFS daemon communications. The behavior differs by version—in IBM Storage Scale 5.0.0 and later, enabling this feature allows RDMA connections between compatible nodes, whereas in 4.2.3.x deployments, clusters exceeding 500 nodes should not activate this setting.

### Performance Optimization Parameters

For large clusters exceeding 2,100 nodes, the `scatterBufferSize` attribute may require adjustment beyond its default value of 32,768 to improve NSD I/O server performance.

### Hardware Considerations

The documentation recommends disabling CPU voltage-reduction C-states on Intel Sandy Bridge processors when RDMA performance falls below expectations.

## Scope

Documentation covers IBM Storage Scale versions 4.2.3.x and 5.0.x with version-specific guidance for each configuration parameter.
