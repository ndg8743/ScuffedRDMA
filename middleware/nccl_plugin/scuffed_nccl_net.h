/*
 * scuffed_nccl_net.h - NCCL net plugin interface for libscuffedrdma
 *
 * Targets ncclNet_v8_t (NCCL 2.23.x). Self-contained: we define the
 * NCCL types directly rather than including nccl_net.h, because the
 * installed libnccl-dev package is missing nccl_common.h / net_device.h.
 * All definitions match the upstream NVIDIA headers exactly.
 */

#ifndef SCUFFED_NCCL_NET_H
#define SCUFFED_NCCL_NET_H

#include <stdint.h>
#include <stddef.h>
#include <infiniband/verbs.h>
#include <netinet/in.h>

/* ---- NCCL types (from nccl.h, nccl_common.h, net_device.h) ---- */

typedef enum {
    ncclSuccess         = 0,
    ncclUnhandledCudaError = 1,
    ncclSystemError     = 2,
    ncclInternalError   = 3,
    ncclInvalidArgument = 4,
    ncclInvalidUsage    = 5,
    ncclRemoteError     = 6,
    ncclInProgress      = 7,
} ncclResult_t;

typedef enum {
    NCCL_LOG_NONE=0, NCCL_LOG_VERSION=1, NCCL_LOG_WARN=2,
    NCCL_LOG_INFO=3, NCCL_LOG_ABORT=4, NCCL_LOG_TRACE=5
} ncclDebugLogLevel;

typedef void (*ncclDebugLogger_t)(ncclDebugLogLevel level, unsigned long flags,
                                  const char *file, int line,
                                  const char *fmt, ...);

#define NCCL_NET_HANDLE_MAXSIZE 128
#define NCCL_PTR_HOST   0x1
#define NCCL_PTR_CUDA   0x2
#define NCCL_PTR_DMABUF 0x4
#define NCCL_NET_MAX_REQUESTS 32

#define NCCL_NET_DEVICE_INVALID_VERSION 0x0

typedef enum {
    NCCL_NET_DEVICE_HOST   = 0,
    NCCL_NET_DEVICE_UNPACK = 1,
} ncclNetDeviceType;

typedef struct {
    ncclNetDeviceType netDeviceType;
    int               netDeviceVersion;
    void             *handle;
    size_t            size;
    int               needsProxyProgress;
} ncclNetDeviceHandle_v8_t;

/* ---- ncclNet_v8_t: the struct NCCL loads via dlsym ---- */

typedef struct {
    char            *name;
    char            *pciPath;
    uint64_t         guid;
    int              ptrSupport;
    int              regIsGlobal;
    int              speed;
    int              port;
    float            latency;
    int              maxComms;
    int              maxRecvs;
    ncclNetDeviceType netDeviceType;
    int              netDeviceVersion;
} ncclNetProperties_v8_t;

typedef struct {
    const char *name;
    ncclResult_t (*init)(ncclDebugLogger_t logFunction);
    ncclResult_t (*devices)(int *ndev);
    ncclResult_t (*getProperties)(int dev, ncclNetProperties_v8_t *props);
    ncclResult_t (*listen)(int dev, void *handle, void **listenComm);
    ncclResult_t (*connect)(int dev, void *handle, void **sendComm, ncclNetDeviceHandle_v8_t **sendDevComm);
    ncclResult_t (*accept)(void *listenComm, void **recvComm, ncclNetDeviceHandle_v8_t **recvDevComm);
    ncclResult_t (*regMr)(void *comm, void *data, size_t size, int type, void **mhandle);
    ncclResult_t (*regMrDmaBuf)(void *comm, void *data, size_t size, int type, uint64_t offset, int fd, void **mhandle);
    ncclResult_t (*deregMr)(void *comm, void *mhandle);
    ncclResult_t (*isend)(void *sendComm, void *data, int size, int tag, void *mhandle, void **request);
    ncclResult_t (*irecv)(void *recvComm, int n, void **data, int *sizes, int *tags, void **mhandles, void **request);
    ncclResult_t (*iflush)(void *recvComm, int n, void **data, int *sizes, void **mhandles, void **request);
    ncclResult_t (*test)(void *request, int *done, int *sizes);
    ncclResult_t (*closeSend)(void *sendComm);
    ncclResult_t (*closeRecv)(void *recvComm);
    ncclResult_t (*closeListen)(void *listenComm);
    ncclResult_t (*getDeviceMr)(void *comm, void *mhandle, void **dptr_mhandle);
    ncclResult_t (*irecvConsumed)(void *recvComm, int n, void *request);
} ncclNet_v8_t;

/* ---- Plugin-internal structures ---- */

#define SCUFFED_HOT_THRESHOLD   4096  /* bytes: < this goes to hot QP */
#define SCUFFED_MAX_REQUESTS    32
#define SCUFFED_CQ_DEPTH        256
#define SCUFFED_QP_DEPTH        128

/* Per-connection dual QP pair */
typedef struct {
    struct ibv_qp  *hot_qp;   /* small msgs, busy-poll CQ */
    struct ibv_qp  *cold_qp;  /* large msgs, standard CQ poll */
    struct ibv_cq  *hot_cq;
    struct ibv_cq  *cold_cq;
    struct ibv_pd  *pd;
} scuffed_qp_pair_t;

/* Async request tracking */
typedef struct {
    int              used;
    int              done;
    int              size;
    int              is_hot;
    scuffed_qp_pair_t *qpp;
} scuffed_request_t;

/* Send/recv comm */
typedef struct {
    scuffed_qp_pair_t qpp;
    scuffed_request_t reqs[SCUFFED_MAX_REQUESTS];
    int               fd;
} scuffed_comm_t;

/* Listen comm (TCP acceptor) */
typedef struct {
    int              fd;
    int              dev;
    struct sockaddr_in addr;
} scuffed_listen_comm_t;

/* MR handle */
typedef struct {
    struct ibv_mr *mr;
} scuffed_mr_handle_t;

/* OOB exchange payload for QP setup */
typedef struct {
    uint16_t      hot_lid;
    uint32_t      hot_qpn;
    uint32_t      hot_psn;
    uint16_t      cold_lid;
    uint32_t      cold_qpn;
    uint32_t      cold_psn;
    union ibv_gid gid;
} scuffed_qp_info_t;

/* Global device state */
typedef struct {
    struct ibv_context *ctx;
    struct ibv_pd      *pd;
    int                 port_num;
    uint16_t            lid;
    union ibv_gid       gid;
} scuffed_device_t;

#endif /* SCUFFED_NCCL_NET_H */
