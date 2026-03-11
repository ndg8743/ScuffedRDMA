# NFS over SoftRoCE Setup

**Source URL:** https://wiki.linux-nfs.org/wiki/index.php/NFS_over_SoftRoCE_setup
**Date Accessed:** 2026-03-11

**Source:** Linux NFS Wiki
**Last Modified:** August 11, 2021

## Overview

"Soft ROCE is a software implementation of RoCE that allows RDMA to be used on any Ethernet adapter." This technology requires Linux kernels version 4.8 or later.

## Common Setup Steps (Client & Server)

The process begins by verifying the `rdma_rxe` kernel module availability and enabling three kernel configuration options: `CONFIG_INFINIBAND`, `CONFIG_INFINIBAND_RDMAVT`, and `CONFIG_RDMA_RXE`.

Users must install the `iproute2` package and execute the command: `sudo rdma link add rxe0 type rxe netdev eth0` to initialize the RDMA interface. Note: the deprecated `rxe_cfg` tool has been replaced by the `rdma` command as of January 2020.

### Connectivity Testing

The setup includes a ping test using `rping` to verify RDMA connectivity between machines before NFS deployment.

## NFS Configuration

**Server Setup:** Install `nfs-utils`, enable RDMA in `/etc/nfs.conf` by setting `rdma=y` and `rdma-port=20049`, create an export directory, and restart the NFS server.

**Client Setup:** Install `nfs-utils` and mount using: `sudo mount -o rdma,port=20049,vers=4.2 [server-ip]:/expdir /mnt/nfsmp`
