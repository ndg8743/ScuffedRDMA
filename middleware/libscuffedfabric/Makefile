# libscuffedfabric: libfabric dual-endpoint pool + sf_bench
# Needs libfabric-dev (fi_info --version >= 1.9). On the cluster:
#   sudo apt install libfabric-dev libfabric-bin
CC ?= gcc
CFLAGS ?= -O2 -g -Wall -Wextra -fPIC -std=gnu11
LDLIBS = -lfabric -lpthread -lm

all: libscuffedfabric.so sf_bench

libscuffedfabric.so: scuffed_fabric.c scuffed_fabric.h
	$(CC) $(CFLAGS) -shared -o $@ scuffed_fabric.c $(LDLIBS)

sf_bench: sf_bench.c scuffed_fabric.c scuffed_fabric.h
	$(CC) $(CFLAGS) -o $@ sf_bench.c scuffed_fabric.c $(LDLIBS)

clean:
	rm -f libscuffedfabric.so sf_bench

.PHONY: all clean
