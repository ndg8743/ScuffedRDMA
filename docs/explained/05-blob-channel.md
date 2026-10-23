# 5. FabricBlobChannel: credits and one-sided writes

[← back to the README section](../../README.md#5-fabricblobchannel-credits-and-one-sided-writes)

![FabricBlobChannel](../media/05_blobchannel.gif)

`FabricBlobChannel` turns the pool's one-sided writes into "send this named blob". This page specifies the protocol precisely and proves the properties it depends on:

- a slot is never overwritten while its contents are still in use;
- a staging buffer is never reused while the NIC is still reading it;
- a notification never arrives before its data;
- a blob is reassembled correctly;
- the throughput limit depends on the number of slots, as given by Little's law.

Code: `middleware/fabric/pool.py`, class `FabricBlobChannel` (`send`, `_take_slot`, `_pump`, `_consume`). Tests: `tests/test_fabric_pool.py`.

---

## 1. Layout

Each side registers one memory region, split as follows ($`N`$ slots of $`B`$ bytes, defaults $`N = 8`$, $`B = 4`$ MiB):

| range | name | written by |
|---|---|---|
| $`[0, NB)`$ | receive slots $`0..N-1`$ | the **peer**, with one-sided writes |
| $`[NB, 2NB)`$ | staging slots $`0..N-1`$ | this side, before sending from them |
| $`[2NB, \dots)`$ | scratch | source of 8-byte credit writes |

Each slot holds a 64-byte header (magic, blob id, key length, flags, total length, chunk offset, chunk length), then the key, then a chunk of the payload.

## 2. Protocol

**Sender** keeps a queue `free` of slot numbers it may write at the peer, initially $`\{0, \dots, N-1\}`$.

1. Split the blob into chunks of at most $`B - 64 - |\text{key}|`$ bytes.
2. For each chunk: take a slot $`s`$ from `free` (pumping completions until one is available). If staging slot $`s`$ was used before, wait until that earlier write has completed locally.
3. Write header, key and chunk into staging slot $`s`$.
4. Post one `fi_writedata` from staging slot $`s`$ to the peer's receive slot $`s`$, with immediate data `DATA | s`, on the hot or cold endpoint (cold unless the blob is tagged hot).

**Receiver**, on a completion carrying `DATA | s`:

5. Check the magic, read the header, and copy the chunk into the blob's reassembly buffer at `chunk_off`.
6. Post an 8-byte `fi_writedata` on the **hot** endpoint with immediate `CREDIT | s`.
7. When the bytes received for the blob equal `total`, hand the blob to the application.

**Sender**, on a completion carrying `CREDIT | s`: put $`s`$ back in `free`.

## 3. Safety: a receive slot is never overwritten while in use

**Invariant.** For each slot $`s`$, exactly one of these holds at any time:

- (A) $`s`$ is in the sender's `free` queue;
- (B) a data write to $`s`$ is in flight, or has landed and is not yet consumed (steps 4–5);
- (C) the receiver has consumed $`s`$ and the credit for $`s`$ is in flight (step 6).

**Proof by induction over protocol steps.**

- **Initially** all slots are in `free`: (A) holds for every $`s`$.
- **Sender takes $`s`$ and posts a write (steps 2–4).** $`s`$ leaves `free` (A) and a write to it is in flight (B). The sender only takes slots from `free`, so it never writes a slot that is in (B) or (C).
- **Receiver consumes $`s`$ and posts the credit (steps 5–6).** The credit is posted *after* the copy finishes (in `_consume` the copy into the reassembly buffer precedes `p.write(... CREDIT | s)`). So $`s`$ moves from (B) to (C) only when its contents are no longer needed.
- **Credit arrives (sender).** $`s`$ moves from (C) back to (A).

Every step moves $`s`$ along A → B → C → A and no step adds a second state, so the invariant holds. A write to $`s`$ happens only from (A), at which point the previous contents of receive slot $`s`$ were already consumed. $`\square`$

## 4. Safety: a staging buffer is never reused too early

A one-sided write reads its source buffer after it is posted. If the sender overwrote staging slot $`s`$ before the NIC finished reading it, the peer could receive a mix of two chunks.

**Claim.** Staging slot $`s`$ is not rewritten until the previous write from it has completed locally.

**Proof.** When the sender posts from staging slot $`s`$ it records `(endpoint, posted count)` in `_staged_at[s]`. Before reusing $`s`$, `_take_slot` checks whether the endpoint's completed-operation count has reached that number and, if not, waits (`wait_tx`). Completions on one endpoint are counted in order, so reaching the count means that write has completed, and a completed write no longer reads its source. Small writes are posted with `FI_INJECT`, which copies the payload at post time, so their source is free immediately. $`\square`$

## 5. Safety: the notification never arrives before the data

**Claim.** When the receiver sees `DATA | s`, the full chunk is already in receive slot $`s`$.

**Argument.** Data and notification are **one operation** (`fi_writedata`, which is RDMA write-with-immediate on verbs). The target-side completion carrying the immediate is generated only after the write's data has been placed in target memory. That is the defined semantics of write-with-immediate in the InfiniBand architecture, and of remote CQ data in libfabric (`fi_rma(3)`: the completion is reported after the data is available). There is no second message that could overtake the first. $`\square`$

Contrast: sending the data with one write and a separate "done" message on another endpoint would need an ordering guarantee between endpoints, which does not exist.

## 6. Reassembly is correct

**Claim.** A blob is delivered exactly when all its chunks have arrived, and its bytes are correct.

**Proof.** The sender cuts $`[0, \text{total})`$ into consecutive, disjoint intervals: `off` starts at 0 and advances by `clen` after each chunk until it reaches `total`. Each chunk's header carries its `off` and `clen`, and the receiver copies it to exactly that range, so arrival order does not matter. The transport is reliable (no duplicates, no loss), so each interval arrives exactly once. The received byte count therefore equals `total` exactly when every interval has arrived, which is the delivery condition. $`\square`$

## 7. Throughput is limited by the number of slots

Let $`R`$ be the credit round trip: the time from posting a chunk until its credit is back in `free` (wire time + receiver copy + credit write). At most $`N`$ chunks of up to $`B`$ bytes are outstanding. By **Little's law** (average number in system = arrival rate × average time in system), throughput $`X`$ satisfies

```math
N \ge X \cdot \frac{R}{B} \quad\Longrightarrow\quad X \le \frac{N B}{R}.
```

To run at link rate $`C`$ the window must cover the bandwidth-delay product: $`N B \ge C \cdot R`$. With the defaults ($`N = 8`$, $`B = 4`$ MiB, so 32 MiB in flight) and a 10 Gb/s link, this holds for any $`R`$ up to about 27 ms, far above a realistic credit round trip. On a 100 Gb/s link the limit is about 2.7 ms, still comfortable.

## 8. Why credits ride the hot endpoint

A credit is 8 bytes and gates the sender's next chunk. If credits shared the cold endpoint, each credit would wait behind queued bulk writes from receiver to sender (README section 2), and the sender would sit idle with work to do. On the hot endpoint they have no bulk ahead of them.

## 9. Status

| Claim | Status |
|---|---|
| Receive slots never overwritten in use | proven (invariant) |
| Staging buffers not reused early | proven from the completion-count check |
| Notification after data | follows from write-with-immediate semantics |
| Correct reassembly | proven |
| Throughput ≤ $`NB/R`$ | Little's law; the actual $`R`$ is measured by `benchmarks/fabric/blob_bench.py` (E6) |

## References

1. InfiniBand Trade Association. *InfiniBand Architecture Specification, Volume 1* (RDMA Write with Immediate: the target completion is generated after the data is placed). [infinibandta.org](https://www.infinibandta.org/ibta-specification/). *Used for: §5.*
2. OpenFabrics Interfaces Working Group. `fi_rma(3)` (`fi_writedata`, remote CQ data) and `fi_cq(3)`. [ofiwg.github.io/libfabric](https://ofiwg.github.io/libfabric/). *Used for: §2 and §5.*
3. J. D. C. Little. "A Proof for the Queuing Formula: L = λW." *Operations Research* 9(3):383–387, 1961. [doi:10.1287/opre.9.3.383](https://doi.org/10.1287/opre.9.3.383). *Used for: the throughput bound (§7).*
4. V. Jacobson. "Congestion Avoidance and Control." *Proc. ACM SIGCOMM*, 1988. [doi:10.1145/52324.52356](https://doi.org/10.1145/52324.52356). *Used for: the window must cover the bandwidth-delay product (§7).*
5. `middleware/fabric/pool.py` (`FabricBlobChannel`: `send`, `_take_slot`, `_pump`, `_consume`) and `tests/test_fabric_pool.py`. *The implementation the invariants are checked against.*
