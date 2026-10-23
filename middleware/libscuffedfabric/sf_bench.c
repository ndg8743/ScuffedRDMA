/*
 * sf_bench: benchmarks for libscuffedfabric. Run the same command on both
 * sides, one with -r server and one with -r client.
 *
 * Modes
 *   sig   hot-path ping-pong, one completion-signaling mechanism per run:
 *           cq        fi_writedata, receiver polls RX CQ for remote CQ data
 *           flag      fi_write, last 8 bytes carry a sequence, receiver spins on memory
 *           sentinel  fi_write payload then 8-byte sentinel write (needs WAW ordering)
 *           cntr      fi_write, receiver polls a FI_REMOTE_WRITE counter (needs FI_RMA_EVENT)
 *           read      fi_write then 8-byte fi_read; initiator-side delivery confirmation,
 *                     one-way (GPFS-style flush), not a ping-pong
 *         reports one-way latency (RTT/2) percentiles per size
 *   bw    streaming one-sided writes on one class, window W, MB/s per size
 *   hol   mixed traffic: cold class streams bulk writes while the hot class
 *         ping-pongs small writes. Reports hot RTT percentiles and cold MB/s.
 *         With -s (single endpoint) both classes share one endpoint: the
 *         head-of-line baseline.
 *
 * Output: one JSON object on stdout (or -j file).
 */
#define _GNU_SOURCE
#include "scuffed_fabric.h"
#ifndef SF_BENCH_TOOL
#define SF_BENCH_TOOL "sf_bench"
#endif

#include <getopt.h>
#include <linux/perf_event.h>
#include <math.h>
#include <poll.h>
#include <stdarg.h>
#include <rdma/fi_errno.h>
#include <pthread.h>
#include <sched.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/syscall.h>
#include <unistd.h>

#define HOT_RX 0ul
#define HOT_TX (512ul << 10)
#define SENT_RX (1000ul << 10)
#define SENT_TX (1004ul << 10)
#define COLD_OFF (2ul << 20)
#define STOP_IMM 0xFFFFFFF0ull
#define BW_DONE_IMM 0xFFFFFFE0ull

typedef struct {
    const char *role, *host, *bind, *mode, *mech, *json;
    int port, iters, warmup, window, single, hot_cntr, cold_wait, perf, cold_on, bw_cls, timeout_ms;
    size_t sizes[64];
    int nsizes;
    size_t hot_size, cold_size, arena;
    int hot_gap_us;
    int hot_cpu, cold_cpu;
    sf_opts_t o;
} args_t;

/* ---------------------------------------------------------------- utils */

typedef struct { char *s; size_t n, cap; } sbuf;
static void sb(sbuf *b, const char *fmt, ...) __attribute__((format(printf, 2, 3)));
static void sb(sbuf *b, const char *fmt, ...) {
    va_list ap;
    for (;;) {
        va_start(ap, fmt);
        int w = vsnprintf(b->s + b->n, b->cap - b->n, fmt, ap);
        va_end(ap);
        if (w >= 0 && (size_t)w < b->cap - b->n) { b->n += (size_t)w; return; }
        b->cap = b->cap ? b->cap * 2 : 4096;
        b->s = realloc(b->s, b->cap);
    }
}

static int cmpd(const void *a, const void *b) {
    double x = *(const double *)a, y = *(const double *)b;
    return x < y ? -1 : x > y;
}

static double pct(double *s, int n, double p) {
    if (n <= 0) return NAN;
    double k = (n - 1) * p / 100.0;
    int lo = (int)floor(k), hi = (int)ceil(k);
    return s[lo] + (s[hi] - s[lo]) * (k - lo);
}

