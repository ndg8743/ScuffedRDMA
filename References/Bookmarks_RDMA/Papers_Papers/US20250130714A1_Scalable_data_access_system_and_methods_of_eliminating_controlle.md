# US20250130714A1 - Scalable data access system and methods of eliminating controller bottlenecks - Google Patents

- **Source:** https://patents.google.com/patent/US20250130714A1/en?q=(RDMA+GPFS)&oq=RDMA+GPFS&sort=new
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > Papers > Papers)
- **Retrieved:** 2026-10-22


---

# US20250130714A1 - Scalable data access system and methods of eliminating controller bottlenecks - Google Patents

Scalable data access system and methods of eliminating controller bottlenecks
[Download PDF](https://patentimages.storage.googleapis.com/dc/1a/78/1a1d19114832ef/US20250130714A1.pdf)

## Info

- Publication number
- US20250130714A1 US20250130714A1 US19/005,557 US202419005557A US2025130714A1 US 20250130714 A1 US20250130714 A1 US 20250130714A1 US 202419005557 A US202419005557 A US 202419005557A US 2025130714 A1 US2025130714 A1 US 2025130714A1
- Authority
- US
- United States
- Prior art keywords
- san
- nfe
- nbe
- controller
- write
- Prior art date
- Legal status (The legal status is an assumption and is not a legal conclusion. Google has not performed a legal analysis and makes no representation as to the accuracy of the status listed.)
- Pending

## Links

## Images

## Classifications

  - G—PHYSICS
  - G06—COMPUTING OR CALCULATING; COUNTING
  - G06F—ELECTRIC DIGITAL DATA PROCESSING
  - G06F3/00—Input arrangements for transferring data to be processed into a form capable of being handled by the computer; Output arrangements for transferring data from processing unit to output unit, e.g. interface arrangements
  - G06F3/06—Digital input from, or digital output to, record carriers, e.g. RAID, emulated record carriers or networked record carriers
  - G06F3/0601—Interfaces specially adapted for storage systems
  - G06F3/0602—Interfaces specially adapted for storage systems specifically adapted to achieve a particular effect
  - G06F3/061—Improving I/O performance
  - G—PHYSICS
  - G06—COMPUTING OR CALCULATING; COUNTING
  - G06F—ELECTRIC DIGITAL DATA PROCESSING
  - G06F12/00—Accessing, addressing or allocating within memory systems or architectures
  - G06F12/02—Addressing or allocation; Relocation
  - G06F12/08—Addressing or allocation; Relocation in hierarchically structured memory systems, e.g. virtual memory systems
  - G06F12/0802—Addressing of a memory level in which the access to the desired data or data block requires associative addressing means, e.g. caches
  - G06F12/0804—Addressing of a memory level in which the access to the desired data or data block requires associative addressing means, e.g. caches with main memory updating
  - G—PHYSICS
  - G06—COMPUTING OR CALCULATING; COUNTING
  - G06F—ELECTRIC DIGITAL DATA PROCESSING
  - G06F12/00—Accessing, addressing or allocating within memory systems or architectures
  - G06F12/02—Addressing or allocation; Relocation
  - G06F12/08—Addressing or allocation; Relocation in hierarchically structured memory systems, e.g. virtual memory systems
  - G06F12/0802—Addressing of a memory level in which the access to the desired data or data block requires associative addressing means, e.g. caches
  - G06F12/0806—Multiuser, multiprocessor or multiprocessing cache systems
  - G—PHYSICS
  - G06—COMPUTING OR CALCULATING; COUNTING
  - G06F—ELECTRIC DIGITAL DATA PROCESSING
  - G06F12/00—Accessing, addressing or allocating within memory systems or architectures
  - G06F12/02—Addressing or allocation; Relocation
  - G06F12/08—Addressing or allocation; Relocation in hierarchically structured memory systems, e.g. virtual memory systems
  - G06F12/0802—Addressing of a memory level in which the access to the desired data or data block requires associative addressing means, e.g. caches
  - G06F12/0866—Addressing of a memory level in which the access to the desired data or data block requires associative addressing means, e.g. caches for peripheral storage systems, e.g. disk cache
  - G06F12/0868—Data transfer between cache memory and other subsystems, e.g. storage devices or host systems
  - G—PHYSICS
  - G06—COMPUTING OR CALCULATING; COUNTING
  - G06F—ELECTRIC DIGITAL DATA PROCESSING
  - G06F3/00—Input arrangements for transferring data to be processed into a form capable of being handled by the computer; Output arrangements for transferring data from processing unit to output unit, e.g. interface arrangements
  - G06F3/06—Digital input from, or digital output to, record carriers, e.g. RAID, emulated record carriers or networked record carriers
  - G06F3/0601—Interfaces specially adapted for storage systems
  - G06F3/0602—Interfaces specially adapted for storage systems specifically adapted to achieve a particular effect
  - G06F3/0625—Power saving in storage systems
  - G—PHYSICS
  - G06—COMPUTING OR CALCULATING; COUNTING
  - G06F—ELECTRIC DIGITAL DATA PROCESSING
  - G06F3/00—Input arrangements for transferring data to be processed into a form capable of being handled by the computer; Output arrangements for transferring data from processing unit to output unit, e.g. interface arrangements
  - G06F3/06—Digital input from, or digital output to, record carriers, e.g. RAID, emulated record carriers or networked record carriers
  - G06F3/0601—Interfaces specially adapted for storage systems
  - G06F3/0628—Interfaces specially adapted for storage systems making use of a particular technique
  - G06F3/0629—Configuration or reconfiguration of storage systems
  - G06F3/0634—Configuration or reconfiguration of storage systems by changing the state or mode of one or more devices
  - G—PHYSICS
  - G06—COMPUTING OR CALCULATING; COUNTING
  - G06F—ELECTRIC DIGITAL DATA PROCESSING
  - G06F3/00—Input arrangements for transferring data to be processed into a form capable of being handled by the computer; Output arrangements for transferring data from processing unit to output unit, e.g. interface arrangements
  - G06F3/06—Digital input from, or digital output to, record carriers, e.g. RAID, emulated record carriers or networked record carriers
  - G06F3/0601—Interfaces specially adapted for storage systems
  - G06F3/0628—Interfaces specially adapted for storage systems making use of a particular technique
  - G06F3/0629—Configuration or reconfiguration of storage systems
  - G06F3/0635—Configuration or reconfiguration of storage systems by changing the path, e.g. traffic rerouting, path reconfiguration
  - G—PHYSICS
  - G06—COMPUTING OR CALCULATING; COUNTING
  - G06F—ELECTRIC DIGITAL DATA PROCESSING
  - G06F3/00—Input arrangements for transferring data to be processed into a form capable of being handled by the computer; Output arrangements for transferring data from processing unit to output unit, e.g. interface arrangements
  - G06F3/06—Digital input from, or digital output to, record carriers, e.g. RAID, emulated record carriers or networked record carriers
  - G06F3/0601—Interfaces specially adapted for storage systems
  - G06F3/0628—Interfaces specially adapted for storage systems making use of a particular technique
  - G06F3/0646—Horizontal data movement in storage systems, i.e. moving data in between storage devices or systems
  - G06F3/065—Replication mechanisms
  - G—PHYSICS
  - G06—COMPUTING OR CALCULATING; COUNTING
  - G06F—ELECTRIC DIGITAL DATA PROCESSING
  - G06F3/00—Input arrangements for transferring data to be processed into a form capable of being handled by the computer; Output arrangements for transferring data from processing unit to output unit, e.g. interface arrangements
  - G06F3/06—Digital input from, or digital output to, record carriers, e.g. RAID, emulated record carriers or networked record carriers
  - G06F3/0601—Interfaces specially adapted for storage systems
  - G06F3/0668—Interfaces specially adapted for storage systems adopting a particular infrastructure
  - G06F3/067—Distributed or networked storage systems, e.g. storage area networks \[SAN\], network attached storage \[NAS\]
  - G—PHYSICS
  - G06—COMPUTING OR CALCULATING; COUNTING
  - G06F—ELECTRIC DIGITAL DATA PROCESSING
  - G06F2212/00—Indexing scheme relating to accessing, addressing or allocation within memory systems or architectures
  - G06F2212/10—Providing a specific technical effect
  - G06F2212/1016—Performance improvement
  - G—PHYSICS
  - G06—COMPUTING OR CALCULATING; COUNTING
  - G06F—ELECTRIC DIGITAL DATA PROCESSING
  - G06F2212/00—Indexing scheme relating to accessing, addressing or allocation within memory systems or architectures
  - G06F2212/10—Providing a specific technical effect
  - G06F2212/1032—Reliability improvement, data loss prevention, degraded operation etc
  - G—PHYSICS
  - G06—COMPUTING OR CALCULATING; COUNTING
  - G06F—ELECTRIC DIGITAL DATA PROCESSING
  - G06F2212/00—Indexing scheme relating to accessing, addressing or allocation within memory systems or architectures
  - G06F2212/26—Using a specific storage system architecture
  - G06F2212/263—Network storage, e.g. SAN or NAS
  - G—PHYSICS
  - G06—COMPUTING OR CALCULATING; COUNTING
  - G06F—ELECTRIC DIGITAL DATA PROCESSING
  - G06F2212/00—Indexing scheme relating to accessing, addressing or allocation within memory systems or architectures
  - G06F2212/28—Using a specific disk cache architecture
  - G06F2212/285—Redundant cache memory
  - G06F2212/286—Mirrored cache memory
  - G—PHYSICS
  - G06—COMPUTING OR CALCULATING; COUNTING
  - G06F—ELECTRIC DIGITAL DATA PROCESSING
  - G06F2212/00—Indexing scheme relating to accessing, addressing or allocation within memory systems or architectures
  - G06F2212/50—Control mechanisms for virtual memory, cache or TLB
  - G06F2212/502—Control mechanisms for virtual memory, cache or TLB using adaptive policy
  - G—PHYSICS
  - G06—COMPUTING OR CALCULATING; COUNTING
  - G06F—ELECTRIC DIGITAL DATA PROCESSING
  - G06F2212/00—Indexing scheme relating to accessing, addressing or allocation within memory systems or architectures
  - G06F2212/60—Details of cache memory
  - G06F2212/601—Reconfiguration of cache memory
  - G—PHYSICS
  - G06—COMPUTING OR CALCULATING; COUNTING
  - G06F—ELECTRIC DIGITAL DATA PROCESSING
  - G06F2212/00—Indexing scheme relating to accessing, addressing or allocation within memory systems or architectures
  - G06F2212/62—Details of cache specific to multiprocessor cache arrangements
  - Y—GENERAL TAGGING OF NEW TECHNOLOGICAL DEVELOPMENTS; GENERAL TAGGING OF CROSS-SECTIONAL TECHNOLOGIES SPANNING OVER SEVERAL SECTIONS OF THE IPC; TECHNICAL SUBJECTS COVERED BY FORMER USPC CROSS-REFERENCE ART COLLECTIONS \[XRACs\] AND DIGESTS
  - Y02—TECHNOLOGIES OR APPLICATIONS FOR MITIGATION OR ADAPTATION AGAINST CLIMATE CHANGE
  - Y02D—CLIMATE CHANGE MITIGATION TECHNOLOGIES IN INFORMATION AND COMMUNICATION TECHNOLOGIES \[ICT\], I.E. INFORMATION AND COMMUNICATION TECHNOLOGIES AIMING AT THE REDUCTION OF THEIR OWN ENERGY USE
  - Y02D10/00—Energy efficient computing, e.g. low power processors, power management or thermal management

## Definitions

- This document generally relates to the field of storage controllers and Storage Area Network (SAN) systems.
- the goal for this innovative storage technology is to boost performance by accelerating data access speed while improving overall datacenter efficiency to produce immediate saving in power, cooling costs, and floor space.
- VMs Virtual Servers
- each server may be dedicated to one or more specific applications, such as email server, accounting packages, etc.
- VMs Virtual Servers
- data access and data sharing could be done at different levels such as block level (shared block storage), multiple hosts accessing the same disk drives or Logical Unit Numbers (LUNs), or for file level access using legacy file systems like Network File System (NFS), Common Internet File System (CIFS), or modern parallel file systems such as Lustre, GPFS, QFS, StorNext, etc.
- NFS Network File System
- CIFS Common Internet File System
- TCP/IP protocol overhead together with network latency affects the performance of NFS/CIFS storage systems by significantly increasing access delays for network-attached storage when compared to locally attached disks slowing down applications and lowering overall datacenter utilization that may result in lower employee productivity.
- locally attached disk performance is usually slower than data storage subsystem implementations such as legacy SAN and RAID subsystems.
- Traditional SAN design and implementation even though in many cases superior to locally attached disks, tends to significantly underutilize aggregate data rate of all attached disk drives or SSDs by making use of time division multiplexing over, typically, small number of relatively slow I/O ports (network links) between servers and attached SAN subsystem(s).
- the present system is an improvement over the previously disclosed data storage architectures (Scalable Data Storage Architecture and Methods of Eliminating I/O Traffic Bottlenecks), by means of self-reconfiguring storage controllers and multi-level storage architecture.
- the new hardware architecture and firmware algorithms provide additional data access performance scaling, for bursty I/O traffic, without a need for additional back-end hard disk drives (HDDs) or solid state drives (SSDs). For that reason it is called a “Scalable Data Access System” rather than SAN.
- HDDs hard disk drives
- SSDs solid state drives
- the new architecture still facilitates parallel execution of the Front-End code on independent FE\_SAN and nFE\_SAN (new FE\_SAN design) controllers and employs locking mechanism in the Back-End code (executed on the BE\_SAN and nBE\_SAN (new BE\_SAN design) controllers) to enforce data coherency and prevent data corruption.
- nFE\_SAN nFE\_SAN/FE\_SAN
- controller(s) may be utilized the abbreviated notation will be used herein:
- nBE\_SAN (nBE\_SAN/BE\_SAN)
- the new nFE\_SAN controller hardware design enables a second copy of write data to be maintained locally without a need to first traverse the network fabric and store the second copy of the data on (n)BE\_SAN controller(s).
- the nFE\_SAN controller design includes two independent write-back cache memory buffers, each with corresponding processing,network-interface, and power components.
- a single nFE\_SAN controller card has two operationally independent controllers, FE\_SAN controller and redundant nFE\_SAN-S sub-controllers.
- nFE\_SAN controller cache In order to free up memory buffers with one copy of the data, de-staging of the nFE\_SAN controller cache to (n)BE\_SAN controller(s) is done as soon as possible and upon its completion the duplicate memory buffer (with one copy of the data) may be released, while the nFE\_SAN may optionally retain a single copy in the cache to permit ultrafast data access.
- an nFE\_SAN controller card has two different subsections, FE\_SAN controller and nFE\_SAN-S sub-controller, they may be presented to the host operating system (OS) as a single nFE\_SAN controller while the underlying complexity is hidden away from the host OS and user.
- OS host operating system
- FIGS. 1 and 2 depict the a storage system as shown in U.S. Pat. No. 9,118,698 entitled Scalable Data Storage Architecture and Methods of Eliminating I/O Traffic Bottlenecks.
- FIG. 3 illustrates nFE\_SAN 300 controller design example which accelerates execution of write requests by utilizing write-back-caching-with-mirroring enabled hardware and method.
- FIG. 3 a depicts nFE\_SAN 300 a controller design example with integrated flash storage (SSD) 304 or other non-volatile media to cache frequently accessed read/write data.
- SSD integrated flash storage
- FIG. 3 b shows nBE\_SAN 370 controller of an embodiment with an integrated nFE\_SAN 300 controller.
- FIG. 4 illustrates a memory-mapped file method, commonly used in UNIX/Linux environments. With this method, a file or a portion of a file is mapped onto application address space for directly accessing file data bypassing OS stack and SCSI layers while minimizing overhead associated with file data access.
- FIG. 5 is a system view of I/O related layers to access virtual disk (LUN) utilizing the new SAN architecture.
- the host has notion of having an ordinary SCSI device (disk drive or RAID controller) attached to it.
- the Front-End code creates a virtual device (virtual volume or LUN) that supports all (but not limited) mandatory SCSI commands; other storage interfaces/protocols may be supported as well.
- any other device could be emulated such as tape drive, DVD drive, etc.
- FIG. 6 depicts an application running on host or guest OSs can communicate directly with the Front-End, (n)FE\_SAN, controller firmware 620 via provided Application Programming Interface (API) and Application Binary Interface (ABI).
- API Application Programming Interface
- ABSI Application Binary Interface
- This technique eliminates overhead of host OS 680 , hypervisor or virtualization layers, and SCSI stack 621 , 622 , 623 , and 625 and accelerates data access by mapping portion the controller's memory containing file data into application 627 address space to directly access the data placed in the nFE\_SAN 610 or nFE\_SAN 611 controller. Similar technique could be used, if file system is not present, to directly map LBAs in the host OS 680 or guest OSs 682 .
- FIG. 7 explains how Front-End firmware for a memory-mapped file on the nFE\_SAN 772 controller allocates memory buffers 772 a and 773 a locally and further allocates corresponding memory ( 712 a , 732 a , and 750 a ) on the (n)BE\_SAN 712 , 732 , and 750 controllers for files distributed over a number of (n)BE\_SAN controllers.
- FIG. 8 illustrates a scenario where multiple computers (hosts) 880 and 882 generate very heavy I/O workload that saturates BE\_SAN 812 controller by repeatedly accessing certain range of Logical Block Addresses (LBAs).
- the depicted embodiment includes nFE\_SAN 872 and 874 controllers, BE\_SAN 812 and 832 , and nBE\_SAN 850 controllers.
- nBE\_SAN 850 controller has integrated nFE\_SAN 300 controller while BE\_SAN 812 and 832 controllers use legacy BE\_SAN controller hardware with new firmware that supports DRM 892 and 894 feature and functionality.
- nBE\_SAN 850 controller also contains DRM 895 module.
- FIG. 9 depicts a case where Distributed Resource Manager (DRM) 992 detects excessive workload which causes BE\_SAN controller 912 overload condition.
- DRM Distributed Resource Manager
- FIG. 9 depicts a case where Distributed Resource Manager (DRM) 992 detects excessive workload which causes BE\_SAN controller 912 overload condition.
- DRM redistributes (rebalances) the workload across BE\_SAN 912 and 932 and nBE\_SAN 950 controllers.
- FIG. 10 illustrates that DRM 995 detected excessive workload and nBE\_SAN controller 950 overload condition and further redistributes (rebalances) the workload across nBE\_SAN 951 and 952 controllers creating multi-level (n)BE\_SAN 952 , 951 , 950 , 932 , and 912 controller configuration.
- FIG. 11 illustrates that Distributed Resource Managers (DRMs) 996 , 993 , 995 , 994 , and 992 detected moderate workload directed to BE\_SAN 912 .
- DRMs Distributed Resource Managers
- the BE\_SAN controller 912 can handle all the I/O workload sent to it
- DRM 992 coordinates with other DRMs all dirty buffers to be flushed to the BE\_SAN 912 ; after the flush/sync process is completed DRMs dynamically rebalance the system again by freeing up nBE\_SAN controllers 950 , 951 , and 952 and BE\_SAN controller 932 .
- DRM will dynamically reconfigure the system again to alleviate the overload condition.
- FIG. 12 depicts how this multi-level dynamically reconfigurable data access technology can be integrated with public and/or private clouds 1200 as well as with cloud storage 1201 to accelerate data access speed by leveraging cloud storage cache (high-performance storage tier) 1203 to boost application performance, datacenter efficiency, and lower total cost of ownership.
- cloud storage cache high-performance storage tier
- FIG. 13 shows a flow diagram of an embodiment of a method of the present invention when write-back-with-mirroring is enabled to nFE\_SAN controller's redundant memory buffers, data transfer phase from nFE\_SAN to BE\_SAN controller(s), and once the data transfer has completed one of the allocated memory buffers on the nFE\_SAN controller gets released.
- FIG. 14 illustrates a flow diagram of an embodiment of a method of alleviating controller overload condition by caching certain LBA segments on different nBE\_SAN controller(s); thus, delegating part of its workload to additional controller(s).
- FIG. 15 demonstrates a flow diagram of an embodiment of a method of restoring the original controller system configuration by releasing the additional controllers once the overload condition ends.
- FIG. 16 represents a dataflow diagram of write operations showing time saved and overlap times of write operations using a system disclosed in the U.S. Pat. No. 9,118,698 (571770).
- Write data has to be mirrored between FE\_SAN and BE\_SAN controller(s) before “COMMAND COMPLETE” message can be sent to the host.
- FIG. 17 represents a dataflow diagram of write operations showing time saved and overlap times of write operations using the present system. Because two copies of the data are maintained by the nFE\_SAN controller “COMMAND COMPLETE” message can be returned to the host as soon as data transfer from the host is done and write lock(s) acquired from (n)BE\_SAN controller(s).
- FIG. 18 depicts Data Access System with first and second cache 1812 and 1818 , first and secondary power system 1810 and 1816 , first and second network interface 1814 and 1820 , and first and secondary processor 1824 and 1826 together form an nFE\_SAN controller as herein described.
- FIGS. 3 , 3 a , 3 b , 6 , 7 , 8 , 9 , 10 , 11 , 12 , 13 , 14 , 15 , 17 , and 18 present a system. There are two parts to this system.
- FIGS. 3 , 3 a , 6 , 7 , and 17 reveal improvements over the prior FE\_SAN controller of U.S. Pat. No. 9,118,698,
- FIG. 3 b depicts improvements over the BE\_SAN controller of U.S. Pat. No. 9,118,698, while FIGS. 9 , 10 , and 11 illustrate a method and technique utilized to eliminate hotspots related to (n)BE\_SAN controller(s) overload condition by dynamically reconfiguring (n)BE\_SAN controller(s) configuration.
- FIG. 12 depicts how this data access system may be integrated with public and private clouds and how it can be used as high-performance data cache or block storage tier for cloud storage, remote storage, archive, etc.
- FIG. 3 illustrates the hardware architecture that enables nFE\_SAN 300 controller to keep a redundant copy of the write data locally which eliminates a need to mirror the data to the BE\_SAN controllers before returning “COMMAND COMPLETE” message to the host.
- one of the memory buffers either 302 or 352 containing redundant copy of the data may be released.
- FIGS. 1 and 2 we can accomplish the same effect by configuring a host with two FE\_SAN controllers ( FIGS. 1 and 2 ) similar to those of U.S. Pat. No. 9,118,698 where a device driver creates copies of the same data on both FE\_SAN controllers.
- Such solutions may be more expensive than the nFE\_SAN 300 controller depicted in FIG. 3 , and may require two PCIe (or other type) slots instead of one.
- the allocated data buffers in the host OS 680 ( FIG. 6 ) are released.
- Such method may consume more host main memory bandwidth compared to the hardware implementation involving two or more FE\_SAN 201 controller group, or using nFE\_SAN 300 controller depicted on FIG. 3 .
- this method may be less reliable than the previously described method because servers and compute nodes may lose power, fail, or crash at any time and they are not always protected with uninterruptible backup power systems or devices such as battery backup or ultra-capacitor backup.
- nFE\_SAN 300 controller design enables a redundant copy of write data to be maintained locally on the nFE\_SAN controller card without the need to first traverse the network fabric and store the data on BE\_SAN controller(s) before returning “COMMAND COMPLETE” message to the host.
- nFE\_SAN controller improves write performance, if write-back-caching-with-mirroring is enabled, the write data is simultaneously transferred, using Copy-on-Write (CoW) to two independent memory buffers 302 and 352 and a “COMMAND COMPLETE” message is returned to the host OS as soon as the data transfer is completed and lock(s) from (n)BE\_SAN controller(s) acquired.
- CoW Copy-on-Write
- the key feature of the nFE\_SAN 300 controller design is that the two independent memory buffers 302 and 352 and corresponding processing 303 and 353 and network components 320 and 321 are functionally and physically self-sufficient, effectively creating two operationally independent controller cards (FE\_SAN 301 controller and nFE\_SAN-S 350 sub-controller).
- nFE\_SAN 300 controller may be presented to the host OS while the underlying complexity is hidden away from the host OS and user. This design also mitigates single-point-of-failure issues. De-staging of the nFE\_SAN 300 controller data cache to (n)BE\_SAN controller(s) is done as soon as possible and upon its completion the one of the memory buffers 302 or 352 may be released keeping one copy of the data in the nFE\_SAN 300 controller.
- the device driver together with nFE\_SAN firmware may present multiple virtual nFE\_SAN 300 controllers to the host OS, hypervisor manager or other virtualization layers, guest OSs, and their applications.
- FIG. 3 b depicts an nBE\_SAN 370 controller of an embodiment with an integrated nFE\_SAN 300 controller.
- FE\_SAN 301 controller with BE\_SAN 371 controller.
- FE\_SAN 301 or nFE\_SAN 300 controller is integrated and used depends on the reliability, resiliency, performance, and cost requirements.
- NVMe based or other flash storage (SSD) 374 may be integrated to absorb extended I/O bursts, reduce memory requirements, and also to cache frequently read data locally.
- a storage device is a disk drive such as a traditional hard disk, a flash-memory based “thumb drive”, a solid-state disk (SSD), non-volatile memory express (NVMe), an optical storage device such as a digital versatile disk (DVD-RW) or blue-ray drive, or other block-oriented machine-readable drive as known in the computing industry.
- SSD solid-state disk
- NVMe non-volatile memory express
- DVD-RW digital versatile disk
- One of the key roles (function) of a SCSI device interface is to protect data residing on the SCSI device from misbehaving host.
- the SCSI command set is designed to provide efficient peer-to-peer (initiator—target) operation of SCSI devices (HBAs, disks, tapes, printers, etc.).
- HBAs peer-to-peer
- NVMe Non-Volatile Memory Express
- the new storage interface standards include SCSI Express (SCSIe), Non-Volatile Memory Express (NVMe), and other proprietary computer manufacturer peripheral device standards.
- the nFE\_SAN and FE\_SAN controllers in addition to conforming to Small Computer System Interface (SCSI) set of standards, also support new and emerging industry storage standards such as SCSI Express (SCSIe), Non-Volatile Memory Express (NVMe), as well as other proprietary computer manufacturer peripheral device standards.
- SCSIe Small Computer System Interface
- NVMe Non-Volatile Memory Express
- multiple nFE\_SAN/FE\_SAN controllers attached to a host may be configured as a controller group conforming to legacy SCSI as well as new and emerging peripheral device and persistent data storage interface standards.
- the nFE\_SAN controller is configured such that data is retained in a first write-back cache and transferred to (n)BE\_SAN controllers over a first network when a first controller and power supply are operational, retained in a second write-back cache and transferred to (n)BE\_SAN controllers over a second network when a second controller and power supply are operational, the first and second controllers and power supplies being independent.
- This configuration provides for storage and transmission of write-back cache data from the nFE\_SAN controller to the (n)BE\_SAN controller even if there is a failure of one unit selected from the group of the first and second controllers, the first and second network, and the first and second write-back cache, and first and second power supplies.
- the new (n)FE\_SAN controller firmware is configurable to logically partition and virtualize controller hardware and software resources to facilitate virtualized and cloud environments such as VMware, OpenBox, Microsoft Hyper-V, KVM, Xen, etc.
- a single physical (n)FE\_SAN controller may present a number of different virtual controllers with different controller properties to different Virtual Machines (VMs) on the same physical server.
- VMs Virtual Machines
- The, (n)FE\_SAN controller may be provided in different physical formats but not limited to PCI, PCIe, SBus, or memory channel interface board formats. However, (n)FE\_SAN controller may support a number of host buses such as PCI, PCIe, SBus, the IBM Coherent Accelerator Processor Interface (CAPI), QuickPath Interconnect (QPI), HyperTransport (HT), and various memory channel interface standards, to mention a few.
- each (n)FE\_SAN interface card has firmware (software) that supports additional services and features such as compression, encryption, de-duplication, thin provisioning (TP), snapshots, remote replication, etc.
- the nBE\_SAN controller (back-end) may be provided in a number of different physical formats such as in the standard disk drive enclosure format (including 19 inch rack and standalone enclosures), or an integrated circuit that is easily adaptable to the standard interior configuration of a SAN controller.
- the hardware design of a nBE\_SAN controller may include integration of one or more of nFE\_SAN or FE\_SAN controller(s) that enables the controller to operate as BE\_SAN controller when servicing requests from other (n)FE\_SAN controllers and to act as nFE\_SAN or FE\_SAN controller when initiating requests and sending data to other BE\_SAN or nBE\_SAN controller(s).
- the hardware design and new firmware features of nBE\_SAN controller enable dynamic reconfiguration of the data access (storage) system and creation of multi-level (n)BE\_SAN controller configurations.
- a number of different storage interfaces may be supported at the back-end of a nBE\_SAN controller, including legacy device standards such as SCSI, SAS, Advanced Technology Attachment (ATA), Serial ATA (SATA), FC, and emerging new standards such as NVMe, SCSIe, and other similar disk storage as well as PCI Express (PCIe), QuickPath Interconnect (QPI), HyperTransport (HT), CAPI, memory channel interfaces, etc.
- legacy device standards such as SCSI, SAS, Advanced Technology Attachment (ATA), Serial ATA (SATA), FC
- emerging new standards such as NVMe, SCSIe, and other similar disk storage as well as PCI Express (PCIe), QuickPath Interconnect (QPI), HyperTransport (HT), CAPI, memory channel interfaces, etc.
- PCIe PCI Express
- QPI QuickPath Interconnect
- HT HyperTransport
- CAPI memory channel interfaces
- Each (n)BE\_SAN controller has firmware (software) that supports legacy features such as SCSI device discovery, fault management, RAID functionality, remote direct memory access (RDMA) capability, and error handling functionality as well as new features such as erasure coding, workload monitoring and when necessary workload sharing with other (n)BE\_SAN controllers.
- the firmware on each (n)BE\_SAN controller provides all necessary functionality to support legacy target disk storage interfaces such as SCSI, SAS, ATA, SATA, or FC disk drives, as well as PCIe or CAPI directly attached flash storage supporting emerging standards such as NVMe and SCSIe.
- (n)BE\_SAN controller resources may be partitioned and virtualized to facilitate guest OSs and applications enabling user code to be executed on the (n)BE\_SAN controllers.
- both (n)FE\_SAN and (n)BE\_SAN have firmware that provide Application Programming Interface (API) and Application Binary Interface (ABI) to allow host operating system (OS), guest OSs, and applications to memory-map a file or part of a file to directly access file and/or block data bypassing OS stack and SCSI/storage layers.
- API Application Programming Interface
- ABSI Application Binary Interface
- ( n )FE\_SAN controllers may simultaneously support network and storage I/O traffic facilitating Converged I/O Interface (CIOI).
- (n)FE\_SAN controller may provide Network Interface Card (NIC) as well as storage controller functionality.
- NIC Network Interface Card
- (n)FE\_SAN controllers are host dedicated resources while (n)BE\_SAN controllers are shared resources.
- (n)BE\_SAN controllers are shared resources.
- every shared resource it is possible to encounter a condition in which the workload sent to a shared resource exceeds the capacity of that resource which may cause the resource to be overwhelmed and driven into saturation over a prolonged period of time. It is probable and expected that different parts of a storage system will be utilized at different levels and that the utilization will vary over time.
- the overload condition can be alleviated by caching selected LBAs on other (n)BE\_SAN controller(s) that are not experiencing an overload condition at the same time.
- DRM Distributed Resource Manager
- nBE\_SAN controller when Distributed Resource Manager (DRM) detects excessive workload on a BE\_SAN/nBE\_SAN controller(s) (overload condition), it coordinates with other DRMs to redistribute (rebalance) the workload across one or more of additional (n)BE\_SAN controllers by inserting them in the I/O path in front of the overloaded (n)BE\_SAN controller.
- DRM Distributed Resource Manager
- one or more of spare (n)BE\_SAN controllers may be dynamically added to the (n)BE\_SAN controller cluster configuration to further boost I/O processing and bandwidth performance in order to alleviate (n)BE\_SAN controller(s) overload condition.
- DRM may find that the system is better utilized if the LUN or part of that LUN from the (n)BE\_SAN that experiences overload condition is transferred to another (n)BE\_SAN controller that has direct access to the LUN.
- FE\_SAN controller resources may be partitioned and virtualized to support guest OSs and applications
- FE\_SAN controller functionality may be implemented in one or more software modules in the firmware to be executed in a physical or logical partition.
- (n)FE\_SAN chipsets may also be embedded within nBE\_SAN controller for additional speed, reliability, and cost savings.
- FIG. 5 illustrates high-level host I/O stack and Front-End firmware API and ABI providing direct access to the FE\_SAN controller memory buffers.
- UNIX/Linux system calls such as mmap( ), munmap( ), msync ( ), mprotect( ), and madvise( ) or equivalent may be used to manage the file data and memory access.
- FIG. 6 embodies a partitioned and virtualized (n)FE\_SAN 610 controller with front-end firmware 620 , OS stack 680 , and SCSI layers 621 , 622 , 623 , and 625 .
- (n)FE\_SAN device driver and related modules 620 a resides in between Front-End code 620 and SCSI Interface 621 .
- the new front-end firmware 620 has a feature that simultaneously supports both host OS 680 and guest OSs 682 and applications 627 providing direct access to the Front-End firmware 620 and to the allocated memory buffers.
- (n)FE\_SAN controller firmware 620 provides API and ABI.
- the provided API and ABI enable guest OSs 682 and applications 627 running in VMs to interact directly with the firmware 620 and to access the allocated resources.
- multiple (n)FE\_SAN controllers attached to a host may be configured as a controller group 611 .
- the firmware 620 may partition and virtualize the entire controller group 611 and present a number of virtual nFE\_SAN controllers to the host OS 680 and guest OSs 682 .
- additional functionality including partitioning and virtualization is added to the previously disclosed FE\_SAN controller 510 and the Front-End firmware 520 capabilities and feature set.
- FIG. 7 illustrates how memory buffers may be allocated, mapped, and distributed in an embodiment across a number of nFE\_SAN 772 and 774 and BE\_SAN (or nBE\_SAN) 712 , 732 , and 750 controllers.
- Front-End firmware running on nFE\_SAN 772 and 774 controllers allocates and manages local memory buffers 772 a , 773 a , 774 a and 775 a , upon receiving a request from an application or host OS via provided API and ABI to map a file or portion of a file into application address space.
- FIG. 7 illustrates how memory buffers may be allocated, mapped, and distributed in an embodiment across a number of nFE\_SAN 772 and 774 and BE\_SAN (or nBE\_SAN) 712 , 732 , and 750 controllers.
- Front-End firmware running on nFE\_SAN 772 and 774 controllers allocates and manages local memory buffers 772 a , 773 a ,
- the size of the allocated redundant/mirrored nFE\_SAN memory buffers 772 a and 773 a needs to be sufficient to keep the data until the data transfer between nFE\_SAN 772 and BE\_SAN 712 , 732 , and 750 (or nBE\_SAN) controllers is completed.
- Front-End firmware running on nFE\_SAN 772 and 774 controllers sends a request, as needed, to the corresponding Back-End firmware running on BE\_SAN 712 , 732 , and 750 controllers to process the request.
- the memory buffers are dynamically allocated and managed upon a specific memory location (and corresponding LBA) is accessed.
- the copy-on-write method is used to automatically copy data from nFE\_SAN “mmapped” memory buffers 772 a to the mirrored buffers 773 a (which may be dynamically allocated and released) and corresponding memory buffers 712 a , 732 a , and 750 a allocated on the BE\_SAN (or nBE\_SAN) controllers. It is presumed that the application(s) that were granted direct memory access to the nFS\_SAN 772 and 774 controllers' memory buffers assume complete control and responsibility for synchronizing and maintaining data coherency. Furthermore, provided API and ABI provide facility to allocate and allow direct access to the memory buffers on nFE\_SAN 772 and 774 (FE\_SAN) of the requested LBA(s) outside of a file system. As previously stated, user/application needs to assume complete control and responsibility for data management when using this feature.
- FIG. 8 illustrates a scenario where a heavy I/O workload from multiple hosts 880 and 882 (via FE\_SAN/nFE\_SAN controllers 872 and 874 ) saturates BE\_SAN 812 controller.
- Distributed Resource Manager (DRM) 892 detects the overload condition and coordinates resource allocation information with other DRMs ( 894 and 895 ) to find an optimal solution that alleviates the BE\_SAN 812 overload condition and maximizes aggregate system performance.
- DRM Distributed Resource Manager
- FIG. 9 further clarifies a scenario where BE\_SAN 912 experiences excessive I/O workload while controllers BE\_SAN 932 and nBE\_SAN 950 are lightly utilized.
- the DRM algorithm finds that the optimal solution is to split the I/O traffic directed to the most frequently accessed LBAs on BE\_SAN 912 into three segments (LBAs-1, LBAs-2, and LBAs-3). Then LBAs-2 and LBAs-3 segments are cached on BE\_SAN 932 and nBE\_SAN 950 controllers respectively by creating corresponding LBAs-2′ and LBAs-3′ cache.
- DRM 992 instructs the FE\_SAN controllers 972 and 974 to transparently redirect the I/O traffic originally intended for the corresponding LBAs on BE\_SAN 912 controller to be sent (from now on) to BE\_SAN 912 if the LBA address range falls within LBAs-1 range, to send to BE\_SAN 932 if the accessed LBAs fall within LBAs-2 range, or to send to nBE\_SAN 950 if the targeted LBAs fall within LBAs-3 range.
- both BE\_SAN 932 and nBE\_SAN 950 may be used to improve the aggregate Back-End processing power and bandwidth during excessive I/O workload periods
- the key difference between BE\_SAN 932 and nBE\_SAN 950 is that nBE\_SAN 950 has additional hardware which provides additional performance acceleration (for additional information, please see FIG. 3 b ).
- nBE\_SAN 950 has additional hardware which provides additional performance acceleration (for additional information, please see FIG. 3 b ).
- all three nBE\_SAN/nBE\_SAN 912 , 932 , and 950 controllers have the same performance, assuming that initially the BE\_SAN 932 and nBE\_SAN 950 controllers were idle, by utilizing the described technique for the previously depicted scenario the peak aggregate performance for that specific workload could be increased as much as 300%.
- the long duration average I/O bandwidth (data rate) directed to the BE\_SAN controller 912 has to be lower than the controller bandwidth and attached back-end storage devices aggregate bandwidth.
- BE\_SAN 912 controller views BE\_SAN 932 and nBE\_SAN 950 controllers as FE\_SAN (nFE\_SAN) controllers when receiving requests directed to LBAs-2 and LBAs-3 segments.
- FE\_SAN FE\_SAN
- the utilized locking algorithm is the same between BE\_SAN 932 and 912 (or BE\_SAN 950 and nBE\_SAN 912 ) as, for instance, between FE\_SAN 972 and BE\_SAN 912 .
- (n)BE\_SAN 912 , 932 , and 950 controllers may play (n)BE\_SAN controller role when servicing (n)FE\_SAN 972 and 974 controllers' requests and to assume (n)FE\_SAN controller's role when caching LBAs (data) from another (n)BE\_SAN controller.
- FIG. 10 depicts a scenario in which DRM 995 detected excessive utilization on the nBE\_SAN 950 controller and determines that the optimal solution is to split the I/O traffic directed to the most frequently accessed LBAs into two segments (LBAs-3.1′ and LBA-s3.2′). It may be appropriate to mention that LBA-3.1′ and LBA-s3.2′ do not have to be of the same size. Then LBAs-3.1′ and LBAs-3.2′ segments are cached on the nBE\_SAN 951 and 952 controllers respectively.
- DRM 995 instructs the (n)FE\_SAN 972 and 974 controllers to redirect the I/O traffic intended for LBAs on nBE\_SAN 950 controller transparently to the host, sending traffic to nBE\_SAN 951 if the LBA address range falls within LBAs-3.1′ range and to send to nBE\_SAN 952 if the accessed LBAs fall within LBAs-3.2′ range.
- the new dynamically created controller configuration takes shape of multi-level storage controller topology.
- the storage controller configuration and topology may be policy driven, which gives administrators additional tools and flexibility to further tune the system performance for specific workloads.
- FIG. 11 Once the overload condition on BE\_SAN controller 912 is alleviated, all the remaining cached data on the nBE\_SAN 952 , 951 , and 950 and BE\_SAN 932 controllers are orderly de-staged to the BE\_SAN controller 912 and the memory buffers LBAs-3.1′′, LBAs-3.2′′, LBAs-3.1′, LBAs-3.2′, LBAs-3′ and LBAs-2′ segments are released.
- nBE\_SAN 950 , 951 , 952 , and 953 are released and made available to be deployed if another hotspot (overload condition) is detected anywhere in the systems.
- DRM 995 may initiate data flush from nBE\_SAN 951 and 952 controllers. Once all data is de-staged from LBAs-3.1′′ and LBAs-3.2′′ to the nBE\_SAN 950 controller, the segments LBAs-3.1′′ and LBAs-3.2′′ are released and nBE\_SAN 951 , and 952 are freed; thus, restoring the previous system configuration depicted in FIG. 9 .
- nBE\_SAN controllers 950 may be the same or similar as nBE\_SAN 950 .
- nBE\_SAN 950 may make use of one or more SSDs, PCIe Flash Memory cards, or additional NVRAM or other persistent memory devices to mitigate cache-full condition during extended periods of heavy writing. In addition, it may cache frequently read (accessed) LBAs to boost read performance.
- NAS Network Attached Storage
- FIG. 12 illustrates how the apparatus disclosed in the embodiment of this application may be used as data cache or high performance storage tier 1203 for cloud storage 1201 , archive, or remote storage and how (n)FE\_SAN 1272 and 1274 controllers may be integrated and utilized with private and public cloud 1200 deployments to improve application performance by accelerating data access speed. Furthermore, as depicted in FIGS. 2 , 3 , and 3 a , and as described above, integrating (n)FE\_SAN 1272 and 1274 controller with a NIC to support Converged I/O Interface may be recommended.
- FIG. 13 illustrates an example of how nFE\_SAN 300 ( FIG. 3 ) controller speeds up writes when write-back-caching-with-mirroring is enabled.
- nFE\_SAN controller receives write command 1300 from the host.
- Front-End firmware immediately sends write-lock request 1310 to the appropriate (n)BE\_SAN controller(s). In addition, it simultaneously requests 1320 write memory buffers ( 302 and 352 ) from 301 and 350 ( FIG. 3 ) controllers. Then front-end firmware initiates data transfer 1322 from the host memory to the allocated memory buffers on the nFE\_SAN controller. In parallel, the firmware checks if the requested lock(s) from the nBE\_SAN controller has/have been granted 1330 .
- the firmware sends “COMMAND COMPLETE” the host OS in 1333 . Also, as soon as the lock(s) were granted and data transfer 1342 to the (n)BE\_SAN controller is initiated. Once the transfer from nFE\_SAN controller to (n)BE\_SAN controller has been completed, in this example, the firmware 1343 releases corresponding buffers on nFE\_SAN-S sub-controller. This completes this example 1344 .
- step 1330 the lock hasn't been granted, then in this simplified example 1341 , the firmware will retry to obtain lock(s) from the nBE\_SAN controller(s) until it either obtains lock(s) or times out; if the time-out occurs then the issues is passed to the upper system management layers. For all practical purposes, we assume that the system is operational and therefore it does grant requested locks every time.
- DRM.b receives request for resources from DRM.a (which is granted). In case that a resource is not granted for some reason in step 1440 , “N”, DRM.a identifies another controller and requests resources for the same LBAs, (step 1433 ). DRM.b sends confirmation message which LBAs will be cached ( 1441 ) to DRM.a. In 1442 DRM.a checks if there are more segments that need to be cached and if “Y” starts the process again from step 1433 . However, in this simplified example, no more segments need to be cached on other controllers, the answer is “N” and the algorithm proceeds to step 1443 . In 1443 DRM.a sends new LUN layout information (map) to all (n)FE\_SAN controllers which can access that LUN. The new map that contains information about new (n)BE\_SAN controller topology.
- FIG. 15 it is shown how the system returns to its original configuration once the overload condition has ended.
- DRM.a gets a notification that overload condition has ended 1500 .
- DRM.a retrieves a list of all cached LBAs and corresponding controllers, 1520 . Then it gets workload statistics from each controller on the list for the LBAs that have been cached on that controller, 1532 . In 1533 it retrieves information which controller will be freed first/next. Then DRM.a sends DRM\_release\_resource( ) request in 1534 which implies that related cached LBAs should be synced first.
- Controller cache gets synhed; DRM\_cache\_synced( ) succeeds in 1540 and DRM\_release\_resource( ) request succeeds in 154 . Then DRM.b sends DRM\_release\_resource( ) notification in 1541 and starts “writing through” all incoming write requests. Then in step 1542 it checks if there are more cached LBA segments that should be restored. If the answer is yes, then the process starts again from step 1533 . If in step 1540 DRM on the alternate controller fails to release the allocated resources then the DRM simply proceeds with freeing up resources on the other controllers and retries to release resources after went through the entire list.
- the original FE\_SAN design FIG. 2 has one CPU, memory, etc.
- the new design consists of a FE\_SAN 301 controller and nFE\_SAN-S 350 sub-controller card or chip.
- nFE\_SAN ⁇ 300 ( FE\_SAN ⁇ 301 ) + ( nFE\_SAN - S ⁇ 350 )
- the nFE\_SAN-S 350 sub-controller is operationally, functionally, and electrically independent of the FE\_SAN 301 controller.
- the performance CPU and memory capacity requirements of the nFE\_SAN-S 350 controller may be significantly lower compared FE\_SAN 301 controller, while the memory bandwidth requirement cannot be lower than the host side bus (channel) bandwidth.
- Both controllers 301 & 350 are physically built into a single PCI, PCIe, or other standard card format.
- write-back-cache-with-mirroring feature requires to maintain at least two copies of the write data until the data is written to the back-end HDDs, SSDs, or other permanent storage media.
- this implementation does not have single point of failure while the data coherency is maintained via locking mechanism which maintains the information where each piece of data may be found and retrieved from.
- the write data has to be mirrored front-to-back (FE\_SAN->BE\_SAN controller) by sending the data over the network before “COMMAND COMPLETE” message could be returned to the host.
- the write data is simultaneously written to both MEM 302 and 352 on the controller nFE\_SAN 300 and then as soon as the lock(s) are granted by (n)BE\_SAN controller(s) the “COMMAND COMPLETE” message is immediately returned to the host without the need to first “mirror” the data to the nBE\_SAN controller(s); apparently this method is significantly faster and it is comparably reliable as the original method.
- the SCSI standard does not guarantee the order in which SCSI commands are executed.
- “COMMAND COMPLETE” message may be immediately returned to the host without waiting for lock(s) to be granted by nBE\_SAN controller(s). However, if the order of execution has to be guaranteed, every request has to be associated with an appropriate lock.
- NVMe/SSD 304 with nFE\_SAN 300 creates nFE\_SAN 300 a controller; 304 could be a high-speed NVMe based flash memory or NVRAM device/chip. This enables 300 a controller to keep more write and read data locally; the flash memory may have TBs of capacity as the price of SSD and NVMe technology continue to decline.
- An additional feature allows for keeping of some specific blocks locally in the nonvolatile or flash memory.
- the improved nBE\_SAN controller 370 consists of BE\_SAN 371 with additional SSD 374 and nFE\_SAN 300 or FE\_SAN 301 :
- nBE\_SAN controller 370 enable the Data Access System to dynamically change its topology to adapt to the changing workload requirements.
- a (n)BE\_SAN controller can be automatically and dynamically inserted in front of another (n)BE\_SAN controller to boost its I/O processing capability by caching certain LBAs from the (n)BE\_SAN controller.
- BE\_SAN 371 controller when receiving commands from (n)FE\_SAN controller(s) and as nFE\_SAN 300 when forwarding the data to a BE\_SAN controller.
- nBE\_SAN controllers also have new firmware with Distributed Resource Manager (DRM) and virtualization capability to run guest OS and user applications on the nBE\_SAN controller.
- DRM Distributed Resource Manager
- Each (n)BE\_SAN controller may incorporate a multi-core CPU server motherboard with sufficient memory and additional components such as battery backup, NVRAM and NVMe SSDs, etc.
- each (n)BE\_SAN controller is capable of running VMware or any other virtualization software to allow user application to run on the (n)BE\_SAN controllers. Therefore, (n)BE\_SAN controller provides capability to locally run applications or execute user code close to the dataset that it needs to process.
- FIG. 1 (PRIOR ART)—As disclosed in the original patent, it is possible to install and configure two or more FE\_SAN controllers in a server to create a controller group aggregating the I/O performance and capacity of all installed FE\_SAN controllers. Then, the controller group is presented by the device driver to the host OS as a virtual FE\_SAN controller with significantly higher performance compared to a single FE\_SAN controller.
- (n)FE\_SAN controller can virtualize its resources using hypervisor or other virtualization method to create multiple virtual (n)FE\_SAN controllers 610 and present different VIRTUAL controllers with different features and properties to different OSs 680 , guest OSs 682 , and applications 627 .
- the new firmware 620 features provide facility to virtualize (n)FE\_SAN controller group 611 and present virtual (n)FE\_SAN controllers to different OSs and guest OSs.
- FIG. 7 As described in \[ 0008 \] the data is written simultaneously to both memory buffers 772 a and 773 a on the nFE\_SAN 772 controller and based on the mode pages, the firmware may immediately return “COMMAND COMPLETE” to the host without the need to, first, write data to the BE\_SAN controller(s). Then the data is de-staged (flushed) to the BE\_SAN controllers at the first opportunity and the buffers with one copy of the data (either 772 a or 773 a ) are released while the second copy of the data is retained maintaining front to back mirroring.
- the new nFE\_SAN 772 hardware and data handing method provides write speed up while maintaining data integrity and reliability at the same level as any other modern SAN or RAID systems that utilize write-back caching with mirroring.
- FIG. 8 in this example, applications running on computers 880 and 882 produce intensive I/O workload, writing the data to the same LBAs on BE\_SAN controller 812 , driving the controller into saturation due to excessive workload.
- Distributed Resource Manager (DRM) 892 receives notification of the BE\_SAN 812 controller extended overload condition. DRM then looks at the distribution of the writes, which LBAs are accessed most often. After reviewing the statistics and finding optimal solution, DRM 892 decides to split this with heavily used LBAs segment on BE\_SAN 812 into three smaller segments LBAs-1, LBAs-2, and LBAs-3 (please see FIG. 9 ). Then DRM 892 further coordinates with DRMs 894 and 895 on other BE\_SAN, it may find that BE\_SANs 832 and 850 have low utilization or that they are idle.
- DRM Distributed Resource Manager
- FIG. 9 Thus, if an under-utilized (n)BE\_SAN controller is found (say DRM 994 and 995 ), DRM 992 instructs DRM 994 to create LBAs-2′ and DRM 995 to create LBAs-3′ cache.
- LBAs-2′ acts as cache and points to LBAs-2, the same applies for LBAs-3′ and LBAs-3 that are utilized to offload the heavily utilized (n)BE\_SAN controller.
- DRM 992 instructs (n)FE\_SAN controller(s) DRM 999 and 998 to stop sending data to LBAs-2 and LBAs-3 on the original BE\_SAN 912 and instead start sending the newly written data to the offloaded LBAs-2′ and LBAs-3′ on the controllers (n)BE\_SAN 932 and 950 controllers.
- BE\_SAN 932 has new firmware that allows LBAs-2 caching in the LBAs-2′ buffers.
- the write data from nFE\_SAN controllers, after data aggregation and coalescing is forwarded to the LBAs-2 on the BE\_SAN 912 controller.
- nBE\_SAN 950 has firmware and nFE\_SAN hardware (such as nFE\_SAN 972 controller card or silicon) integrated within nBE\_SAN 950 controller that speeds up writes to the BE\_SAN 912 controller.
- firmware and nFE\_SAN hardware such as nFE\_SAN 972 controller card or silicon
- FIG. 9 depicts the new (n)BE\_SAN controller topology with two levels of (n)BE\_SAN controllers. Therefore, the (n)BE\_SAN controller topology may change dynamically so the storage system can adapt to workload requirements in real-time.
- FIG. 10 illustrates (n)BE\_SAN controller topology with THREE levels of (n)BE\_SAN controllers. Therefore, (n)BE\_SAN controllers can dynamically and in real-time adapt to any type of workload up to the point when all (n)BE\_SAN controllers are configured to handle storage I/O workload.
- the storage system maintains optimal level of service and resource utilization by dynamically in real-time responding to the workload requirements by deploying additional hardware resources when and where they are needed and freeing up unutilized resources when they are not needed.
- hardware resources (n)BE\_SAN controllers, consume less power when they are idle compared to when they are heavily used.
- the additional benefits of this technology is saving power during periods when the system is not heavily used, while boosting performance when the system is heavily used.
- the (n)BE\_SAN controllers may be incrementally added to boost storage system peak performance if and when needed enabling storage performance to scale independently from storage capacity.
- DRM 992 on nBE\_SAN 912 controller receives notification that the heavy workload sent to the BE\_SAN 912 LBAs has subsided and RDMs coordinate the process of de-staging cached data to the BE\_SAN 912 attached back-end storage media and restore the initial controller configuration (topology) freeing up nBE\_SAN controllers 951 , 952 , 950 , and 932 .
- heavily accessed data or files may be relocated from storage on one BE\_SAN to a less-heavily loaded BE\_SAN that holds part of the same logical drive.
- logical and physical drive (volume) location may be dissociated.
- FIG. 12 illustrates how herein described embodiment supports and accelerates data access in private and public cloud environments by having (n)FE\_SAN controllers installed in cloud servers 1280 and 1282 .
- nFE\_SAN controllers installed in cloud servers 1280 and 1282 .
- multiple (n)BE\_SAN controllers in this simplified example BE\_SAN 1212 and 1232 controllers
- DR remote replication Disaster Recover
- FIG. 16 depicts a dataflow diagram of write operations showing the execution sequence and interaction between application, host SCSI driver, FE\_SAN and BE\_SAN controllers for a system disclosed in the U.S. Pat. No. 9,118,698 ( 571770 ).
- Write data has to be mirrored between FE\_SAN and BE\_SAN controller(s) before “COMMAND COMPLETE” message can be sent to the host.
- FIG. 17 illustrates timing of a write sequence as executed on a system according to the herein described embodiments, as partially illustrated in FIG. 18 .
- a CPU of CPUs 1802 executing an application 1804 and a driver 1805 associated with an operating system determines a write command to storage is required.
- the write command 1702 is modified by driver 1805 and passed as an extended write command 1704 with buffer info through bus interface 1809 to FE\_SAN 1808 .
- FE\_SAN 1808 has a first, primary, power system 1810 , a first cache memory 1812 , and a first network interface 1814 .
- FE\_SAN 1808 also has a secondary power system 1816 , a secondary cache 1818 , and in some embodiments a second network interface 1820 .
- FE\_SAN operates under control of FE\_SAN firmware 1822 executing on a primary processor 1824 and FE\_SAN-S firmware 1823 executing on a secondary processor 1826 , primary processor powered by power system 1810 and secondary processor 1826 powered by second power system 1816 .
- Primary network interface 1814 couples through a first storage area network interconnect 1830 to a primary network interface 1832 of a BE\_SAN 1834
- second network interface 1820 couples through a second storage area network interface 1828 to a secondary network interface 1836 of BE\_SAN 1834
- BE\_SAN 1834 has a primary cache 1838 powered by a primary power supply 1840
- a second cache 1842 powered by a second power supply 1844
- BE\_SAN 1834 has a primary processor 1846 and a secondary processor 1848 operating under control of BE\_SAN firmware 1850 and 1851 respectively.
- BE\_SAN 1834 also has two or more disk drive interfaces 1852 , 1854 , each coupled to one or more storage drives 1856 , 1858 , 1860 , 1862 , 1864 , 1866 .
- BE\_SAN firmware 1850 is configured to operate one or more virtual drives on storage drives 1856 - 1866 using a Redundant Array of Independent Drives (RAID) protocol permitting reconstruction of data on the virtual drives should a failure occur of any one of storage drives 1856 , 1858 , 1860 , 1862 , 1864 , 1866 .
- RAID Redundant Array of Independent Drives
- Erasure Coding (EC) or other method of data protection may be implemented on the system depicted in FIG. 18 .
- Second cache 1818 , secondary power system 1816 , second network interface 1820 , and secondary processor 1826 together form an FE\_SAN\_S as herein described.
- FE\_SAN 1808 passes a write lock request 1706 to BE\_SAN 1834 .
- FE\_SAN 1808 also begins processing the write request by instructing 1708 driver 1805 , including allocating 1709 and setting up any memory mapped buffers, to begin transferring 1710 data into both the primary and secondary cache 1812 and 1818 using “put (data)” operations.
- data is written directly to primary cache 1812
- that data is copied (CoW) 1711 to secondary cache 1818 .
- BE\_SAN 1834 responds to FE\_SAN 1808 with a lock-request-granted signal 1712 .
- FE\_SAN 1808 provides a write complete “ack” signal 1714 to driver 1805 , which passes a command complete signal 1716 to the executing application 1804 .
- FE\_SAN 1808 begins transferring 1718 the data to BE\_SAN 1834 where this data is mirrored in cache memories 1834 , 1840 .
- Write data at this point may reside in duplicate in FE\_SAN caches 1812 , 1818 ; while data transfers 1718 continue.
- the BE\_SAN sends a final acknowledgement signal 1720 to the FE\_SAN, which may then release one or both copies in FE\_SAN cache 1812 , 1818 .
- the secondary processor 1826 continues to transfer data from the secondary cache 1818 to the BE\_SAN to ensure completion of the write operation.
- BE\_SAN primary processor 1846 , primary cache 1838 , or primary power 1840 fail, BE\_SAN secondary processor 1848 completes receiving the data over BE\_SAN secondary network 1836 into secondary cache 1840 and completes writing data to storage devices 1856 - 1866 .
- the data is retained in battery-backup secondary cache 1840 and alarms sounded; data writing is completed upon repair of the BE\_SAN.

## Landscapes

- Engineering & Computer Science (AREA)
- Theoretical Computer Science (AREA)
- Physics & Mathematics (AREA)
- General Physics & Mathematics (AREA)
- General Engineering & Computer Science (AREA)
- Human Computer Interaction (AREA)
- Computer Networks & Wireless Communication (AREA)
- Information Retrieval, Db Structures And Fs Structures Therefor (AREA)
- Signal Processing (AREA)
- Acoustics & Sound (AREA)
- Health & Medical Sciences (AREA)
- Life Sciences & Earth Sciences (AREA)
- Chemical & Material Sciences (AREA)
- Analytical Chemistry (AREA)
- Biochemistry (AREA)
- General Health & Medical Sciences (AREA)
- Immunology (AREA)
- Pathology (AREA)
- Power Engineering (AREA)
- Mathematical Physics (AREA)
- Spectroscopy & Molecular Physics (AREA)

## Abstract

## Description

-  This application is a continuation of U.S. patent application Ser. No. 18/226,513, filed Jul. 26, 2023 which is a continuation of U.S. patent application Ser. No. 17/201,115, filed Mar. 15, 2021, now U.S. Pat. No. 11,747,981, which is a continuation of U.S. patent application Ser. No. 16/449,874, filed Jun. 24, 2019, now U.S. Pat. No. 10,949,093, which is a continuation of U.S. patent application Ser. No. 15/482,726 filed Apr. 8, 2017, now U.S. Pat. No. 10,331,353, which claims priority to U.S. Provisional Patent Application No. 62/320,349 filed Apr. 8, 2016. This application is also related generally to improvements on the storage technology described in U.S. patent application Ser. No. 15/173,043 (now U.S. Pat. No. 9,823,866), which in turn claims priority to U.S. patent application Ser. No. 11/292,838 (now U.S. Pat. No. 8,347,010) and U.S. patent application Ser. No. 14/252,838 (now U.S. Pat. No. 9,527,190). The contents of all the aforementioned patent applications and patents are incorporated herein by reference.
-  This document generally relates to the field of storage controllers and Storage Area Network (SAN) systems. The goal for this innovative storage technology is to boost performance by accelerating data access speed while improving overall datacenter efficiency to produce immediate saving in power, cooling costs, and floor space.
-  According to Moore's law, CPU performance improves about 2× over two years, or approximately 50% per year. Although, historically Hard Disk Drive (HDD) capacity improves at the same rate, data access speed improvements lag behind the CPU performance and HDD capacity improvements. Based on a number of published papers and study reports, the CPU performance improves roughly 50% per year while storage I/O performance improves only about 5% per year. Thus, since 1980, the CPU performance has increased over quarter of a million times while the performance of legacy SAN systems (many of which are Redundant Array of Independent Disks (RAID) systems) has improved only about 12 times. Therefore, it is clear that in a computer system there is a growing I/O performance gap between compute and storage performance, which may limit the maximum achievable utilization of such unbalanced computer systems. Even with new advances in Flash Memory and Solid-State Drive (SSD) technology, the data access speed fails to match performance advances in CPU and memory technologies.
-  To further improve data storage scalability and performance to be able to meet Big Data and Exascale computational requirements for ultra-high data access speeds and capacity, a new herein-disclosed technology leverages the architecture and methods we have disclosed in our previous U.S. Pat. No. 9,118,698, the disclosure of which is incorporated herein by reference. With the world's data more than doubling every two years, there is ever-increasing demand for more storage capacity and performance. Legacy SAN and RAID technologies available today are unable to meet performance requirements and, with prohibitively high cost, are out of reach for the majority of the small and some medium size businesses.
-  To reduce cost, organizations often utilize large number of disjoint individual physical servers with one or more Virtual Servers (VMs) where each server may be dedicated to one or more specific applications, such as email server, accounting packages, etc. However, such approach introduces other issues such as insufficient storage I/O performance, system and network administration, fault tolerance, fragmented data storage, online storage and backup management problems, as well as system complexity, and so forth. Data access and data sharing could be done at different levels such as block level (shared block storage), multiple hosts accessing the same disk drives or Logical Unit Numbers (LUNs), or for file level access using legacy file systems like Network File System (NFS), Common Internet File System (CIFS), or modern parallel file systems such as Lustre, GPFS, QFS, StorNext, etc.
-  In addition, TCP/IP protocol overhead together with network latency affects the performance of NFS/CIFS storage systems by significantly increasing access delays for network-attached storage when compared to locally attached disks slowing down applications and lowering overall datacenter utilization that may result in lower employee productivity. However, locally attached disk performance is usually slower than data storage subsystem implementations such as legacy SAN and RAID subsystems. Traditional SAN design and implementation, even though in many cases superior to locally attached disks, tends to significantly underutilize aggregate data rate of all attached disk drives or SSDs by making use of time division multiplexing over, typically, small number of relatively slow I/O ports (network links) between servers and attached SAN subsystem(s).
-  The present system is an improvement over the previously disclosed data storage architectures (Scalable Data Storage Architecture and Methods of Eliminating I/O Traffic Bottlenecks), by means of self-reconfiguring storage controllers and multi-level storage architecture. In addition, the new hardware architecture and firmware algorithms provide additional data access performance scaling, for bursty I/O traffic, without a need for additional back-end hard disk drives (HDDs) or solid state drives (SSDs). For that reason it is called a “Scalable Data Access System” rather than SAN. Thus, with this new data access system further decoupling of I/O performance from storage capacity was made possible. The new architecture still facilitates parallel execution of the Front-End code on independent FE\_SAN and nFE\_SAN (new FE\_SAN design) controllers and employs locking mechanism in the Back-End code (executed on the BE\_SAN and nBE\_SAN (new BE\_SAN design) controllers) to enforce data coherency and prevent data corruption.
-  To denote that either nFE\_SAN or FE\_SAN, (nFE\_SAN/FE\_SAN), controller(s) may be utilized the abbreviated notation will be used herein:
-  Similarly, we denote that either nBE\_SAN or BE\_SAN controller(s) may be used using notation: (n)BE\_SAN=(nBE\_SAN/BE\_SAN)
-  Furthermore, to accelerate execution of write requests and to improve reliability and resiliency, the new nFE\_SAN controller hardware design enables a second copy of write data to be maintained locally without a need to first traverse the network fabric and store the second copy of the data on (n)BE\_SAN controller(s). In order to prevent single-points-of-failure, the nFE\_SAN controller design includes two independent write-back cache memory buffers, each with corresponding processing,network-interface, and power components. Thus, a single nFE\_SAN controller card has two operationally independent controllers, FE\_SAN controller and redundant nFE\_SAN-S sub-controllers. In order to free up memory buffers with one copy of the data, de-staging of the nFE\_SAN controller cache to (n)BE\_SAN controller(s) is done as soon as possible and upon its completion the duplicate memory buffer (with one copy of the data) may be released, while the nFE\_SAN may optionally retain a single copy in the cache to permit ultrafast data access. Even though, an nFE\_SAN controller card has two different subsections, FE\_SAN controller and nFE\_SAN-S sub-controller, they may be presented to the host operating system (OS) as a single nFE\_SAN controller while the underlying complexity is hidden away from the host OS and user.
-  The foregoing and other objects, features and advantages of the invention will be apparent from the following more comprehensive description of embodiments of the system, as illustrated in the accompanying drawings in which like reference characters refer to similar parts throughout the different views.
- FIGS. **1** and **2** (PRIOR ART) depict the a storage system as shown in U.S. Pat. No. 9,118,698 entitled Scalable Data Storage Architecture and Methods of Eliminating I/O Traffic Bottlenecks.
- FIG. **3** illustrates nFE\_SAN **300** controller design example which accelerates execution of write requests by utilizing write-back-caching-with-mirroring enabled hardware and method.
- FIG. **3** *a* depicts nFE\_SAN **300** *a* controller design example with integrated flash storage (SSD) **304** or other non-volatile media to cache frequently accessed read/write data. As non-volatile media becomes more affordable, it creates an opportunity to leverage additionalnon-volatile storage capacity **304** to reduce network traffic by writing data to **304** and keeping frequently read data locally.
- FIG. **3** *b* shows nBE\_SAN **370** controller of an embodiment with an integratednFE\_SAN **300** controller.
- FIG. **4** (PRIOR ART) illustrates a memory-mapped file method, commonly used in UNIX/Linux environments. With this method, a file or a portion of a file is mapped onto application address space for directly accessing file data bypassing OS stack and SCSI layers while minimizing overhead associated with file data access.
- FIG. **5** (PRIOR ART) is a system view of I/O related layers to access virtual disk (LUN) utilizing the new SAN architecture. Same as in traditional SAN solutions, the host has notion of having an ordinary SCSI device (disk drive or RAID controller) attached to it. The Front-End code creates a virtual device (virtual volume or LUN) that supports all (but not limited) mandatory SCSI commands; other storage interfaces/protocols may be supported as well. However, using the same method any other device could be emulated such as tape drive, DVD drive, etc.
- FIG. **6** depicts an application running on host or guest OSs can communicate directly with the Front-End, (n)FE\_SAN,controller firmware **620** via provided Application Programming Interface (API) and Application Binary Interface (ABI). This technique eliminates overhead ofhost OS **680**, hypervisor or virtualization layers, andSCSI stack **621**, **622**, **623**, and **625** and accelerates data access by mapping portion the controller's memory containing file data intoapplication **627** address space to directly access the data placed in the nFE\_SAN **610** ornFE\_SAN **611** controller. Similar technique could be used, if file system is not present, to directly map LBAs in thehost OS **680** orguest OSs **682**.
- FIG. **7** explains how Front-End firmware for a memory-mapped file on thenFE\_SAN **772** controller allocates memory buffers **772** *a* and **773** *a* locally and further allocates corresponding memory (**712** *a*, **732** *a*, and **750** *a*) on the (n)BE\_SAN **712**, **732**, and **750** controllers for files distributed over a number of (n)BE\_SAN controllers.
- FIG. **8** illustrates a scenario where multiple computers (hosts) **880** and **882** generate very heavy I/O workload that saturatesBE\_SAN **812** controller by repeatedly accessing certain range of Logical Block Addresses (LBAs). The depicted embodiment includesnFE\_SAN **872** and **874** controllers,BE\_SAN **812** and **832**, andnBE\_SAN **850** controllers. As illustrated inFIG. **3**  b nBE\_SAN **850** controller has integratednFE\_SAN **300** controller whileBE\_SAN **812** and **832** controllers use legacy BE\_SAN controller hardware with new firmware that supportsDRM **892** and **894** feature and functionality.nBE\_SAN **850** controller also containsDRM **895** module.
- FIG. **9** depicts a case where Distributed Resource Manager (DRM) **992** detects excessive workload which causesBE\_SAN controller **912** overload condition. In order to alleviate theBE\_SAN controller **912** overload condition, DRM redistributes (rebalances) the workload acrossBE\_SAN **912** and **932** andnBE\_SAN **950** controllers.
- FIG. **10** illustrates thatDRM **995** detected excessive workload andnBE\_SAN controller **950** overload condition and further redistributes (rebalances) the workload acrossnBE\_SAN **951** and **952** controllers creating multi-level (n)BE\_SAN **952**, **951**, **950**, **932**, and **912** controller configuration.
- FIG. **11** illustrates that Distributed Resource Managers (DRMs) **996**, **993**, **995**, **994**, and **992** detected moderate workload directed toBE\_SAN **912**. Because the overload condition has subsided and theBE\_SAN controller **912** can handle all the I/O workload sent to it,DRM **992** coordinates with other DRMs all dirty buffers to be flushed to theBE\_SAN **912**; after the flush/sync process is completed DRMs dynamically rebalance the system again by freeing upnBE\_SAN controllers **950**, **951**, and **952** andBE\_SAN controller **932**. Hoverer, if excessive workload is detected again anywhere in the system on one or more controllers, DRM will dynamically reconfigure the system again to alleviate the overload condition.
- FIG. **12** depicts how this multi-level dynamically reconfigurable data access technology can be integrated with public and/orprivate clouds **1200** as well as withcloud storage **1201** to accelerate data access speed by leveraging cloud storage cache (high-performance storage tier) **1203** to boost application performance, datacenter efficiency, and lower total cost of ownership.
- FIG. **13** shows a flow diagram of an embodiment of a method of the present invention when write-back-with-mirroring is enabled to nFE\_SAN controller's redundant memory buffers, data transfer phase from nFE\_SAN to BE\_SAN controller(s), and once the data transfer has completed one of the allocated memory buffers on the nFE\_SAN controller gets released.
- FIG. **14** illustrates a flow diagram of an embodiment of a method of alleviating controller overload condition by caching certain LBA segments on different nBE\_SAN controller(s); thus, delegating part of its workload to additional controller(s).
- FIG. **15** demonstrates a flow diagram of an embodiment of a method of restoring the original controller system configuration by releasing the additional controllers once the overload condition ends.
- FIG. **16** (PRIOR ART) represents a dataflow diagram of write operations showing time saved and overlap times of write operations using a system disclosed in the U.S. Pat. No. 9,118,698 (571770). Write data has to be mirrored between FE\_SAN and BE\_SAN controller(s) before “COMMAND COMPLETE” message can be sent to the host.
- FIG. **17** represents a dataflow diagram of write operations showing time saved and overlap times of write operations using the present system. Because two copies of the data are maintained by the nFE\_SAN controller “COMMAND COMPLETE” message can be returned to the host as soon as data transfer from the host is done and write lock(s) acquired from (n)BE\_SAN controller(s).
- FIG. **18** depicts Data Access System with first andsecond cache **1812** and **1818**, first andsecondary power system **1810** and **1816**, first andsecond network interface **1814** and **1820**, and first andsecondary processor **1824** and **1826** together form an nFE\_SAN controller as herein described.
- FIGS. **3**, **3** *a*, **3** *b*, **6**, **7**, **8**, **9**, **10**, **11**, **12**, **13**, **14**, **15**, **17**, and **18** present a system. There are two parts to this system.FIGS. **3**, **3** *a*, **6**, **7**, and **17** reveal improvements over the prior FE\_SAN controller of U.S. Pat. No. 9,118,698,FIG. **3** *b* depicts improvements over the BE\_SAN controller of U.S. Pat. No. 9,118,698, whileFIGS. **9**, **10**, and **11** illustrate a method and technique utilized to eliminate hotspots related to (n)BE\_SAN controller(s) overload condition by dynamically reconfiguring (n)BE\_SAN controller(s) configuration.FIG. **12** depicts how this data access system may be integrated with public and private clouds and how it can be used as high-performance data cache or block storage tier for cloud storage, remote storage, archive, etc.
- FIG. **3** illustrates the hardware architecture that enablesnFE\_SAN **300** controller to keep a redundant copy of the write data locally which eliminates a need to mirror the data to the BE\_SAN controllers before returning “COMMAND COMPLETE” message to the host. However, as soon as the data is copied to the (n)BE\_SAN controller(s), one of the memory buffers (either **302** or **352**) containing redundant copy of the data may be released. However, we can accomplish the same effect by configuring a host with two FE\_SAN controllers (FIGS. **1** and **2** ) similar to those of U.S. Pat. No. 9,118,698 where a device driver creates copies of the same data on both FE\_SAN controllers. Such solutions may be more expensive than thenFE\_SAN **300** controller depicted inFIG. **3** , and may require two PCIe (or other type) slots instead of one. Similarly, it is possible to, in addition to caching write data in theFE\_SAN **201** controller'smemory **202**, to keep second copy of the data in the FE\_SAN controller'sdevice driver **620** *a* or software module allocated memory in the host (FIG. **6** ). Thus, one copy of the data would exist on theFE\_SAN **201** controller while the second copy of the same data in the host main memory. Once the data is transferred to the (n)BE\_SAN controllers, the allocated data buffers in the host OS **680** (FIG. **6** ) are released. However, such method may consume more host main memory bandwidth compared to the hardware implementation involving two ormore FE\_SAN **201** controller group, or usingnFE\_SAN **300** controller depicted onFIG. **3** . In addition, this method may be less reliable than the previously described method because servers and compute nodes may lose power, fail, or crash at any time and they are not always protected with uninterruptible backup power systems or devices such as battery backup or ultra-capacitor backup.
-  Host read/write command execution and algorithms to process storage I/O commands in parallel remains similar to that as described in U.S. Pat. No. 9,118,698 entitled “Scalable Data Storage Architecture and Methods of Eliminating I/O Traffic Bottlenecks”. However, thenew nFE\_SAN **300** controller design enables a redundant copy of write data to be maintained locally on the nFE\_SAN controller card without the need to first traverse the network fabric and store the data on BE\_SAN controller(s) before returning “COMMAND COMPLETE” message to the host. To further explain how nFE\_SAN controller improves write performance, if write-back-caching-with-mirroring is enabled, the write data is simultaneously transferred, using Copy-on-Write (CoW) to twoindependent memory buffers **302** and **352** and a “COMMAND COMPLETE” message is returned to the host OS as soon as the data transfer is completed and lock(s) from (n)BE\_SAN controller(s) acquired. Thus, the key feature of thenFE\_SAN **300** controller design is that the twoindependent memory buffers **302** and **352** andcorresponding processing **303** and **353** andnetwork components **320** and **321** are functionally and physically self-sufficient, effectively creating two operationally independent controller cards (FE\_SAN **301** controller and nFE\_SAN-S **350** sub-controller). However, asingle nFE\_SAN **300** controller may be presented to the host OS while the underlying complexity is hidden away from the host OS and user. This design also mitigates single-point-of-failure issues. De-staging of thenFE\_SAN **300** controller data cache to (n)BE\_SAN controller(s) is done as soon as possible and upon its completion the one of the memory buffers **302** or **352** may be released keeping one copy of the data in thenFE\_SAN **300** controller. However, in order to improve performance and support for virtual environments, the device driver together with nFE\_SAN firmware may present multiplevirtual nFE\_SAN **300** controllers to the host OS, hypervisor manager or other virtualization layers, guest OSs, and their applications.
- FIG. **3** *b* depicts annBE\_SAN **370** controller of an embodiment with an integratednFE\_SAN **300** controller. However, it is also entirely possible to integratelower cost FE\_SAN **301** controller withBE\_SAN **371** controller. Obviously, whetherFE\_SAN **301** ornFE\_SAN **300** controller is integrated and used depends on the reliability, resiliency, performance, and cost requirements. Furthermore, NVMe based or other flash storage (SSD) **374** may be integrated to absorb extended I/O bursts, reduce memory requirements, and also to cache frequently read data locally.
-  SCSI standard defines device interface model and SCSI command set for all SCSI devices. For purposes of this document, a storage device is a disk drive such as a traditional hard disk, a flash-memory based “thumb drive”, a solid-state disk (SSD), non-volatile memory express (NVMe), an optical storage device such as a digital versatile disk (DVD-RW) or blue-ray drive, or other block-oriented machine-readable drive as known in the computing industry. One of the key roles (function) of a SCSI device interface is to protect data residing on the SCSI device from misbehaving host. The SCSI command set is designed to provide efficient peer-to-peer (initiator—target) operation of SCSI devices (HBAs, disks, tapes, printers, etc.). However, with improvements in non-volatile memory, flash memory, and SSD technology, the new solid state based persistent memory devices have outperformed legacy SCSI interface which became performance bottleneck. Thus, in recent years a new set emerging storage industry interface standards have been developed to overcome the legacy SCSI standard shortcomings. The new storage interface standards include SCSI Express (SCSIe), Non-Volatile Memory Express (NVMe), and other proprietary computer manufacturer peripheral device standards. (n)FE\_SAN controllers can readily take advantage or the newly developed standards to further reduce latency and boost transfer rate between host memory andnFE\_SAN controller memory **302** and **352**. Furthermore, multiple FE\_SAN/nFE\_SAN controllers attached to a host via host or memory bus may be configured as a controller group conforming to legacy SCSI as well as new and emerging peripheral/storage device interface standards.
-  In an embodiment, on the host side, the nFE\_SAN and FE\_SAN controllers, in addition to conforming to Small Computer System Interface (SCSI) set of standards, also support new and emerging industry storage standards such as SCSI Express (SCSIe), Non-Volatile Memory Express (NVMe), as well as other proprietary computer manufacturer peripheral device standards. Still, multiple nFE\_SAN/FE\_SAN controllers attached to a host may be configured as a controller group conforming to legacy SCSI as well as new and emerging peripheral device and persistent data storage interface standards.
-  In an embodiment, the nFE\_SAN controller is configured such that data is retained in a first write-back cache and transferred to (n)BE\_SAN controllers over a first network when a first controller and power supply are operational, retained in a second write-back cache and transferred to (n)BE\_SAN controllers over a second network when a second controller and power supply are operational, the first and second controllers and power supplies being independent. This configuration provides for storage and transmission of write-back cache data from the nFE\_SAN controller to the (n)BE\_SAN controller even if there is a failure of one unit selected from the group of the first and second controllers, the first and second network, and the first and second write-back cache, and first and second power supplies.
-  Furthermore, the new (n)FE\_SAN controller firmware is configurable to logically partition and virtualize controller hardware and software resources to facilitate virtualized and cloud environments such as VMware, OpenBox, Microsoft Hyper-V, KVM, Xen, etc. Thus, a single physical (n)FE\_SAN controller may present a number of different virtual controllers with different controller properties to different Virtual Machines (VMs) on the same physical server.
-  The, (n)FE\_SAN controller may be provided in different physical formats but not limited to PCI, PCIe, SBus, or memory channel interface board formats. However, (n)FE\_SAN controller may support a number of host buses such as PCI, PCIe, SBus, the IBM Coherent Accelerator Processor Interface (CAPI), QuickPath Interconnect (QPI), HyperTransport (HT), and various memory channel interface standards, to mention a few. In addition to basic functionality, such as SCSI device discovery, error handling and recovery, and some RAID functionality, each (n)FE\_SAN interface card has firmware (software) that supports additional services and features such as compression, encryption, de-duplication, thin provisioning (TP), snapshots, remote replication, etc. The nBE\_SAN controller (back-end) may be provided in a number of different physical formats such as in the standard disk drive enclosure format (including 19 inch rack and standalone enclosures), or an integrated circuit that is easily adaptable to the standard interior configuration of a SAN controller.
-  In an embodiment, the hardware design of a nBE\_SAN controller may include integration of one or more of nFE\_SAN or FE\_SAN controller(s) that enables the controller to operate as BE\_SAN controller when servicing requests from other (n)FE\_SAN controllers and to act as nFE\_SAN or FE\_SAN controller when initiating requests and sending data to other BE\_SAN or nBE\_SAN controller(s). The hardware design and new firmware features of nBE\_SAN controller enable dynamic reconfiguration of the data access (storage) system and creation of multi-level (n)BE\_SAN controller configurations.
-  A number of different storage interfaces may be supported at the back-end of a nBE\_SAN controller, including legacy device standards such as SCSI, SAS, Advanced Technology Attachment (ATA), Serial ATA (SATA), FC, and emerging new standards such as NVMe, SCSIe, and other similar disk storage as well as PCI Express (PCIe), QuickPath Interconnect (QPI), HyperTransport (HT), CAPI, memory channel interfaces, etc.
-  Each (n)BE\_SAN controller has firmware (software) that supports legacy features such as SCSI device discovery, fault management, RAID functionality, remote direct memory access (RDMA) capability, and error handling functionality as well as new features such as erasure coding, workload monitoring and when necessary workload sharing with other (n)BE\_SAN controllers. The firmware on each (n)BE\_SAN controller provides all necessary functionality to support legacy target disk storage interfaces such as SCSI, SAS, ATA, SATA, or FC disk drives, as well as PCIe or CAPI directly attached flash storage supporting emerging standards such as NVMe and SCSIe. In addition, (n)BE\_SAN controller resources may be partitioned and virtualized to facilitate guest OSs and applications enabling user code to be executed on the (n)BE\_SAN controllers.
-  In an embodiment, both (n)FE\_SAN and (n)BE\_SAN have firmware that provide Application Programming Interface (API) and Application Binary Interface (ABI) to allow host operating system (OS), guest OSs, and applications to memory-map a file or part of a file to directly access file and/or block data bypassing OS stack and SCSI/storage layers. Because of its hardware architecture and new firmware features (seeFIGS. **2**, **3**, and **3** *a*), (*n*)FE\_SAN controllers may simultaneously support network and storage I/O traffic facilitating Converged I/O Interface (CIOI). Thus, (n)FE\_SAN controller may provide Network Interface Card (NIC) as well as storage controller functionality.
-  In an embodiment, (n)FE\_SAN controllers are host dedicated resources while (n)BE\_SAN controllers are shared resources. As with every shared resource, it is possible to encounter a condition in which the workload sent to a shared resource exceeds the capacity of that resource which may cause the resource to be overwhelmed and driven into saturation over a prolonged period of time. It is probable and expected that different parts of a storage system will be utilized at different levels and that the utilization will vary over time. Thus, if a particular I/O workload disproportionately targets a specific (n)BE\_SAN controller or set of controllers exceeding the controller(s) performance limits, the overload condition can be alleviated by caching selected LBAs on other (n)BE\_SAN controller(s) that are not experiencing an overload condition at the same time. Thus, when Distributed Resource Manager (DRM) detects excessive workload on a BE\_SAN/nBE\_SAN controller(s) (overload condition), it coordinates with other DRMs to redistribute (rebalance) the workload across one or more of additional (n)BE\_SAN controllers by inserting them in the I/O path in front of the overloaded (n)BE\_SAN controller. Using the same method, one or more of spare (n)BE\_SAN controllers may be dynamically added to the (n)BE\_SAN controller cluster configuration to further boost I/O processing and bandwidth performance in order to alleviate (n)BE\_SAN controller(s) overload condition. Additionally, if a LUN is attached to two or more (n)BE\_SAN controllers, DRM may find that the system is better utilized if the LUN or part of that LUN from the (n)BE\_SAN that experiences overload condition is transferred to another (n)BE\_SAN controller that has direct access to the LUN.
-  Furthermore, as (n)BE\_SAN controller resources may be partitioned and virtualized to support guest OSs and applications, FE\_SAN controller functionality may be implemented in one or more software modules in the firmware to be executed in a physical or logical partition. Yet, (n)FE\_SAN chipsets may also be embedded within nBE\_SAN controller for additional speed, reliability, and cost savings.
- FIG. **5** (PRIOR ART) illustrates high-level host I/O stack and Front-End firmware API and ABI providing direct access to the FE\_SAN controller memory buffers. UNIX/Linux system calls such as mmap( ), munmap( ), msync ( ), mprotect( ), and madvise( ) or equivalent may be used to manage the file data and memory access.
- FIG. **6** embodies a partitioned and virtualized (n)FE\_SAN **610** controller with front-end firmware **620**,OS stack **680**, and SCSI layers **621**, **622**, **623**, and **625**. (n)FE\_SAN device driver andrelated modules **620** *a*, resides in between Front-End code **620** andSCSI Interface **621**. The new front-end firmware **620** has a feature that simultaneously supports bothhost OS **680** andguest OSs **682** andapplications **627** providing direct access to the Front-End firmware **620** and to the allocated memory buffers. Furthermore, (n)FE\_SAN controller firmware **620** provides API and ABI. The provided API and ABI enableguest OSs **682** andapplications **627** running in VMs to interact directly with thefirmware **620** and to access the allocated resources. In addition, multiple (n)FE\_SAN controllers attached to a host may be configured as acontroller group **611**. Thefirmware **620** may partition and virtualize theentire controller group **611** and present a number of virtual nFE\_SAN controllers to thehost OS **680** andguest OSs **682**. Thus, additional functionality including partitioning and virtualization is added to the previously disclosedFE\_SAN controller **510** and the Front-End firmware **520** capabilities and feature set.
- FIG. **7** , illustrates how memory buffers may be allocated, mapped, and distributed in an embodiment across a number ofnFE\_SAN **772** and **774** and BE\_SAN (or nBE\_SAN) **712**, **732**, and **750** controllers. Front-End firmware running onnFE\_SAN **772** and **774** controllers allocates and manages local memory buffers **772** *a*, **773** *a*, **774** *a* and **775** *a*, upon receiving a request from an application or host OS via provided API and ABI to map a file or portion of a file into application address space. As presented inFIG. **7** Front-End firmware allocates all necessary memory buffers including redundant memory buffers **773** *a* and **775** *a* on nFE\_SAN-S **773** and **775** sub-controller (also please seeFIG. **3** ). Because, nFE\_SAN memory buffers are exposed in an application user space, when the application writes to the nFE\_SAN controller “mmapped” (memory mapped) memory buffers **772** *a* and **774** *a*, Copy-on-Write mechanism automatically mirrors the data into the allocated redundant memory buffers **773** *a* and **775** *a* on the nFE\_SAN-S sub-controller **773** and **775** and initiates data transfer to the corresponding BE\_SAN controller(s) **712**, **732**, and **750**. The size of the allocated redundant/mirrored nFE\_SAN memory buffers **772** *a* and **773** *a* needs to be sufficient to keep the data until the data transfer betweennFE\_SAN **772** andBE\_SAN **712**, **732**, and **750** (or nBE\_SAN) controllers is completed.
-  Applications running on thehosts **780** and **782** (FIG. **7** ) request to map a file or portion of a file into their respective address spaces. Front-End firmware running onnFE\_SAN **772** and **774** controllers sends a request, as needed, to the corresponding Back-End firmware running onBE\_SAN **712**, **732**, and **750** controllers to process the request. The memory buffers are dynamically allocated and managed upon a specific memory location (and corresponding LBA) is accessed. The copy-on-write method is used to automatically copy data from nFE\_SAN “mmapped” memory buffers **772** *a* to the mirroredbuffers **773** *a* (which may be dynamically allocated and released) and corresponding memory buffers **712** *a*, **732** *a*, and **750** *a* allocated on the BE\_SAN (or nBE\_SAN) controllers. It is presumed that the application(s) that were granted direct memory access to thenFS\_SAN **772** and **774** controllers' memory buffers assume complete control and responsibility for synchronizing and maintaining data coherency. Furthermore, provided API and ABI provide facility to allocate and allow direct access to the memory buffers onnFE\_SAN **772** and **774** (FE\_SAN) of the requested LBA(s) outside of a file system. As previously stated, user/application needs to assume complete control and responsibility for data management when using this feature.
- FIG. **8** illustrates a scenario where a heavy I/O workload frommultiple hosts **880** and **882** (via FE\_SAN/nFE\_SAN controllers **872** and **874**) saturatesBE\_SAN **812** controller. Distributed Resource Manager (DRM) **892** detects the overload condition and coordinates resource allocation information with other DRMs (**894** and **895**) to find an optimal solution that alleviates theBE\_SAN **812** overload condition and maximizes aggregate system performance.
-  In an exampleFIG. **9** further clarifies a scenario whereBE\_SAN **912** experiences excessive I/O workload while controllers BE\_SAN **932** andnBE\_SAN **950** are lightly utilized. The DRM algorithm finds that the optimal solution is to split the I/O traffic directed to the most frequently accessed LBAs onBE\_SAN **912** into three segments (LBAs-1, LBAs-2, and LBAs-3). Then LBAs-2 and LBAs-3 segments are cached onBE\_SAN **932** andnBE\_SAN **950** controllers respectively by creating corresponding LBAs-2′ and LBAs-3′ cache.DRM **992** instructs theFE\_SAN controllers **972** and **974** to transparently redirect the I/O traffic originally intended for the corresponding LBAs onBE\_SAN **912** controller to be sent (from now on) to BE\_SAN **912** if the LBA address range falls within LBAs-1 range, to send to BE\_SAN **932** if the accessed LBAs fall within LBAs-2 range, or to send tonBE\_SAN **950** if the targeted LBAs fall within LBAs-3 range. Although, bothBE\_SAN **932** andnBE\_SAN **950** may be used to improve the aggregate Back-End processing power and bandwidth during excessive I/O workload periods, the key difference betweenBE\_SAN **932** andnBE\_SAN **950** is thatnBE\_SAN **950** has additional hardware which provides additional performance acceleration (for additional information, please seeFIG. **3** *b* ). In this example, if all three nBE\_SAN/nBE\_SAN **912**, **932**, and **950** controllers have the same performance, assuming that initially theBE\_SAN **932** andnBE\_SAN **950** controllers were idle, by utilizing the described technique for the previously depicted scenario the peak aggregate performance for that specific workload could be increased as much as 300%. It is apparent that if sufficient hardware resources are provided, that significant performance gain may be attained during busy periods and the performance gain is limited only by the available hardware resources. Obviously, the long duration average I/O bandwidth (data rate) directed to theBE\_SAN controller **912** has to be lower than the controller bandwidth and attached back-end storage devices aggregate bandwidth.
-  In the previously described example, all the configuration changes to LBA caching occur transparently in respect to thehost computers **980** and **982**. In addition,BE\_SAN **912** controller viewsBE\_SAN **932** andnBE\_SAN **950** controllers as FE\_SAN (nFE\_SAN) controllers when receiving requests directed to LBAs-2 and LBAs-3 segments. Furthermore, as described in column 8 line 16 through column 9 line 12 of the U.S. Pat. No. 9,118,698, (PRIOR ART) the utilized locking algorithm is the same betweenBE\_SAN **932** and **912** (or BE\_SAN **950** and nBE\_SAN **912**) as, for instance, betweenFE\_SAN **972** andBE\_SAN **912**. Thus, with this new firmware features, (n)BE\_SAN **912**, **932**, and **950** controllers may play (n)BE\_SAN controller role when servicing (n)FE\_SAN **972** and **974** controllers' requests and to assume (n)FE\_SAN controller's role when caching LBAs (data) from another (n)BE\_SAN controller.
- FIG. **10** depicts a scenario in whichDRM **995** detected excessive utilization on thenBE\_SAN **950** controller and determines that the optimal solution is to split the I/O traffic directed to the most frequently accessed LBAs into two segments (LBAs-3.1′ and LBA-s3.2′). It may be appropriate to mention that LBA-3.1′ and LBA-s3.2′ do not have to be of the same size. Then LBAs-3.1′ and LBAs-3.2′ segments are cached on thenBE\_SAN **951** and **952** controllers respectively.DRM **995** instructs the (n)FE\_SAN **972** and **974** controllers to redirect the I/O traffic intended for LBAs onnBE\_SAN **950** controller transparently to the host, sending traffic tonBE\_SAN **951** if the LBA address range falls within LBAs-3.1′ range and to send tonBE\_SAN **952** if the accessed LBAs fall within LBAs-3.2′ range. As it can be seen inFIG. **10** the new dynamically created controller configuration takes shape of multi-level storage controller topology. Furthermore, the storage controller configuration and topology may be policy driven, which gives administrators additional tools and flexibility to further tune the system performance for specific workloads.
- FIG. **11** Once the overload condition onBE\_SAN controller **912** is alleviated, all the remaining cached data on thenBE\_SAN **952**, **951**, and **950** andBE\_SAN **932** controllers are orderly de-staged to theBE\_SAN controller **912** and the memory buffers LBAs-3.1″, LBAs-3.2″, LBAs-3.1′, LBAs-3.2′, LBAs-3′ and LBAs-2′ segments are released. Thus,nBE\_SAN **950**, **951**, **952**, and **953** are released and made available to be deployed if another hotspot (overload condition) is detected anywhere in the systems. Similarly, ifnBE\_SAN **950** controller detects moderate workload whileBE\_SAN **912** still experiences overload condition,DRM **995** may initiate data flush fromnBE\_SAN **951** and **952** controllers. Once all data is de-staged from LBAs-3.1″ and LBAs-3.2″ to thenBE\_SAN **950** controller, the segments LBAs-3.1″ and LBAs-3.2″ are released andnBE\_SAN **951**, and **952** are freed; thus, restoring the previous system configuration depicted inFIG. **9** .
-  The system allows to add/deploy as many (n)BE\_SAN controllers **950**, **951**, **952**, **953**, etc. as needed to satisfy quality of service during busy periods. Typically, the additional nBE\_SAN controllers may be the same or similar asnBE\_SAN **950**.nBE\_SAN **950** may make use of one or more SSDs, PCIe Flash Memory cards, or additional NVRAM or other persistent memory devices to mitigate cache-full condition during extended periods of heavy writing. In addition, it may cache frequently read (accessed) LBAs to boost read performance. Furthermore, in Network Attached Storage (NAS) systems or file systems using file servers, the same concept may be used to alleviate a file server overload condition; thus, this technique may be universally applied to broad range of applications.
- FIG. **12** illustrates how the apparatus disclosed in the embodiment of this application may be used as data cache or highperformance storage tier **1203** forcloud storage **1201**, archive, or remote storage and how (n)FE\_SAN **1272** and **1274** controllers may be integrated and utilized with private andpublic cloud **1200** deployments to improve application performance by accelerating data access speed. Furthermore, as depicted inFIGS. **2**, **3**, and **3** *a*, and as described above, integrating (n)FE\_SAN **1272** and **1274** controller with a NIC to support Converged I/O Interface may be recommended.
- FIG. **13** illustrates an example of how nFE\_SAN **300** (FIG. **3** ) controller speeds up writes when write-back-caching-with-mirroring is enabled. nFE\_SAN controller receiveswrite command **1300** from the host. Front-End firmware immediately sends write-lock request **1310** to the appropriate (n)BE\_SAN controller(s). In addition, it simultaneously requests **1320** write memory buffers (**302** and **352**) from **301** and **350** (FIG. **3** ) controllers. Then front-end firmware initiatesdata transfer **1322** from the host memory to the allocated memory buffers on the nFE\_SAN controller. In parallel, the firmware checks if the requested lock(s) from the nBE\_SAN controller has/have been granted **1330**. Once the data transfer is complete in **1322** and locks acquired from (n)BE\_SAN controller(s) (see **1331**), the firmware sends “COMMAND COMPLETE” the host OS in **1333**. Also, as soon as the lock(s) were granted anddata transfer **1342** to the (n)BE\_SAN controller is initiated. Once the transfer from nFE\_SAN controller to (n)BE\_SAN controller has been completed, in this example, thefirmware **1343** releases corresponding buffers on nFE\_SAN-S sub-controller. This completes this example **1344**. However, if instep **1330** the lock hasn't been granted, then in this simplified example **1341**, the firmware will retry to obtain lock(s) from the nBE\_SAN controller(s) until it either obtains lock(s) or times out; if the time-out occurs then the issues is passed to the upper system management layers. For all practical purposes, we assume that the system is operational and therefore it does grant requested locks every time.
- FIG. **14** illustrates an example of how (n)BE\_SAN handles excessive workload and how the controller DRM (DRM.a) alleviates controller overload condition. When firmware detects controller overload condition, it sends overload\_condition( ) notification to its DRM.a **1400**. Then, **1420** DRM.a checks workload statistics check\_stats( ) and in **1430** identifies which LBAs have been accessed most often. In **1431** DRM.a gets the controller utilization from other (n)BE\_SAN controllers. In **1432** DRM.a creates a list of the controllers and LBAs that will be cached on those controllers. In the next step, **1433**, DRM.a sends a request for resources to the first identified controller (DRM.b). In **1440** DRM.b receives request for resources from DRM.a (which is granted). In case that a resource is not granted for some reason instep **1440**, “N”, DRM.a identifies another controller and requests resources for the same LBAs, (step **1433**). DRM.b sends confirmation message which LBAs will be cached (**1441**) to DRM.a. In **1442** DRM.a checks if there are more segments that need to be cached and if “Y” starts the process again fromstep **1433**. However, in this simplified example, no more segments need to be cached on other controllers, the answer is “N” and the algorithm proceeds to step **1443**. In **1443** DRM.a sends new LUN layout information (map) to all (n)FE\_SAN controllers which can access that LUN. The new map that contains information about new (n)BE\_SAN controller topology.
-  In another example,FIG. **15** , it is shown how the system returns to its original configuration once the overload condition has ended. DRM.a gets a notification that overload condition has ended **1500**. DRM.a retrieves a list of all cached LBAs and corresponding controllers, **1520**. Then it gets workload statistics from each controller on the list for the LBAs that have been cached on that controller, **1532**. In **1533** it retrieves information which controller will be freed first/next. Then DRM.a sends DRM\_release\_resource( ) request in **1534** which implies that related cached LBAs should be synced first. Controller cache gets synhed; DRM\_cache\_synced( ) succeeds in **1540** and DRM\_release\_resource( ) request succeeds in **154**. Then DRM.b sends DRM\_release\_resource( ) notification in **1541** and starts “writing through” all incoming write requests. Then instep **1542** it checks if there are more cached LBA segments that should be restored. If the answer is yes, then the process starts again fromstep **1533**. If instep **1540** DRM on the alternate controller fails to release the allocated resources then the DRM simply proceeds with freeing up resources on the other controllers and retries to release resources after went through the entire list. If for some reason, DRM\_cache\_released\_LBAs( ) did not succeed then DRM.a proceeds with freeing up all other resources until all the resources are free and original configuration restored or the process times out and upper management layers take over the process. However, for this exercise, the system is fully operational and all the resources eventually will be freed. Thus, when all LBAs are released, DRM.a sends a DRM\_new-map\_LBAs( ) message to all (n)FE\_SAN controllers that have access to the previously cached LBAs. During normal operation, each of these requests should succeed almost immediately on the first request. Only in case that a controller is temporarily overloaded, it may be possible to observe a delayed completion of a request. The goal for the examples presented here is to give an insight into the basic system operation without going into great level of detail covering more complex scenarios. Furthermore, these examples do not cover error handling, error recovery and failure (degraded) modes of operation.
-  The original FE\_SAN designFIG. **2** has one CPU, memory, etc. With reference toFIGS. **3** & **3** *a*, the new design consists of aFE\_SAN **301** controller and nFE\_SAN-S **350** sub-controller card or chip.
-  The nFE\_SAN-S **350** sub-controller is operationally, functionally, and electrically independent of theFE\_SAN **301** controller.
-  To keep the cost down, the performance CPU and memory capacity requirements of the nFE\_SAN-S **350** controller may be significantly lower comparedFE\_SAN **301** controller, while the memory bandwidth requirement cannot be lower than the host side bus (channel) bandwidth. Bothcontrollers **301** & **350** are physically built into a single PCI, PCIe, or other standard card format.
-  Traditionally, write-back-cache-with-mirroring feature requires to maintain at least two copies of the write data until the data is written to the back-end HDDs, SSDs, or other permanent storage media. In that respect, this implementation does not have single point of failure while the data coherency is maintained via locking mechanism which maintains the information where each piece of data may be found and retrieved from.
-  With the original design,FIG. **1** , the write data has to be mirrored front-to-back (FE\_SAN->BE\_SAN controller) by sending the data over the network before “COMMAND COMPLETE” message could be returned to the host. However, with the new design the write data is simultaneously written to bothMEM **302** and **352** on thecontroller nFE\_SAN **300** and then as soon as the lock(s) are granted by (n)BE\_SAN controller(s) the “COMMAND COMPLETE” message is immediately returned to the host without the need to first “mirror” the data to the nBE\_SAN controller(s); apparently this method is significantly faster and it is comparably reliable as the original method. The SCSI standard does not guarantee the order in which SCSI commands are executed. Therefore, if we relax the ordering requirement, “COMMAND COMPLETE” message may be immediately returned to the host without waiting for lock(s) to be granted by nBE\_SAN controller(s). However, if the order of execution has to be guaranteed, every request has to be associated with an appropriate lock.
- FIG. **3** *a* depicts new FE\_SAN controller with additional NVMe/SSD or other permanent storage media (nFE\_SAN **300** *a*)=(nFE\_SAN **300**FIG. **3** )+(SSD **304**). NVMe/SSD **304** withnFE\_SAN **300** createsnFE\_SAN **300** *a* controller; **304** could be a high-speed NVMe based flash memory or NVRAM device/chip. This enables **300** *a* controller to keep more write and read data locally; the flash memory may have TBs of capacity as the price of SSD and NVMe technology continue to decline. An additional feature allows for keeping of some specific blocks locally in the nonvolatile or flash memory. For instance we could keep entire boot image locally for fast boots, without the need to go to the BE\_SAN controllers to retrieve the boot image; the remainder of local NVRAM is available as additional cache. However, broadcasting/multicasting boot image from nBE\_SAN to (n)FE\_SAN controllers my result in significantly faster boot process because the boot image would be retrieved from the nFE\_SAN controller cache which uses the fastest memory technology available.
-  As depicted onFIG. **3** *b* theimproved nBE\_SAN controller **370** consists ofBE\_SAN **371** withadditional SSD **374** andnFE\_SAN **300** or FE\_SAN **301**:
-  The additional features of thenBE\_SAN controller **370** enable the Data Access System to dynamically change its topology to adapt to the changing workload requirements. Thus, a (n)BE\_SAN controller can be automatically and dynamically inserted in front of another (n)BE\_SAN controller to boost its I/O processing capability by caching certain LBAs from the (n)BE\_SAN controller. Thus, it behaves asBE\_SAN **371** controller when receiving commands from (n)FE\_SAN controller(s) and asnFE\_SAN **300** when forwarding the data to a BE\_SAN controller. nBE\_SAN controllers also have new firmware with Distributed Resource Manager (DRM) and virtualization capability to run guest OS and user applications on the nBE\_SAN controller.
-  Each (n)BE\_SAN controller may incorporate a multi-core CPU server motherboard with sufficient memory and additional components such as battery backup, NVRAM and NVMe SSDs, etc. Thus, each (n)BE\_SAN controller is capable of running VMware or any other virtualization software to allow user application to run on the (n)BE\_SAN controllers. Therefore, (n)BE\_SAN controller provides capability to locally run applications or execute user code close to the dataset that it needs to process.
- FIG. **1** (PRIOR ART)—As disclosed in the original patent, it is possible to install and configure two or more FE\_SAN controllers in a server to create a controller group aggregating the I/O performance and capacity of all installed FE\_SAN controllers. Then, the controller group is presented by the device driver to the host OS as a virtual FE\_SAN controller with significantly higher performance compared to a single FE\_SAN controller.
- FIG. **6** —with thenew firmware **620**, (n)FE\_SAN controller can virtualize its resources using hypervisor or other virtualization method to create multiple virtual (n)FE\_SAN controllers **610** and present different VIRTUAL controllers with different features and properties todifferent OSs **680**,guest OSs **682**, andapplications **627**. In addition, as depicted onFIG. **6** , thenew firmware **620** features, provide facility to virtualize (n)FE\_SAN controller group **611** and present virtual (n)FE\_SAN controllers to different OSs and guest OSs.
- FIG. **7** —As described in \[**0008**\] the data is written simultaneously to bothmemory buffers **772** *a* and **773** *a* on thenFE\_SAN **772** controller and based on the mode pages, the firmware may immediately return “COMMAND COMPLETE” to the host without the need to, first, write data to the BE\_SAN controller(s). Then the data is de-staged (flushed) to the BE\_SAN controllers at the first opportunity and the buffers with one copy of the data (either **772** *a* or **773** *a*) are released while the second copy of the data is retained maintaining front to back mirroring. Thus, there is one copy of the data on thenFE\_SAN **772** controller and second copy of the data on (n)BE\_SAN controller(s) (on one or more of **712**, **732**, or **750** controllers). Once the data is mirrored between nFE\_SAN and (n)BE\_SAN controller(s), the system is at the same state as described in the original patent when write data is mirrored between FE\_SAN and BE\_SAN controller(s). Thus, the process of writing the data to the back-end storage devices (drives) is identical to the process described in the original patent. It is apparent that by maintaining two copies of the data at any point in time, thenew nFE\_SAN **772** hardware and data handing method provides write speed up while maintaining data integrity and reliability at the same level as any other modern SAN or RAID systems that utilize write-back caching with mirroring.
- FIG. **8** —in this example, applications running oncomputers **880** and **882** produce intensive I/O workload, writing the data to the same LBAs onBE\_SAN controller **812**, driving the controller into saturation due to excessive workload. Distributed Resource Manager (DRM) **892** receives notification of theBE\_SAN **812** controller extended overload condition. DRM then looks at the distribution of the writes, which LBAs are accessed most often. After reviewing the statistics and finding optimal solution,DRM **892** decides to split this with heavily used LBAs segment onBE\_SAN **812** into three smaller segments LBAs-1, LBAs-2, and LBAs-3 (please seeFIG. **9** ). ThenDRM **892** further coordinates withDRMs **894** and **895** on other BE\_SAN, it may find thatBE\_SANs **832** and **850** have low utilization or that they are idle.
- FIG. **9** —Thus, if an under-utilized (n)BE\_SAN controller is found (sayDRM **994** and **995**),DRM **992** instructsDRM **994** to create LBAs-2′ andDRM **995** to create LBAs-3′ cache. Thus, LBAs-2′ acts as cache and points to LBAs-2, the same applies for LBAs-3′ and LBAs-3 that are utilized to offload the heavily utilized (n)BE\_SAN controller. ThenDRM **992** instructs (n)FE\_SAN controller(s)DRM **999** and **998** to stop sending data to LBAs-2 and LBAs-3 on theoriginal BE\_SAN **912** and instead start sending the newly written data to the offloaded LBAs-2′ and LBAs-3′ on the controllers (n)BE\_SAN **932** and **950** controllers.BE\_SAN **932** has new firmware that allows LBAs-2 caching in the LBAs-2′ buffers. Thus, the write data from nFE\_SAN controllers, after data aggregation and coalescing is forwarded to the LBAs-2 on theBE\_SAN **912** controller. This is firmware only implementation, however,nBE\_SAN **950** has firmware and nFE\_SAN hardware (such asnFE\_SAN **972** controller card or silicon) integrated withinnBE\_SAN **950** controller that speeds up writes to theBE\_SAN **912** controller. This technology enables more scalable and less expensive controllers because the controllers do not have to be over-engineered to deliver expected peak performance. Less powerful CPUs would work perfectly fine as long as there is sufficient front-end and back-end I/O bandwidth. Thus,FIG. **9** —depicts the new (n)BE\_SAN controller topology with two levels of (n)BE\_SAN controllers. Therefore, the (n)BE\_SAN controller topology may change dynamically so the storage system can adapt to workload requirements in real-time.
- FIG. **10** —illustrates (n)BE\_SAN controller topology with THREE levels of (n)BE\_SAN controllers. Therefore, (n)BE\_SAN controllers can dynamically and in real-time adapt to any type of workload up to the point when all (n)BE\_SAN controllers are configured to handle storage I/O workload.
-  As shown onFIG. **11** —the storage system maintains optimal level of service and resource utilization by dynamically in real-time responding to the workload requirements by deploying additional hardware resources when and where they are needed and freeing up unutilized resources when they are not needed. Apparently, hardware resources, (n)BE\_SAN controllers, consume less power when they are idle compared to when they are heavily used. Thus, the additional benefits of this technology is saving power during periods when the system is not heavily used, while boosting performance when the system is heavily used. In addition, unlike with the legacy storage systems designs where a system needs to be architected to meet the peak performance in advance, the (n)BE\_SAN controllers may be incrementally added to boost storage system peak performance if and when needed enabling storage performance to scale independently from storage capacity. In this example,DRM **992** onnBE\_SAN **912** controller receives notification that the heavy workload sent to theBE\_SAN **912** LBAs has subsided and RDMs coordinate the process of de-staging cached data to theBE\_SAN **912** attached back-end storage media and restore the initial controller configuration (topology) freeing upnBE\_SAN controllers **951**, **952**, **950**, and **932**.
-  In alternative embodiments, instead of automatically offloading or splitting individual LBAs, heavily accessed data or files may be relocated from storage on one BE\_SAN to a less-heavily loaded BE\_SAN that holds part of the same logical drive. As disclosed in the original U.S. Pat. Nos. 8,347,010, 8,725,906, 9,118,698, and 9,361,038 entitled “Scalable data storage architecture and methods of eliminating I/O traffic bottlenecks,” the contents of which are incorporated herein by reference for disclosure purposes, logical and physical drive (volume) location may be dissociated.
- FIG. **12** —illustrates how herein described embodiment supports and accelerates data access in private and public cloud environments by having (n)FE\_SAN controllers installed incloud servers **1280** and **1282**. In addition, it is possible to configure multiple (n)BE\_SAN controllers (in thissimplified example BE\_SAN **1212** and **1232** controllers) to act as block storage high-speed tier (cache) for local and remote cloud storage, online and near-line data archive, and remote replication Disaster Recover (DR) site.
- FIG. **16** (PRIOR ART) depicts a dataflow diagram of write operations showing the execution sequence and interaction between application, host SCSI driver, FE\_SAN and BE\_SAN controllers for a system disclosed in the U.S. Pat. No. 9,118,698 (**571770**). Write data has to be mirrored between FE\_SAN and BE\_SAN controller(s) before “COMMAND COMPLETE” message can be sent to the host.
- FIG. **17** illustrates timing of a write sequence as executed on a system according to the herein described embodiments, as partially illustrated inFIG. **18** . A CPU of CPUs **1802** executing anapplication **1804** and adriver **1805** associated with an operating system determines a write command to storage is required. Thewrite command **1702** is modified bydriver **1805** and passed as anextended write command **1704** with buffer info through bus interface **1809** toFE\_SAN **1808**.
- FE\_SAN **1808** has a first, primary,power system **1810**, afirst cache memory **1812**, and afirst network interface **1814**.FE\_SAN **1808** also has asecondary power system **1816**, asecondary cache **1818**, and in some embodiments asecond network interface **1820**. FE\_SAN operates under control ofFE\_SAN firmware **1822** executing on aprimary processor **1824** and FE\_SAN-S firmware **1823** executing on asecondary processor **1826**, primary processor powered bypower system **1810** andsecondary processor **1826** powered bysecond power system **1816**.Primary network interface **1814** couples through a first storagearea network interconnect **1830** to aprimary network interface **1832** of aBE\_SAN **1834**, andsecond network interface **1820** couples through a second storagearea network interface **1828** to asecondary network interface **1836** ofBE\_SAN **1834**.BE\_SAN **1834** has aprimary cache **1838** powered by aprimary power supply **1840**, and asecond cache **1842** powered by a second power supply **1844**.BE\_SAN **1834** has aprimary processor **1846** and asecondary processor **1848** operating under control ofBE\_SAN firmware **1850** and **1851** respectively.BE\_SAN **1834** also has two or moredisk drive interfaces **1852**, **1854**, each coupled to one or more storage drives **1856**, **1858**, **1860**, **1862**, **1864**, **1866**.BE\_SAN firmware **1850** is configured to operate one or more virtual drives on storage drives **1856**-**1866** using a Redundant Array of Independent Drives (RAID) protocol permitting reconstruction of data on the virtual drives should a failure occur of any one of storage drives **1856**, **1858**, **1860**, **1862**, **1864**, **1866**. Also, Erasure Coding (EC) or other method of data protection may be implemented on the system depicted inFIG. **18** .
- Second cache **1818**,secondary power system **1816**,second network interface **1820**, andsecondary processor **1826** together form an FE\_SAN\_S as herein described.
-  Oncewrite command **1704** is passed toFE\_SAN **1808**, FE\_SAN **1808** passes awrite lock request **1706** toBE\_SAN **1834**.FE\_SAN **1808** also begins processing the write request by instructing **1708**driver **1805**, including allocating **1709** and setting up any memory mapped buffers, to begin transferring **1710** data into both the primary andsecondary cache **1812** and **1818** using “put (data)” operations. In embodiments where data is written directly toprimary cache **1812**, that data is copied (CoW) **1711** tosecondary cache **1818**.
-  Once theBE\_SAN **1834** has locked the destination blocks of the RAID virtual drives maintained on storage devices **1856**-**1866** to prevent intervening writes from other FE\_SANs (not shown), and has allocated buffer space in both its primary andsecondary caches **1840**, **1838**,BE\_SAN **1834** responds toFE\_SAN **1808** with a lock-request-grantedsignal **1712**.
-  Once lock-request-grantedsignal **1712** is received byFE\_SAN **1808** andcopies **1711** to secondary cache are complete,FE\_SAN **1808** provides a write complete “ack”signal **1714** todriver **1805**, which passes a commandcomplete signal **1716** to the executingapplication **1804**. Once lock request grantedsignal **1712** is received byFE\_SAN **1808**,FE\_SAN **1808** begins transferring **1718** the data toBE\_SAN **1834** where this data is mirrored incache memories **1834**, **1840**.
-  Write data at this point may reside in duplicate inFE\_SAN caches **1812**, **1818**; whiledata transfers **1718** continue. When all data is transferred to the BE\_SAN, the BE\_SAN sends afinal acknowledgement signal **1720** to the FE\_SAN, which may then release one or both copies inFE\_SAN cache **1812**, **1818**.
-  In the event transfer is interrupted by failure of the FE\_SANprimary cache **1812**,primary power supply **1810**,primary network interface **1814**, orprimary processor **1824**, after write complete **1714** has been sent todriver **1805**, but before all data has been transferred to the BE\_SAN, thesecondary processor **1826** continues to transfer data from thesecondary cache **1818** to the BE\_SAN to ensure completion of the write operation. In the event BE\_SANprimary processor **1846**,primary cache **1838**, orprimary power **1840** fail, BE\_SANsecondary processor **1848** completes receiving the data over BE\_SANsecondary network **1836** intosecondary cache **1840** and completes writing data to storage devices **1856**-**1866**. In an alternative embodiment, instead of completing the write, the data is retained in battery-backupsecondary cache **1840** and alarms sounded; data writing is completed upon repair of the BE\_SAN.
-  As can be seen from the diagram, data transfer between host and nFE\_SAN controller is decoupled from the data transfer between nFE\_SAN and (n)BE\_SAN controller(s). Furthermore, to complete host write I/O transaction it is not necessary to copy the data between (n)FE\_SAN and (n)BE\_SAN controllers because two independent copies of the data are maintained on the nFE\_SAN controller. Therefore, it is sufficient to obtain only write lock(s) from (n)BE\_SAN controller(s) and complete data transfer from the host before a “COMMAND COMPLETE” message can be sent back to the host. Once the data is mirrored between nFE\_SAN and (n)BE\_SAN controller(s) the memory buffers containing the second copy of the data are released. Apparently, this technique facilitates additional performance improvements for small I/O writes because data transfer between nFE\_SAN and (n)BE\_SAN controllers can be done asynchronously.
-  The foregoing description should not be taken as limiting. It should thus be noted that the matter contained in the above description or shown in the accompanying drawings should be interpreted as illustrative and not in a limiting sense. The following claims are intended to cover generic and specific features described herein, as well as all statements of the scope of the present method and system.

## Claims (11)

**1**. A method of writing write data to at least one storage device in a multiple computer system comprising:

**2**. The method of

**3**. The method of

**4**. The method of

**5**. The method of

**6**. A system comprising:

**7**. The system of

**8**. The system of

**9**. The system of

**10**. The system of

**11**. The system of

[US20250130714A1 (en)](/patent/US20250130714A1/en)

## Priority Applications (1)

| Application Number | Priority Date | Filing Date | Title | 
|---|---|---|---|
| US19/005,557                [US20250130714A1                 (en)](/patent/US20250130714A1/en)              | 2016-04-08 | 2024-12-30 | Scalable data access system and methods of eliminating controller bottlenecks | 

## Applications Claiming Priority (6)

| Application Number | Priority Date | Filing Date | Title | 
|---|---|---|---|
| US201662320349P | 2016-04-08 | 2016-04-08 |  | 
| US15/482,726                [US10331353B2                 (en)](/patent/US10331353B2/en)              | 2016-04-08 | 2017-04-08 | Scalable data access system and methods of eliminating controller bottlenecks | 
| US16/449,874                [US10949093B2                 (en)](/patent/US10949093B2/en)              | 2016-04-08 | 2019-06-24 | Scalable data access system and methods of eliminating controller bottlenecks | 
| US17/201,115                [US11747981B2                 (en)](/patent/US11747981B2/en)              | 2016-04-08 | 2021-03-15 | Scalable data access system and methods of eliminating controller bottlenecks | 
| US18/226,513                [US12182405B2                 (en)](/patent/US12182405B2/en)              | 2016-04-08 | 2023-07-26 | Scalable data access system and methods of eliminating controller bottlenecks | 
| US19/005,557                [US20250130714A1                 (en)](/patent/US20250130714A1/en)              | 2016-04-08 | 2024-12-30 | Scalable data access system and methods of eliminating controller bottlenecks | 

## Related Parent Applications (1)

| Application Number | Title | Priority Date | Filing Date | 
|---|---|---|---|
| US18/226,513             Continuation                [US12182405B2               (en)](/patent/US12182405B2/en)              | 2016-04-08 | 2023-07-26 | Scalable data access system and methods of eliminating controller bottlenecks | 

## Publications (1)

| Publication Number | Publication Date | 
|---|---|
| US20250130714A1                          true                [US20250130714A1               (en)](/patent/US20250130714A1/en)              | 2025-04-24 | 

# Family

## ID=59999407

## Family Applications (5)

| Application Number | Title | Priority Date | Filing Date | 
|---|---|---|---|
| US15/482,726             Active             2037-05-05                [US10331353B2                 (en)](/patent/US10331353B2/en)              | 2016-04-08 | 2017-04-08 | Scalable data access system and methods of eliminating controller bottlenecks | 
| US16/449,874             Active                [US10949093B2                 (en)](/patent/US10949093B2/en)              | 2016-04-08 | 2019-06-24 | Scalable data access system and methods of eliminating controller bottlenecks | 
| US17/201,115             Active             2037-08-29                [US11747981B2                 (en)](/patent/US11747981B2/en)              | 2016-04-08 | 2021-03-15 | Scalable data access system and methods of eliminating controller bottlenecks | 
| US18/226,513             Active                [US12182405B2                 (en)](/patent/US12182405B2/en)              | 2016-04-08 | 2023-07-26 | Scalable data access system and methods of eliminating controller bottlenecks | 
| US19/005,557             Pending                [US20250130714A1                 (en)](/patent/US20250130714A1/en)              | 2016-04-08 | 2024-12-30 | Scalable data access system and methods of eliminating controller bottlenecks | 

## Family Applications Before (4)

| Application Number | Title | Priority Date | Filing Date | 
|---|---|---|---|
| US15/482,726             Active             2037-05-05                  [US10331353B2                 (en)](/patent/US10331353B2/en)                | 2016-04-08 | 2017-04-08 | Scalable data access system and methods of eliminating controller bottlenecks | 
| US16/449,874             Active                  [US10949093B2                 (en)](/patent/US10949093B2/en)                | 2016-04-08 | 2019-06-24 | Scalable data access system and methods of eliminating controller bottlenecks | 
| US17/201,115             Active             2037-08-29                  [US11747981B2                 (en)](/patent/US11747981B2/en)                | 2016-04-08 | 2021-03-15 | Scalable data access system and methods of eliminating controller bottlenecks | 
| US18/226,513             Active                  [US12182405B2                 (en)](/patent/US12182405B2/en)                | 2016-04-08 | 2023-07-26 | Scalable data access system and methods of eliminating controller bottlenecks | 

## Country Status (1)

| Country | Link | 
|---|---|
| US (5) |                [US10331353B2               (en)](/patent/US10331353B2/en)              | 

## Families Citing this family (16)

| \* Cited by examiner, † Cited by third party |  |  |  |  | 
|---|---|---|---|---|
| Publication number | Priority date | Publication date | Assignee | Title | 
|---|---|---|---|---|
|                [US10331353B2               (en)](/patent/US10331353B2/en)              | 2016-04-08 | 2019-06-25 | Branislav Radovanovic | Scalable data access system and methods of eliminating controller bottlenecks | 
|                [US10241956B2               (en)](/patent/US10241956B2/en)              | 2016-09-12 | 2019-03-26 | International Business Machines Corporation | Virtualizing coherent hardware accelerators | 
|                [US10524022B2               (en)](/patent/US10524022B2/en)             \* | 2017-05-02 | 2019-12-31 | Seagate Technology Llc | Data storage system with adaptive data path routing | 
|                [CN107800576A               (en)](/patent/CN107800576A/en)             \* | 2017-11-16 | 2018-03-13 | 郑州云海信息技术有限公司 | A kind of system integrating management method and system based on multi-controller framework | 
|                [US10481834B2               (en)](/patent/US10481834B2/en)              | 2018-01-24 | 2019-11-19 | Samsung Electronics Co., Ltd. | Erasure code data protection across multiple NVME over fabrics storage devices | 
|                [US20190265902A1               (en)](/patent/US20190265902A1/en)             \* | 2018-02-28 | 2019-08-29 | International Business Machines Corporation | Live migration of applications using capi flash | 
|                [US10649674B2               (en)](/patent/US10649674B2/en)              | 2018-05-03 | 2020-05-12 | Western Digital Technologies, Inc. | Extended controller pre-initialization using boot partitions in solid state systems | 
|                [US11163460B2               (en)](/patent/US11163460B2/en)             \* | 2018-06-07 | 2021-11-02 | Karim Jean Yaghmour | Dynamically-reconfigurable storage device | 
|                [US10599334B2               (en)](/patent/US10599334B2/en)              | 2018-06-12 | 2020-03-24 | International Business Machines Corporation | Use of capi-attached storage as extended memory | 
|                [TWI778363B               (en)](/patent/TWI778363B/en)             \* | 2020-05-29 | 2022-09-21 | 慧榮科技股份有限公司 | Data storage device with multi-stage controller | 
|                [US11507507B2               (en)](/patent/US11507507B2/en)             \* | 2020-07-24 | 2022-11-22 | Dell Products L.P. | System and method of backing up data from a volatile memory medium to a non-volatile memory medium | 
|                [US11561727B2               (en)](/patent/US11561727B2/en)             \* | 2020-07-27 | 2023-01-24 | EMC IP Holding Company LLC | Hardware virtualization | 
|                [US11811867B2               (en)](/patent/US11811867B2/en)              | 2020-09-01 | 2023-11-07 | International Business Machines Corporation | Data transmission routing based on replication path capability | 
|                [CN115309694A               (en)](/patent/CN115309694A/en)              | 2021-05-07 | 2022-11-08 | 脸萌有限公司 | On-chip integrated circuit, data processing apparatus and method | 
|                [US12406056B2               (en)](/patent/US12406056B2/en)             \* | 2023-02-06 | 2025-09-02 | Dell Products L.P. | Providing quality of service for secure workspaces having copy-on-write layers | 
|                [US12572422B2               (en)](/patent/US12572422B2/en)             \* | 2024-04-11 | 2026-03-10 | Dell Products L.P. | Delayed log write of input/outputs using persistent memory | 

## Citations (5)

| \* Cited by examiner, † Cited by third party |  |  |  |  | 
|---|---|---|---|---|
| Publication number | Priority date | Publication date | Assignee | Title | 
|---|---|---|---|---|
|                [US7127633B1               (en)](/patent/US7127633B1/en)             \* | 2001-11-15 | 2006-10-24 | Xiotech Corporation | System and method to failover storage area network targets from one interface to another | 
|                [US20130145064A1               (en)](/patent/US20130145064A1/en)             \* | 2005-12-02 | 2013-06-06 | Branislav Radovanovic | Scalable Data Storage Architecture And Methods Of Eliminating I/O Traffic Bottlenecks | 
|                [US20160085460A1               (en)](/patent/US20160085460A1/en)             \* | 2014-09-22 | 2016-03-24 | Netapp, Inc. | Optimized read access to shared data via monitoring of mirroring operations | 
|                [US20160203080A1               (en)](/patent/US20160203080A1/en)             \* | 2015-01-12 | 2016-07-14 | Avago Technologies General Ip (Singapore) Pte. Ltd | Multi-node cache coherency with input output virtualization | 
|                [US20170220249A1               (en)](/patent/US20170220249A1/en)             \* | 2016-01-29 | 2017-08-03 | Netapp, Inc. | Systems and Methods to Maintain Consistent High Availability and Performance in Storage Area Networks | 

## Family Cites Families (19)

| \* Cited by examiner, † Cited by third party |  |  |  |  | 
|---|---|---|---|---|
| Publication number | Priority date | Publication date | Assignee | Title | 
|---|---|---|---|---|
|                [US6029168A               (en)](/patent/US6029168A/en)              | 1998-01-23 | 2000-02-22 | Tricord Systems, Inc. | Decentralized file mapping in a striped network file system in a distributed computing environment | 
|                [US6148414A               (en)](/patent/US6148414A/en)              | 1998-09-24 | 2000-11-14 | Seek Systems, Inc. | Methods and systems for implementing shared disk array management functions | 
|                [US6427212B1               (en)](/patent/US6427212B1/en)              | 1998-11-13 | 2002-07-30 | Tricord Systems, Inc. | Data fault tolerance software apparatus and method | 
|                [US6530036B1               (en)](/patent/US6530036B1/en)              | 1999-08-17 | 2003-03-04 | Tricord Systems, Inc. | Self-healing computer system storage | 
|                [US6877044B2               (en)](/patent/US6877044B2/en)              | 2000-02-10 | 2005-04-05 | Vicom Systems, Inc. | Distributed storage management platform architecture | 
|                [US20020103889A1               (en)](/patent/US20020103889A1/en)              | 2000-02-11 | 2002-08-01 | Thomas Markson | Virtual storage layer approach for dynamically associating computer storage with processing hosts | 
|                [US6820171B1               (en)](/patent/US6820171B1/en)              | 2000-06-30 | 2004-11-16 | Lsi Logic Corporation | Methods and structures for an extensible RAID storage architecture | 
|                [US8281022B1               (en)](/patent/US8281022B1/en)              | 2000-06-30 | 2012-10-02 | Emc Corporation | Method and apparatus for implementing high-performance, scaleable data processing and storage systems | 
|                [US7216258B2               (en)](/patent/US7216258B2/en)              | 2002-05-17 | 2007-05-08 | Xiotech Corporation | Method and apparatus for recovering from a non-fatal fault during background operations | 
|                [EP1561159A4               (en)](/patent/EP1561159A4/en)              | 2002-11-12 | 2007-08-29 | Zetera Corp | Electrical devices with improved communication | 
|                [CA2435148A1               (en)](/patent/CA2435148A1/en)              | 2003-07-15 | 2005-01-15 | Robert J. Blainey | System and method for lock caching for compound atomic operations on shared memory | 
|                [US20050289152A1               (en)](/patent/US20050289152A1/en)              | 2004-06-10 | 2005-12-29 | Earl William J | Method and apparatus for implementing a file system | 
|                [US7484021B2               (en)](/patent/US7484021B2/en)             \* | 2005-10-27 | 2009-01-27 | Cisco Technology, Inc. | Technique for implementing virtual fabric membership assignments for devices in a storage area network | 
|                [US8938574B2               (en)](/patent/US8938574B2/en)             \* | 2010-10-26 | 2015-01-20 | Lsi Corporation | Methods and systems using solid-state drives as storage controller cache memory | 
|                [US8965937B2               (en)](/patent/US8965937B2/en)             \* | 2011-09-28 | 2015-02-24 | International Business Machines Corporation | Automated selection of functions to reduce storage capacity based on performance requirements | 
|                [US20130246705A1               (en)](/patent/US20130246705A1/en)             \* | 2012-03-15 | 2013-09-19 | Aboubacar Diare | Balancing logical units in storage systems | 
|                [US8930311B1               (en)](/patent/US8930311B1/en)             \* | 2012-12-14 | 2015-01-06 | Netapp, Inc. | Push-based piggyback system for source-driven logical replication in a storage environment | 
|                [US10037245B2               (en)](/patent/US10037245B2/en)             \* | 2016-03-29 | 2018-07-31 | International Business Machines Corporation | Raid system performance enhancement using compressed data and byte addressable storage devices | 
|                [US10331353B2               (en)](/patent/US10331353B2/en)             \* | 2016-04-08 | 2019-06-25 | Branislav Radovanovic | Scalable data access system and methods of eliminating controller bottlenecks | 

- 
        2017
        
  - 
            2017-04-08
            US
            US15/482,726
            [patent/US10331353B2/en](/patent/US10331353B2/en) active
            Active
- 
        2019
        
  - 
            2019-06-24
            US
            US16/449,874
            [patent/US10949093B2/en](/patent/US10949093B2/en) active
            Active
- 
        2021
        
  - 
            2021-03-15
            US
            US17/201,115
            [patent/US11747981B2/en](/patent/US11747981B2/en) active
            Active
- 
        2023
        
  - 
            2023-07-26
            US
            US18/226,513
            [patent/US12182405B2/en](/patent/US12182405B2/en) active
            Active
- 
        2024
        
  - 
            2024-12-30
            US
            US19/005,557
            [patent/US20250130714A1/en](/patent/US20250130714A1/en) active
            Pending

## Patent Citations (5)

| \* Cited by examiner, † Cited by third party |  |  |  |  | 
|---|---|---|---|---|
| Publication number | Priority date | Publication date | Assignee | Title | 
|---|---|---|---|---|
|                [US7127633B1               (en)](/patent/US7127633B1/en)             \* | 2001-11-15 | 2006-10-24 | Xiotech Corporation | System and method to failover storage area network targets from one interface to another | 
|                [US20130145064A1               (en)](/patent/US20130145064A1/en)             \* | 2005-12-02 | 2013-06-06 | Branislav Radovanovic | Scalable Data Storage Architecture And Methods Of Eliminating I/O Traffic Bottlenecks | 
|                [US20160085460A1               (en)](/patent/US20160085460A1/en)             \* | 2014-09-22 | 2016-03-24 | Netapp, Inc. | Optimized read access to shared data via monitoring of mirroring operations | 
|                [US20160203080A1               (en)](/patent/US20160203080A1/en)             \* | 2015-01-12 | 2016-07-14 | Avago Technologies General Ip (Singapore) Pte. Ltd | Multi-node cache coherency with input output virtualization | 
|                [US20170220249A1               (en)](/patent/US20170220249A1/en)             \* | 2016-01-29 | 2017-08-03 | Netapp, Inc. | Systems and Methods to Maintain Consistent High Availability and Performance in Storage Area Networks | 

## Also Published As

| Publication number | Publication date | 
|---|---|
|                [US20170293428A1               (en)](/patent/US20170293428A1/en)              | 2017-10-12 | 
|                [US12182405B2               (en)](/patent/US12182405B2/en)              | 2024-12-31 | 
|                [US10949093B2               (en)](/patent/US10949093B2/en)              | 2021-03-16 | 
|                [US10331353B2               (en)](/patent/US10331353B2/en)              | 2019-06-25 | 
|                [US20190310773A1               (en)](/patent/US20190310773A1/en)              | 2019-10-10 | 
|                [US20210199493A1               (en)](/patent/US20210199493A1/en)              | 2021-07-01 | 
|                [US11747981B2               (en)](/patent/US11747981B2/en)              | 2023-09-05 | 
|                [US20240020007A1               (en)](/patent/US20240020007A1/en)              | 2024-01-18 | 

## Similar Documents

| Publication | Publication Date | Title | 
|---|---|---|
|                  [US12182405B2                 (en)](/patent/US12182405B2/en)                |  | Scalable data access system and methods of eliminating controller bottlenecks | 
|                  [US9361038B1                 (en)](/patent/US9361038B1/en)                |  | Scalable data storage architecture and methods of eliminating I/O traffic bottlenecks | 
|                  [US8725906B2                 (en)](/patent/US8725906B2/en)                |  | Scalable data storage architecture and methods of eliminating I/O traffic bottlenecks | 
|                  [US9069587B2                 (en)](/patent/US9069587B2/en)                |  | System and method to cache hypervisor data | 
|                  [US10466912B2                 (en)](/patent/US10466912B2/en)                |  | Operation method of distributed memory disk cluster storage system | 
|                  [US7778960B1                 (en)](/patent/US7778960B1/en)                |  | Background movement of data between nodes in a storage cluster | 
|                  [US10318393B2                 (en)](/patent/US10318393B2/en)                |  | Hyperconverged infrastructure supporting storage and compute capabilities | 
|                  [US8521685B1                 (en)](/patent/US8521685B1/en)                |  | Background movement of data between nodes in a storage cluster | 
|                  [US9811276B1                 (en)](/patent/US9811276B1/en)                |  | Archiving memory in memory centric architecture | 
|                  [US10409508B2                 (en)](/patent/US10409508B2/en)                |  | Updating of pinned storage in flash based on changes to flash-to-disk capacity ratio | 
|                  [US8782335B2                 (en)](/patent/US8782335B2/en)                |  | Latency reduction associated with a response to a request in a storage system | 
|                  [US8433888B2                 (en)](/patent/US8433888B2/en)                |  | Network boot system | 
|                  [US9262097B2                 (en)](/patent/US9262097B2/en)                |  | System and method for non-volatile random access memory emulation | 
|                  [US9823955B2                 (en)](/patent/US9823955B2/en)                |  | Storage system which is capable of processing file access requests and block access requests, and which can manage failures in A and storage system failure management method having a cluster configuration | 
|                  [US10459652B2                 (en)](/patent/US10459652B2/en)                |  | Evacuating blades in a storage array that includes a plurality of blades | 
|                  [WO2014051639A1                 (en)](/patent/WO2014051639A1/en)                |  | Storage architecture for server flash and storage array operation | 
|                  [US12099443B1                 (en)](/patent/US12099443B1/en)                |  | Multi-modal write cache for data storage system | 
|                  [US20250156322A1                 (en)](/patent/US20250156322A1/en)                |  | Single-phase commit for replicated cache data | 
|                  [US12327018B2                 (en)](/patent/US12327018B2/en)                |  | Systems, methods, and devices for near storage elasticity | 
|                  [US10210060B2                 (en)](/patent/US10210060B2/en)                |  | Online NVM format upgrade in a data storage system operating with active and standby memory controllers | 
|                  [US11782634B2                 (en)](/patent/US11782634B2/en)                |  | Dynamic use of non-volatile ram as memory and storage on a storage system | 
|                  [US12411620B2                 (en)](/patent/US12411620B2/en)                |  | Low hiccup time fail-back in active-active dual-node storage systems with large writes | 
|                  [RU2646312C1                 (en)](/patent/RU2646312C1/en)                |  | Integrated hardware and software system | 
|                  [WO2025106220A1                 (en)](/patent/WO2025106220A1/en)                |  | Single-phase commit for replicated cache data | 

## Legal Events

| Date | Code | Title | Description | 
|---|---|---|---|
|  | STPP | Information on status: patent application and granting procedure in general | **Free format text**:               DOCKETED NEW CASE - READY FOR EXAMINATION **Free format text**:               NON FINAL ACTION COUNTED, NOT YET MAILED | 
|  | STPP | Information on status: patent application and granting procedure in general | **Free format text**:               NON FINAL ACTION COUNTED, NOT YET MAILED | 
|  | STPP | Information on status: patent application and granting procedure in general | **Free format text**:               NON FINAL ACTION MAILED | 
|  | STPP | Information on status: patent application and granting procedure in general | **Free format text**:               RESPONSE TO NON-FINAL OFFICE ACTION ENTERED AND FORWARDED TO EXAMINER | 
|  | STPP | Information on status: patent application and granting procedure in general | **Free format text**:               ALLOWED -- NOTICE OF ALLOWANCE NOT YET MAILED | 
|  | STPP | Information on status: patent application and granting procedure in general | **Free format text**:               NOTICE OF ALLOWANCE MAILED -- APPLICATION RECEIVED IN OFFICE OF PUBLICATIONS |