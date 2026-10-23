/*
 * libscuffedfabric implementation. See scuffed_fabric.h for the model.
 */
#define _GNU_SOURCE
#include "scuffed_fabric.h"

#include <arpa/inet.h>
#include <errno.h>
#include <netdb.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <poll.h>
#include <pthread.h>
#include <stdarg.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>

#include <rdma/fabric.h>
#include <rdma/fi_cm.h>
#include <rdma/fi_domain.h>
#include <rdma/fi_endpoint.h>
#include <rdma/fi_eq.h>
#include <rdma/fi_errno.h>
#include <rdma/fi_rma.h>

#define SF_FI_VERSION FI_VERSION(1, 9)
#define SF_MAGIC 0x53434652u /* 'SCFR' */
#define TX_TAG(cls) ((void *)(uintptr_t)(0x10 + (cls)))
#define RX_TAG(cls, slot) ((void *)(uintptr_t)(0x40000000u | ((uint32_t)(cls) << 24) | (uint32_t)(slot)))
#define IS_RX_TAG(p) ((((uintptr_t)(p)) & 0xC0000000u) == 0x40000000u)
#define RX_TAG_CLS(p) ((int)((((uintptr_t)(p)) >> 24) & 0x3f))
#define RX_TAG_SLOT(p) ((size_t)(((uintptr_t)(p)) & 0xffffffu))

typedef struct sf_res {
    struct fi_info *info;
    struct fid_fabric *fab;
    struct fid_domain *dom;
    struct fid_mr *mr;
    void *desc;
    uint64_t key;
    struct fid_eq *eq;
    struct fid_av *av;
    struct fid_pep *pep;
    struct fid_cntr *rmacntr; /* remote-write counter, bound to the MR and to endpoints */
    int virt_addr;
    int threading_safe;
    pthread_mutex_t lock; /* used only when the provider is not FI_THREAD_SAFE */
    int refs;
    int idx;
} sf_res_t;

typedef struct sf_ep {
    sf_res_t *r;
    struct fi_info *info; /* info the endpoint was created from */
    int owns_info;
    struct fid_ep *ep;
    struct fid_cq *txcq, *rxcq;
    struct fid_cntr *txcntr, *rmacntr;
    fi_addr_t peer;
    int ep_type;
    int cls;
    int use_cntr;
    int wait;
    int manual_progress;
    size_t rx_slots, rx_base, rx_slot_bytes;
    size_t inject_size;
    int cq_data_size;
    uint64_t rbase, rkey;
    int rvirt;
    int refs;
    char desc[384];
} sf_ep_t;

struct sf_ctx {
    sf_opts_t o;
    char *arena;
    size_t arena_len, data_len;
    sf_res_t *res[SF_NCLASS];
    sf_ep_t *ep[SF_NCLASS];
    int oob;
    int server;
    _Atomic uint64_t posted[SF_NCLASS];
    _Atomic uint64_t done[SF_NCLASS];
    char prov[SF_NCLASS][64];
};

struct sf_wire {
    uint32_t magic, version;
    uint64_t base;
    uint64_t key[SF_NCLASS];
    uint32_t virt[SF_NCLASS];
    uint32_t ep_type[SF_NCLASS];
    uint32_t namelen[SF_NCLASS];
    uint8_t name[SF_NCLASS][256];
    uint32_t single;
};

static __thread char g_err[512];

static void seterr(const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(g_err, sizeof g_err, fmt, ap);
    va_end(ap);
}

const char *sf_strerror(int err) {
    if (g_err[0]) return g_err;
    return fi_strerror(err < 0 ? -err : err);
}

uint64_t sf_now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC_RAW, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
}

#define CHK(call, what)                                                     \
    do {                                                                    \
        int _r = (int)(call);                                               \
        if (_r) {                                                           \
            seterr("%s: %s (%d)", what, fi_strerror(-_r), _r);              \
            return _r < 0 ? _r : -_r;                                       \
        }                                                                   \
    } while (0)

static void lock_res(sf_res_t *r) { if (!r->threading_safe) pthread_mutex_lock(&r->lock); }
static void unlock_res(sf_res_t *r) { if (!r->threading_safe) pthread_mutex_unlock(&r->lock); }

void sf_opts_default(sf_opts_t *o) {
    memset(o, 0, sizeof *o);
    o->ep_type[SF_HOT] = SF_EP_MSG;
    o->ep_type[SF_COLD] = SF_EP_MSG;
    o->arena_bytes = 64ull << 20;
    o->hot_comp = SF_COMP_CQ;
    o->cold_wait = 0;
    o->tx_depth[SF_HOT] = 64;
    o->tx_depth[SF_COLD] = 512;
    o->rx_depth[SF_HOT] = 256;
    o->rx_depth[SF_COLD] = 64;
    o->rx_slot_bytes = 4096;
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

int sf_oob_barrier(sf_ctx_t *c) {
    char b = 'b', r;
    int ret = sendall(c->oob, &b, 1);
    if (ret) return ret;
    return recvall(c->oob, &r, 1);
}

int sf_oob_xchg(sf_ctx_t *c, uint64_t mine, uint64_t *theirs) {
    int ret = sendall(c->oob, &mine, sizeof mine);
    if (ret) return ret;
    return recvall(c->oob, theirs, sizeof *theirs);
}

int sf_oob_fd(sf_ctx_t *c) { return c->oob; }

static int oob_listen_fd(const char *addr, int port) {
    int fd = socket(AF_INET, SOCK_STREAM, 0), one = 1;
    if (fd < 0) return -errno;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &one, sizeof one);
    struct sockaddr_in sa = {.sin_family = AF_INET, .sin_port = htons((uint16_t)port)};
    sa.sin_addr.s_addr = htonl(INADDR_ANY);
    (void)addr; /* OOB listens on all interfaces; fabric binds to addr */
    if (bind(fd, (struct sockaddr *)&sa, sizeof sa) || listen(fd, 1)) {
        int e = -errno;
        close(fd);
        seterr("oob bind/listen on port %d: %s", port, strerror(-e));
        return e;
    }
    return fd;
}