static void stats_json(sbuf *b, double *s, int n) {
    qsort(s, (size_t)n, sizeof *s, cmpd);
    double sum = 0;
    for (int i = 0; i < n; i++) sum += s[i];
    sb(b, "\"n\":%d,\"mean_us\":%.4f,\"min_us\":%.4f,\"p50_us\":%.4f,\"p90_us\":%.4f,\"p99_us\":%.4f,\"p999_us\":%.4f,\"max_us\":%.4f",
       n, n ? sum / n : NAN, n ? s[0] : NAN, pct(s, n, 50), pct(s, n, 90), pct(s, n, 99), pct(s, n, 99.9), n ? s[n - 1] : NAN);
}

static void die(const char *what, int r) {
    fprintf(stderr, SF_BENCH_TOOL ": %s failed: %s (%d)\n", what, sf_strerror(r), r);
    exit(2);
}

/* instructions retired in user space by this thread */
static int perf_open(void) {
    struct perf_event_attr pa;
    memset(&pa, 0, sizeof pa);
    pa.type = PERF_TYPE_HARDWARE;
    pa.size = sizeof pa;
    pa.config = PERF_COUNT_HW_INSTRUCTIONS;
    pa.exclude_kernel = 1;
    pa.exclude_hv = 1;
    return (int)syscall(SYS_perf_event_open, &pa, 0, -1, -1, 0);
}
static inline uint64_t perf_read(int fd) {
    uint64_t v = 0;
    if (fd >= 0 && read(fd, &v, sizeof v) != sizeof v) v = 0;
    return v;
}

static void pin(int cpu) {
    if (cpu < 0) return;
    cpu_set_t set;
    CPU_ZERO(&set);
    CPU_SET(cpu, &set);
    if (pthread_setaffinity_np(pthread_self(), sizeof set, &set))
        fprintf(stderr, "sf_bench: could not pin to cpu %d\n", cpu);
}

static void spin_us(int us) {
    if (us <= 0) return;
    uint64_t end = sf_now_ns() + (uint64_t)us * 1000ull;
    while (sf_now_ns() < end) __builtin_ia32_pause();
}

/* ------------------------------------------------------------ signaling */

enum { M_CQ, M_FLAG, M_SENT, M_CNTR, M_READ };

static int mech_id(const char *m) {
    if (!strcmp(m, "cq")) return M_CQ;
    if (!strcmp(m, "flag")) return M_FLAG;
    if (!strcmp(m, "sentinel")) return M_SENT;
    if (!strcmp(m, "cntr")) return M_CNTR;
    if (!strcmp(m, "read")) return M_READ;
    fprintf(stderr, "unknown mechanism %s\n", m);
    exit(1);
}

static uint64_t imm_mask(sf_ctx_t *c) {
    int b = sf_cq_data_size(c, SF_HOT);
    return b >= 8 ? ~0ull : (1ull << (8 * b)) - 1;
}

static void sig_send(sf_ctx_t *c, int m, size_t size, uint64_t seq) {
    char *buf = sf_buf(c);
    int r;
    switch (m) {
    case M_CQ:
        r = sf_write(c, SF_HOT, HOT_TX, size, HOT_RX, seq & imm_mask(c), SF_F_IMM | SF_F_INJECT);
        break;
    case M_FLAG:
        memcpy(buf + HOT_TX + size - 8, &seq, 8);
        r = sf_write(c, SF_HOT, HOT_TX, size, HOT_RX, 0, SF_F_INJECT);
        break;
    case M_SENT:
        r = sf_write(c, SF_HOT, HOT_TX, size, HOT_RX, 0, SF_F_INJECT | SF_F_MORE);
        if (!r) {
            memcpy(buf + SENT_TX, &seq, 8);
            r = sf_write(c, SF_HOT, SENT_TX, 8, SENT_RX, 0, SF_F_INJECT);
        }
        break;
    case M_CNTR:
        r = sf_write(c, SF_HOT, HOT_TX, size, HOT_RX, 0, SF_F_INJECT);
        break;
    default:
        r = -1;
    }
    if (r) die("sig send", r);
    sf_progress(c, SF_HOT);
}

