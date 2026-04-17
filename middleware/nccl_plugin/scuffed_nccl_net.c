/*
 * scuffed_nccl_net.c - NCCL v8 net plugin with dual QP pools (libibverbs)
 *
 * Each connection gets TWO RC queue pairs:
 *   hot QP  - messages < 4KB, CQ busy-polled (low latency)
 *   cold QP - messages >= 4KB, standard CQ poll (throughput)
 * This is the WFA classifier from the thesis at the NCCL transport layer.
 */
#include "scuffed_nccl_net.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <unistd.h>
#include <errno.h>
#include <sys/socket.h>
#include <arpa/inet.h>

static ncclDebugLogger_t logger_fn;
static scuffed_device_t  g_dev;
static int               g_init_done;

#define LOG_WARN(fmt, ...) do { \
    if (logger_fn) logger_fn(NCCL_LOG_WARN, 0, __FILE__, __LINE__, \
                             "SCUFFED " fmt, ##__VA_ARGS__); \
} while(0)

/* ---- helpers ---- */

static int qp_bring_up(struct ibv_qp *qp, uint32_t rqpn, uint16_t rlid,
                        uint32_t rpsn, union ibv_gid *rgid, int port) {
    struct ibv_qp_attr a;
    memset(&a, 0, sizeof(a));
    a.qp_state = IBV_QPS_INIT;  a.pkey_index = 0;  a.port_num = port;
    a.qp_access_flags = IBV_ACCESS_REMOTE_WRITE|IBV_ACCESS_REMOTE_READ|IBV_ACCESS_LOCAL_WRITE;
    if (ibv_modify_qp(qp, &a, IBV_QP_STATE|IBV_QP_PKEY_INDEX|IBV_QP_PORT|IBV_QP_ACCESS_FLAGS))
        return -1;

    memset(&a, 0, sizeof(a));
    a.qp_state = IBV_QPS_RTR;  a.path_mtu = IBV_MTU_1024;
    a.dest_qp_num = rqpn;  a.rq_psn = rpsn;
    a.max_dest_rd_atomic = 1;  a.min_rnr_timer = 12;
    a.ah_attr.dlid = rlid;  a.ah_attr.port_num = port;
    a.ah_attr.is_global = 1;  a.ah_attr.grh.dgid = *rgid;
    a.ah_attr.grh.hop_limit = 64;
    if (ibv_modify_qp(qp, &a, IBV_QP_STATE|IBV_QP_AV|IBV_QP_PATH_MTU|
            IBV_QP_DEST_QPN|IBV_QP_RQ_PSN|IBV_QP_MAX_DEST_RD_ATOMIC|IBV_QP_MIN_RNR_TIMER))
        return -1;

    memset(&a, 0, sizeof(a));
    a.qp_state = IBV_QPS_RTS;  a.timeout = 14;  a.retry_cnt = 7;
    a.rnr_retry = 7;  a.sq_psn = 0;  a.max_rd_atomic = 1;
    if (ibv_modify_qp(qp, &a, IBV_QP_STATE|IBV_QP_TIMEOUT|IBV_QP_RETRY_CNT|
            IBV_QP_RNR_RETRY|IBV_QP_SQ_PSN|IBV_QP_MAX_QP_RD_ATOMIC))
        return -1;
    return 0;
}

static struct ibv_qp *create_rc_qp(struct ibv_pd *pd, struct ibv_cq *cq) {
    struct ibv_qp_init_attr a = {
        .send_cq = cq, .recv_cq = cq,
        .cap = { .max_send_wr = SCUFFED_QP_DEPTH, .max_recv_wr = SCUFFED_QP_DEPTH,
                 .max_send_sge = 1, .max_recv_sge = 1 },
        .qp_type = IBV_QPT_RC,
    };
    return ibv_create_qp(pd, &a);
}

static int oob_xfer(int fd, void *buf, size_t len, int do_write) {
    size_t off = 0;
    while (off < len) {
        ssize_t n = do_write ? write(fd, (char*)buf+off, len-off)
                             : read(fd, (char*)buf+off, len-off);
        if (n <= 0) { if (errno == EINTR) continue; return -1; }
        off += n;
    }
    return 0;
}

/* ---- plugin functions ---- */

