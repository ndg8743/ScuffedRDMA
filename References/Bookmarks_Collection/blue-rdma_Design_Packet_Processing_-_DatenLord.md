# Blue-RDMA Packet Processing Design

**Source URL:** https://medium.com/@datenlord/blue-rdma-design-introduction-iii-packet-processing-ec14f463effd  
**Date Fetched:** 2026-04-12

## Overview

Blue-RDMA is a new RDMA implementation that handles packet processing differently than traditional InfiniBand systems. Unlike standard Reliable Connected (RC) mode, which requires strict packet ordering, blue-RDMA employs direct data placement (DDP) mode, where received packets are directly written to the specified memory address.

## Key Mechanisms

### Packet Sequence Numbers (PSN)
Each packet in a Send Queue receives a unique, incrementing PSN for tracking purposes on both sender and receiver sides.

### Hardware-Software Division
The system divides responsibilities: the HCA cannot store the complete required state. Therefore, the software driver participates in maintaining the global state of packet reception. The hardware maintains a 128-bit bitmap window while the driver preserves comprehensive global state.

### Bitmap Window Operations
The hardware sliding window follows three rules:
- Sets bits to 1 when packets arrive within the window
- Discards duplicate packets arriving before the window
- Advances the window when packets arrive beyond it

### ACK/NAK Reporting
The hardware sends acknowledgment messages to the driver in two scenarios: after timer expiration or upon receiving a message's final packet. NAK messages are sent both locally and to remote endpoints to trigger retransmission.

### Driver Bitmap Merging
The driver maintains a larger bitmap and merges intermittent hardware reports using a mechanism where all packets before the latest bitmap are considered successfully received, and the driver's base PSN is updated accordingly.

## Reliability Features

The system implements timeout-based retransmission for unacknowledged messages, with configurable retry limits. Retransmitted packets are marked with a retry flag for identification, enabling sophisticated error recovery.