static void sig_wait(sf_ctx_t *c, int m, size_t size, uint64_t seq, uint64_t *rma_expect) {
    char *buf = sf_buf(c);
    sf_rx_ev_t ev[16];
    if (m == M_CQ) {
        uint64_t want = seq & imm_mask(c);
        for (;;) {
            int n = sf_poll_rx(c, SF_HOT, ev, 16);
            if (n < 0) die("poll_rx", n);
            for (int i = 0; i < n; i++)
                if (ev[i].kind == SF_RX_DATA && ev[i].data == want) return;
            sf_progress(c, SF_HOT);
        }
    }
    if (m == M_CNTR) {
        (*rma_expect)++;
        while (sf_rma_events(c, SF_HOT) < *rma_expect) sf_progress(c, SF_HOT);
        return;
    }
    volatile uint64_t *f = (volatile uint64_t *)(buf + (m == M_FLAG ? HOT_RX + size - 8 : SENT_RX));
    while (__atomic_load_n(f, __ATOMIC_ACQUIRE) != seq) {
        sf_progress(c, SF_HOT);
        sf_poll_rx(c, SF_HOT, ev, 16); /* drives manual-progress providers */
    }
}

static void run_sig(sf_ctx_t *c, args_t *a, sbuf *out) {
    int m = mech_id(a->mech), server = !strcmp(a->role, "server");
    int pfd = a->perf && !server ? perf_open() : -1;
    /* both sides must agree, or one side waits forever */
    uint64_t mine = 1, theirs = 1;
    if (m == M_SENT) mine = (uint64_t)sf_capable(c, SF_HOT, "waw");
    if (m == M_CNTR) {
        /* a bound counter is not proof the provider counts: probe one write each way */
        mine = (uint64_t)sf_capable(c, SF_HOT, "rma_event");
        if (sf_oob_xchg(c, mine, &theirs)) die("oob xchg", -1);
        if (mine && theirs) {
            for (int dir = 0; dir < 2; dir++) {
                int writer = (dir == 0) != server;
                uint64_t before = sf_rma_events(c, SF_HOT);
                sf_oob_barrier(c);
                if (writer) {
                    if (sf_write(c, SF_HOT, HOT_TX, 8, HOT_RX, 0, 0)) die("probe write", -1);
                    sf_wait_tx(c, SF_HOT, sf_tx_posted(c, SF_HOT), a->timeout_ms);
                } else {
                    uint64_t end = sf_now_ns() + 500000000ull;
                    while (sf_rma_events(c, SF_HOT) == before && sf_now_ns() < end) sf_progress(c, SF_HOT);
                    if (sf_rma_events(c, SF_HOT) == before) mine = 0;
                }
                sf_oob_barrier(c);
            }
        }
        theirs = 1;
    }
    if (sf_oob_xchg(c, mine, &theirs)) die("oob xchg", -1);
    if (m == M_SENT && !(mine && theirs)) {
        sb(out, "\"skipped\":\"provider does not advertise write-after-write ordering\"");
        return;
    }
    if (m == M_CNTR && !(mine && theirs)) {
        sb(out, "\"skipped\":\"remote-write counter missing or not incremented by this provider (probed)\"");
        return;
    }
    uint64_t seq = 1, rma_expect = sf_rma_events(c, SF_HOT);
    double *samp = malloc(sizeof(double) * (size_t)a->iters);
    double *post_ins = malloc(sizeof(double) * (size_t)a->iters);
    sb(out, "\"results\":[");
    for (int si = 0; si < a->nsizes; si++) {
        size_t size = a->sizes[si];
        if ((m == M_FLAG) && size < 8) continue;
        sf_oob_barrier(c);
        int total = a->warmup + a->iters, n = 0;
        if (m == M_READ) {
            if (!server) {
                for (int i = 0; i < total; i++) {
                    uint64_t i0 = perf_read(pfd), t0 = sf_now_ns();
                    int r = sf_write(c, SF_HOT, HOT_TX, size, HOT_RX, 0, SF_F_INJECT | SF_F_MORE);
                    if (!r) r = sf_read(c, SF_HOT, SENT_TX, 8, HOT_RX);
                    uint64_t i1 = perf_read(pfd);
                    if (r) die("write+read", r);
                    r = sf_wait_tx(c, SF_HOT, sf_tx_posted(c, SF_HOT), a->timeout_ms);
                    if (r) die("wait read", r);
                    uint64_t t1 = sf_now_ns();
                    if (i >= a->warmup) { samp[n] = (double)(t1 - t0) / 1e3; post_ins[n] = (double)(i1 - i0); n++; }
                }
                char go = 1;
                if (write(sf_oob_fd(c), &go, 1) != 1) die("oob", -1);
            } else {
                struct pollfd p = {.fd = sf_oob_fd(c), .events = POLLIN};
                sf_rx_ev_t ev[16];
                while (poll(&p, 1, 0) == 0) { sf_progress(c, SF_HOT); sf_poll_rx(c, SF_HOT, ev, 16); }
                char go;
                if (read(sf_oob_fd(c), &go, 1) != 1) die("oob", -1);
            }
        } else {
            for (int i = 0; i < total; i++, seq++) {
                if (!server) {
                    uint64_t i0 = perf_read(pfd), t0 = sf_now_ns();
                    sig_send(c, m, size, seq);
                    uint64_t i1 = perf_read(pfd);
                    sig_wait(c, m, size, seq, &rma_expect);
                    uint64_t t1 = sf_now_ns();
                    if (i >= a->warmup) { samp[n] = (double)(t1 - t0) / 2e3; post_ins[n] = (double)(i1 - i0); n++; }
                } else {
                    sig_wait(c, m, size, seq, &rma_expect);
                    sig_send(c, m, size, seq);
                }
            }
        }
        if (!server) {
            if (out->s[out->n - 1] != '[') sb(out, ",");
            sb(out, "{\"size\":%zu,", size);
            stats_json(out, samp, n);
            if (pfd >= 0) {
                double s = 0;
                for (int i = 0; i < n; i++) s += post_ins[i];
                sb(out, ",\"post_instructions_mean\":%.1f", n ? s / n : NAN);
            }
            sb(out, ",\"metric\":\"%s\"}", m == M_READ ? "write_plus_read_completion_us" : "one_way_us_rtt_over_2");
        }
        /* reap outstanding local completions before the next size */
        sf_wait_tx(c, SF_HOT, sf_tx_posted(c, SF_HOT), a->timeout_ms);
    }
    sb(out, "]");
    sb(out, ",\"perf_counters\":%s", pfd >= 0 ? "true" : "false");
    free(samp);
    free(post_ins);
}