static ncclResult_t scuffed_init(ncclDebugLogger_t logFunction) {
    logger_fn = logFunction;
    if (g_init_done) return ncclSuccess;

    const char *dev_name = getenv("SCUFFED_IB_DEV");
    if (!dev_name) dev_name = "rxe0";

    int num_devs;
    struct ibv_device **dl = ibv_get_device_list(&num_devs);
    if (!dl || num_devs == 0) { LOG_WARN("No RDMA devices"); return ncclSystemError; }

    struct ibv_device *tgt = dl[0];
    for (int i = 0; i < num_devs; i++)
        if (strcmp(ibv_get_device_name(dl[i]), dev_name) == 0) { tgt = dl[i]; break; }

    g_dev.ctx = ibv_open_device(tgt);
    if (!g_dev.ctx) { LOG_WARN("open %s failed", ibv_get_device_name(tgt)); ibv_free_device_list(dl); return ncclSystemError; }
    ibv_free_device_list(dl);

    g_dev.pd = ibv_alloc_pd(g_dev.ctx);
    if (!g_dev.pd) { LOG_WARN("alloc_pd failed"); ibv_close_device(g_dev.ctx); return ncclSystemError; }

    g_dev.port_num = 1;
    struct ibv_port_attr pa;
    if (ibv_query_port(g_dev.ctx, g_dev.port_num, &pa)) { LOG_WARN("query_port failed"); return ncclSystemError; }
    g_dev.lid = pa.lid;
    ibv_query_gid(g_dev.ctx, g_dev.port_num, 0, &g_dev.gid);
    g_init_done = 1;
    return ncclSuccess;
}

static ncclResult_t scuffed_devices(int *ndev) { *ndev = g_init_done ? 1 : 0; return ncclSuccess; }

static ncclResult_t scuffed_get_properties(int dev, ncclNetProperties_v8_t *p) {
    memset(p, 0, sizeof(*p));
    p->name = "ScuffedRDMA";   p->ptrSupport = NCCL_PTR_HOST;
    p->speed = 25000;          p->maxComms = 65536;       p->maxRecvs = 1;
    p->netDeviceType = NCCL_NET_DEVICE_HOST;
    p->netDeviceVersion = NCCL_NET_DEVICE_INVALID_VERSION;
    return ncclSuccess;
}

/* ---- connection setup ---- */

static ncclResult_t scuffed_listen(int dev, void *handle, void **listenComm) {
    scuffed_listen_comm_t *lc = calloc(1, sizeof(*lc));
    if (!lc) return ncclSystemError;
    lc->dev = dev;
    lc->fd = socket(AF_INET, SOCK_STREAM, 0);
    if (lc->fd < 0) { free(lc); return ncclSystemError; }
    int opt = 1;
    setsockopt(lc->fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
    lc->addr.sin_family = AF_INET;
    lc->addr.sin_addr.s_addr = INADDR_ANY;
    lc->addr.sin_port = 0;
    if (bind(lc->fd, (struct sockaddr*)&lc->addr, sizeof(lc->addr)) < 0 ||
        (getsockname(lc->fd, (struct sockaddr*)&lc->addr, &(socklen_t){sizeof(lc->addr)}), 0) ||
        listen(lc->fd, 16) < 0) {
        close(lc->fd); free(lc); return ncclSystemError;
    }
    memset(handle, 0, NCCL_NET_HANDLE_MAXSIZE);
    memcpy(handle, &lc->addr, sizeof(lc->addr));
    *listenComm = lc;
    return ncclSuccess;
}

static ncclResult_t setup_qps(int fd, scuffed_comm_t *comm) {
    scuffed_qp_pair_t *q = &comm->qpp;
    q->pd = g_dev.pd;
    q->hot_cq  = ibv_create_cq(g_dev.ctx, SCUFFED_CQ_DEPTH, NULL, NULL, 0);
    q->cold_cq = ibv_create_cq(g_dev.ctx, SCUFFED_CQ_DEPTH, NULL, NULL, 0);
    if (!q->hot_cq || !q->cold_cq) return ncclSystemError;
    q->hot_qp  = create_rc_qp(q->pd, q->hot_cq);
    q->cold_qp = create_rc_qp(q->pd, q->cold_cq);
    if (!q->hot_qp || !q->cold_qp) return ncclSystemError;

    scuffed_qp_info_t local = {
        .hot_lid = g_dev.lid, .hot_qpn = q->hot_qp->qp_num, .hot_psn = 0,
        .cold_lid = g_dev.lid, .cold_qpn = q->cold_qp->qp_num, .cold_psn = 0,
        .gid = g_dev.gid,
    };
    scuffed_qp_info_t remote;
    if (oob_xfer(fd, &local, sizeof(local), 1) || oob_xfer(fd, &remote, sizeof(remote), 0))
        return ncclSystemError;
    if (qp_bring_up(q->hot_qp, remote.hot_qpn, remote.hot_lid, remote.hot_psn,
                     &remote.gid, g_dev.port_num) ||
        qp_bring_up(q->cold_qp, remote.cold_qpn, remote.cold_lid, remote.cold_psn,
                     &remote.gid, g_dev.port_num))
        return ncclSystemError;
    return ncclSuccess;
}

static ncclResult_t scuffed_connect(int dev, void *handle, void **sendComm,
                                    ncclNetDeviceHandle_v8_t **sendDevComm) {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) return ncclSystemError;
    if (connect(fd, (struct sockaddr*)handle, sizeof(struct sockaddr_in)) < 0) {
        close(fd); *sendComm = NULL; return ncclSuccess;
    }
    scuffed_comm_t *c = calloc(1, sizeof(*c));
    if (!c) { close(fd); return ncclSystemError; }
    c->fd = fd;
    ncclResult_t r = setup_qps(fd, c);
    if (r != ncclSuccess) { close(fd); free(c); return r; }
    *sendComm = c;
    if (sendDevComm) *sendDevComm = NULL;
    return ncclSuccess;
}

