# RDMA and LACP Compatibility Discussion

**Source URL:** https://forums.developer.nvidia.com/t/can-rdma-be-used-with-lacp/219669
**Date Accessed:** 2026-03-11

**Title:** Can RDMA be used with LACP?

**Forum:** NVIDIA Developer Forums - Infrastructure & Networking

**Original Question Posted By:** sezgink059 (July 4, 2022)

The user asked whether RDMA works with LACP on Windows servers using ConnectX-5/6 NICs and requested guidance on link redundancy for planned IP SAN deployment.

## Key Technical Response

**Responder:** tsechl (December 1, 2022)

### Main Findings

Microsoft recommends using "Switch Embedded Teaming (SET) and SMB Direct for RDMA link aggregation" rather than traditional LACP. The responder notes that "the teaming mode set to be 'switch independent' instead of LACP, that means RDMA is not preferred to be used in conjunction with LACP."

### Implementation Approach

The recommended solution involves:
- Creating a Hyper-V vSwitch with SET enabled
- Establishing a management vNIC with "-AllowManagementOS" option
- Extensive tuning of CPU affinity, VMQ/RSS, and driver settings
- Ensuring consistent NIC models and speeds within teams

### Alternative Solution

For IP SAN requirements, the responder recommends Windows Storage Spaces Direct (S2D) on failover clusters, highlighting features like "automatic tiering, deduplication, volume encryption, sync/async volume replication" and noting it's free with Windows Server licensing.