/* -------------------------------------------------------------------- bw */

static void run_bw(sf_ctx_t *c, args_t *a, sbuf *out) {
    int server = !strcmp(a->role, "server"), cls = a->bw_cls;
    size_t region = sf_buf_len(c) - COLD_OFF;
    sb(out, "\"class\":\"%s\",\"window\":%d,\"results\":[", cls == SF_HOT ? "hot" : "cold", a->window);
    for (int si = 0; si < a->nsizes; si++) {
        size_t size = a->sizes[si];
        if (size > region) continue;
        size_t slots = region / size;
        sf_oob_barrier(c);
        if (!server) {
            uint64_t base = sf_tx_posted(c, cls), t0 = sf_now_ns();
            for (int i = 0; i < a->iters; i++) {
                while (sf_tx_posted(c, cls) - sf_tx_done(c, cls) >= (uint64_t)a->window) {
                    int r = a->cold_wait && cls == SF_COLD ? sf_wait_tx(c, cls, sf_tx_done(c, cls) + 1, a->timeout_ms)
                                                           : sf_progress(c, cls);
                    if (r < 0) die("progress", r);
                }
                size_t off = COLD_OFF + ((size_t)i % slots) * size;
                int r = sf_write(c, cls, off, size, off, 0, SF_F_MORE * (i + 1 < a->iters));
                if (r) die("bw write", r);
            }
            int r = sf_wait_tx(c, cls, base + (uint64_t)a->iters, a->timeout_ms);
            if (r) die("bw drain", r);
            uint64_t t1 = sf_now_ns();
            r = sf_write(c, cls, 0, 8, 0, BW_DONE_IMM & imm_mask(c), SF_F_IMM | SF_F_INJECT);
            if (r) die("bw done", r);
            double secs = (double)(t1 - t0) / 1e9;
            if (out->s[out->n - 1] != '[') sb(out, ",");
            sb(out, "{\"size\":%zu,\"iters\":%d,\"seconds\":%.6f,\"MBps\":%.3f,\"Gbps\":%.4f}", size, a->iters, secs,
               (double)size * a->iters / secs / 1e6, (double)size * a->iters * 8 / secs / 1e9);
            sf_wait_tx(c, cls, sf_tx_posted(c, cls), a->timeout_ms);
        } else {
            sf_rx_ev_t ev[16];
            int done = 0;
            while (!done) {
                int n = sf_poll_rx(c, cls, ev, 16);
                if (n < 0) die("bw poll", n);
                for (int i = 0; i < n; i++)
                    if (ev[i].kind == SF_RX_DATA && ev[i].data == (BW_DONE_IMM & imm_mask(c))) done = 1;
                sf_progress(c, cls);
            }
        }
    }
    sb(out, "]");
}

