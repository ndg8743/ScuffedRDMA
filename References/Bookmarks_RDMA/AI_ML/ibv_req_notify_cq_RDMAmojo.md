# ibv_req_notify_cq() « RDMAmojo

- **Source:** https://www.rdmamojo.com/2013/02/22/ibv_req_notify_cq/
- **Author:** Dotan Barak (2013, updated 2016)
- **Bookmarked:** Chrome, Bookmarks bar > RDMA > AI & ML
- **Retrieved:** 2026-10-22 via browser; notes below, read the source for the full man-page text.

---

Notes relevant to the hot/cold CQ split:
- `ibv_req_notify_cq(cq, solicited_only)` arms a CQ so the *next* completion of the requested type raises an event read with `ibv_get_cq_event()`. Completions already in the CQ when you arm it do not fire an event, so the standard loop is arm, then poll-drain, then sleep.
- `solicited_only=0`: any completion fires. Non-zero: only solicited receives (sender set `IBV_SEND_SOLICITED` on a Send or Write-with-Imm) or any error completion.
- Arming is one-shot: you must re-arm after each notification. There is no "notify after N completions" and no auto-rearm.
- Multiple arms before an event collapse to one notification; a "next completion" arm overrides a "solicited only" arm on the same CQ.
- Rationale given: event mode trades latency for CPU, since the thread sleeps until a WC arrives. This is the cold-path (event-driven CQ) half of the dual QP pool; the hot path busy-polls with `ibv_poll_cq()`.
