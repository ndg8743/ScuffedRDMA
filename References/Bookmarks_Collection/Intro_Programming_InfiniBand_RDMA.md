# Introduction to Programming Infiniband RDMA
**Source URL:** https://insujang.github.io/2020-02-09/introduction-to-programming-infiniband/
**Date Fetched:** 2026-04-12

**Author:** Insu Jang  
**Published:** February 9, 2020

## Overview

This tutorial explains fundamental concepts of RDMA (Remote Direct Memory Access) programming using Infiniband technology. The author addresses a common gap in existing documentation by providing detailed explanations of how RDMA operations work.

## Key Concepts

**Channel Adapters (HCAs):** These are Infiniband network interface cards serving as end nodes in Infiniband networks, offering enhanced capabilities beyond standard Ethernet NICs.

**Queue Pairs (QP):** Work queues comprise send queues (SQ), receive queues (RQ), and completion queues (CQ). Users post work requests that are directly processed by hardware, with results returned as work completions.

## Programming Workflow

The implementation follows nine essential steps:

1. Create an Infiniband context by opening the HCA device
2. Allocate a protection domain for resource management
3. Establish a completion queue
4. Initialize a queue pair
5-6. Exchange peer identifiers and transition the queue pair through states (RESET → INIT → RTR → RTS)
7. Register memory regions for data access
8-9. Exchange memory region details and execute data transfers

## Operations Supported

The framework enables several communication types:

- **Send/Receive:** Traditional paired operations requiring both sides' participation
- **RDMA Read:** Remote data retrieval without peer awareness
- **RDMA Write:** Remote data placement without peer notification

## Practical Implementation

The author emphasizes dividing the workflow into initialization (steps 1-6) and runtime (steps 7-9) phases. The libibverbs library provides the necessary APIs for all operations, with TCP sockets typically facilitating initial peer information exchange.
