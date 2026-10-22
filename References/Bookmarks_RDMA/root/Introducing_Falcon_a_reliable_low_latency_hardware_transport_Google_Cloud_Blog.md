# Introducing Falcon: a reliable low-latency hardware transport | Google Cloud Blog

- **Source:** https://cloud.google.com/blog/topics/systems/introducing-falcon-a-reliable-low-latency-hardware-transport
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA)
- **Retrieved:** 2026-10-22


---

# Google opens Falcon, a reliable low-latency hardware transport, to the ecosystem

##### Dan Lenoski

VP of Engineering, Google Cloud

##### Nandita Dukkipati

Principal Software Engineer, Google Cloud

At Google, we have a long history of solving problems at scale using Ethernet, and rethinking the transport layer to satisfy demanding workloads that require high burst bandwidth, high message rates, and low latency. Workloads such as storage have needed some of these attributes for a long time, however, with newer use cases such as massive-scale AI/ML training and high performance computing (HPC), the need has grown significantly. In the past, we’ve openly shared our learnings in traffic shaping, congestion control, load balancing, and more with the industry by contributing our ideas to the [Association for Computing Machinery](https://www.acm.org/) and [Internet Engineering Task Force](https://ietf.org/). These ideas have been implemented in software and a few in hardware for several years. But going forward, we believe the industry at large will see more gains by implementing the set with dedicated and flexible hardware assist.

To achieve this goal, we developed Falcon to enable a step function in performance over software-only transports. Today at the [OCP Global Summit](https://www.opencompute.org/summit/global-summit), we are excited to open Falcon to the ecosystem through the [Open Compute Project](https://www.opencompute.org/), the natural venue to empower the community with Google’s production learnings to help modernize Ethernet.

As a hardware-assisted transport layer, Falcon is designed to be reliable, high performance, and low latency and leverages production-proven technologies including [Carousel](https://research.google/pubs/pub46460/), [Snap](https://research.google/pubs/pub48630/), [Swift](https://research.google/pubs/pub49448/), [PLB](https://research.google/pubs/pub52149/), and [CSIG](https://datatracker.ietf.org/doc/html/draft-ravi-ippm-csig-00).

Falcon’s layers are illustrated in the figure below, including their associated function. We show the RDMA and NVM Express™ Upper layer protocols (ULPs), however, Falcon is extensible to additional ULPs as needed by the ecosystem.

The lower layers of Falcon use three key insights to achieve low latency in high-bandwidth, yet lossy, Ethernet data center networks. Fine-grained hardware-assisted round-trip time (RTT) measurements with flexible, per-flow hardware-enforced traffic shaping, and fast and accurate packet retransmissions, are combined with multipath-capable and [PSP-encrypted](https://cloud.google.com/blog/products/identity-security/announcing-psp-security-protocol-is-now-open-source) Falcon connections. On top of this foundation, Falcon has been designed from the ground up as a multi-protocol transport capable of supporting ULPs with widely varying performance requirements and application semantics. The ULP mapping layer not only provides out-of-the-box compatibility with Infiniband Verbs RDMA and NVMe ULPs, but also includes additional innovations critical for warehouse-scale applications such as flexible ordering semantics and graceful error handling. Last but not least, the hardware and software are co-designed to work together to help achieve the desired attributes of high message rate, low latency, and high bandwidth, while maintaining flexibility for programmability and continued innovation.

Falcon reflects the central role that Ethernet continues to play in our industry. Falcon is designed for predictable high performance at warehouse scale, as well as flexibility and extensibility. We look forward to working with the community and industry partners to modernize Ethernet to serve the networking requirements of our AI-driven future. We believe that Falcon will be a valuable addition to the other ongoing efforts in this space.

### Industry perspectives

Our partners across the industry are enthusiastic about the promise that Falcon holds for developing the next generation of Ethernet.

*“We welcome Google’s contribution of Falcon as it shares the Ultra Ethernet Consortium’s vision to drive Ethernet as the best data center fabric for AI and HPC, and look forward to continuing industry innovations in this important space.”* - Dr. J Metz, Chair, Ultra Ethernet Consortium (led by AMD, Arista, Broadcom, Cisco, Eviden, Hewlett Packard Enterprise, Intel, Meta, Microsoft, and Oracle)

*“Falcon is first available in the Intel IPU E2000 series of products. The value of these IPUs is further enhanced as the first instance of an Ethernet transport to add low tail latency and congestion handling at scale. Intel is a Steering Member of Ultra Ethernet Consortium, which is working to evolve Ethernet for high performance AI and HPC workloads. We plan to deploy the resulting standards-based enhancements in future IPU and Ethernet products.”* - Sachin Katti, SVP & GM, Network and Edge Group, Intel

*"We are pleased to see a high-performance transport protocol for critical workloads such as AI and HPC that works over standard Ethernet/IP networks and enables massive application bandwidth at scale."* - Hugh Holbrook, Group VP, SW Eng., Arista Networks

*“Cisco is pleased to see the contribution of Falcon to the OCP. Cisco has long supported open standards and believes in broad ecosystems. The rate and scale of modern data center networks and particularly AI/ML networks is unprecedented, presenting a challenge and opportunity to the industry. Falcon addresses many of the challenges of these networks, enabling efficient network utilization.”* - Ofer Iny, Cisco Fellow, Cisco

*“Juniper is a strong supporter of open ecosystems, and therefore we are pleased to see Falcon being opened to the OCP community. Falcon allows Ethernet to serve as the data center network-of-choice for demanding workloads, providing high-bandwidth, low tail latency and congestion mitigation. Falcon provides the industry with a proven solution today for demanding AI & ML workloads.”* - Raj Yavatkar, Chief Technology Officer, Juniper

*“Marvell strongly supports and is committed to the open Ethernet ecosystem as it evolves to support emerging, demanding workloads such as AI. We applaud the contribution of Falcon to OCP and welcome Google sharing practical experiences with the industry.”* - Nick Kucharewski, SVP & GM Network Switching Group, Marvell

### Learn more

Networking is a foundational component in building the sustainable, secure, scalable societal infrastructure that we need for this AI-driven future. To learn more about Falcon, join us for the OCP Summit presentation, “A Reliable and Low Latency Ethernet Hardware Transport” by Google’s Nandita Dukkipati at 11:45am at the Expo Hall. We’ll contribute the Falcon specification to OCP in the first quarter of 2024.

To learn more about Google’s contributions to the Open Compute Project and our presence at the OCP Global Summit, check out the blog “[How we’ll build sustainable, scalable, secure infrastructure for an AI-driven future](https://cloud.google.com/blog/topics/systems/google-systems-innovations-at-ocp-global-summit)”.