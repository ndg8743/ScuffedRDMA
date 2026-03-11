# Tesla's TTPoE at Hot Chips 2024: Replacing TCP for Low Latency Applications

**Source URL:** https://chipsandcheese.com/p/teslas-ttpoe-at-hot-chips-2024-replacing-tcp-for-low-latency-applications
**Date Accessed:** 2026-03-11

**Author:** Chester Lam
**Published:** August 27, 2024

## Overview

Tesla presented their custom transport protocol, Tesla Transport Protocol over Ethernet (TTPoE), designed to replace TCP for high-speed supercomputer networking. The protocol addresses bandwidth limitations when feeding data into Tesla's Dojo supercomputer for machine learning training on automotive video applications.

## Key Technical Innovations

**Simplified State Machine**
TTPoE eliminates TCP's complexity by removing unnecessary wait states. The connection closure sequence reduces from three transmissions to two, eliminating the TIME_WAIT state entirely. This streamlines microsecond-scale latency requirements where even millisecond delays become problematic.

**Two-Way Handshake**
Rather than TCP's three-way SYN/SYN-ACK/ACK handshake, TTPoE implements a "two-way" connection opening, reducing transmission overhead and cutting latency.

**Hardware-Optimized Congestion Control**
TTPoE employs a fixed congestion window managed by SRAM buffers rather than TCP's dynamic scaling. A 1 MB transmit buffer tolerates approximately 80 microseconds of network latency while maintaining near 100 Gbps throughput. This brute-force approach suits controlled datacenter environments better than variable TCP algorithms like Reno.

## Implementation

The protocol runs on Tesla's "Dumb-NIC" (Mojo card), featuring a custom TTPoE MAC designed by CPU architects. The hardware includes PCIe Gen 3 x16 connectivity, 8 GB DDR4, and handles packet retirement in-order like CPU instruction reordering.

**Result:** A cost-effective solution enabling deployment of multiple host nodes feeding the Dojo supercomputer without requiring expensive Infiniband infrastructure.
