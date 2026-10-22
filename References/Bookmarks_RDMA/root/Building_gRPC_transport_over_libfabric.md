# Building gRPC transport over libfabric

- **Source:** https://groups.google.com/g/grpc-io/c/TRXfV-_X5ms
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA)
- **Retrieved:** 2026-10-22


---

You do not have permission to delete messages in this group

Copy link

Report message

Show original message

Either email addresses are anonymous for this group or you need the view member email addresses permission to view the original message

to grpc.io

Hello,

We
are experimenting with a different solution to implement the gRPC transport
using libfabric (OpenFabric https://ofiwg.github.io/libfabric). The solution
will allow gRPC apps to take advantage of high-speed network devices to speed
up data transfer, if available. Otherwise, it will fall back to the libfabric default provider (i.e.,
default network stack.) Our experiment shows > 50% latency
reduction for a simple request-response benchmark over a libfabric verbs
provider. Is there any design guidance or rule on plugging in such
a customized solution? What will be a better way to hook our solution into the
gRPC framework?