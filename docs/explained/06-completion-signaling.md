# 6. How the receiver learns data arrived

[← back to the README section](../../README.md#6-how-the-receiver-learns-data-arrived)

![Completion signaling](../media/06_completion.gif)

An RDMA write puts bytes into the target's memory without the target's CPU taking part. So the target needs some way to learn that the data is complete. There are five common ways. For each, this page states what guarantee it relies on, why that guarantee makes it correct, and when the guarantee does not hold.

Code: `middleware/libscuffedfabric/sf_bench.c`, mode `-m sig -M cq|flag|sentinel|cntr|read`. Notebook 02, experiment E5.

---

## Background: what the hardware does and doesn't promise

On a reliable connected queue pair (verbs RC, or a libfabric MSG endpoint over verbs):

1. **Operations execute in order at the target.** Requests posted to one QP are executed at the target in the order posted.
2. **Placement order *within* one message is not promised.** A large write is many packets. The NIC may write them into memory in any order, and PCIe may make them visible to the CPU in any order. Only the *completion* of the message guarantees that all of it is placed.
3. **Completions are generated after placement.** A target-side completion for a write-with-immediate is reported after the data is in memory.

Every mechanism below leans on one of these.

## 1. CQ data (write with immediate)

**How.** `fi_writedata` / `RDMA_WRITE_WITH_IMM`. The target gets a completion queue entry carrying a 32-bit (verbs) or up to 64-bit (libfabric tcp/shm) immediate value.

**Why it is correct.** Fact 3: the completion is generated only after the whole write has been placed. The receiver never sees the entry early.

**Cost.** The target must have a receive posted for every incoming write-with-immediate (the immediate consumes a receive queue entry), and it must poll or wait on a CQ.

## 2. Flag in the payload

**How.** The last 8 bytes of the buffer are a flag (or a sequence number). The target spins on that memory location; when it changes, it reads the rest.

**Why it can be wrong.** It assumes the last bytes become visible after all the others. Fact 2 says that is not guaranteed for a multi-packet message: the flag's packet could be placed before an earlier one. It is safe when:

- the whole message fits in one packet and the NIC writes it in address order (commonly true, not guaranteed), or
- every 8-byte word carries its own flag, so a partially placed message is detectable. NCCL's LL protocol does this, at the cost of half the bandwidth.

**Why bother.** No CQ, no posted receives, and the target reads one cache line. The latency can be lower than a CQ poll. E5 checks whether it actually is, and whether it is ever wrong on our NICs.

## 3. Sentinel write

**How.** After the payload write, post a second, 8-byte write to a separate "sentinel" location. The target spins on the sentinel.

**Why it is correct (when it is).** If writes on one endpoint are executed in order (Fact 1) and the provider guarantees that a later write is placed after an earlier one (libfabric advertises this as write-after-write ordering, `FI_ORDER_WAW`), then by the time the sentinel is visible, the payload write has finished being placed.

**When it is not available.** The `shm` provider does not advertise `FI_ORDER_WAW`, so the benchmark skips this mode there rather than reporting a number that depends on luck.

## 4. Remote-write counter

**How.** The target binds a libfabric counter (`fi_cntr`) to remote writes (`FI_RMA_EVENT` / `FI_REMOTE_WRITE`). Each completed incoming write increments it. The target waits until the counter reaches the expected value.

**Why it is correct.** The counter is incremented as the write's completion event at the target, so after placement (Fact 3).

**Trade-off.** One integer instead of a CQ entry per write, but the target learns only *how many* writes arrived, not *which* ones; the protocol has to make that unambiguous (for example, one counter per channel and in-order use). This is the libfabric equivalent of fabric-lib's `ImmCounter`.

**Observed.** The `tcp` provider advertised `FI_RMA_EVENT` but did not increment an endpoint-bound counter, and `fi_mr_enable` on an `FI_RMA_EVENT` memory region returned `-FI_ENOSYS`. The benchmark probes one write each way before trusting a counter.

## 5. Write, then an 8-byte read

**How.** After the payload write, the **initiator** posts a small RDMA read from the target on the same QP and waits for it to complete.

**Why it is correct.** By Fact 1, the target executes the read after the write. A read's response carries the target's memory contents at the time it is executed, so it cannot be answered until the earlier write has been executed. When the initiator sees the read complete, the write has been placed at the target. This is the "flush" IBM Storage Scale made its default (`verbsRdmaWriteFlush = rdma-read`) after write-flush defects (APARs IJ44524/IJ44525).

**What it tells whom.** It tells the *initiator* the data is placed (useful before telling a third party "go read it"). The target still needs one of the other mechanisms if it must react. Cost: one extra round trip.

## Summary

| mechanism | relies on | target work | caveat |
|---|---|---|---|
| CQ data | completion after placement | poll/wait a CQ, post receives | receive queue management |
| flag | NIC places the last bytes last | spin on memory | not guaranteed for multi-packet messages |
| sentinel | in-order execution + `FI_ORDER_WAW` | spin on memory | provider must advertise WAW |
| counter | counter bumped at completion | read one integer | counts only; tcp did not count |
| write + read | in-order execution on RC | none (initiator learns) | extra round trip |

## What E5 measures

For each mechanism, p50 and p99 one-way latency for 8 B to 64 KiB, and user-space instructions retired per post (`perf_event`), following Papadopoulou, Oden and Balaji's per-operation accounting. Rule: adopt a mechanism only if it moves p99.

## References

- InfiniBand Trade Association, *InfiniBand Architecture Specification Vol. 1* (RC ordering and write-with-immediate semantics).
- libfabric `fi_endpoint(3)` (`FI_ORDER_WAW`), `fi_cntr(3)`, `fi_rma(3)`.
- N. Papadopoulou, L. Oden, P. Balaji, "A Performance Study of UCX over InfiniBand," CCGrid 2017.
- IBM Spectrum Scale alert for APARs IJ44524/IJ44525 (RDMA write flush).
- N. Licker et al., "fabric-lib: RDMA Point-to-Point Communication for LLM Systems," arXiv:2510.27656.
