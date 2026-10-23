/*
 * libscuffedverbs: the same API as libscuffedfabric (scuffed_fabric.h),
 * implemented directly on libibverbs RC queue pairs. sv_bench is sf_bench.c
 * linked against this file, so the libfabric and native verbs numbers come
 * from identical benchmark code, payloads and timing.
 *
 * Mapping
 *   class endpoint      one RC QP per class (single_ep: one QP for both)
 *   shared domain       one PD and one MR for both QPs (the dual QP pool)
 *   TX CQ / RX CQ       one send CQ and one recv CQ per QP
 *   cold_wait           cold send CQ gets a completion channel
 *                       (ibv_req_notify_cq + ibv_get_cq_event)
 *   remote CQ data      RDMA_WRITE_WITH_IMM, 32-bit immediate
 *   hot counters,
 *   FI_RMA_EVENT        not in verbs: sf_capable() reports 0, benches skip
 *
 * Every completion's wc.status is checked. A failed or flushed work request
 * is an error, never a fast completion.
 *
 * Environment
 *   SV_IB_PORT      HCA port (default 1)
 *   SV_GID_INDEX    GID index (default: first IPv4-mapped GID, i.e. RoCEv2 over IPv4)
 *   SV_MTU          256..4096 (default: port active_mtu)
 *   SV_INLINE       max_inline_data request for the hot QP (default 64)
 */
#define _GNU_SOURCE
#include "../libscuffedfabric/scuffed_fabric.h"

#include <arpa/inet.h>
#include <errno.h>
#include <infiniband/verbs.h>
#include <netdb.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <poll.h>
#include <stdarg.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>

#define SV_MAGIC 0x53435642u /* 'SCVB' */
#define TX_TAG(cls) ((uint64_t)(0x10 + (cls)))
#define RX_TAG(cls, slot) ((uint64_t)0x40000000u | ((uint64_t)(cls) << 24) | (uint64_t)(slot))
#define IS_RX_TAG(t) ((((t)) & 0xC0000000u) == 0x40000000u)
#define RX_TAG_CLS(t) ((int)(((t) >> 24) & 0x3f))
#define RX_TAG_SLOT(t) ((size_t)((t) & 0xffffffu))

typedef struct sv_qp {
    int cls;
    struct ibv_qp *qp;
    struct ibv_cq *scq, *rcq;
    struct ibv_comp_channel *ch;
    int wait;
    uint32_t psn;
    uint32_t max_inline;
    size_t rx_slots, rx_base, rx_slot_bytes;
    uint32_t rqpn, rpsn;
    union ibv_gid rgid;
    uint16_t rlid;
    uint64_t rbase;
    uint32_t rkey;
    char desc[384];
} sv_qp_t;

struct sf_ctx {
    sf_opts_t o;
    char *arena;
    size_t arena_len, data_len;
    struct ibv_context *ctx;
    struct ibv_pd *pd;
    struct ibv_mr *mr;
    struct ibv_port_attr port;
    int ib_port, gid_idx;
    union ibv_gid gid;
    enum ibv_mtu mtu;
    sv_qp_t *q[SF_NCLASS];
    int oob, server;
    _Atomic uint64_t posted[SF_NCLASS];
    _Atomic uint64_t done[SF_NCLASS];
};

struct sv_wire {
    uint32_t magic, single;
    uint64_t base;
    uint32_t rkey;
    uint16_t lid;
    uint8_t gid[16];
    uint32_t qpn[SF_NCLASS], psn[SF_NCLASS];
};

static __thread char g_err[512];
static void seterr(const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(g_err, sizeof g_err, fmt, ap);
    va_end(ap);
}
const char *sf_strerror(int err) { return g_err[0] ? g_err : strerror(err < 0 ? -err : err); }

uint64_t sf_now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC_RAW, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
}

void sf_opts_default(sf_opts_t *o) {
    memset(o, 0, sizeof *o);
    o->ep_type[SF_HOT] = o->ep_type[SF_COLD] = SF_EP_MSG;
    o->arena_bytes = 64ull << 20;
    o->tx_depth[SF_HOT] = 64;
    o->tx_depth[SF_COLD] = 512;
    o->rx_depth[SF_HOT] = 256;
    o->rx_depth[SF_COLD] = 64;
    o->rx_slot_bytes = 4096;
}