static ncclResult_t scuffed_accept(void *listenComm, void **recvComm,
                                   ncclNetDeviceHandle_v8_t **recvDevComm) {
    scuffed_listen_comm_t *lc = (scuffed_listen_comm_t*)listenComm;
    int fd = accept(lc->fd, NULL, NULL);
    if (fd < 0) { *recvComm = NULL; return ncclSuccess; }
    scuffed_comm_t *c = calloc(1, sizeof(*c));
    if (!c) { close(fd); return ncclSystemError; }
    c->fd = fd;
    ncclResult_t r = setup_qps(fd, c);
    if (r != ncclSuccess) { close(fd); free(c); return r; }
    *recvComm = c;
    if (recvDevComm) *recvDevComm = NULL;
    return ncclSuccess;
}

/* ---- memory registration ---- */

static ncclResult_t scuffed_reg_mr(void *comm, void *data, size_t size, int type, void **mhandle) {
    struct ibv_mr *mr = ibv_reg_mr(g_dev.pd, data, size,
        IBV_ACCESS_LOCAL_WRITE|IBV_ACCESS_REMOTE_WRITE|IBV_ACCESS_REMOTE_READ);
    if (!mr) return ncclSystemError;
    scuffed_mr_handle_t *h = malloc(sizeof(*h));
    if (!h) { ibv_dereg_mr(mr); return ncclSystemError; }
    h->mr = mr;  *mhandle = h;
    return ncclSuccess;
}

static ncclResult_t scuffed_reg_mr_dmabuf(void *comm, void *data, size_t size,
                                          int type, uint64_t offset, int fd, void **mhandle) {
    return scuffed_reg_mr(comm, data, size, type, mhandle);
}

static ncclResult_t scuffed_dereg_mr(void *comm, void *mhandle) {
    scuffed_mr_handle_t *h = (scuffed_mr_handle_t*)mhandle;
    if (h) { if (h->mr) ibv_dereg_mr(h->mr); free(h); }
    return ncclSuccess;
}

/* ---- async send/recv: WFA classifier ---- */

static scuffed_request_t *alloc_req(scuffed_comm_t *c, int is_hot) {
    for (int i = 0; i < SCUFFED_MAX_REQUESTS; i++) {
        if (!c->reqs[i].used) {
            scuffed_request_t *r = &c->reqs[i];
            r->used = 1; r->done = 0; r->size = 0; r->is_hot = is_hot; r->qpp = &c->qpp;
            return r;
        }
    }
    return NULL;
}

static ncclResult_t scuffed_isend(void *sendComm, void *data, int size,
                                  int tag, void *mhandle, void **request) {
    scuffed_comm_t *c = (scuffed_comm_t*)sendComm;
    scuffed_mr_handle_t *h = (scuffed_mr_handle_t*)mhandle;
    int is_hot = (size < SCUFFED_HOT_THRESHOLD);

    scuffed_request_t *req = alloc_req(c, is_hot);
    if (!req) { *request = NULL; return ncclSuccess; }
    req->size = size;

    struct ibv_sge sge = { .addr = (uintptr_t)data, .length = size, .lkey = h->mr->lkey };
    struct ibv_send_wr wr = {
        .wr_id = (uintptr_t)req, .sg_list = &sge, .num_sge = 1,
        .opcode = IBV_WR_SEND, .send_flags = IBV_SEND_SIGNALED,
    };
    if (is_hot && size <= 256) wr.send_flags |= IBV_SEND_INLINE;

    struct ibv_send_wr *bad;
    if (ibv_post_send(is_hot ? c->qpp.hot_qp : c->qpp.cold_qp, &wr, &bad)) {
        req->used = 0; *request = NULL; return ncclSuccess;
    }
    *request = req;
    return ncclSuccess;
}

