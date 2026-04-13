# Explorations of RDMA in LLM Systems

**Source URL:** https://www.glennklockwood.com/garden/papers/Explorations-of-RDMA-in-LLM-Systems

**Date Fetched:** 2026-04-12

## Overview

This article examines Remote Direct Memory Access (RDMA) technology in large language model infrastructure, highlighting practical challenges in distributed inference systems.

## Key Technical Insights

The piece identifies several limitations of collective communication protocols in disaggregated inference:

**Scalability constraints:** "Collectives require a fixed 'world' of participants. Nodes can't be added or removed. This is a production nightmare."

**Dynamic resource management:** The blocking initialization process becomes problematic during autoscaling. "Every time you scale up or down, the whole world must pause."

**Ordering guarantees:** While collective protocols enforce global message ordering, this overhead may be unnecessary. For KV cache transfers specifically, "we only care that all pages eventually arrive; the order doesn't matter."

**Message size requirements:** Rigidity in tensor specifications forces inefficiencies—using collectives for RPC "forces you to always send the maximum possible message size."

## Protocol Considerations

The author notes that AWS EFA uses Scalable Reliable Datagram (SRD) rather than the traditional Reliable Connection (RC) protocol, enabling unordered but reliable delivery—a better fit for certain workloads.

**Hardware constraints:** Direct GPU-to-NIC operations require ConnectX support; otherwise CPU mediation is necessary. PCIe latency between CPU and GPU remains minimal at approximately 2 microseconds.

The article concludes that production inference systems increasingly require custom networking stacks rather than relying solely on existing frameworks.