/* ------------------------------------------------------------------- hol */

typedef struct {
    sf_ctx_t *c;
    args_t *a;
    _Atomic int stop;
    uint64_t bytes, t0, t1, ops;
} cold_t;

static void *cold_client(void *p) {
    cold_t *x = p;
    sf_ctx_t *c = x->c;
    args_t *a = x->a;
    size_t region = sf_buf_len(c) - COLD_OFF, slots = region / a->cold_size;
    pin(a->cold_cpu);
    uint64_t base = sf_tx_done(c, SF_COLD), i = 0;
    x->t0 = sf_now_ns();
    while (!atomic_load(&x->stop)) {
        while (sf_tx_posted(c, SF_COLD) - sf_tx_done(c, SF_COLD) >= (uint64_t)a->window && !atomic_load(&x->stop)) {
            int r = a->cold_wait ? sf_wait_tx(c, SF_COLD, sf_tx_done(c, SF_COLD) + 1, 1000) : sf_progress(c, SF_COLD);
            if (r < 0 && r != -FI_ETIMEDOUT) die("cold progress", r);
        }
        if (atomic_load(&x->stop)) break;
        size_t off = COLD_OFF + (size_t)(i++ % slots) * a->cold_size;
        int r = sf_write(c, SF_COLD, off, a->cold_size, off, 0, 0);
        if (r) die("cold write", r);
    }
    sf_wait_tx(c, SF_COLD, sf_tx_posted(c, SF_COLD), a->timeout_ms);
    x->t1 = sf_now_ns();
    x->ops = sf_tx_done(c, SF_COLD) - base;
    x->bytes = x->ops * a->cold_size;
    return NULL;
}

/* Target-side progress for the cold endpoint. Needed by manual-progress
 * providers (rxm, shm) and, in practice, by tcp, which advertises auto
 * progress but stalls RMA once socket buffers fill unless the target reads
 * its CQ. On verbs it polls an empty CQ. It yields between polls so it does
 * not compete with the hot echo loop for a core. */
static void *cold_server_progress(void *p) {
    cold_t *x = p;
    sf_rx_ev_t ev[16];
    pin(x->a->cold_cpu);
    while (!atomic_load(&x->stop)) {
        int a = sf_progress(x->c, SF_COLD);
        int b = sf_poll_rx(x->c, SF_COLD, ev, 16);
        if (a <= 0 && b <= 0) sched_yield();
    }
    return NULL;
}

