# Which Queue Pair type to use? « RDMAmojo

- **Source:** https://www.rdmamojo.com/2013/06/01/which-queue-pair-type-to-use/
- **Author:** Dotan Barak (2013, updated 2019)
- **Bookmarked:** Chrome, Bookmarks bar > RDMA > AI & ML
- **Retrieved:** 2026-10-22 via browser; notes below, read the source for full text.

---

| | UD | UC | RC |
|---|---|---|---|
| Send (± imm) | yes | yes | yes |
| RDMA Write (± imm) | no | yes | yes |
| RDMA Read / Atomics | no | no | yes |
| Reliability | no | no | yes (PSN + ACK + retry) |
| Connection | one-to-any, multicast | one-to-one | one-to-one |
| Max message | path MTU | 2 GB | 2 GB |

Notes:
- All types CRC-check packets; "reliable" refers to whole-message delivery (at most once, in order).
- RC requester completes on the responder's ACK; UC/UD requester completes once bytes hit the wire. This is why RC completion latency includes a round trip, relevant when comparing CQ completion against flag-in-payload signaling.
- Guidance: RC for fabric-level reliability at modest scale (file systems over RDMA); UC when the app handles reliability and messages exceed MTU; UD for all-to-all scale and multicast.
- Both QP pools in libscuffedrdma are RC because WRITE_WITH_IMM and RDMA_WRITE with reliable delivery are required; UD would only fit a control channel.
