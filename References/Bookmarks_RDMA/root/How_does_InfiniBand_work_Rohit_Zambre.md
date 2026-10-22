# How does InfiniBand work? — Rohit Zambre

- **Source:** https://www.rohitzambre.com/blog/2019/4/27/how-are-messages-transmitted-on-infiniband
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA)
- **Retrieved:** 2026-10-22


---

**Summary**: This post describes the series of coordinated events that occur under the hood between the CPU and NIC through the PCI Express fabric to transmit a message and signal its completion over the InfiniBand interconnect.

The primary method of sending a message over InfiniBand is through the Verbs API. `libibverbs` is the standard implementation of this API and is maintained by the Linux-RDMA community. There are two kinds of functions in Verbs: slow-path and fast-path functions. Slow-path functions (such as `ibv_open_device`, `ibv_alloc_pd`, etc.) are those related to the creation and configuration of resources (such as the Context, Protection Domain, and Memory Region). They are called “slow” because they involve the kernel and hence incur the expensive overhead of a context switch. Fast-path functions (such as `ibv_post_send`, `ibv_poll_cq`, etc.) deal with initiation and completion of operations. They are called “fast” because they bypass the kernel and, hence, are much faster than the slow-path functions. The critical path of communication consists primarily of fast-path functions and occasionally a slow-path function such as `ibv_reg_mr` to register Memory Regions on the fly (depending on the communication middleware). This post focuses on mechanisms that occur after the programmer has executed an `ibv_post_send`.

### Quick PCIe background

The Network Interface Card (NIC) is typically attached to the server through a PCI Express (PCIe) slot. The main conductor of the PCIe I/O subsystem is the Root Complex (RC). The RC connects the processor and memory to the PCIe fabric. The PCIe fabric may consist a hierarchy of devices. The peripherals connected to the PCIe fabric are called PCIe endpoints. The PCIe protocol consists of three layers: the Transaction layer, the Data Link layer, and the Physical layer. The first, the upper-most layer, describes the type of transaction occurring. For this post, two types of Transaction Layer Packets (TLPs) are relevant: MemoryWrite (MWr), and Memory Read (MRd). Unlike the standalone MWr TLP, the MRd TLP is coupled with a Completion with Data (CplD) transaction from the target PCIe endpoint which contains the data requested by the initiator. The Data Link layer ensures the successful execution of all transactions using Data Link Layer Packet (DLLP) acknowledgements (ACK/NACK) and a credit-based flow-control mechanism. An initiator can issue a transaction as long as it has enough credits for that transaction. Its credits are replenished when it receives Update Flow Control (UpdateFC) DLLPs from its neighbors. Such a flow-control mechanism allows the PCIe protocol to have multiple outstanding transactions.

### Basic mechanisms involved

First, I will describe how messages are sent using the completely offloaded approach, that is, the CPU only informs the NIC that there is a message to be transmitted; the NIC will do everything else to transmit the data. In such an approach, the CPU is more available for computation activities. However, such an approach can be detrimental for the communication performance of small messages (it will become evident soon). To improve the communication performance in such cases, InfiniBand offers certain operational features which I will describe in the next section.

From a CPU programmer’s perspective, there exists a transmit queue (the send queue in Verbs is the Queue Pair (QP)) and a completion queue (long for CQ in Verbs). The user posts their message descriptor (MD; Work Queue Element/Entry (WQE; wookie) in Verbs) to the transmit queue, after which they poll on the CQ to confirm the completion of the posted message. The user could also request to be notified with an interrupt regarding the completion. However, the polling approach is latency-oriented since there is no context switch to the kernel in the critical path. The actual transmission of a message over the network occurs through coordination between the processor chip and the NIC using memory mapped I/O (MMIO) and direct memory access (DMA) reads and writes. I will describe these steps below the following figure.

Step 0: The user first enqueues an MD into the TxQ. The network driver then prepares the device-specific MD that contains headers for the NIC, and a pointer to the payload.

Step 1: Using an 8-byte atomic write to a memory-mapped location, the CPU (the network driver) notifies the NIC that a message is ready to be sent. This is called ringing the DoorBell. The RC executes the DoorBell using a MWr PCIe transaction.

Step 2: After the DoorBell ring, the NIC fetches the MD using a DMA read. A MRd PCIe transaction conducts the DMA read.

Step 3:The NIC will then fetch the payload from a registered memory region using another DMA read (another MRd TLP). Note that the virtual address has to be translated to its physical address before the NIC can perform DMA-reads.

Step 4: Once the NIC receives the payload, it transmits the read data over the network. Upon a successful transmission, the NIC receives an acknowledgment (ACK) from the target-NIC.

Step 5: Upon the reception of the ACK, the NIC will DMA-write (using a MWr TLP) a completion queue entry (CQE; a.k.a. cookie in Verbs; 64 bytes in Mellanox InfiniBand) to the CQ associated with the TxQ. The CPU will then poll for this completion to make progress.

In summary, the critical data path of each post entails one MMIO write, two DMA reads, and one DMA write. The DMA-reads translate to round-trip PCIe latencies which are expensive. For example, the roundtrip PCIe latency of a ThunderX2 machine is around 125 nanoseconds.

### Operational features

Inlining, Postlist, Unsignaled Completions, and Programmed I/O are IB’s operational features that help reduce this overhead. I describe them below considering the depth of the QP to be n.

***Postlist***: Instead of posting only one WQE per ibv\_post\_send, IB allows the application to post a linked list of WQEs with just one call to ibv\_post\_send. It can reduce the number of DoorBell rings from n to 1.

***Inlining***: Here, the CPU (the network driver) copies the data into the WQE. Hence, with its first DMA read for the WQE, the NIC gets the payload as well, eliminating the second DMA read for the payload.

***Unsignaled Completions***: Instead of signaling a completion for each WQE, IB allows the application to turn off completions for WQEs provided that at least one out of every n WQEs is signaled. Turning off completions reduces the DMA writes of CQEs by the NIC. Additionally, the application polls fewer CQEs, reducing the overhead of making progress.

***BlueFlame***: BlueFlame is Mellanox’s terminology for programmed I/O—it writes the WQE along with the DoorBell, cutting off the DMA read for the WQE itself. Note that BlueFlame is used only without Postlist. With Postlist, the NIC will DMA-read the WQEs in the linked list.

To reduce the overheads of the PCIe roundtrip latency, developers typically use both Inlining and BlueFlame together for small messages. It eliminates two PCIe round-trip latencies. While the use of Inlining and BlueFlame is dependent on message size, the use of Postlist and Unsignaled Completions is reliant primarily on the user’s design choices and application semantics.