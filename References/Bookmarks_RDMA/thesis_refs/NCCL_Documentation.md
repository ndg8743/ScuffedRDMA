# NCCL Documentation

- **Source:** https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/index.html
- **Cited in:** REFERENCES.md [19]
- **Retrieved:** 2026-10-22

---

NCCL
2.32
Overview of NCCL
Setup
Building with TLS support
Configuring TCP encryption
Using NCCL
Creating a Communicator
Using MIG instances
Creating a communicator with options
Creating a communicator using multiple ncclUniqueIds
Shrinking a communicator
Growing a communicator
Creating more communicators
Using multiple NCCL communicators concurrently
Finalizing a communicator
Destroying a communicator
Error handling and communicator abort
Asynchronous errors and error handling
Fault Tolerance
Quality of Service
Collective Operations
AllReduce
Broadcast
Reduce
AllGather
ReduceScatter
AlltoAll
Gather
Scatter
Data Pointers
CUDA Stream Semantics
Mixing Multiple Streams within the same ncclGroupStart/End() group
Group Calls
Management Of Multiple GPUs From One Thread
Aggregated Operations (2.2 and later)
Group Operation Ordering Semantics
Nonblocking Group Operation
Point-to-point communication
Two-sided communication
Sendrecv
One-to-all (scatter)
All-to-one (gather)
All-to-all
Neighbor exchange
One-sided communication
PutSignal and WaitSignal
Barrier
All-to-all
Thread Safety
In-place Operations
Using NCCL with CUDA Graphs
Requirements and Limitations
User Buffer Registration
NVLink Sharp Buffer Registration
IB Sharp Buffer Registration
General Buffer Registration
Buffer Registration, GPU Direct RDMA, and MPS with MLOPart
Buffer Registration and PXN
Memory Allocator
Window Registration
Zero-CTA Optimization
Device-Initiated Communication
Device API
Requirements
Cross-Version Compatibility
Host-Side Setup
Simple LSA Kernel
Multimem Device Kernel
Thread Groups
Teams
Segment Types
Host-Accessible Device Pointer Functions
GIN Device Kernel
Multiple GIN Backends
Compatibility adjustments
Compute Fabric Transport
Requirements
Device Communicator Setup
Teams and Endpoints
CFT Operations
CFT Barriers
CFT Counted Operations
Examples
Cross-proxy Fences
NCCL API
Communicator Creation and Management Functions
ncclGetLastError
ncclGetErrorString
ncclGetVersion
ncclGetUniqueId
ncclSetEncryption
ncclCommInitRank
ncclCommInitAll
ncclCommInitRankConfig
ncclCommInitRankScalable
ncclCommSplit
ncclCommShrink
ncclCommGetUniqueId
ncclCommGrow
ncclCommRevoke
ncclCommFinalize
ncclCommDestroy
ncclCommAbort
ncclCommGetAsyncError
ncclCommCount
ncclCommCuDevice
ncclCommUserRank
ncclCommRegister
ncclCommDeregister
ncclCommWindowRegister
ncclCommWindowDeregister
ncclMemAlloc
ncclMemFree
ncclCommSuspend
ncclCommResume
ncclCommMemStats
Collective Communication Functions
ncclAllReduce
ncclBroadcast
ncclReduce
ncclAllGather
ncclReduceScatter
ncclAlltoAll
ncclGather
ncclScatter
Per-Collective Configuration Variants
Group Calls
ncclGroupStart
ncclGroupEnd
ncclGroupSimulateEnd
Point To Point Communication Functions
Two-Sided Point-to-Point Operations
ncclSend
ncclRecv
One-Sided Point-to-Point Operations (RMA)
ncclPutSignal
ncclSignal
ncclWaitSignal
Types
ncclComm\_t
ncclResult\_t
ncclDataType\_t
ncclRedOp\_t
ncclScalarResidence\_t
ncclConfig\_t
ncclEncryptionConfig\_t
ncclCollConfig\_t
ncclSimInfo\_t
ncclCommMemStat\_t
ncclWindow\_t
User Defined Reduction Operators
ncclRedOpCreatePreMulSum
ncclRedOpDestroy
NCCL API Supported Flags
Window Registration Flags
NCCL Communicator CTA Policy Flags
Communicator Shrink Flags
GIN Optimization Flags
Device API
Device API – Host-Side Setup
Host-Side Setup
Host-Accessible Device Pointer Functions
Device API – Memory and LSA
LSA
Multimem
Device API – GIN
GIN
Device API - CFT
Compute Fabric Transport
CFT Communicator Requirements
CFT Teams
Logical Endpoint Queries
CFT Operations
Reduction Operations
CFT Barriers
Device API – Remote Reduce and Copy: Building Blocks for Custom Communication Kernels
Compile-Time Requirements
API Overview
ReduceSum — N Sources to One Destination
Copy (Broadcast) — One Source to N Destinations
ReduceSumCopy
Lambda-Based (Custom Layouts)
Custom Reduction Operators
NCCL Parameter API
Types
Handle-Based API
ncclParamBind
Accessor Family of Functions - ncclResult\_t ncclParamGet\*(ncclParamHandle\_t h, T\* out)
ncclParamGetStr
ncclParamGet
Key-Based API
ncclParamGetParameter
ncclParamGetAllParameterKeys
ncclParamDumpAll
Language Bindings
Python Bindings (NCCL4Py)
Communicator
Communicator Class
Creation and Lifecycle Methods
Collective Communication Methods
Point-to-Point and Signal Methods
Memory Registration Methods
Device Communicator Setup
Status and Utility Methods
Configuration
NCCLConfig
NCCLCollConfig
CTAPolicy
NCCLDevCommRequirements
Requirement entries
Group Operations
group
group\_start
group\_end
GroupSimInfo
Memory Management
mem\_alloc
mem\_free
Communicator Resources
CommResource
RegisteredBufferHandle
RegisteredWindowHandle
CftLeInfo
CustomRedOp
DevCommResource
Device resource handles
Types and Constants
Data type
Reduction operator
Team
Type aliases
Exceptions
Parameters
params
dump\_params
Versions
show\_versions
get\_version
VersionInfo
LibraryInfo
Framework Interop
CuPy
PyTorch
Migrating from NCCL 1 to NCCL 2
Initialization
Communication
Counts
In-place usage for AllGather and ReduceScatter
AllGather arguments order
Datatypes
Error codes
Examples
Communicator Creation and Destruction Examples
Example 1: Single Process, Single Thread, Multiple Devices
Example 2: One Device per Process or Thread
Example 3: Multiple Devices per Thread
Example 4: Multiple communicators per device
Communication Examples
Example 1: One Device per Process or Thread
Example 2: Multiple Devices per Thread
NCCL and MPI
API
Using multiple devices per process
ReduceScatter operation
Send and Receive counts
Other collectives and point-to-point operations
In-place operations
Using NCCL within an MPI Program
MPI Progress
Inter-GPU Communication with CUDA-aware MPI
Environment Variables
System configuration
NCCL\_SOCKET\_IFNAME
Values accepted
NCCL\_SOCKET\_FAMILY
Values accepted
NCCL\_SOCKET\_MAGIC
Values accepted
NCCL\_SOCKET\_RETRY\_CNT
Values accepted
NCCL\_SOCKET\_RETRY\_SLEEP\_MSEC
Values accepted
NCCL\_SOCKET\_POLL\_TIMEOUT\_MSEC
Values accepted
NCCL\_SOCKET\_NTHREADS
Values accepted
NCCL\_NSOCKS\_PERTHREAD
Values accepted
NCCL\_CROSS\_NIC
Values accepted
NCCL\_IB\_HCA
Values accepted
NCCL\_IB\_RAIL\_POLICY
Values accepted
NCCL\_IB\_TIMEOUT
Values accepted
NCCL\_IB\_RETRY\_CNT
Values accepted
NCCL\_IB\_GID\_INDEX
Values accepted
NCCL\_IB\_ADDR\_FAMILY
Values accepted
NCCL\_IB\_ADDR\_RANGE
Values accepted
NCCL\_IB\_ROCE\_VERSION\_NUM
Values accepted
NCCL\_IB\_PKEY
Values accepted
NCCL\_IB\_PKEY\_VALUE
Values accepted
NCCL\_IB\_SL
Values accepted
NCCL\_IB\_TC
Values accepted
NCCL\_IB\_FIFO\_TC
Values accepted
NCCL\_IB\_RETURN\_ASYNC\_EVENTS
Values accepted
NCCL\_IB\_EVENT\_BASED\_LB
Values accepted
NCCL\_OOB\_NET\_ENABLE
Values accepted
NCCL\_OOB\_NET\_IFNAME
Values accepted
NCCL\_UID\_STAGGER\_THRESHOLD
Values accepted
NCCL\_UID\_STAGGER\_RATE
Values accepted
NCCL\_NET
Values accepted
NCCL\_NET\_PLUGIN
Values accepted
NCCL\_GIN\_PLUGIN
Values accepted
NCCL\_RMA\_PLUGIN
Values accepted
NCCL\_TUNER\_PLUGIN
Values accepted
NCCL\_PROFILER\_PLUGIN
Values accepted
NCCL\_ENV\_PLUGIN
Values accepted
NCCL\_IGNORE\_CPU\_AFFINITY
Values accepted
NCCL\_CONF\_FILE
Values accepted
NCCL\_DEBUG
Values accepted
NCCL\_DEBUG\_LEVELS
NCCL\_DEBUG\_FILE
Values accepted
NCCL\_DEBUG\_SUBSYS
Values accepted
NCCL\_DEBUG\_TIMESTAMP\_FORMAT
Value accepted
NCCL\_DEBUG\_TIMESTAMP\_LEVELS
Value accepted
NCCL\_COLLNET\_ENABLE
Value accepted
NCCL\_COLLNET\_NODE\_THRESHOLD
Value accepted
NCCL\_CTA\_POLICY
Value accepted
NCCL\_NETDEVS\_POLICY
Value accepted
NCCL\_MULTI\_RANK\_GPU\_ENABLE
Values accepted
NCCL\_TOPO\_FILE
Value accepted
NCCL\_TOPO\_DUMP\_FILE
Value accepted
NCCL\_SET\_THREAD\_NAME
Value accepted
Debugging
NCCL\_P2P\_DISABLE
Values accepted
NCCL\_P2P\_LEVEL
Values accepted
Integer Values (Legacy)
NCCL\_P2P\_DIRECT\_DISABLE
Values accepted
NCCL\_SHM\_DISABLE
Values accepted
NCCL\_BUFFSIZE
Values accepted
NCCL\_NTHREADS
Values accepted
NCCL\_MAX\_NCHANNELS
Values accepted
NCCL\_MIN\_NCHANNELS
Values accepted
NCCL\_CHECKS\_DISABLE
Values accepted
NCCL\_CHECK\_POINTERS
Values accepted
NCCL\_CHECK\_MODE
Values accepted
NCCL\_LAUNCH\_MODE
Values accepted
NCCL\_IB\_DISABLE
Values accepted
NCCL\_IB\_AR\_THRESHOLD
Values accepted
NCCL\_IB\_OOO\_RQ
Values accepted
NCCL\_IB\_QPS\_PER\_CONNECTION
Values accepted
NCCL\_IB\_SPLIT\_DATA\_ON\_QPS
Values accepted
NCCL\_IB\_CUDA\_SUPPORT
Values accepted
NCCL\_IB\_PCI\_RELAXED\_ORDERING
Values accepted
NCCL\_IB\_ADAPTIVE\_ROUTING
Values accepted
NCCL\_IB\_ECE\_ENABLE
Values accepted
NCCL\_MEM\_SYNC\_DOMAIN
Values accepted
NCCL\_CUMEM\_ENABLE
Values accepted
NCCL\_CUMEM\_HOST\_ENABLE
Values accepted
NCCL\_NET\_GDR\_LEVEL (formerly NCCL\_IB\_GDR\_LEVEL)
Values accepted
Integer Values (Legacy)
NCCL\_NET\_GDR\_C2C
Values accepted
NCCL\_NET\_GDR\_READ
Values accepted
NCCL\_GDRCOPY\_ENABLE
Values accepted
NCCL\_GDRCOPY\_FIFO\_ENABLE
Values accepted
NCCL\_GDRCOPY\_SYNC\_ENABLE
Values accepted
NCCL\_GDRCOPY\_FLUSH\_ENABLE
Values accepted
NCCL\_NET\_SHARED\_BUFFERS
Value accepted
NCCL\_NET\_SHARED\_COMMS
Value accepted
NCCL\_IGNORE\_NET\_MISMATCH
Values accepted
NCCL\_IGNORE\_COLLNET\_MISMATCH
Values accepted
NCCL\_SINGLE\_RING\_THRESHOLD
Values accepted
NCCL\_LL\_THRESHOLD
Values accepted
NCCL\_TREE\_THRESHOLD
Values accepted
NCCL\_ALGO
Values accepted
NCCL\_PROTO
Values accepted
NCCL\_NVB\_DISABLE
Value accepted
NCCL\_PXN\_DISABLE
Value accepted
NCCL\_P2P\_PXN\_LEVEL
Value accepted
NCCL\_PXN\_C2C
Value accepted
NCCL\_RUNTIME\_CONNECT
Value accepted
NCCL\_GRAPH\_REGISTER
Value accepted
NCCL\_LOCAL\_REGISTER
Value accepted
NCCL\_LEGACY\_CUDA\_REGISTER
Value accepted
NCCL\_WIN\_ENABLE
Value accepted
NCCL\_SET\_STACK\_SIZE
Value accepted
NCCL\_GRAPH\_MIXING\_SUPPORT
Value accepted
NCCL\_GRAPH\_STREAM\_ORDERING
Value accepted
NCCL\_RMA\_EAGER\_INIT
Value accepted
NCCL\_DMABUF\_ENABLE
Value accepted
NCCL\_P2P\_NET\_CHUNKSIZE
Values accepted
NCCL\_P2P\_LL\_THRESHOLD
Values accepted
NCCL\_ALLOC\_P2P\_NET\_LL\_BUFFERS
Values accepted
NCCL\_COMM\_BLOCKING
Values accepted
NCCL\_CGA\_CLUSTER\_SIZE
Values accepted
NCCL\_MAX\_CTAS
Values accepted
NCCL\_MIN\_CTAS
Values accepted
NCCL\_NVLS\_ENABLE
Values accepted
NCCL\_IB\_MERGE\_NICS
Values accepted
NCCL\_NET\_MERGE\_POLICY
Values accepted
NCCL\_MNNVL\_ENABLE
Values accepted
NCCL\_MNNVL\_UUID
Values accepted
NCCL\_MNNVL\_CLIQUE\_ID
Values accepted
NCCL\_RAS\_ENABLE
Values accepted
NCCL\_RAS\_ADDR
Values accepted
NCCL\_RAS\_TIMEOUT\_FACTOR
Values accepted
NCCL\_LAUNCH\_ORDER\_IMPLICIT
Values accepted
NCCL\_LAUNCH\_RACE\_FATAL
Values accepted
NCCL\_IPC\_USE\_ABSTRACT\_SOCKET
Values accepted
NCCL\_SYM\_GIN\_KERNELS\_ENABLE
Values accepted
Troubleshooting
Diagnostics
RAS Diagnostics
Active Diagnostics
Running Active Diagnostics
Available Checks
GPU troubleshooting
GPU Direct
GPU-to-GPU communication
Linux bare-metal IOMMU and PCIe peer-to-peer
GPU-to-NIC communication
PCI Access Control Services (ACS)
Topology detection
Networking Troubleshooting
Networking issues
IP network interfaces
IP ports
NIC-level diagnostics
InfiniBand
RDMA over Converged Ethernet (RoCE)
Runtime and MPI issues
Errors
Memory issues
Shared memory
Stack size
Unified Memory (UVM)
File Descriptors
MPI
Open MPI based MPIs (e.g. NVIDIA HPC-X)
Performance and tuning
Performance issues
Intra-node communication
Inter-node communication
Multi-node NVLink (MNNVL) issues
Tuning NCCL configuration
CPU and memory affinity
Logging
Logging Environment Variables
Logging Levels
Setting the Logging Level
Adding Logging Levels
Example Output
Filtering by Subsystem
Basic Usage
Available Subsystems
Example Output by Subsystem
Logging to Files
Timestamp Configuration
Timestamp Format
Timestamp Levels
Common Debugging Scenarios
Diagnosing Initialization Hangs
Investigating Network Issues
Understanding Topology Detection
Debugging Performance Issues
Tracing NCCL API Calls
Full Debugging Session
RAS
Principle of Operation
RAS Queries
Sample Output
JSON Output
Monitoring Mode
Control Commands
RAS Diagnostics
Available Checks
Prerequisites
Running During Communicator Initialization
Running On Demand
Output Format
Concurrent Requests
NCCL
NVIDIA Collective Communication Library (NCCL) Documentation
View page source
NVIDIA Collective Communication Library (NCCL) Documentation
Contents:
Overview of NCCL
Setup
Building with TLS support
Configuring TCP encryption
Using NCCL
Creating a Communicator
Using MIG instances
Creating a communicator with options
Creating a communicator using multiple ncclUniqueIds
Shrinking a communicator
Growing a communicator
Creating more communicators
Using multiple NCCL communicators concurrently
Finalizing a communicator
Destroying a communicator
Error handling and communicator abort
Asynchronous errors and error handling
Fault Tolerance
Quality of Service
Collective Operations
AllReduce
Broadcast
Reduce
AllGather
ReduceScatter
AlltoAll
Gather
Scatter
Data Pointers
CUDA Stream Semantics
Mixing Multiple Streams within the same ncclGroupStart/End() group
Group Calls
Management Of Multiple GPUs From One Thread
Aggregated Operations (2.2 and later)
Group Operation Ordering Semantics
Nonblocking Group Operation
Point-to-point communication
Two-sided communication
One-sided communication
Thread Safety
In-place Operations
Using NCCL with CUDA Graphs
Requirements and Limitations
User Buffer Registration
NVLink Sharp Buffer Registration
IB Sharp Buffer Registration
General Buffer Registration
Buffer Registration, GPU Direct RDMA, and MPS with MLOPart
Buffer Registration and PXN
Memory Allocator
Window Registration
Zero-CTA Optimization
Device-Initiated Communication
Device API
Requirements
Cross-Version Compatibility
Host-Side Setup
Simple LSA Kernel
Multimem Device Kernel
Thread Groups
Teams
Segment Types
Host-Accessible Device Pointer Functions
GIN Device Kernel
Compute Fabric Transport
Requirements
Device Communicator Setup
Teams and Endpoints
CFT Operations
CFT Barriers
CFT Counted Operations
Examples
Cross-proxy Fences
NCCL API
Communicator Creation and Management Functions
ncclGetLastError
ncclGetErrorString
ncclGetVersion
ncclGetUniqueId
ncclSetEncryption
ncclCommInitRank
ncclCommInitAll
ncclCommInitRankConfig
ncclCommInitRankScalable
ncclCommSplit
ncclCommShrink
ncclCommGetUniqueId
ncclCommGrow
ncclCommRevoke
ncclCommFinalize
ncclCommDestroy
ncclCommAbort
ncclCommGetAsyncError
ncclCommCount
ncclCommCuDevice
ncclCommUserRank
ncclCommRegister
ncclCommDeregister
ncclCommWindowRegister
ncclCommWindowDeregister
ncclMemAlloc
ncclMemFree
ncclCommSuspend
ncclCommResume
ncclCommMemStats
Collective Communication Functions
ncclAllReduce
ncclBroadcast
ncclReduce
ncclAllGather
ncclReduceScatter
ncclAlltoAll
ncclGather
ncclScatter
Per-Collective Configuration Variants
Group Calls
ncclGroupStart
ncclGroupEnd
ncclGroupSimulateEnd
Point To Point Communication Functions
Two-Sided Point-to-Point Operations
One-Sided Point-to-Point Operations (RMA)
Types
ncclComm\_t
ncclResult\_t
ncclDataType\_t
ncclRedOp\_t
ncclScalarResidence\_t
ncclConfig\_t
ncclEncryptionConfig\_t
ncclCollConfig\_t
ncclSimInfo\_t
ncclCommMemStat\_t
ncclWindow\_t
User Defined Reduction Operators
ncclRedOpCreatePreMulSum
ncclRedOpDestroy
NCCL API Supported Flags
Window Registration Flags
NCCL Communicator CTA Policy Flags
Communicator Shrink Flags
GIN Optimization Flags
Device API
Device API – Host-Side Setup
Device API – Memory and LSA
Device API – GIN
Device API - CFT
Device API – Remote Reduce and Copy: Building Blocks for Custom Communication Kernels
NCCL Parameter API
Types
Handle-Based API
Key-Based API
Language Bindings
Python Bindings (NCCL4Py)
Communicator
Configuration
Group Operations
Memory Management
Communicator Resources
Types and Constants
Parameters
Versions
Framework Interop
Migrating from NCCL 1 to NCCL 2
Initialization
Communication
Counts
In-place usage for AllGather and ReduceScatter
AllGather arguments order
Datatypes
Error codes
Examples
Communicator Creation and Destruction Examples
Example 1: Single Process, Single Thread, Multiple Devices
Example 2: One Device per Process or Thread
Example 3: Multiple Devices per Thread
Example 4: Multiple communicators per device
Communication Examples
Example 1: One Device per Process or Thread
Example 2: Multiple Devices per Thread
NCCL and MPI
API
Using multiple devices per process
ReduceScatter operation
Send and Receive counts
Other collectives and point-to-point operations
In-place operations
Using NCCL within an MPI Program
MPI Progress
Inter-GPU Communication with CUDA-aware MPI
Environment Variables
System configuration
NCCL\_SOCKET\_IFNAME
NCCL\_SOCKET\_FAMILY
NCCL\_SOCKET\_MAGIC
NCCL\_SOCKET\_RETRY\_CNT
NCCL\_SOCKET\_RETRY\_SLEEP\_MSEC
NCCL\_SOCKET\_POLL\_TIMEOUT\_MSEC
NCCL\_SOCKET\_NTHREADS
NCCL\_NSOCKS\_PERTHREAD
NCCL\_CROSS\_NIC
NCCL\_IB\_HCA
NCCL\_IB\_RAIL\_POLICY
NCCL\_IB\_TIMEOUT
NCCL\_IB\_RETRY\_CNT
NCCL\_IB\_GID\_INDEX
NCCL\_IB\_ADDR\_FAMILY
NCCL\_IB\_ADDR\_RANGE
NCCL\_IB\_ROCE\_VERSION\_NUM
NCCL\_IB\_PKEY
NCCL\_IB\_PKEY\_VALUE
NCCL\_IB\_SL
NCCL\_IB\_TC
NCCL\_IB\_FIFO\_TC
NCCL\_IB\_RETURN\_ASYNC\_EVENTS
NCCL\_IB\_EVENT\_BASED\_LB
NCCL\_OOB\_NET\_ENABLE
NCCL\_OOB\_NET\_IFNAME
NCCL\_UID\_STAGGER\_THRESHOLD
NCCL\_UID\_STAGGER\_RATE
NCCL\_NET
NCCL\_NET\_PLUGIN
NCCL\_GIN\_PLUGIN
NCCL\_RMA\_PLUGIN
NCCL\_TUNER\_PLUGIN
NCCL\_PROFILER\_PLUGIN
NCCL\_ENV\_PLUGIN
NCCL\_IGNORE\_CPU\_AFFINITY
NCCL\_CONF\_FILE
NCCL\_DEBUG
NCCL\_DEBUG\_LEVELS
NCCL\_DEBUG\_FILE
NCCL\_DEBUG\_SUBSYS
NCCL\_DEBUG\_TIMESTAMP\_FORMAT
NCCL\_DEBUG\_TIMESTAMP\_LEVELS
NCCL\_COLLNET\_ENABLE
NCCL\_COLLNET\_NODE\_THRESHOLD
NCCL\_CTA\_POLICY
NCCL\_NETDEVS\_POLICY
NCCL\_MULTI\_RANK\_GPU\_ENABLE
NCCL\_TOPO\_FILE
NCCL\_TOPO\_DUMP\_FILE
NCCL\_SET\_THREAD\_NAME
Debugging
NCCL\_P2P\_DISABLE
NCCL\_P2P\_LEVEL
NCCL\_P2P\_DIRECT\_DISABLE
NCCL\_SHM\_DISABLE
NCCL\_BUFFSIZE
NCCL\_NTHREADS
NCCL\_MAX\_NCHANNELS
NCCL\_MIN\_NCHANNELS
NCCL\_CHECKS\_DISABLE
NCCL\_CHECK\_POINTERS
NCCL\_CHECK\_MODE
NCCL\_LAUNCH\_MODE
NCCL\_IB\_DISABLE
NCCL\_IB\_AR\_THRESHOLD
NCCL\_IB\_OOO\_RQ
NCCL\_IB\_QPS\_PER\_CONNECTION
NCCL\_IB\_SPLIT\_DATA\_ON\_QPS
NCCL\_IB\_CUDA\_SUPPORT
NCCL\_IB\_PCI\_RELAXED\_ORDERING
NCCL\_IB\_ADAPTIVE\_ROUTING
NCCL\_IB\_ECE\_ENABLE
NCCL\_MEM\_SYNC\_DOMAIN
NCCL\_CUMEM\_ENABLE
NCCL\_CUMEM\_HOST\_ENABLE
NCCL\_NET\_GDR\_LEVEL (formerly NCCL\_IB\_GDR\_LEVEL)
NCCL\_NET\_GDR\_C2C
NCCL\_NET\_GDR\_READ
NCCL\_GDRCOPY\_ENABLE
NCCL\_GDRCOPY\_FIFO\_ENABLE
NCCL\_GDRCOPY\_SYNC\_ENABLE
NCCL\_GDRCOPY\_FLUSH\_ENABLE
NCCL\_NET\_SHARED\_BUFFERS
NCCL\_NET\_SHARED\_COMMS
NCCL\_IGNORE\_NET\_MISMATCH
NCCL\_IGNORE\_COLLNET\_MISMATCH
NCCL\_SINGLE\_RING\_THRESHOLD
NCCL\_LL\_THRESHOLD
NCCL\_TREE\_THRESHOLD
NCCL\_ALGO
NCCL\_PROTO
NCCL\_NVB\_DISABLE
NCCL\_PXN\_DISABLE
NCCL\_P2P\_PXN\_LEVEL
NCCL\_PXN\_C2C
NCCL\_RUNTIME\_CONNECT
NCCL\_GRAPH\_REGISTER
NCCL\_LOCAL\_REGISTER
NCCL\_LEGACY\_CUDA\_REGISTER
NCCL\_WIN\_ENABLE
NCCL\_SET\_STACK\_SIZE
NCCL\_GRAPH\_MIXING\_SUPPORT
NCCL\_GRAPH\_STREAM\_ORDERING
NCCL\_RMA\_EAGER\_INIT
NCCL\_DMABUF\_ENABLE
NCCL\_P2P\_NET\_CHUNKSIZE
NCCL\_P2P\_LL\_THRESHOLD
NCCL\_ALLOC\_P2P\_NET\_LL\_BUFFERS
NCCL\_COMM\_BLOCKING
NCCL\_CGA\_CLUSTER\_SIZE
NCCL\_MAX\_CTAS
NCCL\_MIN\_CTAS
NCCL\_NVLS\_ENABLE
NCCL\_IB\_MERGE\_NICS
NCCL\_NET\_MERGE\_POLICY
NCCL\_MNNVL\_ENABLE
NCCL\_MNNVL\_UUID
NCCL\_MNNVL\_CLIQUE\_ID
NCCL\_RAS\_ENABLE
NCCL\_RAS\_ADDR
NCCL\_RAS\_TIMEOUT\_FACTOR
NCCL\_LAUNCH\_ORDER\_IMPLICIT
NCCL\_LAUNCH\_RACE\_FATAL
NCCL\_IPC\_USE\_ABSTRACT\_SOCKET
NCCL\_SYM\_GIN\_KERNELS\_ENABLE
Troubleshooting
Indices and tables
Index
Module Index
Search Page