static int oob_accept(int lfd, int timeout_ms) {
    struct pollfd p = {.fd = lfd, .events = POLLIN};
    int r = poll(&p, 1, timeout_ms <= 0 ? -1 : timeout_ms);
    if (r <= 0) { seterr("oob accept timed out"); return -ETIMEDOUT; }
    int fd = accept(lfd, NULL, NULL), one = 1;
    if (fd < 0) return -errno;
    setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &one, sizeof one);
    return fd;
}

static int oob_connect(const char *host, int port, int timeout_ms) {
    char svc[16];
    snprintf(svc, sizeof svc, "%d", port);
    struct addrinfo hints = {.ai_family = AF_INET, .ai_socktype = SOCK_STREAM}, *ai = NULL;
    int r = getaddrinfo(host, svc, &hints, &ai);
    if (r) { seterr("resolve %s: %s", host, gai_strerror(r)); return -EHOSTUNREACH; }
    uint64_t deadline = sf_now_ns() + (uint64_t)(timeout_ms > 0 ? timeout_ms : 30000) * 1000000ull;
    int fd = -1;
    while (sf_now_ns() < deadline) {
        fd = socket(AF_INET, SOCK_STREAM, 0);
        if (connect(fd, ai->ai_addr, ai->ai_addrlen) == 0) break;
        close(fd);
        fd = -1;
        usleep(50000);
    }
    freeaddrinfo(ai);
    if (fd < 0) { seterr("oob connect %s:%d timed out", host, port); return -ETIMEDOUT; }
    int one = 1;
    setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &one, sizeof one);
    return fd;
}

/* ------------------------------------------------------------- resources */

static struct fi_info *mk_hints(sf_ctx_t *c, int cls, int rma_event, int safe) {
    struct fi_info *h = fi_allocinfo();
    if (!h) return NULL;
    h->caps = FI_MSG | FI_RMA | FI_READ | FI_WRITE | FI_REMOTE_READ | FI_REMOTE_WRITE | FI_SEND | FI_RECV;
    if (rma_event) h->caps |= FI_RMA_EVENT;
    h->ep_attr->type = c->o.ep_type[cls] == SF_EP_RDM ? FI_EP_RDM : FI_EP_MSG;
    h->mode = FI_RX_CQ_DATA;
    h->domain_attr->mr_mode = FI_MR_LOCAL | FI_MR_VIRT_ADDR | FI_MR_ALLOCATED | FI_MR_PROV_KEY;
    h->domain_attr->threading = safe ? FI_THREAD_SAFE : FI_THREAD_DOMAIN;
    h->domain_attr->resource_mgmt = FI_RM_ENABLED;
    h->tx_attr->size = c->o.tx_depth[cls];
    h->rx_attr->size = c->o.rx_depth[cls];
    if (c->o.provider[cls]) h->fabric_attr->prov_name = strdup(c->o.provider[cls]);
    if (c->o.domain) h->domain_attr->name = strdup(c->o.domain);
    return h;
}

/* Try FI_THREAD_SAFE (+ FI_RMA_EVENT if asked), then relax. */
static int getinfo_cls(sf_ctx_t *c, int cls, const char *node, const char *svc, uint64_t flags,
                       struct fi_info **out, int *rma_event_ok, int *safe_ok) {
    int tries[4][2] = {{1, 1}, {1, 0}, {0, 1}, {0, 0}};
    int last = -FI_ENODATA;
    for (int i = 0; i < 4; i++) {
        int ev = tries[i][0] && c->o.rma_event, safe = tries[i][1];
        if (!c->o.rma_event && tries[i][0]) continue;
        struct fi_info *h = mk_hints(c, cls, ev, safe);
        last = fi_getinfo(SF_FI_VERSION, node, svc, flags, h, out);
        fi_freeinfo(h);
        if (!last) {
            *rma_event_ok = ev;
            *safe_ok = safe;
            return 0;
        }
    }
    seterr("fi_getinfo(prov=%s, ep=%s, node=%s, svc=%s): %s", c->o.provider[cls] ? c->o.provider[cls] : "any",
           c->o.ep_type[cls] == SF_EP_RDM ? "rdm" : "msg", node ? node : "-", svc ? svc : "-", fi_strerror(-last));
    return last;
}

