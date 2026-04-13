# US20240419364A1: Tiering Data Strategy for a Distributed Storage System
**Source URL:** https://patents.google.com/patent/US20240419364A1/en
**Date Fetched:** 2026-04-12

## Title
Tiering Data Strategy for a Distributed Storage System

## Abstract
A plurality of computing devices are communicatively coupled to each other via a network, and each of the plurality of computing devices is operably coupled to one or more of a plurality of storage devices. The storage devices may be assigned to one of a plurality of memory tiers, and the data in a storage device may be reassigned to another storage device in a different memory tier.

## Patent Information
- **Publication Number:** US20240419364A1
- **Assignee:** Weka Io Ltd
- **Inventors:** Maor Ben Dayan, Omri Palmon, Liran Zvibel, Kanael Arditti
- **Priority Date:** November 13, 2017
- **Publication Date:** December 19, 2024
- **Status:** Pending

## Key Technical Overview

The patent describes a virtual file system (VFS) architecture implementing automated data tiering across multiple storage layers. The system manages data movement between four memory tiers: a main tier with highest-performance non-volatile memory, a low-endurance tier, an object storage tier, and an archival tier.

The innovation centers on assigning state tags to data extents, tracking whether data should be demoted to lower tiers or deleted from read caches. Data blocks use 3-bit tags representing demotion states (local0, local1, local2) and deletion states (retention0, retention1, retention2). When demotion or retention periods expire without write or read activity respectively, the system automatically moves data accordingly.

The architecture distributes metadata functionality across numerous servers using buckets and penta-groups, enabling scalability to thousands of nodes without centralized control bottlenecks.
