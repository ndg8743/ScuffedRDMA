# Connection Manager (CM) ID Operations

**Source URL:** https://www.ibm.com/docs/en/aix/7.3.0?topic=verbs-connection-manager-cm-id-operations
**Date Accessed:** 2026-03-11

## Overview

This documentation describes the Connection Manager ID operation functionality, which handles identity-related tasks in RDMA communication. The operations enable creation, destruction, migration, address resolution, connection establishment, request listening, request rejection, and address information provision.

## Core Operations

The page lists 21 distinct operations organized by function:

### Identifier Management

- `rdma_create_id` - Allocates a communication identifier
- `rdma_destroy_id` - Releases a communication identifier
- `rdma_migrate_id` - Moves an identifier to another event channel

### Address Operations

- `rdma_bind_addr` - Binds an RDMA identifier to a source address
- `rdma_resolve_addr` - "Resolves the destination and optional source addresses"
- `rdma_resolve_route` - Determines routing information for connections

### Connection Management

- `rdma_connect` - Initiates active connection requests
- `rdma_listen` - Monitors incoming connection requests
- `rdma_accept` - Accepts connection requests
- `rdma_reject` - Denies connection requests
- `rdma_disconnect` - Terminates connections

### Information Retrieval

- `rdma_get_src_port`, `rdma_get_dst_port` - Port number access
- `rdma_get_local_addr`, `rdma_get_peer_addr` - IP address retrieval
- `rdma_getaddrinfo` - Translates transport-independent addresses
- `rdma_notify` - Reports asynchronous queue pair events

### Endpoint Operations

- `rdma_create_ep` - Creates identifiers for tracking communication
- `rdma_destroy_ep` - Destroys identifiers and associated resources