static ncclResult_t scuffed_irecv(void *recvComm, int n, void **data,
                                  int *sizes, int *tags, void **mhandles, void **request) {
    scuffed_comm_t *c = (scuffed_comm_t*)recvComm;
    scuffed_mr_handle_t *h = (scuffed_mr_handle_t*)mhandles[0];
    int size = sizes[0], is_hot = (size < SCUFFED_HOT_THRESHOLD);

    scuffed_request_t *req = alloc_req(c, is_hot);
    if (!req) { *request = NULL; return ncclSuccess; }
    req->size = size;

    struct ibv_sge sge = { .addr = (uintptr_t)data[0], .length = size, .lkey = h->mr->lkey };
    struct ibv_recv_wr wr = { .wr_id = (uintptr_t)req, .sg_list = &sge, .num_sge = 1 };
    struct ibv_recv_wr *bad;
    if (ibv_post_recv(is_hot ? c->qpp.hot_qp : c->qpp.cold_qp, &wr, &bad)) {
        req->used = 0; *request = NULL; return ncclSuccess;
    }
    *request = req;
    return ncclSuccess;
}

static ncclResult_t scuffed_iflush(void *recvComm, int n, void **data,
                                   int *sizes, void **mhandles, void **request) {
    *request = NULL; return ncclSuccess; /* host-only, no GPU flush needed */
}

static ncclResult_t scuffed_test(void *request, int *done, int *sizes) {
    scuffed_request_t *req = (scuffed_request_t*)request;
    *done = 0;
    if (req->done) { *done = 1; if (sizes) *sizes = req->size; req->used = 0; return ncclSuccess; }

    struct ibv_wc wc;
    int ne = ibv_poll_cq(req->is_hot ? req->qpp->hot_cq : req->qpp->cold_cq, 1, &wc);
    if (ne < 0) return ncclSystemError;
    if (ne > 0) {
        if (wc.status != IBV_WC_SUCCESS) { LOG_WARN("CQ: %s", ibv_wc_status_str(wc.status)); return ncclSystemError; }
        scuffed_request_t *cr = (scuffed_request_t*)(uintptr_t)wc.wr_id;
        cr->done = 1;
        if (cr->size == 0 && wc.byte_len > 0) cr->size = wc.byte_len;
        if (cr == req) { *done = 1; if (sizes) *sizes = req->size; req->used = 0; }
    }
    return ncclSuccess;
}

/* ---- teardown ---- */

static void destroy_qpp(scuffed_qp_pair_t *q) {
    if (q->hot_qp)  ibv_destroy_qp(q->hot_qp);
    if (q->cold_qp) ibv_destroy_qp(q->cold_qp);
    if (q->hot_cq)  ibv_destroy_cq(q->hot_cq);
    if (q->cold_cq) ibv_destroy_cq(q->cold_cq);
}

static ncclResult_t scuffed_close_send(void *sendComm) {
    scuffed_comm_t *c = (scuffed_comm_t*)sendComm;
    if (c) { destroy_qpp(&c->qpp); if (c->fd >= 0) close(c->fd); free(c); }
    return ncclSuccess;
}
static ncclResult_t scuffed_close_recv(void *r) { return scuffed_close_send(r); }

static ncclResult_t scuffed_close_listen(void *listenComm) {
    scuffed_listen_comm_t *lc = (scuffed_listen_comm_t*)listenComm;
    if (lc) { if (lc->fd >= 0) close(lc->fd); free(lc); }
    return ncclSuccess;
}

static ncclResult_t scuffed_get_device_mr(void *c, void *m, void **d) { return ncclInternalError; }
static ncclResult_t scuffed_irecv_consumed(void *r, int n, void *req) { return ncclSuccess; }

/* ---- export ---- */

ncclNet_v8_t ncclNetPlugin_v8 = {
    .name          = "ScuffedRDMA",
    .init          = scuffed_init,
    .devices       = scuffed_devices,
    .getProperties = scuffed_get_properties,
    .listen        = scuffed_listen,
    .connect       = scuffed_connect,
    .accept        = scuffed_accept,
    .regMr         = scuffed_reg_mr,
    .regMrDmaBuf   = scuffed_reg_mr_dmabuf,
    .deregMr       = scuffed_dereg_mr,
    .isend         = scuffed_isend,
    .irecv         = scuffed_irecv,
    .iflush        = scuffed_iflush,
    .test          = scuffed_test,
    .closeSend     = scuffed_close_send,
    .closeRecv     = scuffed_close_recv,
    .closeListen   = scuffed_close_listen,
    .getDeviceMr   = scuffed_get_device_mr,
    .irecvConsumed = scuffed_irecv_consumed,
};