static int envint(const char *k, int d) {
    const char *v = getenv(k);
    return v && *v ? atoi(v) : d;
}

/* ------------------------------------------------------------------ OOB */

static int sendall(int fd, const void *p, size_t n) {
    const char *c = p;
    while (n) {
        ssize_t w = send(fd, c, n, MSG_NOSIGNAL);
        if (w < 0) { if (errno == EINTR) continue; return -errno; }
        c += w; n -= (size_t)w;
    }
    return 0;
}
static int recvall(int fd, void *p, size_t n) {
    char *c = p;
    while (n) {
        ssize_t r = recv(fd, c, n, 0);
        if (r == 0) return -ECONNRESET;
        if (r < 0) { if (errno == EINTR) continue; return -errno; }
        c += r; n -= (size_t)r;
    }
    return 0;
}
int sf_oob_fd(sf_ctx_t *c) { return c->oob; }
int sf_oob_barrier(sf_ctx_t *c) {
    char b = 'b', r;
    int ret = sendall(c->oob, &b, 1);
    return ret ? ret : recvall(c->oob, &r, 1);
}
int sf_oob_xchg(sf_ctx_t *c, uint64_t mine, uint64_t *theirs) {
    int ret = sendall(c->oob, &mine, sizeof mine);
    return ret ? ret : recvall(c->oob, theirs, sizeof *theirs);
}

/* --------------------------------------------------------------- setup */

static int pick_gid(sf_ctx_t *c) {
    int want = envint("SV_GID_INDEX", -1);
    if (want >= 0) {
        c->gid_idx = want;
        if (ibv_query_gid(c->ctx, (uint8_t)c->ib_port, want, &c->gid)) { seterr("ibv_query_gid(%d) failed", want); return -EINVAL; }
        return 0;
    }
    for (int i = 0; i < c->port.gid_tbl_len; i++) {
        union ibv_gid g;
        if (ibv_query_gid(c->ctx, (uint8_t)c->ib_port, i, &g)) continue;
        const uint8_t *r = g.raw;
        int v4 = 1;
        for (int k = 0; k < 10; k++) v4 &= r[k] == 0;
        v4 &= r[10] == 0xff && r[11] == 0xff;
        if (v4) { c->gid_idx = i; c->gid = g; return 0; }
    }
    /* InfiniBand or IPv6-only RoCE: fall back to index 0 */
    c->gid_idx = 0;
    return ibv_query_gid(c->ctx, (uint8_t)c->ib_port, 0, &c->gid) ? -EINVAL : 0;
}

static int open_device(sf_ctx_t *c) {
    int n = 0;
    struct ibv_device **list = ibv_get_device_list(&n);
    if (!list || !n) { seterr("no RDMA devices (load rdma_rxe and add rxe0, or check MOFED)"); return -ENODEV; }
    struct ibv_device *dev = NULL;
    for (int i = 0; i < n; i++)
        if (!c->o.domain || !strcmp(ibv_get_device_name(list[i]), c->o.domain)) { dev = list[i]; break; }
    if (!dev) { seterr("RDMA device %s not found", c->o.domain); ibv_free_device_list(list); return -ENODEV; }
    c->ctx = ibv_open_device(dev);
    ibv_free_device_list(list);
    if (!c->ctx) { seterr("ibv_open_device failed"); return -EIO; }
    c->ib_port = envint("SV_IB_PORT", 1);
    if (ibv_query_port(c->ctx, (uint8_t)c->ib_port, &c->port)) { seterr("ibv_query_port failed"); return -EIO; }
    if (c->port.state != IBV_PORT_ACTIVE) { seterr("port %d not ACTIVE", c->ib_port); return -ENETDOWN; }
    int mtu = envint("SV_MTU", 0);
    c->mtu = mtu == 256 ? IBV_MTU_256 : mtu == 512 ? IBV_MTU_512 : mtu == 1024 ? IBV_MTU_1024
           : mtu == 2048 ? IBV_MTU_2048 : mtu == 4096 ? IBV_MTU_4096 : c->port.active_mtu;
    int r = pick_gid(c);
    if (r) return r;
    c->pd = ibv_alloc_pd(c->ctx);
    if (!c->pd) { seterr("ibv_alloc_pd failed"); return -EIO; }
    c->mr = ibv_reg_mr(c->pd, c->arena, c->arena_len,
                       IBV_ACCESS_LOCAL_WRITE | IBV_ACCESS_REMOTE_WRITE | IBV_ACCESS_REMOTE_READ);
    if (!c->mr) { seterr("ibv_reg_mr(%zu) failed: %s", c->arena_len, strerror(errno)); return -errno; }
    return 0;
}

