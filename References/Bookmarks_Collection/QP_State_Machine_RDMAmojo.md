# QP State Machine
**Source URL:** https://www.rdmamojo.com/2012/05/05/qp-state-machine/
**Date Fetched:** 2026-04-12

## Overview

A Queue Pair (QP) is a fundamental RDMA object that transitions through seven distinct states during its lifetime: Reset, Init, Ready To Receive (RTR), Ready To Send (RTS), Send Queue Drained (SQD), Send Queue Error (SQE), and Error.

## State Transitions

A QP is being created in the Reset state and can move between states through explicit calls to `ibv_modify_qp()` or automatically when the device encounters processing errors. Any QP can transition to Reset or Error states from any other state.

## Key States Explained

**Reset & Init**: Work requests cannot be posted to send queues, and incoming packets are silently dropped. Only receive requests are permitted in Init state.

**RTR (Ready To Receive)**: The QP functions as a responder only, processing incoming packets and posting responses while incoming data is handled.

**RTS (Ready To Send)**: The QP operates as both requester and responder, processing work requests from both queues and initiating outgoing packets.

**SQD (Send Queue Drained)**: New send requests are blocked, though in-progress requests complete. The QP maintains two internal substates—Draining and Drained.

**SQE & Error**: Both states flush new send requests with errors. Error represents the terminal state where incoming packets which are targeted to this QP will be silently dropped.

## Summary

The table contrasts how each state handles work request posting, processing, packet handling, and outgoing packet transmission, creating a comprehensive framework for managing QP lifecycle and data flow.
