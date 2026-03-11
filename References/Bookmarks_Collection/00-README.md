# RDMA Papers Collection

A comprehensive collection of technical documentation and articles on Remote Direct Memory Access (RDMA), GPU acceleration, and high-performance networking.

## Collection Overview

**Created:** 2026-03-11
**Total Files:** 15 markdown files + 3 supporting documents
**Total Content:** ~2,010 lines of technical documentation

## Getting Started

1. Start with [INDEX.md](INDEX.md) for a quick navigation guide
2. Read [SUMMARY.md](SUMMARY.md) for collection statistics and overview
3. Refer to [MANIFEST.txt](MANIFEST.txt) for detailed file information

## Files Organized by Topic

### Communication Frameworks
- UCX_Unified_Communication_X_Introduction.md
- MVAPICH_Overview.md
- rdma_cm_-_IBM_AIX.md
- Connection_Manager_CM_ID_Operations_-_IBM.md

### GPU Integration
- GPU_enabled_MPI_-_AMD.md
- GPUDirect_Storage_IBM_Storage_Scale.md
- DeepSeek-R1_Multi-host_Deployment_AIBrix.md

### Network Configuration & Tuning
- RDMA_Tuning_-_IBM_Storage_Scale.md
- Planning_100Gbps_Adapter_-_IBM.md
- Can_RDMA_be_Used_with_LACP_-_NVIDIA_Forums.md

### Testing & Validation
- Manual_RDMA_Testing_OFA_FSDP_Cluster.md
- RDMA_RoCE_Test_MPI_Tools_-_Pansolusi.md

### Container & Cloud Deployment
- SCHMAUSTECH_RDMA_Shared_Hostdevice_SRIOV.md

### Restricted Access (Stub Files)
- blue-rdma_Design_Packet_Processing_-_DatenLord.md (HTTP 403)
- Algorithmic_GPU_Scheduling_Survey_-_MDPI.md (HTTP 403)

## File Format

Each markdown file includes:
- Title (H1 heading)
- Source URL
- Date accessed: 2026-03-11
- Complete technical content
- Relevant code examples and references

All files are UTF-8 encoded and follow standard markdown formatting.

## Key Technologies Covered

### RDMA Protocols
- InfiniBand
- RoCE (RDMA over Converged Ethernet)
- iWARP
- Omni-Path

### GPU Technologies
- GPUDirect RDMA
- GPUDirect Storage (GDS)
- PeerDirect
- ROCm (AMD)
- CUDA (NVIDIA)

### Software Stack
- MPI (Message Passing Interface)
- UCX (Unified Communication X)
- MVAPICH2
- Open MPI
- libfabric

### Deployment Platforms
- Kubernetes
- OpenShift
- IBM Storage Scale
- Hyperscale GPU clusters

## Sources

### Official Documentation (8 files)
- AMD Instinct GPU documentation
- IBM Storage Scale documentation
- IBM AIX RDMA reference
- OpenUCX official site
- Ohio State University MVAPICH project

### Technical Blogs & Articles (4 files)
- Jeremy Spewock (OFA FSDP cluster)
- Benjamin Schmaus (OpenShift RDMA)
- Pansolusi Tech (RoCE testing)
- AIBrix (Deep Learning deployment)

### Community Forums (1 file)
- NVIDIA Developer Forums

## Usage Notes

- All content was fetched on 2026-03-11
- Two URLs returned access restrictions (HTTP 403) - stub files created with metadata
- Content is organized for technical reference and learning
- Files are independent and can be read in any order
- Each file is self-contained with full technical details

## Finding Information

To search across all files:
```bash
grep -r "keyword" /sessions/eager-ecstatic-meitner/mnt/outputs/RDMA_Papers/
```

For example:
- Search for "InfiniBand": grep -r "InfiniBand"
- Search for "GPU": grep -r "GPU"
- Search for "performance": grep -r "performance"

## Document Structure

Each markdown file follows this structure:
1. Title (H1 heading)
2. Metadata (URL, date accessed)
3. Overview section
4. Technical content organized by subsections
5. Key findings or recommendations
6. References where applicable

## Quality Notes

- All fetched content is complete and unmodified
- Technical accuracy verified where possible
- Code examples and commands preserved as-is
- Performance metrics and specifications retained
- All URLs remain accessible (except the 2 restricted files)

## Navigation Tips

Start with one of these based on your interest:

**New to RDMA?**
- Start with: RDMA_Tuning_-_IBM_Storage_Scale.md
- Then read: UCX_Unified_Communication_X_Introduction.md

**GPU Acceleration Focus?**
- Start with: GPU_enabled_MPI_-_AMD.md
- Then read: GPUDirect_Storage_IBM_Storage_Scale.md

**Testing & Validation?**
- Start with: Manual_RDMA_Testing_OFA_FSDP_Cluster.md
- Then read: RDMA_RoCE_Test_MPI_Tools_-_Pansolusi.md

**Cloud/Container Deployment?**
- Start with: SCHMAUSTECH_RDMA_Shared_Hostdevice_SRIOV.md
- Then read: DeepSeek-R1_Multi-host_Deployment_AIBrix.md

## File Statistics

| Category | Count | Notes |
|----------|-------|-------|
| Total Files | 15 | 13 complete + 2 stub files |
| Successful Fetches | 13 | Full technical content |
| Failed Fetches | 2 | Metadata-only stub files |
| Supporting Docs | 3 | INDEX, SUMMARY, MANIFEST |
| Total Lines | ~2,010 | Markdown content |
| Estimated Size | ~35 KB | Uncompressed |

## Last Updated

2026-03-11 - Initial collection complete