static int res_open(sf_ctx_t *c, sf_res_t *r) {
    CHK(fi_fabric(r->info->fabric_attr, &r->fab, NULL), "fi_fabric");
    struct fi_eq_attr eqa = {.size = 64, .wait_obj = FI_WAIT_UNSPEC};
    CHK(fi_eq_open(r->fab, &eqa, &r->eq, NULL), "fi_eq_open");
    CHK(fi_domain(r->fab, r->info, &r->dom, NULL), "fi_domain");
    if (r->info->domain_attr->mr_mode & FI_MR_ENDPOINT) {
        seterr("provider %s needs FI_MR_ENDPOINT, not supported here", r->info->fabric_attr->prov_name);
        return -FI_ENOSYS;
    }
    if (r->info->ep_attr->type == FI_EP_RDM) {
        struct fi_av_attr ava = {.type = r->info->domain_attr->av_type != FI_AV_UNSPEC ? r->info->domain_attr->av_type : FI_AV_MAP,
                                 .count = 8};
        CHK(fi_av_open(r->dom, &ava, &r->av, NULL), "fi_av_open");
    }
    uint64_t acc = FI_READ | FI_WRITE | FI_REMOTE_READ | FI_REMOTE_WRITE | FI_SEND | FI_RECV;
    int mr_ev = 0;
    if (c->o.rma_event && (r->info->caps & FI_RMA_EVENT)) {
        struct fi_cntr_attr ca = {.events = FI_CNTR_EVENTS_COMP, .wait_obj = FI_WAIT_NONE};
        if (fi_cntr_open(r->dom, &ca, &r->rmacntr, NULL)) r->rmacntr = NULL;
    }
    if (r->rmacntr &&
        fi_mr_reg(r->dom, c->arena, c->arena_len, acc, 0, 0x5cf0u + (uint64_t)r->idx, FI_RMA_EVENT, &r->mr, NULL) == 0) {
        mr_ev = 1;
        /* some providers (tcp) count remote writes through the MR, others (shm) through the endpoint */
        if (fi_mr_bind(r->mr, &r->rmacntr->fid, FI_REMOTE_WRITE)) mr_ev = 0;
        int er = fi_mr_enable(r->mr);
        if (er && er != -FI_ENOSYS) { seterr("fi_mr_enable: %s", fi_strerror(-er)); return er; }
    } else {
        r->mr = NULL;
        CHK(fi_mr_reg(r->dom, c->arena, c->arena_len, acc, 0, 0x5cf0u + (uint64_t)r->idx, 0, &r->mr, NULL), "fi_mr_reg");
    }
    (void)mr_ev;
    r->desc = fi_mr_desc(r->mr);
    r->key = fi_mr_key(r->mr);
    r->virt_addr = (r->info->domain_attr->mr_mode & FI_MR_VIRT_ADDR) != 0;
    r->threading_safe = r->info->domain_attr->threading == FI_THREAD_SAFE;
    pthread_mutex_init(&r->lock, NULL);
    return 0;
}

static void res_close(sf_res_t *r) {
    if (!r) return;
    if (r->pep) fi_close(&r->pep->fid);
    if (r->mr) fi_close(&r->mr->fid);
    if (r->rmacntr) fi_close(&r->rmacntr->fid);
    if (r->av) fi_close(&r->av->fid);
    if (r->dom) fi_close(&r->dom->fid);
    if (r->eq) fi_close(&r->eq->fid);
    if (r->fab) fi_close(&r->fab->fid);
    if (r->info) fi_freeinfo(r->info);
    pthread_mutex_destroy(&r->lock);
    free(r);
}

static int post_rx(sf_ctx_t *c, sf_ep_t *e, size_t slot) {
    void *buf = c->arena + e->rx_base + slot * e->rx_slot_bytes;
    for (;;) {
        lock_res(e->r);
        int ret = (int)fi_recv(e->ep, buf, e->rx_slot_bytes, e->r->desc, FI_ADDR_UNSPEC, RX_TAG(e->cls, slot));
        unlock_res(e->r);
        if (ret != -FI_EAGAIN) {
            if (ret) seterr("fi_recv: %s", fi_strerror(-ret));
            return ret;
        }
        lock_res(e->r);
        fi_cq_read(e->rxcq, NULL, 0); /* progress without consuming */
        unlock_res(e->r);
    }
}

