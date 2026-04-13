# Harnessing 3200 Gbps Network (1): RDMA and EFA

**Source URL:** https://le.qun.ch/en/blog/2024/12/25/libfabric-efa-1-rdma/

**Date Fetched:** 2026-04-12

**Author:** Lequn Chen  
**Date:** December 25, 2024

## Overview

This article explains the foundational hardware and software concepts needed to work with ultra-high-speed networks (3200 Gbps). It contrasts traditional TCP/IP networking with RDMA technology and introduces AWS's EFA service.

## Key Concepts

**RDMA (Remote Direct Memory Access)** represents a fundamentally different networking approach compared to conventional socket-based TCP/IP. The stack consists of:

- **Application Layer:** Uses the ibverbs API, which differs significantly from socket programming philosophies
- **Protocol Layer:** Custom RDMA protocols replacing TCP/IP
- **Network Layer:** Typically InfiniBand or RoCE (RDMA over Converged Ethernet)
- **Hardware:** Often Mellanox ConnectX NICs, with ConnectX-7 supporting 400 Gbps

## RDMA Operations

The technology supports rich communication patterns:

**Two-sided operations** require both parties' involvement (SEND/RECV), while **one-sided operations** allow direct memory access without target CPU awareness (READ, WRITE, ATOMIC operations).

RDMA uses Queue Pairs in three types: Reliable Connected (RC), Unreliable Connected (UC), and Unreliable Datagram (UD).

## AWS EFA

For cloud users, AWS provides "Elastic Fabric Adapter" on p5 instances, utilizing Amazon's custom SRD protocol. Applications access EFA through the libfabric library rather than direct hardware interaction.
