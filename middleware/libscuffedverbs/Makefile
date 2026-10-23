# libscuffedverbs: native libibverbs implementation of the scuffed_fabric.h API.
# sv_bench is ../libscuffedfabric/sf_bench.c linked against it, so both stacks
# run the identical benchmark code. Needs libibverbs-dev (rdma-core).
CC ?= gcc
CFLAGS ?= -O2 -g -Wall -Wextra -fPIC -std=gnu11
LDLIBS = -libverbs -lpthread -lm
FAB = ../libscuffedfabric

all: libscuffedverbs.so sv_bench

libscuffedverbs.so: scuffed_verbs.c $(FAB)/scuffed_fabric.h
	$(CC) $(CFLAGS) -shared -o $@ scuffed_verbs.c $(LDLIBS)

sv_bench: $(FAB)/sf_bench.c scuffed_verbs.c $(FAB)/scuffed_fabric.h
	$(CC) $(CFLAGS) -DSF_BENCH_TOOL='"sv_bench"' -I$(FAB) -o $@ $(FAB)/sf_bench.c scuffed_verbs.c $(LDLIBS)

clean:
	rm -f libscuffedverbs.so sv_bench

.PHONY: all clean