static int ep_setup(sf_ctx_t *c, sf_ep_t *e, struct fi_info *info) {
    sf_res_t *r = e->r;
    int cls = e->cls;
    e->info = info;
    CHK(fi_endpoint(r->dom, info, &e->ep, NULL), "fi_endpoint");

    struct fi_cq_attr cqa = {.format = FI_CQ_FORMAT_DATA, .wait_obj = FI_WAIT_NONE};
    cqa.size = c->o.tx_depth[cls] * 2 + 64;
    e->wait = 0;
    if (cls == SF_COLD && c->o.cold_wait && !c->o.single_ep) {
        cqa.wait_obj = FI_WAIT_UNSPEC;
        if (fi_cq_open(r->dom, &cqa, &e->txcq, NULL) == 0) e->wait = 1;
        else cqa.wait_obj = FI_WAIT_NONE;
    }
    if (!e->txcq) CHK(fi_cq_open(r->dom, &cqa, &e->txcq, NULL), "fi_cq_open(tx)");
    cqa.wait_obj = FI_WAIT_NONE;
    cqa.size = c->o.rx_depth[cls] * 2 + 64;
    CHK(fi_cq_open(r->dom, &cqa, &e->rxcq, NULL), "fi_cq_open(rx)");

    e->use_cntr = 0;
    if (cls == SF_HOT && c->o.hot_comp == SF_COMP_CNTR && !c->o.single_ep) {
        struct fi_cntr_attr ca = {.events = FI_CNTR_EVENTS_COMP, .wait_obj = FI_WAIT_NONE};
        if (fi_cntr_open(r->dom, &ca, &e->txcntr, NULL) == 0 &&
            fi_ep_bind(e->ep, &e->txcntr->fid, FI_WRITE | FI_READ | FI_SEND) == 0) {
            e->use_cntr = 1;
        } else if (e->txcntr) {
            fi_close(&e->txcntr->fid);
            e->txcntr = NULL;
        }
    }
    CHK(fi_ep_bind(e->ep, &e->txcq->fid, FI_TRANSMIT | (e->use_cntr ? FI_SELECTIVE_COMPLETION : 0)), "bind txcq");
    CHK(fi_ep_bind(e->ep, &e->rxcq->fid, FI_RECV), "bind rxcq");
    if (r->rmacntr) {
        fi_ep_bind(e->ep, &r->rmacntr->fid, FI_REMOTE_WRITE); /* ignored where only the MR path exists */
        e->rmacntr = r->rmacntr;
    }
    if (info->ep_attr->type == FI_EP_MSG) CHK(fi_ep_bind(e->ep, &r->eq->fid, 0), "bind eq");
    else CHK(fi_ep_bind(e->ep, &r->av->fid, 0), "bind av");
    CHK(fi_enable(e->ep), "fi_enable");

    e->inject_size = info->tx_attr->inject_size;
    e->cq_data_size = (int)info->domain_attr->cq_data_size;
    e->manual_progress = info->domain_attr->data_progress == FI_PROGRESS_MANUAL;
    for (size_t s = 0; s < e->rx_slots; s++) {
        int ret = post_rx(c, e, s);
        if (ret) return ret;
    }
    snprintf(e->desc, sizeof e->desc,
             "prov=%s ep=%s domain=%s fabric=%s shared_domain=%d mr_virt=%d mr_mode=0x%llx thread_safe=%d "
             "progress=%s inject=%zu cq_data=%d hot_cntr=%d cold_wait=%d rma_event=%d",
             info->fabric_attr->prov_name, info->ep_attr->type == FI_EP_RDM ? "rdm" : "msg",
             info->domain_attr->name, info->fabric_attr->name, r->refs > 1, r->virt_addr,
             (unsigned long long)info->domain_attr->mr_mode, r->threading_safe,
             e->manual_progress ? "manual" : "auto", e->inject_size, e->cq_data_size, e->use_cntr, e->wait,
             e->rmacntr != NULL);
    return 0;
}

static void ep_close(sf_ep_t *e) {
    if (!e) return;
    if (e->ep) fi_close(&e->ep->fid);
    if (e->txcntr) fi_close(&e->txcntr->fid);
    if (e->txcq) fi_close(&e->txcq->fid);
    if (e->rxcq) fi_close(&e->rxcq->fid);
    if (e->owns_info && e->info) fi_freeinfo(e->info);
    free(e);
}

