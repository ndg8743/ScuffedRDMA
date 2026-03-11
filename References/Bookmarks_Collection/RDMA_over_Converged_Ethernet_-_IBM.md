# RDMA over Converged Ethernet

**Source URL:** https://www.ibm.com/docs/en/i/7.4.0?topic=concepts-rdma-over-converged-ethernet
**Date accessed:** 2026-03-11

## Technical Overview

This documentation explains the high-speed network requirements for mirrored database node pairs using Remote Direct Memory Access (RDMA) over Converged Ethernet (RoCE).

## Key Requirements

Both nodes require RDMA-capable adapters with IP addresses configured on their associated line descriptions. "A pair of IP addresses, one from each node, is used to identify each physical RDMA link between the two nodes."

## Supported RDMA Protocols

**RoCE v1:** A non-encrypted, non-routable protocol where adapter ports connect directly or through a single switch, supporting cable lengths up to 200 meters (some adapters reach 10 kilometers).

**RoCE v2:** A non-encrypted, routable protocol allowing multi-switch/router connections up to 10 kilometers maximum distance.

**Encrypted RoCE v2:** An encrypted, routable variant using IPsec for authentication, integrity, and confidentiality—available exclusively on POWER9 or newer systems.

## Critical Configuration Notes

Both link endpoints must use the same RDMA protocol type. "A link can be configured as one type of RDMA protocol only." Changing a link's protocol while active doesn't take effect until the link restarts. When links are shared across multiple Network Redundancy Groups (NRGs), protocol changes affect all associated groups.

## Navigation
- **Next:** Network Redundancy Groups
- **Parent:** Db2 Mirror concepts
