/*
 * libscuffedfabric: the libscuffedrdma dual QP pool expressed on libfabric.
 *
 * Two traffic classes, each on its own endpoint, CQs and (optionally) its
 * own provider/endpoint type:
 *
 *   SF_HOT   small, latency-critical (metadata, decode-step KV reads).
 *            Busy-polled TX CQ or a TX counter (selective completion).
 *   SF_COLD  bulk (prefill KV blocks). Deep TX queue, CQ with a wait
 *            object (fi_cq_sread) or plain polling.
 *
 * Endpoint types are chosen per class: FI_EP_MSG (verbs RC, tcp) or
 * FI_EP_RDM (verbs;ofi_rxm, tcp;ofi_rxm, shm). Classes with the same
 * provider and endpoint type share one fabric, domain and MR, the
 * libfabric analogue of "two QP pools on one PD". single_ep=1 maps both
 * classes onto one endpoint: the head-of-line baseline.
 *
 * One registered arena per side (single fi_mr_reg, like the single
 * ibv_reg_mr over vLLM's PagedAttention buffer). The tail of the arena
 * holds receive slots for two-sided messages and FI_RX_CQ_DATA.
 *
 * Address and key exchange go over an out-of-band TCP socket on `port`;
 * MSG endpoints listen on port+1.
 */
#ifndef SCUFFED_FABRIC_H
#define SCUFFED_FABRIC_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define SF_HOT 0
#define SF_COLD 1
#define SF_NCLASS 2

#define SF_EP_MSG 1
#define SF_EP_RDM 2

#define SF_COMP_CQ 0
#define SF_COMP_CNTR 1

/* sf_write flags */
#define SF_F_IMM 0x1        /* deliver `imm` as remote CQ data */
#define SF_F_INJECT 0x2     /* allow FI_INJECT when len <= inject_size */
#define SF_F_MORE 0x4       /* FI_MORE hint (batching) */

/* sf_poll_rx event kinds */
#define SF_RX_DATA 1        /* remote CQ data from fi_writedata */
#define SF_RX_MSG 2         /* two-sided message landed in a receive slot */

typedef struct sf_opts {
    const char *provider[SF_NCLASS]; /* e.g. "verbs", "tcp", "shm", "verbs;ofi_rxm"; NULL = any */
    const char *domain;              /* optional domain filter (rxe0, mlx5_0, lo, eth0) */
    int ep_type[SF_NCLASS];          /* SF_EP_MSG or SF_EP_RDM */
    int single_ep;                   /* 1: both classes share the hot endpoint */
    size_t arena_bytes;              /* RMA data region per side */
    int hot_comp;                    /* SF_COMP_CQ or SF_COMP_CNTR */
    int cold_wait;                   /* 1: cold TX CQ gets a wait object, waits use fi_cq_sread */
    int rma_event;                   /* 1: request FI_RMA_EVENT and a remote-write counter per class */
    size_t tx_depth[SF_NCLASS];
    size_t rx_depth[SF_NCLASS];
    size_t rx_slot_bytes;            /* size of each two-sided receive slot */
    int verbose;
} sf_opts_t;

typedef struct sf_rx_ev {
    int kind;        /* SF_RX_DATA or SF_RX_MSG */
    int cls;
    uint64_t data;   /* remote CQ data (imm) */
    size_t len;
    size_t slot_off; /* arena offset of the message (SF_RX_MSG) */
} sf_rx_ev_t;

typedef struct sf_ctx sf_ctx_t;

void sf_opts_default(sf_opts_t *o);

sf_ctx_t *sf_open(const sf_opts_t *o);
/* Server: bind OOB on addr:port, wait for one peer. addr must be the IP of the
 * fabric interface for verbs (e.g. the 10GbE address carrying rxe0). */
int sf_listen(sf_ctx_t *c, const char *addr, int port, int timeout_ms);
/* Client: connect to server host:port. */
int sf_connect(sf_ctx_t *c, const char *host, int port, int timeout_ms);
void sf_close(sf_ctx_t *c);

void *sf_buf(sf_ctx_t *c);           /* start of the RMA data region */
size_t sf_buf_len(sf_ctx_t *c);
size_t sf_inject_size(sf_ctx_t *c, int cls);
int sf_cq_data_size(sf_ctx_t *c, int cls);   /* bytes of remote CQ data the provider carries */
const char *sf_describe(sf_ctx_t *c, int cls); /* "prov=verbs ep=msg domain=rxe0 shared_domain=1 ..." */
int sf_capable(sf_ctx_t *c, int cls, const char *what); /* "cntr", "rma_event", "waw", "wait" */

/* One-sided ops. Offsets are into the local / remote data region. */
int sf_write(sf_ctx_t *c, int cls, size_t loff, size_t len, size_t roff, uint64_t imm, int flags);
int sf_read(sf_ctx_t *c, int cls, size_t loff, size_t len, size_t roff);
/* Two-sided small message (copied from local data region). */
int sf_send(sf_ctx_t *c, int cls, size_t loff, size_t len, uint64_t imm, int with_imm);

/* Local completions. Each class has a posted/done count, updated by whoever
 * drains the CQ (with single_ep the CQ is shared and completions are routed
 * by op context). */
uint64_t sf_tx_posted(sf_ctx_t *c, int cls);
uint64_t sf_tx_done(sf_ctx_t *c, int cls);
int sf_progress(sf_ctx_t *c, int cls);                     /* drain TX CQ / read counter; returns events seen or <0 */
int sf_wait_tx(sf_ctx_t *c, int cls, uint64_t target, int timeout_ms); /* until done >= target */
int sf_poll_rx(sf_ctx_t *c, int cls, sf_rx_ev_t *ev, int max);         /* reposts consumed slots */
uint64_t sf_rma_events(sf_ctx_t *c, int cls);              /* remote writes landed (needs rma_event) */

/* OOB helpers for benchmarks: tiny barrier and u64 exchange over the side socket. */
int sf_oob_barrier(sf_ctx_t *c);
int sf_oob_xchg(sf_ctx_t *c, uint64_t mine, uint64_t *theirs);
int sf_oob_fd(sf_ctx_t *c);

const char *sf_strerror(int err);
uint64_t sf_now_ns(void);

#ifdef __cplusplus
}
#endif
#endif