static int post_rx(sf_ctx_t *c, sv_qp_t *q, size_t slot) {
    struct ibv_sge sge = {.addr = (uint64_t)(uintptr_t)(c->arena + q->rx_base + slot * q->rx_slot_bytes),
                          .length = (uint32_t)q->rx_slot_bytes, .lkey = c->mr->lkey};
    struct ibv_recv_wr wr = {.wr_id = RX_TAG(q->cls, slot), .sg_list = &sge, .num_sge = 1}, *bad;
    int r = ibv_post_recv(q->qp, &wr, &bad);
    if (r) seterr("ibv_post_recv: %s", strerror(r));
    return -r;
}

static int create_qp(sf_ctx_t *c, sv_qp_t *q) {
    int cls = q->cls;
    if (cls == SF_COLD && c->o.cold_wait && !c->o.single_ep) {
        q->ch = ibv_create_comp_channel(c->ctx);
        q->wait = q->ch != NULL;
    }
    q->scq = ibv_create_cq(c->ctx, (int)(c->o.tx_depth[cls] * 2 + 64), NULL, q->ch, 0);
    q->rcq = ibv_create_cq(c->ctx, (int)(c->o.rx_depth[cls] * 2 + 64), NULL, NULL, 0);
    if (!q->scq || !q->rcq) { seterr("ibv_create_cq failed"); return -EIO; }
    if (q->wait && ibv_req_notify_cq(q->scq, 0)) { seterr("ibv_req_notify_cq failed"); return -EIO; }
    uint32_t inl = cls == SF_HOT ? (uint32_t)envint("SV_INLINE", 64) : 0;
    for (;;) {
        struct ibv_qp_init_attr ia = {.send_cq = q->scq, .recv_cq = q->rcq, .qp_type = IBV_QPT_RC,
                                      .cap = {.max_send_wr = (uint32_t)c->o.tx_depth[cls],
                                              .max_recv_wr = (uint32_t)c->o.rx_depth[cls],
                                              .max_send_sge = 1, .max_recv_sge = 1, .max_inline_data = inl}};
        q->qp = ibv_create_qp(c->pd, &ia);
        if (q->qp) { q->max_inline = ia.cap.max_inline_data; break; }
        if (!inl) { seterr("ibv_create_qp: %s", strerror(errno)); return -errno; }
        inl = 0; /* device refused inline: retry without */
    }
    struct ibv_qp_attr a = {.qp_state = IBV_QPS_INIT, .pkey_index = 0, .port_num = (uint8_t)c->ib_port,
                            .qp_access_flags = IBV_ACCESS_REMOTE_WRITE | IBV_ACCESS_REMOTE_READ | IBV_ACCESS_LOCAL_WRITE};
    int r = ibv_modify_qp(q->qp, &a, IBV_QP_STATE | IBV_QP_PKEY_INDEX | IBV_QP_PORT | IBV_QP_ACCESS_FLAGS);
    if (r) { seterr("QP to INIT: %s", strerror(r)); return -r; }
    q->psn = (uint32_t)(lrand48() & 0xffffff);
    for (size_t s = 0; s < q->rx_slots; s++)
        if ((r = post_rx(c, q, s))) return r;
    return 0;
}

