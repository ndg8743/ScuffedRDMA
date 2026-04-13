# US20250130714A1: Scalable Data Access System and Methods of Eliminating Controller Bottlenecks
**Source URL:** https://patents.google.com/patent/US20250130714A1/en
**Date Fetched:** 2026-04-12

## Patent Information
- **Publication Number:** US20250130714A1
- **Publication Date:** April 24, 2025
- **Filing Date:** December 30, 2024
- **Inventor:** Branislav Radovanovic
- **Status:** Pending
- **Application Number:** US19/005,557
- **Priority Date:** April 8, 2016

## Abstract

This patent describes a distributed data storage architecture with front-end controllers (nFE_SAN) connected via network interconnect to back-end storage controllers (nBE_SAN) and physical disk drives. The system eliminates controller bottlenecks through self-reconfiguring storage controllers and multi-level storage architecture. Key innovations include:

- Dynamic workload redistribution across controllers to prevent overload
- Redundant, independent CPU and memory systems to eliminate single points of failure
- Write-back caching with local mirroring to accelerate write performance
- Distributed Resource Manager (DRM) for real-time topology reconfiguration

## Key Technical Features

**Hardware Architecture:**
The nFE_SAN controller incorporates two independent write-back cache memory buffers, each with corresponding processing, network-interface, and power components, functioning as operationally independent units within a single card.

**Performance Enhancement:**
Data transfers use Copy-on-Write methodology to simultaneously write to dual memory buffers, enabling COMMAND COMPLETE messages to return to hosts immediately upon lock acquisition, rather than waiting for backend mirroring completion.

**Dynamic Reconfiguration:**
The system creates multi-level controller hierarchies when detecting overload conditions, intelligently delegating part of its workload to additional controller(s) through the Distributed Resource Manager component.

## Classifications

The patent covers multiple technical domains including storage I/O interfaces, cache memory systems, distributed storage networks (SAN/NAS), and dynamic resource management in hierarchical memory architectures.