sf_ctx_t *sf_open(const sf_opts_t *o) {
    sf_ctx_t *c = calloc(1, sizeof *c);
    if (!c) return NULL;
    c->o = *o;
    if (c->o.single_ep) {
        c->o.provider[SF_COLD] = c->o.provider[SF_HOT];
        c->o.ep_type[SF_COLD] = c->o.ep_type[SF_HOT];
    }
    c->oob = -1;
    size_t pg = 4096;
    c->data_len = (o->arena_bytes + pg - 1) & ~(pg - 1);
    size_t slab = 0;
    for (int k = 0; k < SF_NCLASS; k++) slab += o->rx_depth[k] * o->rx_slot_bytes;
    c->arena_len = c->data_len + ((slab + pg - 1) & ~(pg - 1));
    c->arena = mmap(NULL, c->arena_len, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (c->arena == MAP_FAILED) {
        seterr("mmap arena %zu bytes: %s", c->arena_len, strerror(errno));
        free(c);
        return NULL;
    }
    memset(c->arena, 0, c->arena_len);
    return c;
}

static int same_res(sf_ctx_t *c) {
    if (c->o.single_ep) return 1;
    const char *a = c->o.provider[SF_HOT] ? c->o.provider[SF_HOT] : "";
    const char *b = c->o.provider[SF_COLD] ? c->o.provider[SF_COLD] : "";
    return strcmp(a, b) == 0 && c->o.ep_type[SF_HOT] == c->o.ep_type[SF_COLD];
}

/* Build resources and RDM endpoints; MSG endpoints come after the exchange. */
static int setup_side(sf_ctx_t *c, const char *node, int port) {
    int share = same_res(c);
    int nres = share ? 1 : 2;
    size_t rx_off = c->data_len;
    for (int k = 0; k < nres; k++) {
        sf_res_t *r = calloc(1, sizeof *r);
        r->idx = k;
        c->res[k] = r;
        int ev_ok = 0, safe_ok = 0, ret;
        char svc[16];
        if (c->o.ep_type[k] == SF_EP_MSG) {
            snprintf(svc, sizeof svc, "%d", port + 1 + k);
            if (c->server)
                ret = getinfo_cls(c, k, (node && strcmp(node, "0.0.0.0")) ? node : NULL, svc, FI_SOURCE, &r->info, &ev_ok, &safe_ok);
            else
                ret = getinfo_cls(c, k, node, svc, 0, &r->info, &ev_ok, &safe_ok);
        } else {
            const char *n = (c->server && node && strcmp(node, "0.0.0.0")) ? node : NULL;
            ret = getinfo_cls(c, k, n, NULL, n ? FI_SOURCE : 0, &r->info, &ev_ok, &safe_ok);
        }
        if (ret) return ret;
        if (!ev_ok) c->o.rma_event = c->o.rma_event && 0;
        snprintf(c->prov[k], sizeof c->prov[k], "%s", r->info->fabric_attr->prov_name);
        ret = res_open(c, r);
        if (ret) return ret;
        if (c->server && r->info->ep_attr->type == FI_EP_MSG) {
            CHK(fi_passive_ep(r->fab, r->info, &r->pep, NULL), "fi_passive_ep");
            CHK(fi_pep_bind(r->pep, &r->eq->fid, 0), "fi_pep_bind");
            CHK(fi_listen(r->pep), "fi_listen");
        }
    }
    if (share) { c->res[SF_COLD] = c->res[SF_HOT]; }
    for (int k = 0; k < SF_NCLASS; k++) c->res[k]->refs++;

    int nep = c->o.single_ep ? 1 : 2;
    for (int k = 0; k < nep; k++) {
        sf_ep_t *e = calloc(1, sizeof *e);
        e->r = c->res[k];
        e->cls = k;
        e->ep_type = c->o.ep_type[k];
        e->rx_slots = c->o.rx_depth[k];
        e->rx_slot_bytes = c->o.rx_slot_bytes;
        e->rx_base = rx_off;
        rx_off += e->rx_slots * e->rx_slot_bytes;
        e->refs = 1;
        c->ep[k] = e;
        if (e->ep_type == SF_EP_RDM) {
            int ret = ep_setup(c, e, e->r->info);
            if (ret) return ret;
        } else if (!c->server) {
            /* client MSG: endpoint from the dest-addressed info, connect after exchange */
            int ret = ep_setup(c, e, e->r->info);
            if (ret) return ret;
        }
    }
    if (c->o.single_ep) { c->ep[SF_COLD] = c->ep[SF_HOT]; c->ep[SF_HOT]->refs++; }
    return 0;
}

static int exchange(sf_ctx_t *c) {
    struct sf_wire me = {.magic = SF_MAGIC, .version = 1, .base = (uint64_t)(uintptr_t)c->arena, .single = (uint32_t)c->o.single_ep};
    for (int k = 0; k < SF_NCLASS; k++) {
        me.key[k] = c->res[k]->key;
        me.virt[k] = (uint32_t)c->res[k]->virt_addr;
        me.ep_type[k] = (uint32_t)c->o.ep_type[k];
        sf_ep_t *e = c->ep[k];
        if (e->ep_type == SF_EP_RDM && e->ep) {
            size_t len = sizeof me.name[k];
            CHK(fi_getname(&e->ep->fid, me.name[k], &len), "fi_getname");
            me.namelen[k] = (uint32_t)len;
        }
    }
    struct sf_wire them;
    int ret = sendall(c->oob, &me, sizeof me);
    if (!ret) ret = recvall(c->oob, &them, sizeof them);
    if (ret) { seterr("oob exchange: %s", strerror(-ret)); return ret; }
    if (them.magic != SF_MAGIC) { seterr("peer is not libscuffedfabric"); return -FI_EINVAL; }
    if (them.single != me.single || them.ep_type[0] != me.ep_type[0] || them.ep_type[1] != me.ep_type[1]) {
        seterr("peer config mismatch (single_ep or endpoint types differ)");
        return -FI_EINVAL;
    }
    for (int k = 0; k < SF_NCLASS; k++) {
        sf_ep_t *e = c->ep[k];
        e->rbase = them.base;
        e->rkey = them.key[k];
        e->rvirt = (int)them.virt[k];
        if (e->ep_type == SF_EP_RDM && (k == SF_HOT || !c->o.single_ep)) {
            int n = fi_av_insert(e->r->av, them.name[k], 1, &e->peer, 0, NULL);
            if (n != 1) { seterr("fi_av_insert: %d", n); return -FI_EINVAL; }
        }
    }
    return 0;
}

static int wait_eq(sf_res_t *r, uint32_t want, struct fid *fid, struct fi_eq_cm_entry *ent, size_t entsz,
                   int timeout_ms, uint32_t *got_event) {
    for (;;) {
        uint32_t ev = 0;
        ssize_t n = fi_eq_sread(r->eq, &ev, ent, entsz, timeout_ms > 0 ? timeout_ms : 30000, 0);
        if (n == -FI_EAVAIL) {
            struct fi_eq_err_entry ee = {0};
            fi_eq_readerr(r->eq, &ee, 0);
            seterr("eq error: %s (%s)", fi_strerror(ee.err), fi_eq_strerror(r->eq, ee.prov_errno, ee.err_data, NULL, 0));
            return -ee.err;
        }
        if (n < 0) { seterr("fi_eq_sread: %s", fi_strerror((int)-n)); return (int)n; }
        if (got_event) *got_event = ev;
        if (want == 0) return 0;
        if (ev == want && (!fid || ent->fid == fid)) return 0;
    }
}

static int msg_connect_client(sf_ctx_t *c, int timeout_ms) {
    int nep = c->o.single_ep ? 1 : 2;
    for (int k = 0; k < nep; k++) {
        sf_ep_t *e = c->ep[k];
        if (e->ep_type != SF_EP_MSG) continue;
        uint8_t param = (uint8_t)k;
        CHK(fi_connect(e->ep, e->info->dest_addr, &param, sizeof param), "fi_connect");
        char buf[sizeof(struct fi_eq_cm_entry) + 64];
        int ret = wait_eq(e->r, FI_CONNECTED, &e->ep->fid, (struct fi_eq_cm_entry *)buf, sizeof buf, timeout_ms, NULL);
        if (ret) return ret;
    }
    return 0;
}

static int msg_accept_server(sf_ctx_t *c, int timeout_ms) {
    int nep = c->o.single_ep ? 1 : 2, need = 0;
    for (int k = 0; k < nep; k++) need += c->ep[k]->ep_type == SF_EP_MSG;
    int connected = 0;
    while (connected < need) {
        /* events may arrive on either resource's EQ */
        for (int k = 0; k < nep && connected < need; k++) {
            sf_res_t *r = c->ep[k]->r;
            if (c->ep[k]->ep_type != SF_EP_MSG) continue;
            char buf[sizeof(struct fi_eq_cm_entry) + 64];
            struct fi_eq_cm_entry *ent = (struct fi_eq_cm_entry *)buf;
            uint32_t ev = 0;
            ssize_t n = fi_eq_sread(r->eq, &ev, ent, sizeof buf, 50, 0);
            if (n == -FI_EAGAIN) continue;
            if (n == -FI_EAVAIL) {
                struct fi_eq_err_entry ee = {0};
                fi_eq_readerr(r->eq, &ee, 0);
                seterr("eq error during accept: %s", fi_strerror(ee.err));
                return -ee.err;
            }
            if (n < 0) { seterr("fi_eq_sread: %s", fi_strerror((int)-n)); return (int)n; }
            if (ev == FI_CONNREQ) {
                int cls = n > (ssize_t)sizeof(struct fi_eq_cm_entry) ? ent->data[0] : k;
                if (cls < 0 || cls >= nep) cls = k;
                sf_ep_t *e = c->ep[cls];
                e->owns_info = 1;
                /* connreq info does not always carry the listener's optional caps */
                ent->info->caps |= r->info->caps & FI_RMA_EVENT;
                int ret = ep_setup(c, e, ent->info);
                if (ret) return ret;
                CHK(fi_accept(e->ep, NULL, 0), "fi_accept");
            } else if (ev == FI_CONNECTED) {
                connected++;
            }
        }
        (void)timeout_ms;
    }
    return 0;
}

int sf_listen(sf_ctx_t *c, const char *addr, int port, int timeout_ms) {
    c->server = 1;
    int lfd = oob_listen_fd(addr, port);
    if (lfd < 0) return lfd;
    int ret = setup_side(c, addr, port);
    if (ret) { close(lfd); return ret; }
    c->oob = oob_accept(lfd, timeout_ms);
    close(lfd);
    if (c->oob < 0) return c->oob;
    if ((ret = exchange(c))) return ret;
    if ((ret = msg_accept_server(c, timeout_ms))) return ret;
    return sf_oob_barrier(c);
}

int sf_connect(sf_ctx_t *c, const char *host, int port, int timeout_ms) {
    c->server = 0;
    c->oob = oob_connect(host, port, timeout_ms);
    if (c->oob < 0) return c->oob;
    int ret = setup_side(c, host, port);
    if (ret) return ret;
    if ((ret = exchange(c))) return ret;
    if ((ret = msg_connect_client(c, timeout_ms))) return ret;
    return sf_oob_barrier(c);
}

void sf_close(sf_ctx_t *c) {
    if (!c) return;
    sf_ep_t *seen[SF_NCLASS] = {0};
    for (int k = 0; k < SF_NCLASS; k++) {
        sf_ep_t *e = c->ep[k];
        if (!e || e == seen[0]) continue;
        seen[k] = e;
        ep_close(e);
    }
    sf_res_t *rseen = NULL;
    for (int k = 0; k < SF_NCLASS; k++) {
        if (!c->res[k] || c->res[k] == rseen) continue;
        rseen = c->res[k];
        res_close(c->res[k]);
    }
    if (c->oob >= 0) close(c->oob);
    if (c->arena && c->arena != MAP_FAILED) munmap(c->arena, c->arena_len);
    free(c);
}

/* -------------------------------------------------------------- queries */

void *sf_buf(sf_ctx_t *c) { return c->arena; }
size_t sf_buf_len(sf_ctx_t *c) { return c->data_len; }
size_t sf_inject_size(sf_ctx_t *c, int cls) { return c->ep[cls]->inject_size; }
int sf_cq_data_size(sf_ctx_t *c, int cls) { return c->ep[cls]->cq_data_size; }
const char *sf_describe(sf_ctx_t *c, int cls) { return c->ep[cls]->desc; }

int sf_capable(sf_ctx_t *c, int cls, const char *what) {
    sf_ep_t *e = c->ep[cls];
    if (!strcmp(what, "cntr")) return e->use_cntr;
    if (!strcmp(what, "rma_event")) return e->rmacntr != NULL;
    if (!strcmp(what, "wait")) return e->wait;
    if (!strcmp(what, "manual_progress")) return e->manual_progress;
    if (!strcmp(what, "waw")) {
        uint64_t o = e->info->tx_attr->msg_order;
#ifdef FI_ORDER_RMA_WAW
        return (o & (FI_ORDER_WAW | FI_ORDER_RMA_WAW)) != 0;
#else
        return (o & FI_ORDER_WAW) != 0;
#endif
    }
    return 0;
}

uint64_t sf_tx_posted(sf_ctx_t *c, int cls) { return atomic_load(&c->posted[cls]); }
uint64_t sf_tx_done(sf_ctx_t *c, int cls) { return atomic_load(&c->done[cls]); }

uint64_t sf_rma_events(sf_ctx_t *c, int cls) {
    sf_ep_t *e = c->ep[cls];
    if (!e->rmacntr) return 0;
    if (e->manual_progress) fi_cq_read(e->rxcq, NULL, 0);
    return fi_cntr_read(e->rmacntr);
}

/* ------------------------------------------------------------- data path */

static uint64_t raddr(sf_ep_t *e, size_t roff) { return e->rvirt ? e->rbase + roff : (uint64_t)roff; }

static int drain_tx(sf_ctx_t *c, sf_ep_t *e) {
    struct fi_cq_data_entry ents[64];
    lock_res(e->r);
    ssize_t n = fi_cq_read(e->txcq, ents, 64);
    if (n == -FI_EAVAIL) {
        struct fi_cq_err_entry ee = {0};
        fi_cq_readerr(e->txcq, &ee, 0);
        unlock_res(e->r);
        seterr("tx completion error: %s (prov %d: %s)", fi_strerror(ee.err), ee.prov_errno,
               fi_cq_strerror(e->txcq, ee.prov_errno, ee.err_data, NULL, 0));
        return -ee.err;
    }
    unlock_res(e->r);
    if (n <= 0) return 0;
    for (ssize_t i = 0; i < n; i++) {
        uintptr_t t = (uintptr_t)ents[i].op_context;
        int k = (t >= 0x10 && t < 0x10 + SF_NCLASS) ? (int)(t - 0x10) : e->cls;
        atomic_fetch_add(&c->done[k], 1);
    }
    return (int)n;
}

int sf_progress(sf_ctx_t *c, int cls) {
    sf_ep_t *e = c->ep[cls];
    if (e->use_cntr) {
        lock_res(e->r);
        if (e->manual_progress) fi_cq_read(e->rxcq, NULL, 0);
        uint64_t v = fi_cntr_read(e->txcntr), err = fi_cntr_readerr(e->txcntr);
        unlock_res(e->r);
        if (err) {
            int r = drain_tx(c, e); /* errors are still reported to the CQ */
            if (r < 0) return r;
            seterr("tx counter error count %llu", (unsigned long long)err);
            return -FI_EIO;
        }
        uint64_t old = atomic_exchange(&c->done[cls], v);
        return (int)(v - old);
    }
    return drain_tx(c, e);
}

int sf_wait_tx(sf_ctx_t *c, int cls, uint64_t target, int timeout_ms) {
    sf_ep_t *e = c->ep[cls];
    uint64_t deadline = timeout_ms > 0 ? sf_now_ns() + (uint64_t)timeout_ms * 1000000ull : 0;
    while (atomic_load(&c->done[cls]) < target) {
        if (e->wait && !e->use_cntr) {
            struct fi_cq_data_entry ents[64];
            ssize_t n = fi_cq_sread(e->txcq, ents, 64, NULL, 10);
            if (n > 0) {
                for (ssize_t i = 0; i < n; i++) {
                    uintptr_t t = (uintptr_t)ents[i].op_context;
                    int k = (t >= 0x10 && t < 0x10 + SF_NCLASS) ? (int)(t - 0x10) : e->cls;
                    atomic_fetch_add(&c->done[k], 1);
                }
            } else if (n == -FI_EAVAIL) {
                int r = drain_tx(c, e);
                if (r < 0) return r;
            }
        } else {
            int r = sf_progress(c, cls);
            if (r < 0) return r;
        }
        if (deadline && sf_now_ns() > deadline) {
            seterr("wait_tx timeout: class %d done %llu < %llu", cls,
                   (unsigned long long)atomic_load(&c->done[cls]), (unsigned long long)target);
            return -FI_ETIMEDOUT;
        }
    }
    return 0;
}

/* Post with retry on EAGAIN. Bounded: an unresponsive peer (for RDM, one that
 * never progresses the lazy connection) becomes an error, not a hang. */
#define SF_POST_TIMEOUT_NS (60ull * 1000000000ull)
static int post_retry(sf_ctx_t *c, sf_ep_t *e, int cls, ssize_t (*fn)(sf_ep_t *, void *, uint64_t), void *arg,
                      uint64_t fl) {
    uint64_t deadline = 0;
    for (;;) {
        lock_res(e->r);
        ssize_t ret = fn(e, arg, fl);
        unlock_res(e->r);
        if (ret == 0) { atomic_fetch_add(&c->posted[cls], 1); return 0; }
        if (ret != -FI_EAGAIN) { seterr("post on class %d: %s", cls, fi_strerror((int)-ret)); return (int)ret; }
        if (!deadline) deadline = sf_now_ns() + SF_POST_TIMEOUT_NS;
        else if (sf_now_ns() > deadline) {
            seterr("post on class %d: EAGAIN for 60 s (peer not progressing?)", cls);
            return -FI_ETIMEDOUT;
        }
        int r = sf_progress(c, cls);
        if (r < 0) return r;
        if (e->manual_progress) {
            lock_res(e->r);
            fi_cq_read(e->rxcq, NULL, 0);
            unlock_res(e->r);
        }
    }
}

static ssize_t do_writemsg(sf_ep_t *e, void *m, uint64_t fl) { return fi_writemsg(e->ep, m, fl); }
static ssize_t do_readmsg(sf_ep_t *e, void *m, uint64_t fl) { return fi_readmsg(e->ep, m, fl); }
static ssize_t do_sendmsg(sf_ep_t *e, void *m, uint64_t fl) { return fi_sendmsg(e->ep, m, fl); }

int sf_write(sf_ctx_t *c, int cls, size_t loff, size_t len, size_t roff, uint64_t imm, int flags) {
    sf_ep_t *e = c->ep[cls];
    if (loff + len > c->data_len || roff + len > c->data_len) { seterr("sf_write out of range"); return -FI_EINVAL; }
    struct iovec iov = {.iov_base = c->arena + loff, .iov_len = len};
    void *desc = e->r->desc;
    struct fi_rma_iov rma = {.addr = raddr(e, roff), .len = len, .key = e->rkey};
    struct fi_msg_rma m = {.msg_iov = &iov, .desc = &desc, .iov_count = 1, .addr = e->peer,
                           .rma_iov = &rma, .rma_iov_count = 1, .context = TX_TAG(cls), .data = imm};
    uint64_t fl = e->use_cntr ? 0 : FI_COMPLETION;
    if (flags & SF_F_IMM) fl |= FI_REMOTE_CQ_DATA;
    if ((flags & SF_F_INJECT) && len <= e->inject_size) fl |= FI_INJECT;
    if (flags & SF_F_MORE) fl |= FI_MORE;
    return post_retry(c, e, cls, do_writemsg, &m, fl);
}

int sf_read(sf_ctx_t *c, int cls, size_t loff, size_t len, size_t roff) {
    sf_ep_t *e = c->ep[cls];
    if (loff + len > c->data_len || roff + len > c->data_len) { seterr("sf_read out of range"); return -FI_EINVAL; }
    struct iovec iov = {.iov_base = c->arena + loff, .iov_len = len};
    void *desc = e->r->desc;
    struct fi_rma_iov rma = {.addr = raddr(e, roff), .len = len, .key = e->rkey};
    struct fi_msg_rma m = {.msg_iov = &iov, .desc = &desc, .iov_count = 1, .addr = e->peer,
                           .rma_iov = &rma, .rma_iov_count = 1, .context = TX_TAG(cls), .data = 0};
    return post_retry(c, e, cls, do_readmsg, &m, e->use_cntr ? 0 : FI_COMPLETION);
}

int sf_send(sf_ctx_t *c, int cls, size_t loff, size_t len, uint64_t imm, int with_imm) {
    sf_ep_t *e = c->ep[cls];
    if (len > c->o.rx_slot_bytes || loff + len > c->data_len) { seterr("sf_send larger than rx slot"); return -FI_EINVAL; }
    struct iovec iov = {.iov_base = c->arena + loff, .iov_len = len};
    void *desc = e->r->desc;
    struct fi_msg m = {.msg_iov = &iov, .desc = &desc, .iov_count = 1, .addr = e->peer,
                       .context = TX_TAG(cls), .data = imm};
    uint64_t fl = e->use_cntr ? 0 : FI_COMPLETION;
    if (with_imm) fl |= FI_REMOTE_CQ_DATA;
    if (len <= e->inject_size) fl |= FI_INJECT;
    return post_retry(c, e, cls, do_sendmsg, &m, fl);
}

int sf_poll_rx(sf_ctx_t *c, int cls, sf_rx_ev_t *ev, int max) {
    sf_ep_t *e = c->ep[cls];
    struct fi_cq_data_entry ents[64];
    if (max > 64) max = 64;
    lock_res(e->r);
    ssize_t n = fi_cq_read(e->rxcq, ents, (size_t)max);
    if (n == -FI_EAVAIL) {
        struct fi_cq_err_entry ee = {0};
        fi_cq_readerr(e->rxcq, &ee, 0);
        unlock_res(e->r);
        if (ee.err == FI_ECANCELED) { seterr("endpoint shut down (receive flushed)"); return -FI_ECANCELED; }
        seterr("rx completion error: %s", fi_strerror(ee.err));
        return -ee.err;
    }
    unlock_res(e->r);
    if (n <= 0) return 0;
    int out = 0;
    for (ssize_t i = 0; i < n; i++) {
        struct fi_cq_data_entry *x = &ents[i];
        int is_rma = (x->flags & (FI_RMA | FI_REMOTE_WRITE)) != 0;
        int from_slot = IS_RX_TAG(x->op_context);
        sf_rx_ev_t *v = &ev[out++];
        v->cls = from_slot ? RX_TAG_CLS(x->op_context) : cls;
        v->data = (x->flags & FI_REMOTE_CQ_DATA) ? x->data : 0;
        v->len = x->len;
        v->slot_off = 0;
        if (!is_rma && from_slot) {
            v->kind = SF_RX_MSG;
            sf_ep_t *se = c->ep[v->cls];
            v->slot_off = se->rx_base + RX_TAG_SLOT(x->op_context) * se->rx_slot_bytes;
        } else {
            v->kind = SF_RX_DATA;
        }
        if (from_slot) {
            sf_ep_t *se = c->ep[v->cls];
            int r = post_rx(c, se, RX_TAG_SLOT(x->op_context));
            if (r) return r;
        }
    }
    return out;
}