static void run_hol(sf_ctx_t *c, args_t *a, sbuf *out) {
    int server = !strcmp(a->role, "server");
    uint64_t mask = imm_mask(c);
    cold_t cold = {.c = c, .a = a};
    pthread_t th;
    int have_thread = 0;
    pin(a->hot_cpu);
    sf_oob_barrier(c);
    if (!server) {
        if (a->cold_on) { pthread_create(&th, NULL, cold_client, &cold); have_thread = 1; }
        spin_us(20000); /* let the cold stream reach steady state */
        int total = a->warmup + a->iters, n = 0;
        double *samp = malloc(sizeof(double) * (size_t)a->iters);
        sf_rx_ev_t ev[16];
        for (int i = 0; i < total; i++) {
            uint64_t want = (uint64_t)(i + 1) & mask, t0 = sf_now_ns();
            int r = sf_write(c, SF_HOT, HOT_TX, a->hot_size, HOT_RX, want, SF_F_IMM | SF_F_INJECT);
            if (r) die("hot write", r);
            for (int got = 0; !got;) {
                int k = sf_poll_rx(c, SF_HOT, ev, 16);
                if (k < 0) die("hot poll", k);
                for (int j = 0; j < k; j++)
                    if (ev[j].kind == SF_RX_DATA && ev[j].data == want) got = 1;
                if (sf_progress(c, SF_HOT) < 0) die("hot progress", -1);
            }
            uint64_t t1 = sf_now_ns();
            if (i >= a->warmup) samp[n++] = (double)(t1 - t0) / 1e3;
            spin_us(a->hot_gap_us);
        }
        atomic_store(&cold.stop, 1);
        if (have_thread) pthread_join(th, NULL);
        int r = sf_write(c, SF_HOT, HOT_TX, 8, HOT_RX, STOP_IMM & mask, SF_F_IMM | SF_F_INJECT);
        if (r) die("stop", r);
        sf_wait_tx(c, SF_HOT, sf_tx_posted(c, SF_HOT), a->timeout_ms);
        sb(out, "\"hot_rtt\":{");
        stats_json(out, samp, n);
        double secs = have_thread && cold.t1 > cold.t0 ? (double)(cold.t1 - cold.t0) / 1e9 : 0;
        sb(out, "},\"cold\":{\"on\":%d,\"size\":%zu,\"window\":%d,\"ops\":%llu,\"seconds\":%.6f,\"MBps\":%.3f}", a->cold_on,
           a->cold_size, a->window, (unsigned long long)cold.ops, secs, secs > 0 ? (double)cold.bytes / secs / 1e6 : 0.0);
        sb(out, ",\"hot_size\":%zu,\"hot_gap_us\":%d,\"hot_cpu\":%d,\"cold_cpu\":%d", a->hot_size, a->hot_gap_us, a->hot_cpu, a->cold_cpu);
        free(samp);
    } else {
        if (!a->single) {
            pthread_create(&th, NULL, cold_server_progress, &cold);
            have_thread = 1;
        }
        sf_rx_ev_t ev[16];
        for (int done = 0; !done;) {
            int k = sf_poll_rx(c, SF_HOT, ev, 16);
            if (k < 0) die("server poll", k);
            for (int j = 0; j < k; j++) {
                if (ev[j].kind != SF_RX_DATA) continue;
                if (ev[j].data == (STOP_IMM & mask)) { done = 1; break; }
                int r = sf_write(c, SF_HOT, HOT_TX, a->hot_size, HOT_RX, ev[j].data, SF_F_IMM | SF_F_INJECT);
                if (r) die("echo", r);
            }
            sf_progress(c, SF_HOT);
        }
        atomic_store(&cold.stop, 1);
        if (have_thread) pthread_join(th, NULL);
        sb(out, "\"served\":true");
    }
}

