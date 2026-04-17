CC = gcc
CFLAGS = -Wall -O2 -fPIC
LDFLAGS = -shared -libverbs

all: libscuffed_nccl_net.so

libscuffed_nccl_net.so: scuffed_nccl_net.c scuffed_nccl_net.h
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

clean:
	rm -f libscuffed_nccl_net.so
