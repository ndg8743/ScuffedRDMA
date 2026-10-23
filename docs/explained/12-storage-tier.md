# 12. NVMe storage tier

[← back to the README section](../../README.md#12-nvme-storage-tier)

![NVMe storage tier](../media/12_storage.gif)

The storage tier holds KV blocks that do not fit in GPU memory. This page specifies how it lays data out on disk and proves:

- the layout satisfies `O_DIRECT`'s alignment rules;
- the free list never double-allocates space;
- a corrupted block is detected (with a stated probability).

It also fits a simple cost model to the measured coalescing sweep and says plainly which part of the data the model explains and which it does not.

Code: `middleware/rdma_tensor_cache/storage_tier.py`. Tests: `tests/test_storage_tier.py`. Notebook 07.

---

## 1. API

| call | does |
|---|---|
| `spill(key, buf)` | queues the block, returns a future that completes when it is durable |
| `retrieve(key)` | `pread`, checks the CRC32, returns the bytes |
| `retrieve_batch(keys)` | contiguous keys read with one `pread` |
| `delete(key)` | returns the block's space to the free list |
| `flush()` | writes a partial batch now |
| `spill_if(decision, key, buf)` | spills only when the policy or controller decided "spill" |

Every `coalesce` queued blocks are written with **one** `pwrite` into a single backing file, followed by one `fdatasync`.

## 2. Alignment: why `O_DIRECT` accepts every write

`O_DIRECT` bypasses the page cache and requires the file offset, the length and the memory address to be multiples of the device's logical block size (512 B or 4 KiB). The tier uses $`a = 4096`$.

**Claim.** Every write the tier issues satisfies all three.

**Proof.**

- **Lengths.** Each block's slot is $`\lceil \text{len}/a\rceil \cdot a`$ bytes (`_round_up`), a multiple of $`a`$; a batch is a sum of such slots, also a multiple of $`a`$.
- **Offsets.** By induction: the file end starts at 0. The allocator returns either the current end (a multiple of $`a`$, then advances it by a multiple of $`a`$) or the start of a free extent. Free extents are created from previously allocated ranges, whose offsets and sizes are multiples of $`a`$, and splitting or merging multiples of $`a`$ gives multiples of $`a`$.
- **Memory.** Buffers are staged through `mmap` memory, which is page-aligned (4096 B). $`\square`$

If the filesystem rejects `O_DIRECT` (tmpfs, some overlay filesystems), the tier falls back to buffered I/O and records why in `o_direct_reason`, so results from the two modes are never mixed silently.

## 3. The free list never hands out the same space twice

The free list is a list of `(offset, size)` extents.

**Invariant.**

- (I1) Extents in the free list are pairwise disjoint.
- (I2) No free extent overlaps an allocated block.
- (I3) After compaction, extents are sorted and no two are adjacent; a free extent touching the end of the file is removed by shrinking the file end.

**Allocation (first fit).** Scan for the first extent with size ≥ need. If equal, remove it; otherwise shrink it from the front by `need` and return its old offset. If none fits, return the file end and advance it.

- I1 is preserved: shrinking an extent cannot make it overlap another.
- I2 is preserved: the returned range came from free space (or beyond the old end), and is removed from the free list.

**Release.** Add `(offset, alloc)` back, sort, merge neighbours whose `offset + size` equals the next `offset`, and drop a trailing extent at the file end.

- I1 is preserved because the released range was allocated, so by I2 it overlapped no free extent.
- I3 holds by construction of the merge.

Together: every allocated range is disjoint from every other allocated range and from all free space, so no two blocks share bytes. $`\square`$

Merging matters for reuse: two adjacent freed 4 KiB slots become one 8 KiB extent, which can hold a block that neither could alone (the "merged free extent" in the animation).

## 4. Corruption is detected

Each block is stored with its CRC32. `retrieve` recomputes it and raises on mismatch.

- CRC32 detects **every** error of 1 or 2 bits, every error with an odd number of flipped bits, and every burst error of length ≤ 32 bits. These follow from the generator polynomial's degree (32), its nonzero constant term, and its factor $`(x+1)`$.
- For corruption that looks random, the chance that a corrupted block still matches is $`2^{-32} \approx 2.3\times10^{-10}`$.

So a torn or misdirected write is caught before stale bytes reach the GPU.

## 5. A cost model for coalescing, checked against the data

**Model.** Writing a batch of $`n`$ blocks of $`B`$ bytes costs a fixed part $`a`$ (system call, `fdatasync`, device flush) plus a per-block part $`b`$ (moving $`B`$ bytes):

```math
t(n) = a + n\,b, \qquad \text{throughput}(n) = \frac{nB}{a + nb} \;\xrightarrow{n\to\infty}\; \frac{B}{b}.
```

Throughput increases with $`n`$ (its derivative is $`aB/(a+nb)^2 > 0`$) and saturates at $`B/b`$. So batching helps exactly as much as the fixed cost is large relative to one block's transfer.

**Fit to the measured sweep** (server 2's NVMe, $`B`$ = 1,568 KiB; `benchmarks/results/test_arch/chimera_storage_spill.json`). Least squares on the four write times gives $`a \approx 1.6`$ ms, $`b \approx 1.91`$ ms per block, asymptote $`B/b \approx 839`$ MB/s.

| coalesce $`n`$ | measured write MB/s | model MB/s |
|---|---|---|
| 1 | 662 | 457 |
| 10 | 731 | 774 |
| 20 | 803 | 805 |
| 50 | 827 | 825 |

**What this shows.** The model matches the large batches and the asymptote, so the drive's sustained write rate is about 830–840 MB/s for these blocks, and batching gains about 25% over single writes. It does **not** match $`n = 1`$: a single write was faster than a constant fixed cost predicts. So the fixed cost is not constant across batch sizes (one plausible reason: the device's write cache absorbs a single 1.5 MiB write before the flush). Four points cannot separate those effects; the notebook 07 sweep through `StorageTier` should add more batch sizes and repeats.

**Reads.** Read throughput rises to about 2.19 GB/s at 20 blocks and drops to 1.10 GB/s at 50. The model above cannot produce a drop. The benchmark wrote to a temporary directory and did not record whether it was NVMe or tmpfs, or what the page cache held, so the cause is unknown. The honest conclusion is "the batch size is a tuning knob, not bigger-is-better", not a mechanism.

## 6. Status

| Claim | Status |
|---|---|
| `O_DIRECT` alignment always satisfied | proven |
| No double allocation | proven (invariant) |
| Corruption detection | CRC32 properties; probability for random corruption |
| Write throughput saturates near 830–840 MB/s | measured + model fit |
| Single-write and read-drop behavior | not explained; needs more measurements |

## References

1. Linux man-pages. `open(2)` (the `O_DIRECT` alignment rules) and `fsync(2)` (`fdatasync`). [man7.org/open.2](https://man7.org/linux/man-pages/man2/open.2.html), [man7.org/fsync.2](https://man7.org/linux/man-pages/man2/fsync.2.html). *Used for: §2 and the batch cost in §5.*
2. D. E. Knuth. *The Art of Computer Programming, Vol. 1: Fundamental Algorithms*, 3rd ed. Addison-Wesley, 1997, §2.5 (dynamic storage allocation: first fit, coalescing free blocks). *Used for: §3.*
3. W. W. Peterson, D. T. Brown. "Cyclic Codes for Error Detection." *Proceedings of the IRE* 49(1):228–235, 1961. *Used for: what a CRC is guaranteed to detect (§4).*
4. P. Koopman. "32-Bit Cyclic Redundancy Codes for Internet Applications." *Proc. International Conference on Dependable Systems and Networks (DSN)*, 2002. [CMU](https://kilthub.cmu.edu/articles/journal_contribution/32-Bit_Cyclic_Redundancy_Codes_for_Internet_Applications/6620594). *Used for: CRC-32 error-detection properties (§4).*
5. `benchmarks/results/test_arch/chimera_storage_spill.json` (the measured sweep in §5), Update 6 (`Updates/Update6-StorageTier/`), `middleware/rdma_tensor_cache/storage_tier.py`, `tests/test_storage_tier.py`.