/* ------------------------------------------------------------------ main */

static int ep_type(const char *s) { return !strcmp(s, "rdm") ? SF_EP_RDM : SF_EP_MSG; }

static void usage(void) {
    fprintf(stderr,
            "usage: sf_bench -r server|client -H host_or_bind_ip [-P port] -m sig|bw|hol\n"
            "  -p prov           provider for both classes (verbs, tcp, shm, verbs;ofi_rxm, tcp;ofi_rxm)\n"
            "  --hot-prov P --cold-prov P   per-class provider\n"
            "  -t msg|rdm        endpoint type for both; --hot-ep / --cold-ep per class\n"
            "  -d domain         domain filter (rxe0, mlx5_0, lo)\n"
            "  -s                single endpoint for both classes (HOL baseline)\n"
            "  --hot-cntr        hot TX completions via fi_cntr (selective completion)\n"
            "  --cold-wait       cold TX CQ with wait object (fi_cq_sread)\n"
            "  -M mech           sig mechanism: cq flag sentinel cntr read\n"
            "  -S s1,s2,...      sizes (bytes); -n iters; -w warmup; -W window\n"
            "  --hot-size --cold-size --hot-gap-us --no-cold   (hol)\n"
            "  --bw-class hot|cold --arena-mb N --perf -j out.json --timeout-ms N\n"
            "  --hot-cpu N --cold-cpu N   pin hot loop / cold thread (hol)\n");
    exit(1);
}

static void parse_sizes(args_t *a, char *s) {
    a->nsizes = 0;
    for (char *t = strtok(s, ","); t && a->nsizes < 64; t = strtok(NULL, ",")) {
        char *e;
        double v = strtod(t, &e);
        if (*e == 'K' || *e == 'k') v *= 1024;
        else if (*e == 'M' || *e == 'm') v *= 1024 * 1024;
        a->sizes[a->nsizes++] = (size_t)v;
    }
}