static int connect_qp(sf_ctx_t *c, sv_qp_t *q) {
    struct ibv_qp_attr a = {.qp_state = IBV_QPS_RTR, .path_mtu = c->mtu, .dest_qp_num = q->rqpn, .rq_psn = q->rpsn,
                            .max_dest_rd_atomic = 16, .min_rnr_timer = 12};
    a.ah_attr.is_global = 1;
    a.ah_attr.dlid = q->rlid;
    a.ah_attr.port_num = (uint8_t)c->ib_port;
    a.ah_attr.grh.dgid = q->rgid;
    a.ah_attr.grh.sgid_index = (uint8_t)c->gid_idx;
    a.ah_attr.grh.hop_limit = 64;
    int r = ibv_modify_qp(q->qp, &a, IBV_QP_STATE | IBV_QP_AV | IBV_QP_PATH_MTU | IBV_QP_DEST_QPN | IBV_QP_RQ_PSN |
                                         IBV_QP_MAX_DEST_RD_ATOMIC | IBV_QP_MIN_RNR_TIMER);
    if (r) { seterr("QP to RTR: %s (check SV_GID_INDEX / MTU)", strerror(r)); return -r; }
    struct ibv_qp_attr b = {.qp_state = IBV_QPS_RTS, .timeout = 14, .retry_cnt = 7, .rnr_retry = 7,
                            .sq_psn = q->psn, .max_rd_atomic = 16};
    r = ibv_modify_qp(q->qp, &b, IBV_QP_STATE | IBV_QP_TIMEOUT | IBV_QP_RETRY_CNT | IBV_QP_RNR_RETRY |
                                     IBV_QP_SQ_PSN | IBV_QP_MAX_QP_RD_ATOMIC);
    if (r) { seterr("QP to RTS: %s", strerror(r)); return -r; }
    char g[INET6_ADDRSTRLEN];
    inet_ntop(AF_INET6, c->gid.raw, g, sizeof g);
    snprintf(q->desc, sizeof q->desc,
             "prov=libibverbs ep=rc device=%s port=%d gid_idx=%d gid=%s mtu=%d qpn=%u shared_pd=%d inline=%u "
             "cq_data=4 hot_cntr=0 cold_wait=%d rma_event=0",
             ibv_get_device_name(c->ctx->device), c->ib_port, c->gid_idx, g, 128 << c->mtu, q->qp->qp_num,
             !c->o.single_ep, q->max_inline, q->wait);
    return 0;
}

