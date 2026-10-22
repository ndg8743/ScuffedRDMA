# CN121560779A - Multi-level cache implementation method and system suitable for nonvolatile storage data - Google Patents

- **Source:** https://patents.google.com/patent/CN121560779A/en?q=~patent%2fCN120122893B&sort=new
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > Papers > Papers)
- **Retrieved:** 2026-10-22


---

# CN121560779A - Multi-level cache implementation method and system suitable for nonvolatile storage data - Google Patents

Multi-level cache implementation method and system suitable for nonvolatile storage data
## Info

- Publication number
- CN121560779A CN121560779A CN202610092467.6A CN202610092467A CN121560779A CN 121560779 A CN121560779 A CN 121560779A CN 202610092467 A CN202610092467 A CN 202610092467A CN 121560779 A CN121560779 A CN 121560779A
- Authority
- CN
- China
- Prior art keywords
- data
- level cache
- state
- data block
- command
- Prior art date
- Legal status (The legal status is an assumption and is not a legal conclusion. Google has not performed a legal analysis and makes no representation as to the accuracy of the status listed.)
- Granted

[Chinese (zh)](/patent/CN121560779A/zh)

[CN121560779B (en](/patent/CN121560779B/en)

## Links

## Classifications

  - G—PHYSICS
  - G06—COMPUTING OR CALCULATING; COUNTING
  - G06F—ELECTRIC DIGITAL DATA PROCESSING
  - G06F12/00—Accessing, addressing or allocating within memory systems or architectures
  - G06F12/02—Addressing or allocation; Relocation
  - G06F12/08—Addressing or allocation; Relocation in hierarchically structured memory systems, e.g. virtual memory systems
  - G06F12/0802—Addressing of a memory level in which the access to the desired data or data block requires associative addressing means, e.g. caches
  - G06F12/0806—Multiuser, multiprocessor or multiprocessing cache systems
  - G06F12/0811—Multiuser, multiprocessor or multiprocessing cache systems with multilevel cache hierarchies
  - G—PHYSICS
  - G06—COMPUTING OR CALCULATING; COUNTING
  - G06F—ELECTRIC DIGITAL DATA PROCESSING
  - G06F12/00—Accessing, addressing or allocating within memory systems or architectures
  - G06F12/02—Addressing or allocation; Relocation
  - G06F12/08—Addressing or allocation; Relocation in hierarchically structured memory systems, e.g. virtual memory systems
  - G06F12/0802—Addressing of a memory level in which the access to the desired data or data block requires associative addressing means, e.g. caches
  - G06F12/0862—Addressing of a memory level in which the access to the desired data or data block requires associative addressing means, e.g. caches with prefetch
  - G—PHYSICS
  - G06—COMPUTING OR CALCULATING; COUNTING
  - G06F—ELECTRIC DIGITAL DATA PROCESSING
  - G06F12/00—Accessing, addressing or allocating within memory systems or architectures
  - G06F12/02—Addressing or allocation; Relocation
  - G06F12/08—Addressing or allocation; Relocation in hierarchically structured memory systems, e.g. virtual memory systems
  - G06F12/12—Replacement control
  - G06F12/121—Replacement control using replacement algorithms
  - G06F12/123—Replacement control using replacement algorithms with age lists, e.g. queue, most recently used \[MRU\] list or least recently used \[LRU\] list
  - G—PHYSICS
  - G06—COMPUTING OR CALCULATING; COUNTING
  - G06F—ELECTRIC DIGITAL DATA PROCESSING
  - G06F13/00—Interconnection of, or transfer of information or other signals between, memories, input/output devices or central processing units
  - G06F13/14—Handling requests for interconnection or transfer
  - G06F13/20—Handling requests for interconnection or transfer for access to input/output bus
  - G06F13/28—Handling requests for interconnection or transfer for access to input/output bus using burst mode transfer, e.g. direct memory access DMA, cycle steal

## Landscapes

- Engineering & Computer Science (AREA)
- Theoretical Computer Science (AREA)
- Physics & Mathematics (AREA)
- General Engineering & Computer Science (AREA)
- General Physics & Mathematics (AREA)
- Memory System Of A Hierarchy Structure (AREA)

## Abstract

The invention discloses a multi-level cache realization method and a system suitable for nonvolatile storage data, and relates to the technical field of data storage. The method is based on the cooperative execution of a first-level cache managed by a hardware management module and a second-level cache managed by a software management module, and comprises the steps that the hardware management module performs address resolution on a received host command and inquires the state of a corresponding data block in the first-level cache. The states include invalid, loading, available, dirty data, and unloading. When the data block is in an invalid state, a data load operation from the non-volatile memory or the second level cache to the first level cache is triggered. When a data block in a dirty data state needs to be replaced from the first-level cache, triggering the operation of migrating the data block to the second-level cache for temporary storage. According to the invention, through the software and hardware collaborative division architecture and the dirty data priority cache migration strategy, the data access delay is effectively reduced, and the more stable overall performance is realized.

## Description

Technical Field

The present invention relates to the field of data storage technologies, and in particular, to a method and a system for implementing multi-level caching suitable for nonvolatile data storage.

Background

At present, a multi-level cache scheme is mainly used for meeting the high-speed access requirement of a Central Processing Unit (CPU) on near-end volatile storage data, and the overall access efficiency is improved by introducing multi-level caches into a storage hierarchy and utilizing the locality principle of data access.

With the rapid development of solid state storage technology and the evolution of high-speed interconnection protocols such as Compute Express Link, the CPU has an increasing demand for accessing nonvolatile data in remote storage devices. However, the nonvolatile storage medium is limited by physical characteristics, and the read-write delay is significantly higher than that of the dynamic random access memory, which has become a bottleneck for restricting the real-time performance of the system.

To address this challenge, the chinese patent application, issued to CN118331508B, discloses a method for managing data coherency between a cache and a nonvolatile memory NAND through a centralized data state controller, which introduces a dedicated state for nonvolatile memory, but has inherent limitations in its centralized control architecture. Firstly, all state inquiry, judgment and command generation are processed by a single logic unit in series, and the state inquiry, judgment and command generation are easy to become performance bottlenecks under a high concurrency scene, so that the real-time response capability is affected. Secondly, the core defect is that the direct synchronous write-back of the dirty data is required to be carried out on the NAND with high delay, the blocking operation inevitably causes periodic steep increase and severe fluctuation of the input/output delay of the system when the dirty data is in a peak state, the performance is unstable, and in addition, the caching strategy is tightly coupled with the hardware management, so that independent optimization and iteration are difficult.

It should be noted that the information disclosed in the above background section is only for enhancing understanding of the background of the application and thus may include information that does not form the prior art that is already known to those of ordinary skill in the art.

Disclosure of Invention

Aiming at the problems of high access delay, periodic jitter in performance, insufficient flexibility of architecture and the like in the prior art when nonvolatile storage data are managed, the invention provides a multi-level cache implementation method and a multi-level cache implementation system suitable for nonvolatile storage data. The data access delay is effectively reduced through the software and hardware collaborative division architecture and the dirty data priority cache migration strategy, and the smoother overall performance is realized.

In order to achieve the above purpose, the present invention provides the following technical solutions:

a multi-level cache implementation method suitable for non-volatile storage data, a hardware management module managing a first level cache, and a software management module managing a second level cache, the method comprising:

address analysis is carried out on the received host command to obtain the position identification of the target data block in the first-level cache;

Inquiring the state of a corresponding data block in the first-level cache based on the position identification, wherein the state comprises invalid, loading, available, dirty data and unloading;

If the data block is in an invalid state, triggering a data loading operation from the second-level cache or the nonvolatile memory to the first-level cache;

And if the data block in the dirty data state needs to be replaced from the first-level cache, triggering the operation of migrating the data block from the first-level cache to the second-level cache for temporary storage.

As a preferred embodiment of the present invention, the triggering the data loading operation from the second level cache or the nonvolatile memory to the first level cache includes:

The method comprises the steps of distributing a first-level cache destination address for data loading operation and generating a loading command, wherein the loading command at least comprises a command ID, a command type, a source data address and the first-level cache destination address;

querying a second-level cache address mapping table based on the load command;

If the data block is hit in the second-level cache, the data is read from the second-level cache and written into the first-level cache destination address, otherwise, the data is read from the nonvolatile memory and written into the first-level cache destination address.

As a preferred scheme of the present invention, if the status of the data block is in loading, caching the subsequent host commands accessed to the data block until loading is completed;

after successful loading, the status of the data block is updated to available or dirty data and all host commands cached are processed.

As a preferred embodiment of the invention, the state update follows the following conversion rule:

The initial states of all the data blocks are set as invalid;

when a data block in an invalid state is accessed, the data block is converted into a loading state;

after the loading of the data block is successfully completed, if the host command triggering the loading is a read command, the data block is converted into usable data, and if the host command triggering the loading is a write command, the data block is converted into dirty data;

when accessing the data block in the available state, if the host command triggering the access is a read command, the state of the data block is kept available;

when a data block of a dirty data state is selected as a replacement object, converting the data block into an uninstall state;

And after the data block in the unloading state is successfully migrated from the first-level cache to the second-level cache, converting the data block into invalid data, and if the data block is accessed again before the migration is completed, converting the data block into dirty data.

As a preferred embodiment of the present invention, the triggering the operation of migrating the data block from the first-level cache to the second-level cache for temporary storage includes:

generating a migration command, wherein the migration command at least comprises a command ID, a command type, a first-level cache source address where data to be migrated are located and a data length;

based on the migration command, a second-level cache destination address is allocated;

and migrating the data to be migrated from the first-level cache source address to the second-level cache destination address, and updating the state of the data block to be invalid after successful migration.

As a preferred embodiment of the present invention, the method further comprises a migration suspension and rollback mechanism:

If the data block in the unloading state is accessed again before the migration is completed, the migration flow is stopped;

And rolling back part of the data which has been migrated to the second-level cache to the first-level cache, and updating the state of the data block into dirty data.

A multi-level cache implementation system for non-volatile storage of data, comprising:

the hardware management module is used for analyzing the host command, inquiring the state of the data block in the first-level cache and triggering data loading or data migration operation based on the state;

The software management module is used for responding to the trigger of the hardware management module and executing data loading or data migration operation;

the first-level cache is managed by the hardware management module;

and the second level cache is managed by the software management module.

As a preferable scheme of the invention, the capacity of the second level cache is larger than that of the first level cache;

the hardware management module is embedded with a state machine and is used for realizing data block state conversion and maintenance;

The hardware management module and the software management module interact commands and state information through a special communication interface so as to cooperatively realize multi-level cache management.

A computer device comprising a memory storing a computer program and a processor implementing steps of a multi-level cache implementation method suitable for non-volatile storage of data when the computer program is executed.

A computer readable storage medium having stored thereon a computer program which, when executed by a processor, implements steps of a multi-level cache implementation method for non-volatile storage of data.

Compared with the prior art, the method has the beneficial effects that the hardware management module is used for inquiring the state of the data block in real time and triggering the operation, so that extremely low delay and deterministic response to the first-level cache hot spot data access are ensured, and meanwhile, specific data loading and migration operations are executed through the software management module, so that the management strategy of the second-level cache can be flexibly configured, optimized and iterated independently of hardware. The design of the software and hardware coordination and decoupling ensures that the system not only can meet the real-time requirement, but also can flexibly adapt to complex application load changes, thereby realizing the unification of performance and flexibility. By innovatively triggering the operation of transferring temporary storage to the second-level cache when the data in the dirty data state needs to be replaced, the blocking input or output operation of directly writing back the high-delay nonvolatile memory device in the traditional scheme is converted into the rapid data handling in the volatile memory, so that the writing back load of the system is smoothed fundamentally, the periodic burrs of input or output delay are effectively eliminated, and stable and predictable performance output is realized. In addition, the architecture reduces the obstructive access to the nonvolatile memory device, thereby improving the overall throughput and high concurrency processing capacity of the system, simultaneously being beneficial to reducing the write amplification effect and abrasion of the memory medium and prolonging the service life.

The foregoing general description and the following description are exemplary and explanatory only and are not restrictive of the application.

Drawings

In order to more clearly illustrate the technical solutions of the embodiments of the present invention, the drawings that are needed in the description of the embodiments will be briefly described below, it being obvious that the drawings in the following description are only some embodiments of the present invention, and that other drawings may be obtained according to these drawings without inventive effort for a person skilled in the art. Wherein:

FIG. 1 is a flow chart of a method for implementing multi-level caching for non-volatile storage data according to the present invention;

Fig. 2 is a schematic diagram of a modular structure of a multi-level cache implementation system suitable for non-volatile data storage according to the present invention.

Detailed Description

In order to make the objects, technical solutions and advantages of the embodiments of the present invention more clear, the technical solutions of the embodiments of the present invention will be clearly and completely described below with reference to the accompanying drawings of the embodiments of the present invention. It will be apparent that the described embodiments are some, but not all, embodiments of the invention. All other embodiments, which are obtained by a person skilled in the art based on the described embodiments of the invention, fall within the scope of protection of the invention.

As shown in fig. 1, in an embodiment of the present invention, a method for implementing a multi-level cache suitable for nonvolatile data storage is provided, where a hardware management module manages a first level cache and a software management module manages a second level cache, and the method includes:

And carrying out address analysis on the received host command to obtain the position identification of the target data block in the first-level cache.

The first level cache is arranged in a volatile memory, the storage space of the first level cache is divided into S groups, each group comprises B data blocks, and each data block can store data with fixed length and is completely managed and controlled by hardware logic in real time. In a preferred embodiment, the first level cache is provided in DRAM, and each data block may store 4KB of data.

The process of address resolution for the received host command includes:

Read and write commands from the host are received and buffered in an internal host command queue. Wherein the queue ensures sequential processing and Pending capabilities of commands.

And analyzing a target address in the host command, and obtaining a group address and a block label corresponding to the address in the first-level cache through a preset group connection mapping relation.

Based on the location identification, the state of the corresponding data block in the first level cache is queried. Where the state includes invalid, loading, available, dirty data, and unloading.

An invalidation indicates that the data block is not currently storing valid data. The loading indicates that the block of data is loading data from the non-volatile storage device or the second level cache to the first level cache. The data block may be used to indicate that it is loaded with valid data and consistent with the underlying stored data, and may be read directly. Dirty data indicates that the data in the data block has been modified by the host and is inconsistent with the underlying stored data. The offloading indicates that the block of data is being migrated from the first level cache to the second level cache.

And if the data block is in an invalid state, triggering a data loading operation from the second-level cache or the nonvolatile memory to the first-level cache.

Specifically, when the target data block state is found to be invalid, the host command triggering the access is cached in the host command queue, and then the data loading operation is triggered.

Triggering a data load operation from the second level cache or the nonvolatile memory to the first level cache, comprising:

And allocating a first-level cache destination address for the loading operation and generating a loading command. The loading command at least comprises a command ID, a command type, a source data address and a first-level cache destination address, wherein the command type is loading.

Specifically, the load command is in a standardized double word format, DW0 contains a 16-bit command ID and a 16-bit command type, DW1 contains a 32-bit first-level cache destination address, and DW2 contains a 32-bit source data address.

Based on the load command, the second level cache address mapping table is queried.

If the data block is hit in the second-level cache, the data is directly read from the second-level cache and written into the first-level cache destination address, otherwise, the data is read from the nonvolatile memory and written into the first-level cache destination address.

Specifically, the read data is written to the first level cache destination address specified in the load command by the DMA engine.

If the state of the data block is in loading, the subsequent host commands accessed to the data block are cached until loading is successful.

Specifically, from the time the data block status is set to load, all newly arrived access commands for the same data block are buffered to the host command queue until the load is completed.

After the data loading is completed, loading state information is generated.

Specifically, the loading state information comprises a corresponding command ID, a command type and a state type, and a standardized double-word format is adopted, wherein DW0 comprises a 16-bit command ID and a 16-bit command type, and the upper 16 bits of DW1 are the state type and the lower 16 bits are reserved. For example, 0x00 indicates success, and 0x01 indicates failure.

If the status type in the loading status information is successful, the status of the data block is updated to available or dirty data, and all cached host commands are processed based on the updated status.

If the status type in the loading status information is failed, the data loading operation is re-triggered, optionally, a maximum number of attempts may be set.

The state transitions involved in the above-described flow follow the following rules:

the initial state of all data blocks is set to invalid.

When a data block in an invalid state is accessed, the data block state is converted into in-load.

After the loading of the data block is successfully completed, if the host command triggering the loading is a read command, the data block is converted into usable data, and if the host command triggering the loading is a write command, the data block is converted into dirty data.

When accessing the data block in the available state, if the host command triggering the access is a read command, the state of the data block is kept available after the access is completed, and if the host command triggering the access is a write command, the state of the data block is converted into dirty data after the access is completed.

When a data block of a dirty data state is selected as a replacement object, the data block state is transitioned into off-load.

And if the data block is accessed again before the migration is completed, the migration is stopped and the data block state is converted into dirty data.

And if the data block in the dirty data state needs to be replaced from the first-level cache, triggering the operation of migrating the data block from the first-level cache to the second-level cache for temporary storage.

Specifically, when the first level cache space is full, or a data block marked as dirty data needs to be replaced according to a replacement algorithm (such as LRU), the fundamental difference between the traditional cache scheme and forcing the data to be written back to the high latency nonvolatile memory is that the present invention marks the data block state as off-load and triggers a migration operation to the second level cache. This "dirty data priority cache migration" strategy is one of the core advantages of the present invention, which translates into unpredictable slow persistent input or output into deterministic high-speed data handling inside the DRAM.

Triggering the operation of migrating the data block from the first-level cache to the second-level cache for temporary storage, wherein the operation comprises the following steps:

a migration command is generated. The migration command at least comprises a command ID, a command type, a first-level cache source address where data to be migrated is located and a data length, wherein the command type is migration.

Specifically, the migration command adopts a standardized double word format, namely DW0 comprises a 16-bit command ID and a 16-bit command type, DW1 comprises a 32-bit first-level cache source address, and DW2 comprises a 32-bit data length.

Based on the migration command, a second level cache destination address is allocated.

Specifically, the LRU algorithm is used to allocate a temporary storage area of the second level cache.

And migrating the data to be migrated from the first-level cache source address to the second-level cache destination address, and updating the state of the data block to be invalid after successful migration.

Specifically, data to be migrated is migrated from a first level cache source address to a second level cache destination address at a high speed by a DMA engine. This is done entirely within the volatile memory, with a delay typically on the order of microseconds or even nanoseconds, much lower than writing to the non-volatile memory.

After the migration is completed, migration state information is generated, wherein the migration state information at least comprises a corresponding command ID, a command type and a state type, and the specific adopted format is the same as that of the loading state information.

If the state type in the migration state information is successful, the state of the corresponding data block is updated to be invalid, and the original first-level cache space can be redistributed for use. If the status type is failed, the data block status is kept as being unloaded, and the migration operation is triggered again, optionally, a maximum number of attempts may be set.

If the data block in the unloading state is accessed again before the migration is completed, the migration flow is stopped. To ensure data consistency, a rollback mechanism is started to rollback portions of the data that have been migrated to the second level cache to the first level cache and update the state of the data block to dirty data. This mechanism ensures that the host always has access to the latest version of the data, even under concurrent access.

The present invention redirects the alternate path of data in the dirty data state from a high latency persistent input or output to a low latency volatile storage internal transport through the dirty data priority cache migration policy described above. When the data is accessed again, the data can be directly and quickly loaded from the second-level cache, and the performance bottleneck of accessing the nonvolatile memory is completely avoided, so that the system write-back load is basically smoothed, and the performance jitter caused by concentrated write-back in the traditional scheme is eliminated.

For a block of data in an available state, the host command is executed directly and responded to. The data block in the dirty data state is not replaced from the first level cache, and the data block state is kept unchanged, and the host command is directly executed and responded.

The invention also provides a multi-level cache realization system suitable for nonvolatile storage data, which is used for realizing any method embodiment. The system adopts a software and hardware cooperative architecture, and adapts to the data access characteristic of the nonvolatile storage device by efficiently managing two levels of caches.

As shown in fig. 2, another embodiment of the present invention provides a multi-level cache implementation system suitable for nonvolatile data storage, where the system includes a hardware management module, a software management module, a first level cache and a second level cache. The components are interconnected and interacted through a system bus, a memory bus and a special communication interface.

The hardware management module is used for analyzing the host command, inquiring the state of the corresponding data block in the first-level cache, and triggering data loading or data migration operation based on the state.

Specifically, the hardware management module is a core control hub of the system, and is usually implemented in a form of a dedicated hardware circuit (such as FPGA/ASIC), and includes a command processing unit, an address resolution unit, a state management unit, and a synergistic interface unit, where the units cooperate to complete low-latency management of the first level cache.

The command processing unit is connected to the host interface and used for receiving the host read-write command, carrying out validity check and preliminary decoding on the command, writing the valid command into an internal host command queue for caching and scheduling, and returning response data or a completion state to the host after the host command is executed.

And the address analyzing unit is used for analyzing the target address of the host command to obtain a corresponding group address and a corresponding block label. The unit takes out the target address of the command to be processed from the command processing unit, and analyzes the system physical address into a corresponding group address and a block label in the first-level cache according to a preset address mapping rule. In a preferred embodiment, the preset address mapping rule adopts a group-connected mapping mode.

The state management unit is a core decision unit of the hardware management module, and maintains a tag state memory corresponding to the first-level cache structure and used for storing tags of each cache data block and the current state thereof, wherein the current state comprises invalid, loading, available, dirty data and unloading. The unit is used for receiving the group address and the block label from the address analysis unit, inquiring the current state of the target data block, and deciding and updating the next state of the data block in real time according to the embedded state conversion rule, the host command type and the preset replacement algorithm. The decision logic specifically comprises the steps of instructing a command processing unit to directly execute a host command if a data block state is available data, updating the state of the data block to be dirty data before execution for writing operation of the available data block, updating the state of the data block to be loaded and notifying a cooperative interface unit to initiate a loading request if the data block state is invalid, updating the data block state to be unloaded and notifying the cooperative interface unit to initiate a migration request if the data block in the dirty data state needs to be replaced, and instructing the command processing unit to directly execute the host command if the data block in the dirty data state does not need to be replaced. In addition, the unit receives the operation state feedback forwarded by the collaborative interface unit from the software management module, and accordingly performs final state confirmation and subsequent action triggering, namely, if the state is a successful loading state, the corresponding data block state is updated into usable or dirty data, the processing of the corresponding waiting command in the host command queue is triggered, and if the state is a successful migration state, the corresponding data block state is updated into invalid.

And the cooperative interface unit is used as a communication proxy between the hardware management module and the software management module. The unit generates a formatted load command or migration command according to the instruction of the state management unit and transmits the formatted load command or migration command to the software management module through the special communication interface. Meanwhile, the unit is responsible for receiving the response state information from the software management module through the special communication interface and forwarding the response state information to the state management unit for processing.

And the software management module is used for responding to the trigger of the hardware management module and executing data loading or data migration operation.

The software management module is operated in a system main processor and usually exists in the form of a driving program, firmware or system service, and the main functions comprise receiving and analyzing a loading command or a migration command sent by the hardware management module, maintaining an address mapping table of a second-level cache, managing allocation and recovery of a storage space of the second-level cache, executing operation according to a command type, inquiring the address mapping table of the second-level cache, reading data from the second-level cache if the second-level cache is hit, otherwise, reading the data from a nonvolatile memory, writing the data into a first-level cache destination address designated by the hardware management module in a DMA (direct memory) mode, for the migration command, reading the data in a data block in a dirty data state from the designated first-level cache source address, writing the data into the allocated second-level cache destination address, generating corresponding loading state information or migration state information after the operation is completed, and returning the corresponding loading state information to the hardware management module through a special communication interface. All management policies of the second level cache, such as replacement algorithms, data prefetching, and final persistent scheduling to the non-volatile memory, are flexibly configured and executed by the software management module.

The first-level cache is arranged in the high-speed volatile memory. The storage space of the cache is organized into a group-contiguous structure, divided into S groups, each group containing B fixed-size data blocks. The first level cache is directly accessed and controlled by the hardware management module through hardware logic to provide nanosecond access delay.

The second level cache is also provided in the high-speed volatile memory. The total capacity of the cache is significantly greater than the first level cache. The second-level buffer is managed by the software management module through system memory read-write, is used as a large-capacity backup buffer area of the first-level buffer, and is specially used for temporarily storing data in a data block in a dirty data state and prefetched data replaced by the first-level buffer, so that a data migration chain is formed in the volatile memory, and direct access to the slow nonvolatile memory is avoided.

The hardware management module and the software management module interact through a special communication interface, and the interface is used for transmitting formatted commands and state information, which is the key for realizing the cooperation of software and hardware.

Taking the example of a read request cache miss, the system workflow is as follows:

The host issues a read command, which is received by the command processing unit and stored in the host command queue. The address analysis unit analyzes the command address to obtain a group address and a block label. The state management unit queries the tag state memory, finds that the target block state is invalid, updates the state of the target block into loading, and instructs the collaboration interface unit to initiate a loading request. The collaboration interface unit generates a load command and sends the load command to the software management module. The software management module analyzes the command, queries the second-level cache address mapping table, reads data from the second-level cache if hit, and reads data from the nonvolatile memory if not hit. And then, the software management module writes the data into the first-level cache destination address appointed in the loading command through DMA, and generates loading state information and returns after the completion. The collaboration interface unit receives and analyzes the state information and forwards the state information to the state management unit. If the loading status information indicates successful loading, the status management unit updates the target data block to available and triggers the processing of the original read command of the data block in the host command queue. Finally, the data is read out from the first-level cache and returned to the host computer through the command processing unit, and the access is completed.

The embodiment also provides a computer device, which is suitable for the situation of a multi-level cache implementation method suitable for nonvolatile storage data, and comprises a memory and a processor, wherein the memory is used for storing computer executable instructions, and the processor is used for executing the computer executable instructions to implement all or part of the steps of the method according to the embodiment of the invention.

The present embodiment also provides a storage medium having stored thereon a computer program which, when executed by a processor, performs the method of any of the alternative implementations of the above embodiments. The storage medium may be implemented by any type of volatile or non-volatile Memory device or combination thereof, such as static random access Memory (Static Random Access Memory, SRAM for short), electrically erasable programmable Read-Only Memory (ELECTRICALLY ERASABLE PROGRAMMABLE READ ONLY MEMORY, EEPROM for short), erasable programmable Read-Only Memory (Erasable Programmable Read Only Memory, EPROM for short), programmable Read-Only Memory (Programmable Read Only Memory, PROM for short), read Only Memory (ROM for short), magnetic Memory, flash Memory, magnetic disk, or optical disk.

The storage medium according to the present embodiment belongs to the same inventive concept as the data storage method according to the above embodiment, and technical details not described in detail in the present embodiment can be seen in the above embodiment, and the present embodiment has the same advantageous effects as the above embodiment.

In summary, the present invention provides a method and a system for implementing multi-level cache suitable for nonvolatile storage data, which constructs a complete and efficient multi-level cache management scheme by a collaborative software and hardware architecture, a refined state control, a delay optimization of a critical path and an efficient interaction mechanism, so as to reduce access delay, improve system throughput and resource utilization rate, and implement more stable performance. Specifically, in the architecture level, the first level buffer is directly controlled by a special hardware management module, real-time low-delay access and state maintenance are realized through a hardware circuit, and the second level buffer is dynamically managed by a software management module running on a main processor, so that flexible strategy configuration and large-capacity data temporary storage are supported. The design has both high performance of hardware and strong expansibility of software, and realizes effective unification of performance and flexibility. In the management logic level, the life cycle of the data block is completely covered by defining a state machine containing five states of invalid, loading, available, dirty data and unloading and a clear conversion rule, clear operation basis is provided for hardware, and consistency guarantee logic is embedded to ensure data correctness and execution sequence when concurrent access and cache operation are interwoven. In critical path optimization, a loading mechanism is triggered only when a data block is in an invalid state, so that invalid prefetching is avoided, and the utilization efficiency of cache resources is improved; the method is particularly critical, a strategy of preferentially migrating to a second-level cache is innovatively adopted for the data block to be replaced, and the high-delay operation which is originally required to be written into the nonvolatile memory is converted into a data carrying process in the volatile memory. Subsequent access to the data can be directly and rapidly loaded from the second-level cache, so that direct access to a low-speed storage medium is avoided, and delay shielding and access acceleration are realized. On the cooperative interaction level, the hardware management module and the software management module perform efficient and reliable cooperation according to a predefined interaction protocol through a special communication interface, and the mechanism ensures that a hardware trigger request and software execution feedback can be accurately transmitted with low cost, and ensures the smooth execution of cross-level operation and the reliability of the whole flow. The mechanisms cooperate to enable multiple data accesses to be accomplished within the volatile memory, substantially reducing direct access to high latency nonvolatile memory. The second-level buffer is used as a dirty data buffer area and a persistence transfer area to bear the replacement pressure of the first-level buffer, and delay merging and intelligent scheduling are carried out on the final persistence write operation, so that performance jitter caused by concentrated write-back of the traditional buffer is avoided. And flexible adaptation of strategies is realized through a software layer while the lower limit of basic performance is ensured, and the overall input and output processing capacity and the resource utilization efficiency are effectively improved.

The foregoing is merely illustrative of the present application, and the present application is not limited thereto, and any person skilled in the art will readily recognize that various changes and substitutions are possible within the scope of the present application. Therefore, the protection scope of the application is subject to the protection scope of the claims.

## Claims (10)

[CN121560779B (en)](/patent/CN121560779B/en)

## Priority Applications (1)

| Application Number | Priority Date | Filing Date | Title | 
|---|---|---|---|
| CN202610092467.6A                [CN121560779B                 (en)](/patent/CN121560779B/en)              | 2026-01-23 | 2026-01-23 | Multi-level cache implementation method and system suitable for nonvolatile storage data | 

## Applications Claiming Priority (1)

| Application Number | Priority Date | Filing Date | Title | 
|---|---|---|---|
| CN202610092467.6A                [CN121560779B                 (en)](/patent/CN121560779B/en)              | 2026-01-23 | 2026-01-23 | Multi-level cache implementation method and system suitable for nonvolatile storage data | 

## Publications (2)

| Publication Number | Publication Date | 
|---|---|
| CN121560779A                          true                [CN121560779A               (en)](/patent/CN121560779A/en)              | 2026-02-24 | 
| CN121560779B                [CN121560779B               (en)](/patent/CN121560779B/en)              | 2026-04-14 | 

# Family

## ID=98797465

## Family Applications (1)

| Application Number | Title | Priority Date | Filing Date | 
|---|---|---|---|
| CN202610092467.6A             Active                [CN121560779B                 (en)](/patent/CN121560779B/en)              | 2026-01-23 | 2026-01-23 | Multi-level cache implementation method and system suitable for nonvolatile storage data | 

## Country Status (1)

| Country | Link | 
|---|---|
| CN (1) |                [CN121560779B               (en)](/patent/CN121560779B/en)              | 

## Citations (4)

| \* Cited by examiner, † Cited by third party |  |  |  |  | 
|---|---|---|---|---|
| Publication number | Priority date | Publication date | Assignee | Title | 
|---|---|---|---|---|
|                [CN103034538A               (en)](/patent/CN103034538A/en)             \* | 2012-12-24 | 2013-04-10 | 珠海拓普智能电气股份有限公司 | Multi-level cache processing method of drive program in embedded type operation system | 
|                [CN105138292A               (en)](/patent/CN105138292A/en)             \* | 2015-09-07 | 2015-12-09 | 四川神琥科技有限公司 | Disk data reading method | 
|                [CN114594915A               (en)](/patent/CN114594915A/en)             \* | 2022-03-18 | 2022-06-07 | 苏州浪潮智能科技有限公司 | A data caching method, device and readable storage medium | 
|                [CN117785063A               (en)](/patent/CN117785063A/en)             \* | 2023-12-29 | 2024-03-29 | 山东云海国创云计算装备产业创新中心有限公司 | An NVMe acceleration method and device based on multi-level cache and feedback algorithm | 

- 
        2026
        
  - 
            2026-01-23
            CN
            CN202610092467.6A
            [patent/CN121560779B/en](/patent/CN121560779B/en) active
            Active

## Patent Citations (4)

| \* Cited by examiner, † Cited by third party |  |  |  |  | 
|---|---|---|---|---|
| Publication number | Priority date | Publication date | Assignee | Title | 
|---|---|---|---|---|
|                [CN103034538A               (en)](/patent/CN103034538A/en)             \* | 2012-12-24 | 2013-04-10 | 珠海拓普智能电气股份有限公司 | Multi-level cache processing method of drive program in embedded type operation system | 
|                [CN105138292A               (en)](/patent/CN105138292A/en)             \* | 2015-09-07 | 2015-12-09 | 四川神琥科技有限公司 | Disk data reading method | 
|                [CN114594915A               (en)](/patent/CN114594915A/en)             \* | 2022-03-18 | 2022-06-07 | 苏州浪潮智能科技有限公司 | A data caching method, device and readable storage medium | 
|                [CN117785063A               (en)](/patent/CN117785063A/en)             \* | 2023-12-29 | 2024-03-29 | 山东云海国创云计算装备产业创新中心有限公司 | An NVMe acceleration method and device based on multi-level cache and feedback algorithm | 

## Also Published As

| Publication number | Publication date | 
|---|---|
|                [CN121560779B               (en)](/patent/CN121560779B/en)              | 2026-04-14 | 

## Similar Documents

| Publication | Publication Date | Title | 
|---|---|---|
|                  [CN100505762C                 (en)](/patent/CN100505762C/en)                |  | Distributed multi-stage buffer storage system suitable for object network storage | 
|                  [CN103345451B                 (en)](/patent/CN103345451B/en)                |  | Data buffering method in multi-core processor | 
|                  [CN114490141B                 (en)](/patent/CN114490141B/en)                |  | A High Concurrency IPC Data Interaction Method Based on Shared Memory | 
|                  [CN115391237A                 (en)](/patent/CN115391237A/en)                |  | Garbage recovery system and method applied to flash memory storage controller | 
|                  [JP2017515242A                 (en)](/patent/JP2017515242A/en)                |  | Memory management method and device | 
|                  [CN101149704A                 (en)](/patent/CN101149704A/en)                |  | Design Method of Segmented Cache in Microprocessor and Segmented Cache | 
|                  [CN102063406A                 (en)](/patent/CN102063406A/en)                |  | Network shared Cache for multi-core processor and directory control method thereof | 
|                  [CN108920192B                 (en)](/patent/CN108920192B/en)                |  | Method and device for realizing cache data consistency based on distributed limited directory | 
|                  [CN110750356A                 (en)](/patent/CN110750356A/en)                |  | Multi-core interactive method, system and storage medium suitable for non-volatile memory | 
|                  [EP3835959B1                 (en)](/patent/EP3835959B1/en)                |  | Data pre-fetching method and device | 
|                  [CN118915896B                 (en)](/patent/CN118915896B/en)                |  | CXL bias management method based on cache soft and hard coordination | 
|                  [CN103294611A                 (en)](/patent/CN103294611A/en)                |  | Server node data cache method based on limited data consistency state | 
|                  [US20090083496A1                 (en)](/patent/US20090083496A1/en)                |  | Method for Improved Performance With New Buffers on NUMA Systems | 
|                  [US8977816B2                 (en)](/patent/US8977816B2/en)                |  | Cache and disk management method, and a controller using the method | 
|                  [CN117407194A                 (en)](/patent/CN117407194A/en)                |  | Heterogeneous communication architecture based on cache consistency | 
|                  [CN120523749B                 (en)](/patent/CN120523749B/en)                |  | Active maintenance method and device for cache consistency, electronic equipment and storage medium | 
|                  [CN116795767A                 (en)](/patent/CN116795767A/en)                |  | A method to build a multi-core Cache shared consistency protocol based on the CHI protocol | 
|                  [JP2022015514A                 (en)](/patent/JP2022015514A/en)                |  | Semiconductor device | 
|                  [US9983994B2                 (en)](/patent/US9983994B2/en)                |  | Arithmetic processing device and method for controlling arithmetic processing device | 
|                  [CN111124297B                 (en)](/patent/CN111124297B/en)                |  | A Performance Improvement Method for Stacked DRAM Cache | 
|                  [CN121560779B                 (en)](/patent/CN121560779B/en)                |  | Multi-level cache implementation method and system suitable for nonvolatile storage data | 
|                  [CN102521161B                 (en)](/patent/CN102521161B/en)                |  | Data caching method, device and server | 
|                  [CN104580422A                 (en)](/patent/CN104580422A/en)                |  | Cluster rendering node data access method based on shared cache | 
|                  [US20260019477A1                 (en)](/patent/US20260019477A1/en)                |  | Method for intra-stack zero-copy transmit path in shared-memory-based communication mode | 
|                  [CN120687382A                 (en)](/patent/CN120687382A/en)                |  | Memory access method and electronic device | 

## Legal Events

| Date | Code | Title | Description | 
|---|---|---|---|
|  | PB01 | Publication |  | 
|  | PB01 | Publication |  | 
|  | SE01 | Entry into force of request for substantive examination |  | 
|  | SE01 | Entry into force of request for substantive examination |  | 
|  | GR01 | Patent grant |  | 
|  | GR01 | Patent grant |  |