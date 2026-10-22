# InfiniBand: An Introduction + Simple IB verbs program with RDMA Write - Service Engineering (ICCLab & SPLab)

- **Source:** https://blog.zhaw.ch/icclab/infiniband-an-introduction-simple-ib-verbs-program-with-rdma-write/
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA)
- **Retrieved:** 2026-10-22


---

This blogpost aims to give you a short introduction to InfiniBand. At the end you should have a rough overview over the technology, much of its terminology and on how to program a very simple RDMA application with IB verbs.


The first part explains the basic characteristics/properties of the InfiniBand technology and the physical parts that a network consists of. The second part takes a closer look at the logical parts of the technology that are needed for communication. In the third and last part I’ll explain the structure of a simple IB verbs application. IB verbs are abstract representations of functions. You can think of IB verbs as functions/methods that have to be offered by an (IB)-API.

You might wonder, why there is an article on InfiniBand on a cloud computing blog. The ICCLab is currently one of the members of the [FI-WARE](http://http//www.fi-ware.eu/) open call project “Middleware for efficient and QoS/Security-aware invocation of services and exchange of messages” named [KIARA](http://www.cloudcomp.ch/research/foundation/projects/kiara/). One of its features will be the support of InfiniBand in the transport layer.

This whole blogpost is a big compilation from various sources that I’ve found while researching InfiniBand over the last couple of weeks. The same goes for the IB verbs example program. All those sources that were extremely helpful to me can be found at the end of this blogpost. For those who’ll want to dive deeper into the subject this should give you a good starting point. A big ‘thank you’ to all those writers of introductions, summaries and tutorials.

## Basics, Network and End Nodes

InfiniBand (IB) is a networking technology developed by the InfiniBand Trade Association in 1999. It is used for high-performance computing and in enterprise data centers. Its features include high throughput, low latency, quality of service and failover.

The smallest complete InfiniBand Architecture (IBA) unit is a subnet. A subnet consists of end nodes (e.g. servers), switches, copper or fibre links and a subnet manager. End nodes use so called Channel Adapters (CAs) to connect to links. There are Host Channel Adapters (HCAs) and Target Channel Adapters (TCAs). HCAs are accessible by user-applications, TCAs not. The subnet manager has an overview over and manages the whole subnet.

InfiniBand allows an application to communicate *directly* with another application. This means that an application does not need to rely on the operating system to transfer messages.

This was just a very basic and short overview of what InfiniBand is. The IB specification is 1500 pages long! The important points were to get a rough overview of how an IB network looks like, understand that the NICs are called Channel Adapters and that IB creates a channel between those CAs which allows applications to directly communicate with each other without involving the operating system.

## Communication

CAs communicate with each other using *work queues*. There are three types of work queues: Send, Receive and Completion. Send and Receive Queues are always used as *Queue Pairs* (QP). A particular QP in a CA is the destination or source of all messages. Each QP also has an associated port which is an abstraction of the connection of a CA to a link.

To send or receive messages, W*ork Requests* (WRs) are placed onto a QP. There are send work requests and receive work requests. When processing is completed, a W*ork Completion* (WC) entry is optionally placed onto a C*ompletion Queue* (CQ) associated with the work queue.

To define what address in memory to write to or read from, *Scatter/Gather Elements* (SGE) are used – and associated with a WR. An SGE is a pointer to a *Memory Region* (MR) which the HCA can read from or write to. A memory region is a contiguous set of memory buffers that has been registered with an HCA. Registration of a MR causes the operating system to provide the HCA with the virtual-to-physical mapping of that region and pin the memory (prohibit swapping it out in virtual memory operations). Memory registration also creates objects called *L\_Key* and *R\_Key* which need to be used – for authentication – when accessing MRs. With the L\_Key (local Key) one can access local MRs. The R\_Key (remote Key) can be sent to peers so they can directly access a local MR (RDMA Write, RDMA Read). A MR in turn is part of a *Protection Domain* (PD). PDs effectively glue QPs to memory regions and can be seen as a an aggregating entity. Both QPs and MRs must be defined in the context of a PD.

By now you should be quite fed up with all those new abbreviations. But especially when programming with the *ibverbs* library, it is more than helpful knowing these abbreviations. Therefore here a short recap and clearer overview of those InfiniBand concepts needed for communication.

| **Abbr.** | **Name** | **Function** | 
| PD | Protection Domain | Glues queue pairs and memory regions | 
| MR | Memory Region | Registered memory region that HCA can read from or write to. Contains R\_Key and L\_Key | 
| QP | Queue Pair | Send / Receive work queue. Send or receive work requests are placed onto a queue pair | 
| CQ | Completion Queue | Completion Queue. Completed work requests, so called work completions are placed onto a completion queue. Is associated with queue pair. | 
| WR | Work Request | Either send or receive work request. Specifies action to be processed and will be put onto send or receive queue (QP). References scatter/gather element | 
| SGE | Scatter/Gather Element | Defines address(es) in memory to read from or to write to. Must be given L\_Key or R\_Key to authenticate access to memory region | 
| WC | Work Completion | After a work request has been completed the work completion delivers result | 

## Simple IB verbs RDMA program

The program – simply called *rdma* – described in this section is mainly based on the source code of the ‘ib\_rdma\_bw’ application. This application is part of the *perftest* package, available for various Linux distributions. The link to the source-code file can be found at the end of this blogpost. The code in the example program has been greatly simplified and stripped down.  Almost all the functions were renamed, some functions were put together and lots of code was just removed. Depending on the argument passed to the example you either are the server/sender or the client/receiver. At the moment the client connects to a server and then the server writes a string directly into a local buffer of the client which displays it. The source code of the example program can be downloaded at the end of this blogpost.

First a simplified description of what happens in the program. Most points are identical for the server and the client.

1. **Initialize InfiniBand Context (Structures needed for communication and memory)**
  1. Get and open InfiniBand device. This will give you a ‘context’ which is used to create all the following structures
  2. Allocate a Protection Domain
  3. Register a Memory Region
  4. Create a Send and a Receive Completion Queue
  5. Create a Queue Pair
2. **Initialize the Queue Pair (change QP status to INIT)**
3. **Exchange information to later be able to communicate with peer **via IB**.** This is done via TCP in this example. Another possibility would be to use the RDMA Connection Manager which would need IPoIB enabled hosts. The following information is exchanged
  1. LID – Local Identifier, 16 bit addr. assigned to end nodes by subnet manager
  2. QPN – Queue Pair Number, identifier assigned to QP by HCA
  3. PSN – Packet Sequence Number, used by HCA to verify correct order of packages / detect package loss
  4. R\_Key
  5. VADDR, address of memory region for peer to write into
4. **Change the QP status to Ready to Receive (RTR)**
5. **\* ONLY SERVER \* – Change the QP status to Ready to Send (RTS)**
6. **Perform RDMA write**
  1. Define memory region to read from with scatter/gather element (SGE)
  2. Use work request to define where to write to
  3. RDMA write into buffer of client/receiver

The following diagram shows you the flow of the program. Function names are written in bold text and were arbitrarily chosen by me. Just below the function name is a short description of what the function does. The red text marks used IB\_verbs.

The program is far from being finished. At the moment you cannot pass a buffer to it, choose an IB port number or define the size of the buffer. The client does also not get notified when the RDMA write from the server has been completed (flow control). This additional functionality will be added in the next steps.

# Source Code

## **Example program ‘rdma’**

## **Perftest application ‘ib\_rdma\_bw’**

# Links

# Related Blog Posts


Thanks for article, it’s very useful to understand IB and practice verbs programming. But link for rdma.c is died. How can i get this please ?

Hello Julien,

thanks a lot. I’ve repaired the link.

cheers,

Sandro

Thank you for posting a clear cut intro, this is really useful.

Cheers

Hi,

I have a problem working with your sample code …on debugging i could find that the QP status could not be changed from init to rtr…

The return values of ibv\_modify\_qp are 101 on server and 22 on client…

Any info from you on this would be helpful to me..

thankyou

I also got the same problem : Err: No route to host – Could not modify QP to RTR state

Hi, I believe the image “Queue Pairs (send/receive) in the Channel Adapters” is incorrect and misleading. A Send Request will not be sent to peer Receive Queue. Send/Receive Queue are Work Queues, which can only modified by the requester itself.

Could you explain why ibv\_reg\_mr require root in your example? Is it possible to run the example without root?

I’m afraid our colleague who wrote this article has left, so we will not be able to answer this specific question, unfortunately.

Hi.

The reason is most likely that the default amount of memory which can be locked (i.e. pinned) for “standard” user is limited in most Linux distributions to 64 KBs.

(this can be changed using “ulimit” though).

“root” however, doesn’t have this limitation.

My blog answered this question long time ago..

Thanks

Dotan