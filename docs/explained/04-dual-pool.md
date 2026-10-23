# 4. The dual pool on libfabric

[← back to the README section](../../README.md#4-the-dual-pool-on-libfabric)

![Dual pool on libfabric](../media/04_dualpool.gif)

The dual pool is the mechanism that keeps hot and cold traffic in separate queues. This page explains each design choice and the argument behind it, and why the same benchmark runs on two libraries.

Code: `middleware/libscuffedfabric/` (`scuffed_fabric.h`, `scuffed_fabric.c`, `sf_bench.c`), `middleware/libscuffedverbs/scuffed_verbs.c`.

---

## 1. Vocabulary

- **Endpoint** (libfabric) / **queue pair, QP** (verbs): the object you post send and write requests to. Requests posted to one endpoint are processed in order.
- **Completion queue, CQ**: where the library reports that a posted request finished.
- **Counter, `fi_cntr`**: a lighter alternative to a CQ that only counts completions.
- **Provider**: the libfabric back end that talks to the hardware: `verbs` (RDMA NICs and SoftRoCE), `tcp`, `shm` (same machine).
- **MSG endpoint**: connected, one per peer, like a TCP socket. **RDM endpoint**: reliable but unconnected, addressed per message, like UDP with reliability.

## 2. One endpoint per class

The pool opens two endpoints, hot and cold, each with its own transmit queue and completion objects. Section 2 of the README proves why: in one FIFO queue every message waits for the sum of everything in front of it, so a hot message behind bulk inherits bulk latency. With a hot endpoint, nothing bulk is ever in front of a hot message in its own queue.

## 3. Separate completion queues, and why it matters

**Claim.** With a shared CQ, the time to notice a hot completion grows with the number of cold completions ahead of it; with separate CQs it does not.

**Argument.** A CQ is read in order. If $k$ cold completions are queued before a hot one, the poller must read and dispatch $k$ entries before it sees the hot one, costing $k \cdot c_{\text{poll}}$ extra (with $c_{\text{poll}}$ the per-entry read-and-dispatch cost). With a dedicated hot CQ, the poller's next read is the hot completion, independent of $k$. The cold CQ can be drained by a different thread at its own pace. $\square$

## 4. Different completion styles for different goals

| | hot | cold |
|---|---|---|
| goal | lowest latency per message | throughput with little CPU |
| transmit queue depth | 64 | 512 |
| completion | busy-polled CQ, or `fi_cntr` with `FI_SELECTIVE_COMPLETION` | CQ with a wait object (`FI_WAIT_UNSPEC`), read with `fi_cq_sread` |
| small payloads | `FI_INJECT` (copied at post time, no completion needed for buffer reuse) | n/a |

**Why busy-poll for hot.** A thread that sleeps until the kernel wakes it pays the wake-up latency (typically microseconds) on every message. A spinning thread notices a completion within one poll iteration (tens of nanoseconds), at the cost of one CPU core. For the few, latency-critical hot messages that trade is worth it.

**Why a wait object for cold.** Cold transfers take hundreds of microseconds to milliseconds each. A wake-up of a few microseconds is a small fraction of that, and sleeping frees the core.

**Why selective completion.** With `FI_SELECTIVE_COMPLETION`, only requests posted with `FI_COMPLETION` generate a completion entry. For a burst of hot writes where only the last one matters, that saves one CQ entry per write.

**Why a deeper cold queue.** Bandwidth on a link with round-trip time $R$ requires roughly $C \cdot R$ bytes in flight (the bandwidth-delay product). Bulk writes need many outstanding requests to keep the link busy; hot messages are rarely more than a few at a time.

## 5. Shared resources

Endpoints with the same provider and endpoint type share one fabric, one domain and one memory registration. Registration pins memory and programs the NIC's translation tables, so registering one arena once avoids per-transfer cost (the same reason RDT registers a base tensor once, Update 7).

**Mixed configuration.** Hot on an RDM endpoint (`verbs;ofi_rxm`) and cold on a MSG endpoint (`verbs`) need two domains, so the arena is registered twice. On verbs, `ofi_rxm` runs its own eager/rendezvous protocol over RC connections, which adds a protocol layer to the hot path. Whether that costs more than the RDM endpoint saves is what experiment E4 measures.

## 6. One benchmark, two libraries

`libscuffedverbs` implements the same header (`scuffed_fabric.h`) on raw verbs RC queue pairs. `sv_bench` is the same `sf_bench.c` compiled against it. Payload layout, warm-up, window, clock (`CLOCK_MONOTONIC_RAW`), percentile code and JSON output are identical.

**Why that matters (a controlled comparison).** If two benchmarks differ in both library and harness, a latency difference cannot be attributed to either. Holding the harness fixed makes the library the only variable, so any difference between `sf_bench` and `sv_bench` on the same NIC is the library's software path.

| verbs | libfabric |
|---|---|
| RC QP per class | endpoint per class, `FI_EP_MSG` or `FI_EP_RDM` |
| `RDMA_WRITE_WITH_IMM` | `fi_writedata` with remote CQ data |
| send CQ + completion channel | CQ with a wait object, `fi_cq_sread` |
| (none) | `fi_cntr` counting remote writes (`FI_RMA_EVENT`) |
| QPN / PSN / GID exchanged over TCP | passive endpoint (MSG) or address vector insert (RDM) |

## 7. Provider behavior found while building

From libfabric 1.17's `tcp`, `tcp;ofi_rxm` and `shm` providers (Update 8, Section 4):

- `tcp` needs the target to read its CQ even though it advertises automatic progress; without it a 1 MB write stream stalled after about three writes.
- Remote-write counters are not uniform: `tcp` advertised `FI_RMA_EVENT` but did not count; `ofi_rxm` does not offer it; `shm` counts through the endpoint. The benchmark probes a counter before trusting it.
- Connection-request info dropped `FI_RMA_EVENT` on the passive side; the library copies it back.
- `ofi_rxm` connects on first use, so the first write spins until the target makes progress; posting is bounded at 60 s so an idle peer becomes an error, not a hang.
- `shm` does not advertise write-after-write ordering, so the sentinel signaling method is skipped there.
- With a single endpoint the target cannot tell classes apart, which is exactly the coupling the dual pool removes.

## 8. Status

| Claim | Status |
|---|---|
| No bulk ahead of hot in its own queue | by construction |
| Separate CQs remove completion-dispatch coupling | argued above |
| Busy-poll vs wait-object latency/CPU trade | standard; per-stack numbers come from E1/E2 |
| libfabric vs verbs difference is the library | by harness design; measured in E1–E4 |
| Provider behaviors | observed on libfabric 1.17 in a container; verbs provider is a cluster run |

## References

- P. Grun et al., "A Brief Introduction to the OpenFabrics Interfaces," HotI 2015.
- libfabric man pages: `fi_endpoint(3)`, `fi_cq(3)`, `fi_cntr(3)`, `fi_mr(3)`, `fi_rxm(7)`, `fi_verbs(7)`: https://ofiwg.github.io/libfabric/
