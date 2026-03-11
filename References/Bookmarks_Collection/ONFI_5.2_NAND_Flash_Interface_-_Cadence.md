# ONFI 5.2: What's New in Open NAND Flash Interface's Latest 5.2 Standard

**Source URL:** https://community.cadence.com/cadence_blogs_8/b/fv/posts/onfi-5-2-what-s-new-in-open-nand-flash-interface-s-latest-5-2-standard

**Date Accessed:** 2026-03-11

---

**Author:** Shyam Sharma
**Published:** November 25, 2025
**Category:** Verification IP

## Overview

The article discusses ONFI 5.2, the latest generation of the Open NAND Flash Interface standard published in 2024. NAND flash memory serves as a critical component in modern systems, powering applications from mobile devices to data centers and AI workloads.

## Key Technical Advances

### Separate Command Address (SCA) Protocol

The most significant innovation in ONFI 5.2 is the SCA protocol, which allows hosts to decouple command/address operations from data transfers. This separation enables:

- Concurrent command and data traffic on distinct bus lines
- New signal pins for command/address packets and clock signals
- Improved overall interface throughput similar to DRAM architectures

### New Command Set

ONFI 5.2 introduces "a new SCA Protocol Command Set" alongside existing conventional protocols, adding "a third cycle for operations such as multi-plane page program."

### Power and Current Requirements

The standard specifies "higher values for read, program, standby, and active external supply voltage," with LUN array currents potentially reaching 150 mA, requiring careful power budget planning.

## Memory Model Support

Cadence offers verification IP with ONFI 5.2 memory models that validate both functional accuracy and specification compliance for host implementations.
