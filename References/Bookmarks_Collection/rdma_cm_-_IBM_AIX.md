# rdma_cm Documentation

**Source URL:** https://www.ibm.com/docs/en/aix/7.3.0?topic=operations-rdma-cm
**Date Accessed:** 2026-03-11

## Overview

This IBM AIX technical reference document describes **rdma_cm**, a communication manager that "Establishes communication over RDMA transports."

## Key Functions

The **rdma_cm** serves as an interface for setting up reliable and unreliable data transfers across RDMA devices. Notable capabilities include:

- Queue pair (QP) management and connection establishment
- Integration with the libibverbs library for data transfer operations
- Support for both synchronous and asynchronous operation modes

## Core Verb Operations

The manager provides wrapper functions for common operations, including:
- Memory registration (rdma_reg_msgs, rdma_reg_read, rdma_reg_write)
- Message posting (rdma_post_send, rdma_post_recv)
- RDMA operations (rdma_post_read, rdma_post_write)
- Completion status retrieval (rdma_get_send_comp, rdma_get_recv_comp)

## Connection Workflows

The documentation outlines two primary scenarios:

**Client-side operations** follow these sequential steps: address retrieval, event channel creation, queue pair allocation, route resolution, connection establishment, and eventual disconnection.

**Server-side operations** involve listening for incoming requests, accepting connections, and managing the teardown process.

## Return Values

Functions return 0 for success or -1 for failure, with error details available through the errno variable.
