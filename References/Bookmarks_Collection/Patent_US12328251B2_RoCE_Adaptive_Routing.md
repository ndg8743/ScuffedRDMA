# US12328251B2 - Marking of RDMA-over-Converged-Ethernet (RoCE) Traffic Eligible for Adaptive Routing
**Source URL:** https://patents.google.com/patent/US12328251B2/en
**Date Fetched:** 2026-04-12

## Title
Marking of RDMA-over-converged-ethernet (RoCE) traffic eligible for adaptive routing

## Patent Information
- **Publication Number:** US12328251B2
- **Publication Date:** June 10, 2025
- **Filing Date:** November 20, 2022
- **Priority Date:** September 8, 2022
- **Assignee:** Mellano Technologies Ltd / Mellanox Technologies Ltd
- **Status:** Active (expires October 5, 2043)

## Abstract

A network adapter includes a port and circuitry that decides whether a packet is permitted to undergo Adaptive Routing (AR) in being routed through the network. The adapter marks packets with an eligibility indication and transmits marked packets via the port. The circuitry determines eligibility by negotiating with destination adapters to establish if they can process out-of-order RoCE packets, though hosts may override these decisions or force static routing for specific packets.

## Key Technical Features

**Marking Mechanism:** The invention uses a reserved bit in the Base Transport Header (BTH) of RoCE packets to indicate AR eligibility—setting the bit to "1" means eligible; "0" means ineligible.

**Decision Criteria:** Source NICs employ auto-negotiation to discover destination NIC capabilities regarding out-of-order packet processing, allowing selective AR application rather than network-wide mandatory compliance.

**Switch-Level Implementation:** Layer-2 Ethernet switches extract eligibility marks from encapsulated layer-4 headers and route packets accordingly—using adaptive routing for eligible traffic and static routing otherwise.