sf_ctx_t *sf_open(const sf_opts_t *o) {
    sf_ctx_t *c = calloc(1, sizeof *c);
    if (!c) return NULL;
    c->o = *o;
    c->oob = -1;
    size_t pg = 4096, slab = 0;
    c->data_len = (o->arena_bytes + pg - 1) & ~(pg - 1);
    for (int k = 0; k < SF_NCLASS; k++) slab += o->rx_depth[k] * o->rx_slot_bytes;
    c->arena_len = c->data_len + ((slab + pg - 1) & ~(pg - 1));
    c->arena = mmap(NULL, c->arena_len, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (c->arena == MAP_FAILED) { free(c); return NULL; }
    memset(c->arena, 0, c->arena_len);
    srand48((long)sf_now_ns());
    return c;
}

static int setup(sf_ctx_t *c) {
    int r = open_device(c);
    if (r) return r;
    size_t rx_off = c->data_len;
    int nq = c->o.single_ep ? 1 : 2;
    for (int k = 0; k < nq; k++) {
        sv_qp_t *q = calloc(1, sizeof *q);
        q->cls = k;
        q->rx_slots = c->o.rx_depth[k];
        q->rx_slot_bytes = c->o.rx_slot_bytes;
        q->rx_base = rx_off;
        rx_off += q->rx_slots * q->rx_slot_bytes;
        c->q[k] = q;
        if ((r = create_qp(c, q))) return r;
    }
    if (c->o.single_ep) c->q[SF_COLD] = c->q[SF_HOT];
    return 0;
}

static int exchange_and_connect(sf_ctx_t *c) {
    struct sv_wire me = {.magic = SV_MAGIC, .single = (uint32_t)c->o.single_ep, .base = (uint64_t)(uintptr_t)c->arena,
                         .rkey = c->mr->rkey, .lid = c->port.lid}, them;
    memcpy(me.gid, c->gid.raw, 16);
    for (int k = 0; k < SF_NCLASS; k++) { me.qpn[k] = c->q[k]->qp->qp_num; me.psn[k] = c->q[k]->psn; }
    int r = sendall(c->oob, &me, sizeof me);
    if (!r) r = recvall(c->oob, &them, sizeof them);
    if (r) { seterr("oob exchange: %s", strerror(-r)); return r; }
    if (them.magic != SV_MAGIC || them.single != me.single) { seterr("peer mismatch (not sv or single_ep differs)"); return -EINVAL; }
    int nq = c->o.single_ep ? 1 : 2;
    for (int k = 0; k < nq; k++) {
        sv_qp_t *q = c->q[k];
        q->rqpn = them.qpn[k];
        q->rpsn = them.psn[k];
        q->rlid = them.lid;
        memcpy(q->rgid.raw, them.gid, 16);
        q->rbase = them.base;
        q->rkey = them.rkey;
        if ((r = connect_qp(c, q))) return r;
    }
    return sf_oob_barrier(c);
}

int sf_listen(sf_ctx_t *c, const char *addr, int port, int timeout_ms) {
    (void)addr;
    c->server = 1;
    int lfd = socket(AF_INET, SOCK_STREAM, 0), one = 1;
    setsockopt(lfd, SOL_SOCKET, SO_REUSEADDR, &one, sizeof one);
    struct sockaddr_in sa = {.sin_family = AF_INET, .sin_port = htons((uint16_t)port), .sin_addr.s_addr = htonl(INADDR_ANY)};
    if (bind(lfd, (struct sockaddr *)&sa, sizeof sa) || listen(lfd, 1)) { seterr("oob bind: %s", strerror(errno)); close(lfd); return -errno; }
    int r = setup(c);
    if (r) { close(lfd); return r; }
    struct pollfd p = {.fd = lfd, .events = POLLIN};
    if (poll(&p, 1, timeout_ms > 0 ? timeout_ms : -1) <= 0) { seterr("oob accept timed out"); close(lfd); return -ETIMEDOUT; }
    c->oob = accept(lfd, NULL, NULL);
    close(lfd);
    if (c->oob < 0) return -errno;
    setsockopt(c->oob, IPPROTO_TCP, TCP_NODELAY, &one, sizeof one);
    return exchange_and_connect(c);
}

int sf_connect(sf_ctx_t *c, const char *host, int port, int timeout_ms) {
    c->server = 0;
    char svc[16];
    snprintf(svc, sizeof svc, "%d", port);
    struct addrinfo h = {.ai_family = AF_INET, .ai_socktype = SOCK_STREAM}, *ai;
    if (getaddrinfo(host, svc, &h, &ai)) { seterr("resolve %s failed", host); return -EHOSTUNREACH; }
    uint64_t end = sf_now_ns() + (uint64_t)(timeout_ms > 0 ? timeout_ms : 30000) * 1000000ull;
    while (sf_now_ns() < end) {
        c->oob = socket(AF_INET, SOCK_STREAM, 0);
        if (!connect(c->oob, ai->ai_addr, ai->ai_addrlen)) break;
        close(c->oob);
        c->oob = -1;
        usleep(50000);
    }
    freeaddrinfo(ai);
    if (c->oob < 0) { seterr("oob connect timed out"); return -ETIMEDOUT; }
    int one = 1;
    setsockopt(c->oob, IPPROTO_TCP, TCP_NODELAY, &one, sizeof one);
    int r = setup(c);
    return r ? r : exchange_and_connect(c);
}

void sf_close(sf_ctx_t *c) {
    if (!c) return;
    for (int k = 0; k < SF_NCLASS; k++) {
        sv_qp_t *q = c->q[k];
        if (!q || (k == SF_COLD && q == c->q[SF_HOT])) continue;
        if (q->qp) ibv_destroy_qp(q->qp);
        if (q->scq) ibv_destroy_cq(q->scq);
        if (q->rcq) ibv_destroy_cq(q->rcq);
        if (q->ch) ibv_destroy_comp_channel(q->ch);
        free(q);
    }
    if (c->mr) ibv_dereg_mr(c->mr);
    if (c->pd) ibv_dealloc_pd(c->pd);
    if (c->ctx) ibv_close_device(c->ctx);
    if (c->oob >= 0) close(c->oob);
    if (c->arena && c->arena != MAP_FAILED) munmap(c->arena, c->arena_len);
    free(c);
}

/* ------------------------------------------------------------- queries */

void *sf_buf(sf_ctx_t *c) { return c->arena; }
size_t sf_buf_len(sf_ctx_t *c) { return c->data_len; }
size_t sf_inject_size(sf_ctx_t *c, int cls) { return c->q[cls]->max_inline; }
int sf_cq_data_size(sf_ctx_t *c, int cls) { (void)c; (void)cls; return 4; }
const char *sf_describe(sf_ctx_t *c, int cls) { return c->q[cls]->desc; }
int sf_capable(sf_ctx_t *c, int cls, const char *what) {
    if (!strcmp(what, "waw")) return 1;          /* RC orders RDMA writes within a QP */
    if (!strcmp(what, "wait")) return c->q[cls]->wait;
    return 0;                                    /* cntr, rma_event, manual_progress */
}
uint64_t sf_tx_posted(sf_ctx_t *c, int cls) { return atomic_load(&c->posted[cls]); }
uint64_t sf_tx_done(sf_ctx_t *c, int cls) { return atomic_load(&c->done[cls]); }
uint64_t sf_rma_events(sf_ctx_t *c, int cls) { (void)c; (void)cls; return 0; }

/* ----------------------------------------------------------- data path */

static int wc_fail(const struct ibv_wc *wc, const char *where) {
    seterr("%s: wr_id 0x%llx status %s (%d) vendor_err 0x%x", where, (unsigned long long)wc->wr_id,
           ibv_wc_status_str(wc->status), wc->status, wc->vendor_err);
    return -EIO;
}

static int drain_send(sf_ctx_t *c, sv_qp_t *q) {
    struct ibv_wc wc[64];
    int n = ibv_poll_cq(q->scq, 64, wc);
    if (n < 0) { seterr("ibv_poll_cq(send) failed"); return -EIO; }
    for (int i = 0; i < n; i++) {
        if (wc[i].status != IBV_WC_SUCCESS) return wc_fail(&wc[i], "send completion");
        uint64_t t = wc[i].wr_id;
        int k = (t >= 0x10 && t < 0x10 + SF_NCLASS) ? (int)(t - 0x10) : q->cls;
        atomic_fetch_add(&c->done[k], 1);
    }
    return n;
}

int sf_progress(sf_ctx_t *c, int cls) { return drain_send(c, c->q[cls]); }

int sf_wait_tx(sf_ctx_t *c, int cls, uint64_t target, int timeout_ms) {
    sv_qp_t *q = c->q[cls];
    uint64_t deadline = timeout_ms > 0 ? sf_now_ns() + (uint64_t)timeout_ms * 1000000ull : 0;
    while (atomic_load(&c->done[cls]) < target) {
        if (q->wait) {
            int r = drain_send(c, q);
            if (r < 0) return r;
            if (atomic_load(&c->done[cls]) >= target) break;
            struct pollfd p = {.fd = q->ch->fd, .events = POLLIN};
            if (poll(&p, 1, 10) > 0) {
                struct ibv_cq *ev_cq;
                void *ev_ctx;
                if (!ibv_get_cq_event(q->ch, &ev_cq, &ev_ctx)) {
                    ibv_ack_cq_events(ev_cq, 1);
                    ibv_req_notify_cq(ev_cq, 0);
                }
            }
        } else {
            int r = drain_send(c, q);
            if (r < 0) return r;
        }
        if (deadline && sf_now_ns() > deadline) {
            seterr("wait_tx timeout on class %d", cls);
            return -ETIMEDOUT;
        }
    }
    return 0;
}

static int post_send(sf_ctx_t *c, int cls, struct ibv_send_wr *wr) {
    sv_qp_t *q = c->q[cls];
    struct ibv_send_wr *bad;
    for (;;) {
        int r = ibv_post_send(q->qp, wr, &bad);
        if (!r) { atomic_fetch_add(&c->posted[cls], 1); return 0; }
        if (r != ENOMEM) { seterr("ibv_post_send: %s", strerror(r)); return -r; }
        /* send queue full: reap completions and retry */
        int d = drain_send(c, q);
        if (d < 0) return d;
    }
}

int sf_write(sf_ctx_t *c, int cls, size_t loff, size_t len, size_t roff, uint64_t imm, int flags) {
    sv_qp_t *q = c->q[cls];
    if (loff + len > c->data_len || roff + len > c->data_len) { seterr("sf_write out of range"); return -EINVAL; }
    struct ibv_sge sge = {.addr = (uint64_t)(uintptr_t)(c->arena + loff), .length = (uint32_t)len, .lkey = c->mr->lkey};
    struct ibv_send_wr wr = {.wr_id = TX_TAG(cls), .sg_list = &sge, .num_sge = 1,
                             .opcode = (flags & SF_F_IMM) ? IBV_WR_RDMA_WRITE_WITH_IMM : IBV_WR_RDMA_WRITE,
                             .send_flags = IBV_SEND_SIGNALED};
    if ((flags & SF_F_INJECT) && len <= q->max_inline) wr.send_flags |= IBV_SEND_INLINE;
    if (flags & SF_F_IMM) wr.imm_data = htonl((uint32_t)imm);
    wr.wr.rdma.remote_addr = q->rbase + roff;
    wr.wr.rdma.rkey = q->rkey;
    return post_send(c, cls, &wr);
}

int sf_read(sf_ctx_t *c, int cls, size_t loff, size_t len, size_t roff) {
    sv_qp_t *q = c->q[cls];
    if (loff + len > c->data_len || roff + len > c->data_len) { seterr("sf_read out of range"); return -EINVAL; }
    struct ibv_sge sge = {.addr = (uint64_t)(uintptr_t)(c->arena + loff), .length = (uint32_t)len, .lkey = c->mr->lkey};
    struct ibv_send_wr wr = {.wr_id = TX_TAG(cls), .sg_list = &sge, .num_sge = 1, .opcode = IBV_WR_RDMA_READ,
                             .send_flags = IBV_SEND_SIGNALED};
    wr.wr.rdma.remote_addr = q->rbase + roff;
    wr.wr.rdma.rkey = q->rkey;
    return post_send(c, cls, &wr);
}

int sf_send(sf_ctx_t *c, int cls, size_t loff, size_t len, uint64_t imm, int with_imm) {
    sv_qp_t *q = c->q[cls];
    if (len > q->rx_slot_bytes || loff + len > c->data_len) { seterr("sf_send larger than rx slot"); return -EINVAL; }
    struct ibv_sge sge = {.addr = (uint64_t)(uintptr_t)(c->arena + loff), .length = (uint32_t)len, .lkey = c->mr->lkey};
    struct ibv_send_wr wr = {.wr_id = TX_TAG(cls), .sg_list = &sge, .num_sge = 1,
                             .opcode = with_imm ? IBV_WR_SEND_WITH_IMM : IBV_WR_SEND, .send_flags = IBV_SEND_SIGNALED};
    if (len <= q->max_inline) wr.send_flags |= IBV_SEND_INLINE;
    if (with_imm) wr.imm_data = htonl((uint32_t)imm);
    return post_send(c, cls, &wr);
}

int sf_poll_rx(sf_ctx_t *c, int cls, sf_rx_ev_t *ev, int max) {
    sv_qp_t *q = c->q[cls];
    struct ibv_wc wc[64];
    if (max > 64) max = 64;
    int n = ibv_poll_cq(q->rcq, max, wc);
    if (n < 0) { seterr("ibv_poll_cq(recv) failed"); return -EIO; }
    for (int i = 0; i < n; i++) {
        if (wc[i].status != IBV_WC_SUCCESS) return wc_fail(&wc[i], "recv completion");
        uint64_t t = wc[i].wr_id;
        int k = IS_RX_TAG(t) ? RX_TAG_CLS(t) : cls;
        sv_qp_t *sq = c->q[k];
        ev[i].cls = k;
        ev[i].len = wc[i].byte_len;
        ev[i].data = (wc[i].wc_flags & IBV_WC_WITH_IMM) ? ntohl(wc[i].imm_data) : 0;
        if (wc[i].opcode == IBV_WC_RECV_RDMA_WITH_IMM) {
            ev[i].kind = SF_RX_DATA;
            ev[i].slot_off = 0;
        } else {
            ev[i].kind = SF_RX_MSG;
            ev[i].slot_off = sq->rx_base + RX_TAG_SLOT(t) * sq->rx_slot_bytes;
        }
        int r = post_rx(c, sq, RX_TAG_SLOT(t));
        if (r) return r;
    }
    return n;
}