int main(int argc, char **argv) {
    args_t a;
    memset(&a, 0, sizeof a);
    sf_opts_default(&a.o);
    a.role = "client"; a.host = "127.0.0.1"; a.mode = "sig"; a.mech = "cq";
    a.port = 19870; a.iters = 10000; a.warmup = 500; a.window = 16; a.cold_on = 1; a.bw_cls = SF_COLD;
    a.hot_size = 64; a.cold_size = 1 << 20; a.arena = 64; a.timeout_ms = 60000;
    a.hot_cpu = a.cold_cpu = -1;
    char defsizes[] = "8,64,512,4096,16384,65536";
    parse_sizes(&a, defsizes);
    static struct option lo[] = {
        {"hot-prov", 1, 0, 1}, {"cold-prov", 1, 0, 2}, {"hot-ep", 1, 0, 3}, {"cold-ep", 1, 0, 4},
        {"hot-cntr", 0, 0, 5}, {"cold-wait", 0, 0, 6}, {"hot-size", 1, 0, 7}, {"cold-size", 1, 0, 8},
        {"hot-gap-us", 1, 0, 9}, {"no-cold", 0, 0, 10}, {"bw-class", 1, 0, 11}, {"arena-mb", 1, 0, 12},
        {"perf", 0, 0, 13}, {"timeout-ms", 1, 0, 14}, {"rma-event", 0, 0, 15}, {"hot-cpu", 1, 0, 16}, {"cold-cpu", 1, 0, 17}, {0, 0, 0, 0}};
    int ch;
    while ((ch = getopt_long(argc, argv, "r:H:P:m:p:t:d:sM:S:n:w:W:j:h", lo, NULL)) != -1) {
        switch (ch) {
        case 'r': a.role = optarg; break;
        case 'H': a.host = optarg; break;
        case 'P': a.port = atoi(optarg); break;
        case 'm': a.mode = optarg; break;
        case 'p': a.o.provider[0] = a.o.provider[1] = optarg; break;
        case 't': a.o.ep_type[0] = a.o.ep_type[1] = ep_type(optarg); break;
        case 'd': a.o.domain = optarg; break;
        case 's': a.single = a.o.single_ep = 1; break;
        case 'M': a.mech = optarg; break;
        case 'S': parse_sizes(&a, optarg); break;
        case 'n': a.iters = atoi(optarg); break;
        case 'w': a.warmup = atoi(optarg); break;
        case 'W': a.window = atoi(optarg); break;
        case 'j': a.json = optarg; break;
        case 1: a.o.provider[0] = optarg; break;
        case 2: a.o.provider[1] = optarg; break;
        case 3: a.o.ep_type[0] = ep_type(optarg); break;
        case 4: a.o.ep_type[1] = ep_type(optarg); break;
        case 5: a.hot_cntr = 1; a.o.hot_comp = SF_COMP_CNTR; break;
        case 6: a.cold_wait = a.o.cold_wait = 1; break;
        case 7: a.hot_size = (size_t)atol(optarg); break;
        case 8: a.cold_size = (size_t)atol(optarg); break;
        case 9: a.hot_gap_us = atoi(optarg); break;
        case 10: a.cold_on = 0; break;
        case 11: a.bw_cls = !strcmp(optarg, "hot") ? SF_HOT : SF_COLD; break;
        case 12: a.arena = (size_t)atol(optarg); break;
        case 13: a.perf = 1; break;
        case 14: a.timeout_ms = atoi(optarg); break;
        case 15: a.o.rma_event = 1; break;
        case 16: a.hot_cpu = atoi(optarg); break;
        case 17: a.cold_cpu = atoi(optarg); break;
        default: usage();
        }
    }
    if (!strcmp(a.mode, "sig") && !strcmp(a.mech, "cntr")) a.o.rma_event = 1;
    a.o.arena_bytes = a.arena << 20;
    if (a.o.tx_depth[SF_COLD] < (size_t)a.window * 2) a.o.tx_depth[SF_COLD] = (size_t)a.window * 2;
    int server = !strcmp(a.role, "server");

    sf_ctx_t *c = sf_open(&a.o);
    if (!c) die("sf_open", -1);
    int r = server ? sf_listen(c, a.host, a.port, a.timeout_ms) : sf_connect(c, a.host, a.port, a.timeout_ms);
    if (r) die(server ? "sf_listen" : "sf_connect", r);

    sbuf out = {0};
    char hn[256] = "";
    gethostname(hn, sizeof hn);
    sb(&out, "{\"tool\":\"" SF_BENCH_TOOL "\",\"host\":\"%s\",\"role\":\"%s\",\"mode\":\"%s\",\"single_ep\":%d,", hn, a.role, a.mode, a.single);
    if (!strcmp(a.mode, "sig")) sb(&out, "\"mech\":\"%s\",", a.mech);
    sb(&out, "\"hot\":\"%s\",", sf_describe(c, SF_HOT));
    sb(&out, "\"cold\":\"%s\",", sf_describe(c, SF_COLD));
    sb(&out, "\"iters\":%d,\"warmup\":%d,", a.iters, a.warmup);

    if (!strcmp(a.mode, "sig")) run_sig(c, &a, &out);
    else if (!strcmp(a.mode, "bw")) run_bw(c, &a, &out);
    else if (!strcmp(a.mode, "hol")) run_hol(c, &a, &out);
    else usage();
    sb(&out, "}\n");

    sf_oob_barrier(c);
    if (a.json) {
        FILE *f = fopen(a.json, "w");
        if (!f) { perror(a.json); return 2; }
        fputs(out.s, f);
        fclose(f);
    } else {
        fputs(out.s, stdout);
    }
    sf_close(c);
    free(out.s);
    return 0;
}
