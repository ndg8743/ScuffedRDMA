# DOCA RDMA - NVIDIA Docs

- **Source:** https://docs.nvidia.com/doca/archive/2-5-4/doca+rdma/index.html
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

This guide provides an overview and configuration instructions for the DOCA RDMA API.

## Introduction
 
  
   
  
 

This library is currently supported at beta level only.



DOCA RDMA supports local networks only (i.e., cross-network or routing is not supported).

DOCA RDMA enables direct access to the memory of remote machines, without interrupting the processing of their CPUs or operating systems. Avoiding CPU interruptions reduces context switching for I/O operations, leading to lower latency and higher bandwidth compared to traditional network communication methods.

DOCA RDMA library provides an API to execute the various RDMA operations.

This document is intended for software developers wishing to improve their applications by utilizing RDMA operations.

## Prerequisites
 
  
   
  
 

This library follows the architecture of a DOCA Core Context, it is recommended read the following sections before proceeding:

## Environment
 
  
   
  
 

DOCA RDMA-based applications can run either on the host machine or on the NVIDIA® BlueField® DPU target.

## Architecture
 
  
   
  
 

DOCA RDMA is a DOCA Context as defined by DOCA Core. See [NVIDIA DOCA Core Context](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCAContext>) for more information.

DOCA RDMA consists of two connected sides, passing data between one another. This includes the option for one side to access the remote side's memory if the granted permissions allow it.

The connection between the two sides can either be based on InfiniBand (IB) or based on Ethernet using RoCE. Currently, only reliable connection (RC) transport type is supported.

DOCA RDMA leverages the Core architecture to expose asynchronous tasks/events that are offloaded to hardware.

The supported operations that may be executed between the two sides, using DOCA RDMA, are:

- Receive
- Send
- Send with immediate
- Write
- Write with immediate
- Read
- Atomic compare and swap
- Atomic fetch and add
- Get remote DOCA Sync Event
- Set remote DOCA Sync Event
- Add remote DOCA Sync Event

### Objects
 
  
   
  
 

#### Device
 
  
   
  
 

The RDMA library requires a DOCA device to operate. This device is used to utilize the connection between the peers in RDMA, access memory, and perform the different operations.

The device must stay valid until the RDMA instance is destroyed.

#### Memory Map
 
  
   
  
 

Executing any DOCA RDMA operation in which data is passed between the peers requires creating a memory map (mmap) on each side.

- The mmap's permissions must include the relevant RDMA permission, according to the required RDMA operations. Tasks fail in case of insufficient permissions. Refer to section "[DOCA RDMA | id (2.5.4 LTS)DOCARDMA Permissions](</doca/archive/2-5-4/doca-rdma#id-(2.5.4-LTS)DOCARDMA-Permissions>)" for more information.
- To allow the peer to execute RDMA operations, the mmap must be exported, using `doca_mmap_export_rdma()`, and passed to the peer (i.e., the side requesting the RDMA operation) where the remote mmap is created and used to access the memory.

#### Buffer Inventory and Buffers
 
  
   
  
 

Executing any DOCA RDMA operation, in which data is passed between the peers, requires using buffers, and thus requires a buffer inventory as well.

Each operation calls for a different set-up for the buffers in use, this is explicitly explained in the "[DOCA RDMA | id (2.5.4 LTS)DOCARDMA Tasks](</doca/archive/2-5-4/doca-rdma#id-(2.5.4-LTS)DOCARDMA-Tasks>)" section.

## Configuration Phase
 
  
   
  
 

To start using the library you need to first go through a configuration phase as described in [DOCA Core Context Configuration Phase](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-ConfigurationPhase>)

This section describes how to configure and start the context, to allow execution of tasks and retrieval of events.

### Configurations
 
  
   
  
 

The context can be configured to match the application use case.

#### Mandatory Configurations
 
  
   
  
 

These configurations are mandatory and must be set by the application before attempting to start the context:

##### Task Configurations
 
  
   
  
 

At least one task/event type must be configured. See configuration of [DOCA RDMA | id (2.5.4 LTS)DOCARDMA Tasks](</doca/archive/2-5-4/doca-rdma#id-(2.5.4-LTS)DOCARDMA-Tasks>) and/or [DOCA RDMA | id (2.5.4 LTS)DOCARDMA Events](</doca/archive/2-5-4/doca-rdma#id-(2.5.4-LTS)DOCARDMA-Events>).

##### Permissions
 
  
   
  
 

Different tasks require different permission to be set for both the RDMA and the mmap in use.

The following table summarizes the necessary RDMA and mmap permissions for each RDMA operation:

| **DOCA RDMA task Types** | **Minimal Permissions** |  |  |  | **Should Export** **MMAP?(a)** | 
|---|---|---|---|---|---|
|  | The Side Submitting the Task |  | The Peer |  |  | 
|  | **RDMA** | **MMAP** | **RDMA** | **MMAP** |  | 
| Read Get Remote Sync Event | – | Local read write | RDMA read | Local read write \| RDMA read | Yes | 
| Write Write with Immediate Set Remote Sync Event | – | Local read write | RDMA write | Local read write \| RDMA write | Yes | 
| Atomic Compare and Swap Atomic Fetch and Add Add Remote Sync Event | – | Local read write | RDMA atomic | Local read write \| RDMA atomic | Yes | 
| Send Send with Immediate | – | Local read write | – | Local read write | No | 
| Receive | Depending on the received task | Local read write | Not relevant |  |  | 



<sup>(a)</sup> Refers to the peer. A side that only submits tasks is never required to export an mmap.

#### Optional Configurations
 
  
   
  
 

If these configurations are not set, a default value is used.

Users may edit the default properties of the RDMA instance using the `doca_rdma_set_<property>()`. The user may also query the default/set properties using  `doca_rdma_cap_get`**\_**`<property>(struct doca_rdma *, …)` functions.

The number of tasks that can be submitted in bulk is dependent on the properties `max_send_buf_list_len` and `send_queue_size`.

Refer to [Library Capability](</doca/archive/2-5-4/capability-checking#id-(2.5.4-LTS)CapabilityChecking-LibraryCapability>) for querying valid property values when configuring the library context.

### Device Support
 
  
   
  
 

DOCA RDMA requires a device to operate. For picking a device, see [DOCA Core Device Discovery](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DeviceDiscovery>).

As device capabilities may change in the future, it is recommended to query each `doca_devinfo` for its capabilities relevant to RDMA operations, using `doca_rdma_cap_*(struct doca_devinfo *, …)` functions, and check whether the device is suitable for the required RDMA task types, using `doca_rdma_task_<task_type>_is_supported()`.

Both Bluefield-2 and Bluefield-3 devices are supported, any `doca_dev` is supported.

### Buffer Support
 
  
   
  
 

The DOCA RDMA library utilizes different buffer types, depending on the task and the buffer's purpose:

- Local mmap buffer
- Mmap from RDMA export buffer
- Mmap from PCIe export buffers This type of buffer can be used in an equivalent manner to local mmap buffers. 
- Linked list buffer

For task-specific information, refer to section "[DOCA RDMA | id (2.5.4 LTS)DOCARDMA Tasks](</doca/archive/2-5-4/doca-rdma#id-(2.5.4-LTS)DOCARDMA-Tasks>)".

### Exporting and Connecting RDMA
 
  
   
  
 

To establish the communication between the peers and allow the execution of different DOCA RDMA tasks, the RDMA instances must be connected.

This step should be executed after `doca_ctx_start()` is called and when the context is in Starting state.

Refer to [DOCA RDMA | id (2.5.4 LTS)DOCARDMA StateMachine](</doca/archive/2-5-4/doca-rdma#id-(2.5.4-LTS)DOCARDMA-StateMachine>) section for more information.

Connecting the RDMA instances is performed by exporting each RDMA instance to the remote side to a blob by using `doca_rdma_export()`, transferring the blob to the opposite side, out-of-band (OOB), and providing it as input to the `doca_rdma_connect()` function on that side.

All in all, the configuration flow should be as presented in the following image:

## Execution Phase
 
  
   
  
 

This section describes execution on CPU using [DOCA Core Progress Engine](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-ProgressEngine>) (PE). For additional execution environments refer to section "[DOCA RDMA | id (2.5.4 LTS)DOCARDMA AlternativeDatapathOptions](</doca/archive/2-5-4/doca-rdma#id-(2.5.4-LTS)DOCARDMA-AlternativeDatapathOptions>)".

### Tasks
 
  
   
  
 

DOCA RDMA exposes asynchronous tasks that leverage the DPU hardware according to the DOCA Core architecture. See [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>).

Most DOCA RDMA operations are not atomic and therefore it is imperative that the application handle synchronization appropriately. Moreover, successful completion of a write task, with or without immediate, does not guarantee the data to be written to the remote address.



All buffers used in DOCA RDMA tasks must remain valid until the task result is retrieved.

#### Receive Task
 
  
   
  
 

This task should be submitted prior to an expected submission of a send/send with immediate/write with immediate task on the remote side.

##### Configuration
 
  
   
  
 

| Description | API to Set the Configuration | API to Query Support | 
|---|---|---|
| Enable the task | `doca_rdma_task_receive_set_conf` | `doca_rdma_cap_task_receive_is_supported` | 
| Number of tasks | `doca_rdma_task_receive_set_conf` | – | 
| Destination buffer list length | `doca_rdma_task_receive_set_dst_buf_list_len` | `doca_rdma_cap_task_receive_get_max_dst_buf_list_len` | 

##### Input
 
  
   
  
 

Common input as described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>).

| Name | Description | Notes | 
|---|---|---|
| Destination buffer | Buffer pointing to a local memory address. The data is written to the buffer upon successful completion of the task. |  | 

##### Output
 
  
   
  
 

Common output as described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>).

| Name | Description | Notes | 
|---|---|---|
| Result length | The length of data received by the task | Valid only on successful completion of the task | 
| Result opcode | The opcode of the operation executed by the peer and received by the task | Valid only after task completion, irrespective of success | 
| Result immediate data | The immediate data received by the task |  | 

##### Task Successful Completion
 
  
   
  
 

After the task completes successfully, the following happens:

- The received data is copied to the tail segment extending the original data segment
- The data length is increased by the received data length

##### Task Failed Completion
 
  
   
  
 

If the task fails midway:

- If a fatal error occurs, the context is stopped, and the task should be freed by the user
- If a non-fatal error occurs, the task status is updated. Some buffers may be updated and some may remain unchanged.

##### Limitations
 
  
   
  
 

- The operation is not atomic and therefore it is imperative that the application handle synchronization appropriately
- The destination buffer must remain valid until task is completed
- The total length of the message must not exceed the device's `max_message_size` or 2GB (whichever is lower)
- The buffer list length must not exceed the `dst_buf_list_len` property of the DOCA RDMA receive task
- Other limitations are described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>)

#### Send Task
 
  
   
  
 

This task should be submitted to transfer a message to the remote side, and while the remote side is expecting a message and had submitted a receive task beforehand.

##### Configuration
 
  
   
  
 

| Description | API to Set the Configuration | API to Query Support | 
|---|---|---|
| Enable the task | `doca_rdma_task_send_set_conf` | `doca_rdma_cap_task_send_is_supported` | 
| Number of tasks | `doca_rdma_task_send_set_conf` | – | 
| Source buffer list length | `doca_rdma_set_max_send_buf_list_len`<sup>(a)</sup> | `doca_rdma_cap_get_max_send_buf_list_len` | 



<sup>(a)</sup> This configuration affects other tasks as well.

##### Input
 
  
   
  
 

Common input as described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>).

| Name | Description | Notes | 
|---|---|---|
| Source buffer | Buffer pointing to a local memory address and holds the data to be sent to the remote peer |  | 

##### Output
 
  
   
  
 

Common output as described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>).

##### Task Successful Completion
 
  
   
  
 

After the task completes successfully, the following happens:

- On successful completion of the task, the data in the source buffer will be sent to the remote side.
- It doesn't indicate that the data is received by the remote side.

##### Task Failed Completion
 
  
   
  
 

If the task fails midway:

- If a fatal error occurs, the context is stopped, and the task should be freed by the user
- If a non-fatal error occurs, the task status is updated

##### Limitations
 
  
   
  
 

- The operation is not atomic. Therefore, it is imperative for the application to handle synchronization appropriately.
- The source buffer must remain valid until the task completes
- The total length of the message must not exceed the `max_message_size` device capability or 2GB (whichever is lower)
- The buffer list length must not exceed the `max_send_buf_list_len` property of the DOCA RDMA instance
- Other limitations are described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>)

#### Send With Immediate Task
 
  
   
  
 

This task should be submitted to transfer a message to the remote side with immediate data (a 32-bit value sent to the remote side, out-of-band), and while the remote side is expecting a message and had submitted a receive task beforehand.

##### Configuration
 
  
   
  
 

| Description | API to Set the Configuration | API to Query Support | 
|---|---|---|
| Enable the task | `doca_rdma_task_send_imm_set_conf` | `doca_rdma_cap_task_send_imm_is_supported` | 
| Number of tasks | `doca_rdma_task_send_imm_set_conf` | – | 
| Source buffer list length | `doca_rdma_set_max_send_buf_list_len`<sup>(a)</sup> | `doca_rdma_cap_get_max_send_buf_list_len` | 



<sup>(a)</sup> This configuration affects other tasks as well.

##### Input
 
  
   
  
 

Common input as described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>).

| Name | Description | Notes | 
|---|---|---|
| Source buffer | Buffer pointing to a local memory address and holding the data to be sent to the remote peer |  | 
| Immediate data | 32-bit value sent to the remote side, out-of-band |  | 

##### Output
 
  
   
  
 

Common output as described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>).

##### Task Successful Completion
 
  
   
  
 

After the task completes successfully, the following happens:

- The data in the source buffer is sent to the remote side
- It does not indicate that the data is received by the remote side

##### Task Failed Completion
 
  
   
  
 

If the task fails midway:

- If a fatal error occurs, the context is stopped and the task should be freed by the user
- If a non-fatal error occurs, the task status is updated

##### Limitations
 
  
   
  
 

- The operation is not atomic. Therefore, it is imperative for the application to handle synchronization appropriately.
- The source buffer must remain valid until the task completes
- The total length of the message must not exceed the `max_message_size` device capability or 2GB (whichever is lower)
- The buffer list length must not exceed the `max_send_buf_list_len` property of the DOCA RDMA instance
- Other limitations are described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>)

#### Read Task
 
  
   
  
 

This task should be submitted when wishing to read data from remote memory (i.e., the memory on the remote side of the connection).

##### Configuration
 
  
   
  
 

| Description | API to Set the Configuration | API to Query Support | 
|---|---|---|
| Enable the task | `doca_rdma_task_read_set_conf` | `doca_rdma_cap_task_read_is_supported` | 
| Number of tasks | `doca_rdma_task_read_set_conf` | – | 
| Destination buffer list length | `doca_rdma_set_max_send_buf_list_len`<sup>(a)</sup> | `doca_rdma_cap_get_max_send_buf_list_len` | 



<sup>(a)</sup> This configuration affects other tasks as well.

##### Input
 
  
   
  
 

Common input as described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>).

| Name | Description | Notes | 
|---|---|---|
| Source buffer | Points to a remote memory address and holds the data to be read |  | 
| Destination buffer | Points to a local memory address. The data is written to the buffer upon successful completion of the task |  | 

##### Output
 
  
   
  
 

Common output as described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>).

| Name | Description | Notes | 
|---|---|---|
| Result length | The length of data read by the task | Valid only on successful completion of the task | 

##### Task Successful Completion
 
  
   
  
 

After the task completes successfully, the following happens:

- The read data is appended after the data section in the destination buffer, as it was prior to the task submission
- The data length is increased by the read data length

##### Task Failed Completion
 
  
   
  
 

If the task fails midway:

- If a fatal error occurs, the context is stopped and the task should be freed by the user
- If a non-fatal error occurs, the task status is updated. Some destination buffers may be updated and some may remain unchanged.

##### Limitations
 
  
   
  
 

- The operation is not atomic. Therefore, it is imperative for the application to handle synchronization appropriately.
- The task buffers must remain valid until task is completed
- The given source buffer length must not exceed the `max_message_size` device capability or 2GB (whichever is lower)
- The destination buffer list length must not exceed the `max_send_buf_list_len` property of the DOCA RDMA instance
- Other limitations are described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>)

#### Write Task
 
  
   
  
 

This task should be submitted when wishing to write data to remote memory (i.e., the memory on the remote side of the connection).

##### Configuration
 
  
   
  
 

| Description | API to Set the Configuration | API to Query Support | 
|---|---|---|
| Enable the task | `doca_rdma_task_write_set_conf` | `doca_rdma_cap_task_write_is_supported` | 
| Number of tasks | `doca_rdma_task_write_set_conf` | – | 
| Source buffer list length | `doca_rdma_set_max_send_buf_list_len`<sup>(a)</sup> | `doca_rdma_cap_get_max_send_buf_list_len` | 



<sup>(a)</sup> This configuration affects other tasks as well.

##### Input
 
  
   
  
 

Common input as described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>).

| Name | Description | Notes | 
|---|---|---|
| Source buffer | Buffer pointing to a local memory address and holding the data to be written to the remote peer. |  | 
| Destination buffer | Points to a remote memory address. The data is written to the buffer upon successful completion of the task. |  | 

##### Output
 
  
   
  
 

Common output as described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>).

##### Task Successful Completion
 
  
   
  
 

After the task completes successfully, the following happens:

- The written data is appended after the data section in the destination buffer, as it was prior to the task submission.
- The data length is increased by the written data length

##### Task Failed Completion
 
  
   
  
 

If the task fails midway:

- If a fatal error occurs, the context is stopped and the task should be freed by the user
- If a non-fatal error occurs, the task status is updated. Some destination buffers may be updated and some may remain unchanged.

##### Limitations
 
  
   
  
 

- The operation is not atomic. Therefore, it is imperative for the application to handle synchronization appropriately.
- The task buffers must remain valid until task is completed
- The total length of the given source buffer/list of buffers must be not exceed the `max_message_size` device capability or 2GB (whichever is lower)
- The source buffer list length must not exceed the `max_send_buf_list_len` property of the DOCA RDMA instance
- Other limitations are described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>)

#### Write With Immediate Task
 
  
   
  
 

This task should be submitted when wishing to write data to remote memory (i.e., the memory on the remote side of the connection).

##### Configuration
 
  
   
  
 

| Description | API to Set the Configuration | API to Query Support | 
|---|---|---|
| Enable the task | `doca_rdma_task_write_imm_set_conf` | `doca_rdma_cap_task_write_imm_is_supported` | 
| Number of tasks | `doca_rdma_task_write_imm_set_conf` | – | 
| Source buffer list length | `doca_rdma_set_max_send_buf_list_len`<sup>(a)</sup> | `doca_rdma_cap_get_max_send_buf_list_len` | 



<sup>(a)</sup> This configuration affects other tasks as well.

##### Input
 
  
   
  
 

Common input as described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>).

| Name | Description | Notes | 
|---|---|---|
| Source buffer | Buffer pointing to a local memory address and holding the data to be written to the remote peer |  | 
| Destination buffer | Points to a remote memory address. The data is written to the buffer upon successful completion of the task. |  | 
| Immediate data | 32-bit value sent to the remote side, out-of-band |  | 

##### Output
 
  
   
  
 

Common output as described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>).

##### Task Successful Completion
 
  
   
  
 

A write with immediate task succeeds only if the remote side is expecting the immediate and had submitted a receive task beforehand.

After the task completes successfully, the following happens:

- The written data is appended after the data section in the destination buffer, as it was prior to the task submission
- The data length is increased by the written data length.

##### Task Failed Completion
 
  
   
  
 

If the task fails midway:

- If a fatal error occurs, the context is stopped and the task should be freed by the user
- If a non-fatal error occurs, the task status is updated. Some destination buffers may be updated and some may remain unchanged.

##### Limitations
 
  
   
  
 

- The operation is not atomic. Therefore, it is imperative for the application to handle synchronization appropriately.
- The tasks buffers must remain valid until task is completed
- The total length of the given source buffer/list of buffers must be not exceed the `max_message_size` device capability or 2GB (whichever is lower)
- The source buffer list length must not exceed the `max_send_buf_list_len` property of the DOCA RDMA instance
- Other limitations are described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>)

#### Atomic Compare and Swap Task
 
  
   
  
 

This task should be submitted when wishing to execute an 8-byte atomic read-modify-write operation on the remote memory (i.e., the memory on the remote side of the connection), in which the remote value is retrieved and updated if it is equal to a given value.

##### Configuration
 
  
   
  
 

| Description | API to Set the Configuration | API to Query Support | 
|---|---|---|
| Enable the task | `doca_rdma_task_atomic_cmp_swp_set_conf` | `doca_rdma_cap_task_atomic_cmp_swp_is_supported` | 
| Number of tasks | `doca_rdma_task_atomic_cmp_swp_set_conf` | – | 

##### Input
 
  
   
  
 

Common input as described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>).

| Name | Description | Notes | 
|---|---|---|
| Destination buffer | Buffer pointing to a remote memory address |  | 
| Compare data | 64-bit value to be compared with the value in the destination buffer |  | 
| Swap data | 64-bit value to be swapped with the value in the destination buffer |  | 
| Result buffer | Buffer pointing to a local memory address. The original value of the destination buffer (before executing the atomic operation) is written to the buffer upon success. |  | 

##### Output
 
  
   
  
 

Common output as described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>).

##### Task Successful Completion
 
  
   
  
 

After the task completes successfully, the following happens:

- If the compared values are equal, the value in the destination is swapped with the 64-bit value in the task's swap data field (`swap_data`)
- If the compared values are not equal, the value in the destination value remains unchanged
- The original value of the destination buffer (before executing the atomic operation) is written to the result buffer

##### Task Failed Completion
 
  
   
  
 

If the task fails midway:

- The context is stopped and the task should be freed by the user

##### Limitations
 
  
   
  
 

- Task buffers must remain valid until task is completed
- Other limitations are described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>)

#### Atomic Fetch and Add Task
 
  
   
  
 

This task should be submitted when wishing to execute an 8-byte atomic read-modify-write operation on the remote memory (i.e., the memory on the remote side of the connection), in which the remote value is retrieved and increased by a given value.

##### Configuration
 
  
   
  
 

| Description | API to Set the Configuration | API to Query Support | 
|---|---|---|
| Enable the task | `doca_rdma_task_atomic_fetch_add_set_conf` | `doca_rdma_cap_task_atomic_fetch_add_is_supported` | 
| Number of tasks | `doca_rdma_task_atomic_fetch_add_set_conf` | – | 

##### Input
 
  
   
  
 

Common input as described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>).

| Name | Description | Notes | 
|---|---|---|
| Destination buffer | Buffer that points to a remote memory address |  | 
| Add data | 64-bit value to be added to the value in the destination buffer |  | 
| Result buffer | Buffer pointing to a local memory address. The original value of the destination buffer (before executing the atomic operation) is written to the buffer upon success. |  | 

##### Output
 
  
   
  
 

Common output as described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>).

##### Task Successful Completion
 
  
   
  
 

After the task completes successfully, the following happens:

- The value in the destination is increased by the 64-bit value in the task's add data field
- The original value of the destination buffer (before executing the atomic operation) is written to the result buffer

##### Task Failed Completion
 
  
   
  
 

If the task fails midway:

- The context is stopped and the task should be freed by the user

##### Limitations
 
  
   
  
 

- Task buffers must remain valid until task is completed
- Other limitations are described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>)

#### Get Remote Sync Event Task
 
  
   
  
 

This task should be submitted when wishing to get the value of a remote sync event.

##### Configuration
 
  
   
  
 

| Description | API to Set the Configuration | API to Query Support | 
|---|---|---|
| Enable the task | `doca_rdma_task_remote_net_sync_event_get_set_conf` | `doca_rdma_cap_task_remote_net_sync_event_get_is_supported` | 
| Number of tasks | `doca_rdma_task_remote_net_sync_event_get_set_conf` | – | 
| Destination buffer list length | `doca_rdma_set_max_send_buf_list_len`<sup>(a)</sup> | `doca_rdma_cap_get_max_send_buf_list_len` | 



<sup>(a)</sup> This configuration affects other tasks as well.

##### Input
 
  
   
  
 

Common input as described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>).

| Name | Description | Notes | 
|---|---|---|
| Sync Event | The remote DOCA Sync Event to get its value |  | 
| Destination buffer | Points to a local memory address. The Sync Event value is written to the buffer upon successful completion of the task. |  | 

##### Output
 
  
   
  
 

Common output as described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>).

| Name | Description | Notes | 
|---|---|---|
| Result length | The length of data received by the task | Valid only on successful completion of the task | 

##### Task Successful Completion
 
  
   
  
 

After the task completes successfully, the following happens:

- The remote Sync Event value is appended after the data section in the destination buffer, as it was prior to the task submission
- The data length is increased by the retrieved data length

##### Task Failed Completion
 
  
   
  
 

If the task fails midway:

- If a fatal error occurs, the context is stopped and the task should be freed by the user
- If a non-fatal error occurs, the task status is updated. Some destination buffers may be updated and some may remain unchanged.

##### Limitations
 
  
   
  
 

- The operation is not atomic. Therefore, it is imperative for the application to handle synchronization appropriately.
- The destination buffer must remain valid until the task is completed
- The destination buffer list length must not exceed the `max_send_buf_list_len` property of the DOCA RDMA instance
- Other limitations are described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>)

#### Set Remote Sync Event Task
 
  
   
  
 

This task should be submitted when wishing to set a remote sync event to a given value.

##### Configuration
 
  
   
  
 

| Description | API to Set the Configuration | API to Query Support | 
|---|---|---|
| Enable the task | `doca_rdma_task_remote_net_sync_event_notify_set_set_conf` | `doca_rdma_cap_task_remote_net_sync_event_notify_set_is_supported` | 
| Number of tasks | `doca_rdma_task_remote_net_sync_event_notify_set_set_conf` | – | 
| Source buffer list length | `doca_rdma_set_max_send_buf_list_len`<sup>(a)</sup> | `doca_rdma_cap_get_max_send_buf_list_len` | 



<sup>(a)</sup> This configuration affects other tasks as well.

##### Input
 
  
   
  
 

Common input as described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>).

| Name | Description | Notes | 
|---|---|---|
| Source buffer | Points to a local memory address from which the Sync Event should be retrieved |  | 
| Sync Event | The remote DOCA Sync Event to get its value |  | 

##### Output
 
  
   
  
 

Common output as described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>).

##### Task Successful Completion
 
  
   
  
 

After the task completes successfully, the following happens:

- The remote sync event value is set to the data in the source buffer

##### Task Failed Completion
 
  
   
  
 

If the task fails midway:

- If a fatal error occurs, the context is stopped and the task should be freed by the user
- If a non-fatal error occurs, the task status is updated and the Sync Event value is undefined

##### Limitations
 
  
   
  
 

- The operation is not atomic. Therefore, it is imperative for the application to handle synchronization appropriately.
- The source buffer must remain valid until the task completes
- The source buffer list length must not exceed the `max_send_buf_list_len` property of the DOCA RDMA instance
- Other limitations are described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>)

#### Add Remote Sync Event Task
 
  
   
  
 

This task should be submitted when wishing to atomically increase a remote sync event by a given value.

##### Configuration
 
  
   
  
 

| Description | API to Set the Configuration | API to Query Support | 
|---|---|---|
| Enable the task | `doca_rdma_task_emote_net_sync_event_notify_add_set_conf` | `doca_rdma_cap_task_emote_net_sync_event_notify_add_is_supported` | 
| Number of tasks | `doca_rdma_task_emote_net_sync_event_notify_add_set_conf` | – | 

##### Input
 
  
   
  
 

Common input as described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>).

| Name | Description | Notes | 
|---|---|---|
| Sync event | A remote Sync Event |  | 
| Add data | 64-bit value that is added to the Sync Event value |  | 
| Result buffer | Buffer pointing to a local memory address. The original Sync Event value of the destination buffer (before executing the atomic operation) is written to the buffer upon success. |  | 

##### Output
 
  
   
  
 

Common output as described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>).

##### Task Successful Completion
 
  
   
  
 

After the task completes successfully, the following happens:

- The value of the remote sync event is increased by the 64-bit value in the task's add data field
- The original value of the remote sync event (before executing the operation) is written to the result buffer

##### Task Failed Completion
 
  
   
  
 

If the task fails midway:

- The context is stopped and the task should be freed by the user

##### Limitations
 
  
   
  
 

- Result buffer must remain valid until task is completed
- Other limitations are described in [DOCA Core Task](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCATask>)

### Events
 
  
   
  
 

DOCA RDMA exposes asynchronous events to notify about changes that happen unexpectedly, according to DOCA Core architecture.

The only event DOCA RDMA exposes is common events as described in [DOCA Core Event](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCAEvent>).

## State Machine
 
  
   
  
 

The DOCA RDMA library follows the Context state machine as described in [DOCA Core Context State Machine](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-StateMachine>).

The following section describes how to move states and what is allowed in each state.

#### Idle
 
  
   
  
 

In this state, it is expected that application either:

- Destroys the context
- Starts the context

Allowed operations:

- Configuring the context according to section "[DOCA RDMA | id (2.5.4 LTS)DOCARDMA Configurations](</doca/archive/2-5-4/doca-rdma#id-(2.5.4-LTS)DOCARDMA-Configurations>)"
- Starting the context

It is possible to reach this state as follows:

| Previous State | Transition Action | 
|---|---|
| N/A | Create the context | 
| Running | Call stop after making sure all tasks have been freed | 
| Stopping | Call progress until all tasks are completed and freed | 

#### Starting
 
  
   
  
 

In this state, it is expected that application:

1. Connects the RDMA instances on both peers. Refer to section "[DOCA RDMA | id (2.5.4 LTS)DOCARDMA ExportingandConnectingRDMA](</doca/archive/2-5-4/doca-rdma#id-(2.5.4-LTS)DOCARDMA-ExportingandConnectingRDMA>)" for more information.
2. After connecting the RDMA instance, call progress to allow transition to next state

It is possible to reach this state as follows:

| Previous State | Transition Action | 
|---|---|
| Idle | Call start after configuration | 

#### Running
 
  
   
  
 

In this state, it is expected that application:

1. Allocates and submit tasks
2. Calls progress to complete tasks and/or receive events

Allowed operations:

- Allocating previously configured task
- Submitting an allocated task
- Calling stop

It is possible to reach this state as follows:

| Previous State | Transition Action | 
|---|---|
| Starting | Call progress until context state transitions | 

#### Stopping
 
  
   
  
 

In this state, it is expected that application:

1. Calls progress to complete all inflight tasks (tasks complete with failure)
2. Frees any completed tasks

Allowed operations:

- Call progress

It is possible to reach this state as follows:

| Previous State | Transition Action | 
|---|---|
| Running | Call progress and fatal error occurs | 
| Running | Call stop without freeing all tasks | 

## Alternative Datapath Options
 
  
   
  
 

DOCA RDMA allows data path to be run on DPA.

### DPA Datapath
 
  
   
  
 

DOCA offers the DOCA DPA library which provides a programming model for offloading communication-centric user code to run on the DPA processor on the BlueField DPU. For additional information on the [DOCA DPA library](/doca/archive/2-5-4/doca-dpa).

The user can choose to run an RDMA operation on the DPA datapath by configuring the DOCA RDMA context used by the application in the following manner:

1. Obtain DOCA CTX by calling `doca_rdma_as_ctx()`.
2. Set the datapath of the context to DPA by calling `doca_ctx_set_datapath_on_dpa()`. For additional information, refer to [DOCA Core Alternative Data Path](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-AlternativeDataPath>).
3. Finish context configuration and start the context by calling `doca_ctx_start()`. For additional information, refer to [DOCA Context](</doca/archive/2-5-4/doca-core#id-(2.5.4-LTS)DOCACore-DOCAContext>).

After configuring the datapath, the user can obtain a DPA handle for the DOCA RDMA context by calling `doca_rdma_get_dpa_handle()`.

The DPA handle can be used by the DOCA DPA library for datapath operations. For additional information, refer to [DOCA DPA Communication Model](</doca/archive/2-5-4/doca-dpa#id-(2.5.4-LTS)DOCADPA-CommunicationModel>).

## DOCA RDMA Samples
 
  
   
  
 

These samples illustrate how to use the DOCA RDMA API to execute DOCA RDMA operations.

### Running the Samples
 
  
   
  
 

1. Refer to the following documents: 
  - [NVIDIA DOCA Installation Guide for Linux](/doca/archive/2-5-4/nvidia-doca-installation-guide-for-linux) for details on how to install BlueField-related software.
  - [NVIDIA DOCA Troubleshooting Guide](/doca/archive/2-5-4/nvidia-doca-troubleshooting-guide) for any issue you may encounter with the installation, compilation, or execution of DOCA samples.
2. To build a given sample: ```
cd /opt/mellanox/doca/samples/doca_rdma/<sample_name>
meson /tmp/build
ninja -C /tmp/build
```
The binary `doca_<sample_name>` is created under `/tmp/build/`.
3. Sample usage: 
  - Common arguments Argument Description `-d`, `--device`
IB device name (optional). If not provided, a random IB device is assigned. `-ld`, `--local-descriptor-path`
Local descriptor file path that includes the local connection information to be copied to the remote program `-re`, `--remote-descriptor-path`
Remote descriptor file path that includes the remote connection information to be copied from the remote program `-m`, `--mmap-descriptor-path`
Remote descriptor file path that includes the remote mmap connection information to be copied from the remote program `-g`, `--gid-index`
GID index for DOCA RDMA (optional) 
  - Sample-specific arguments Sample Argument Description RDMA Read Responder `-r`, `--read-string`
String to read (optional). If not provided, "Hi DOCA RDMA!" is defined. RDMA Send RDMA Send Immediate `-s`, `--send-string`
RDMA Write Requester RDMA Write Immediate Requester `-w`, `--write-string`
4. For additional information per sample, use the `-h` option:
```
/tmp/build/<sample_name> -h
```

### Samples
 
  
   
  
 

Each sample presents a connection between two peers, transferring data from one to another, using a different RDMA operation in each sample. For more information on the available RDMA operations, refer to section "[DOCA RDMA | id (2.5.4 LTS)DOCARDMA Tasks](</doca/archive/2-5-4/doca-rdma#id-(2.5.4-LTS)DOCARDMA-Tasks>)".

Each sample is comprised of two executables, each running on a peer.

The samples can run on either DPU or host, as long as the chosen peers have a connection between them.

Prior to running the samples, ensure that the chosen devices, selected by the device name and the GID index, are set correctly and have a connection between one another. In each sample, it is the user's responsibility to copy the descriptors between the peers.

Most of the samples follow the following main basic steps:

1. Allocating resources: 
  1. Locating and opening a device. The chosen device is one that supports the task relevant for the sample. If the sample requires no task, any device may be chosen.
  2. Creating a local MMAP and configuring it (including setting the MMAP memory range and relevant permissions)
  3. Creating a DOCA Progress Engine (PE)
  4. Creating an RDMA instance and configuring it (including setting the relevant permissions)
  5. Connecting the RDMA context to the PE
2. Sample-specific configurations: 
  1. Configuring the tasks relevant to the sample, if any. Including: 
    1. Setting the number of tasks for each task type.
    2. Setting callback functions for each task type, with the following logic: 
      1. Successful completion callback: 
        1. Verifying the data received from the remote, if any, is valid.
        2. Printing the transferred data.
        3. Freeing the task and task-specific resources (such as source/destination buffers).
        4. Saving the result of the callback (If there was an error in steps a. and b., the relevant error value is saved).
        5. Decreasing the number of remaining tasks and stopping the context once it reaches 0.
      2. Failed completion callback: 
        1. Saving the task result.
        2. Freeing the task and task specific resources (such as source/destination buffers).
        3. Decreasing the number of remaining tasks and stopping the context once it reaches 0.
  2. Setting a state change callback function, with the following logic: 
    - Once the context moves to Starting state (can only be reached from Idle), export and connect the RDMA and, in some samples, export the local mmap. During this step, the user is responsible for copying the descriptors between the two peers. 
The descriptors are to be read and used only by the peer, using the relevant DOCA functions (the descriptors contain encoded data). 
    - Once the context moves to Running state (can only be reached from Starting state in RDMA samples): 
      - In some samples, only print a log and wait for the peer.
      - In others, prepare and submit a task: 
        1. If needed, create an mmap from the received exported mmap descriptor, passed from the peer.
        2. Request the required buffers from the buffer inventory.
        3. Allocate and initiate the required task, together with setting the number of remaining tasks parameter as the task's user data.
        4. Submit the task.
    - Once the context moves to Stopping state, print a relevant log.
    - Once the context moves to Idle state: 
      1. Print a relevant log.
      2. Send update that the main loop may be stopped.
3. Setting the program's resources as the context user data to be used in callbacks.
4. Creating a buffer inventory and starting it.
5. Starting the context. After starting the context, the state change callback function is called by the PE which executes the relevant steps. 
In a successful run, each section is executed in the order they are presented in section 2.b. 
6. Progressing the PE until the context returns to Idle state and the main loop may be stooped, either because of a successful run in which all tasks have been successfully completed, or due to a fatal error.
7. Cleaning up the resources.

#### RDMA Read
 
  
   
  
 

##### RDMA Read Requester
 
  
   
  
 

This sample illustrates how to read from a remote peer (the responder) using DOCA RDMA.

The sample logic is as presented in the [DOCA RDMA | id (2.5.4 LTS)DOCARDMA GeneralSampleSteps](</doca/archive/2-5-4/doca-rdma#id-(2.5.4-LTS)DOCARDMA-GeneralSampleSteps>), with attention to the following:

1. The permissions for the local mmap in this sample is set to local read and write.
2. A read task is configured for this sample.
3. In this sample, data is read from the peer, verified to be valid, and printed in the successful task completion callback.
4. The local mmap is not exported as the peer does not intend to access it.
5. To read from the peer, a remote mmap is created from the peer's exported mmap.

Reference:

- `/opt/mellanox/doca/samples/doca_rdma/rdma_read_requester/rdma_read_requester_sample.c`
- `/opt/mellanox/doca/samples/doca_rdma/rdma_read_requester/rdma_read_requester_main.c`
- `/opt/mellanox/doca/samples/doca_rdma/rdma_read_requester/meson.build`

##### RDMA Read Responder
 
  
   
  
 

This sample illustrates how to set up a remote peer for a DOCA RDMA read request.

The sample logic is as presented in the [DOCA RDMA | id (2.5.4 LTS)DOCARDMA GeneralSampleSteps](</doca/archive/2-5-4/doca-rdma#id-(2.5.4-LTS)DOCARDMA-GeneralSampleSteps>), with attention to the following:

1. The permissions for both the local mmap and the RDMA instance in this sample allow for RDMA read.
2. No tasks are configured for this sample, and thus no tasks are prepared and submitted, nor are there task completion callbacks.
3. The local mmap is exported to the remote memory to allow it to be used by the peer for RDMA read.
4. No remote mmap is created as there is no intention to access the remote memory in this sample.

Reference:

- `/opt/mellanox/doca/samples/doca_rdma/rdma_read_responder/rdma_read_responder_sample.c`
- `/opt/mellanox/doca/samples/doca_rdma/rdma_read_responder/rdma_read_responder_main.c`
- `/opt/mellanox/doca/samples/doca_rdma/rdma_read_responder/meson.build`

#### RDMA Write
 
  
   
  
 

##### RDMA Write Requester
 
  
   
  
 

This sample illustrates how to write to a remote peer (the responder) using DOCA RDMA.

The sample logic is as presented in the [DOCA RDMA | id (2.5.4 LTS)DOCARDMA GeneralSampleSteps](</doca/archive/2-5-4/doca-rdma#id-(2.5.4-LTS)DOCARDMA-GeneralSampleSteps>), with attention to the following:

1. The permissions for the local mmap in this sample is set to local read and write.
2. A write task is configured for this sample.
3. In this sample, data is written to the peer and printed in the successful task completion callback.
4. The local mmap is not exported as the peer does not intend to access it.
5. To write to the peer, a remote mmap is created from the peer's exported mmap.

Reference:

- `/opt/mellanox/doca/samples/doca_rdma/rdma_write_requester/rdma_write_requester_sample.c`
- `/opt/mellanox/doca/samples/doca_rdma/rdma_write_requester/rdma_write_requester_main.c`
- `/opt/mellanox/doca/samples/doca_rdma/rdma_write_requester/meson.build`

##### RDMA Write Responder
 
  
   
  
 

This sample illustrates how to set up a remote peer for a DOCA RDMA write request.

The sample logic is as presented in the [DOCA RDMA | id (2.5.4 LTS)DOCARDMA GeneralSampleSteps](</doca/archive/2-5-4/doca-rdma#id-(2.5.4-LTS)DOCARDMA-GeneralSampleSteps>), with attention to the following:

1. The permissions for both the local mmap and the RDMA instance in this sample allow for RDMA write.
2. No tasks are configured for this sample, and thus no tasks are prepared and submitted, nor are there task completion callbacks. In this sample, the data written to the memory of the responder is printed once the context state is changed to Running, using the state change callback. This is done only after receiving input from the user, indicating that the requester had finished writing.
3. The local mmap is exported to the remote memory to allow it to be used by the peer for RDMA write.
4. No remote mmap is created as there is no intention to access the remote memory in this sample.

Reference:

- `/opt/mellanox/doca/samples/doca_rdma/rdma_write_responder/rdma_write_responder_sample.c`
- `/opt/mellanox/doca/samples/doca_rdma/rdma_write_responder/rdma_write_responder_main.c`
- `/opt/mellanox/doca/samples/doca_rdma/rdma_write_responder/meson.build`

#### RDMA Write Immediate
 
  
   
  
 

##### RDMA Write Immediate Requester
 
  
   
  
 

This sample illustrates how to write to a remote peer (the responder) using DOCA RDMA along with a 32-bit immediate value which is sent OOB.

The sample logic is as presented in the [DOCA RDMA | id (2.5.4 LTS)DOCARDMA GeneralSampleSteps](</doca/archive/2-5-4/doca-rdma#id-(2.5.4-LTS)DOCARDMA-GeneralSampleSteps>), with attention to the following:

1. The permissions for the local mmap in this sample is set to local read and write.
2. A write with immediate task is configured for this sample.
3. In this sample, data is written to the peer and printed in the successful task completion callback.
4. The local mmap is not exported as the peer does not intend to access it.
5. To write to the peer, a remote mmap is created from the peer's exported mmap.

Reference:

- `/opt/mellanox/doca/samples/doca_rdma/rdma_write_immediate_requester/rdma_write_immediate_requester_sample.c`
- `/opt/mellanox/doca/samples/doca_rdma/rdma_write_immediate_requester/rdma_write_immediate_requester_main.c`
- `/opt/mellanox/doca/samples/doca_rdma/rdma_write_immediate_requester/meson.build`

##### RDMA Write Immediate Responder
 
  
   
  
 

This sample illustrates how the set up a remote peer for a DOCA RDMA write request whilst receiving a 32-bit immediate value from the peer's OOB.

The sample logic is as presented in the [DOCA RDMA | id (2.5.4 LTS)DOCARDMA GeneralSampleSteps](</doca/archive/2-5-4/doca-rdma#id-(2.5.4-LTS)DOCARDMA-GeneralSampleSteps>), with attention to the following:

1. The permissions for both the local mmap and the RDMA instance in this sample allow for RDMA write.
2. A receive task is configured for this sample to retrieve the immediate value. Failing to submit a receive task prior to the write with immediate task results in a fatal failure.
3. In this sample, the successful task completion callback also includes: 
  1. Checking the result opcode, to verify that the receive task has completed after receiving a write with immediate request.
  2. Verifying the data written to the memory of the responder is valid and printing it, along with the immediate data received.
4. The local mmap is exported to the remote memory, to allow it to be used by the peer for RDMA write.
5. No remote mmap is created as there is no intention to access the remote memory in this sample.

Reference:

- `/opt/mellanox/doca/samples/doca_rdma/rdma_write_immediate_responder/rdma_write_immediate_responder_sample.c`
- `/opt/mellanox/doca/samples/doca_rdma/rdma_write_immediate_responder/rdma_write_immediate_responder_main.c`
- `/opt/mellanox/doca/samples/doca_rdma/rdma_write_immediate_responder/meson.build`

#### RDMA Send and Receive
 
  
   
  
 

##### RDMA Send
 
  
   
  
 

This sample illustrates how to send a message to a remote peer using DOCA RDMA.

The sample logic is as presented in the [DOCA RDMA | id (2.5.4 LTS)DOCARDMA GeneralSampleSteps](</doca/archive/2-5-4/doca-rdma#id-(2.5.4-LTS)DOCARDMA-GeneralSampleSteps>), with attention to the following:

1. The permissions for the local mmap in this sample is set to local read and write.
2. A send task is configured for this sample.
3. In this sample, the data sent is printed during the task preparation, not in the successful task completion callback.
4. The local mmap is not exported as the peer does not intend to access it.
5. No remote mmap is created as there is no intention to access the remote memory in this sample.

Reference:

- `/opt/mellanox/doca/samples/doca_rdma/rdma_send/rdma_send_sample.c`
- `/opt/mellanox/doca/samples/doca_rdma/rdma_send/rdma_send_main.c`
- `/opt/mellanox/doca/samples/doca_rdma/rdma_send/meson.build`

##### RDMA Receive
 
  
   
  
 

This sample illustrates how the remote peer can receive a message sent by the peer (the sender).

The sample logic is as presented in the [DOCA RDMA | id (2.5.4 LTS)DOCARDMA GeneralSampleSteps](</doca/archive/2-5-4/doca-rdma#id-(2.5.4-LTS)DOCARDMA-GeneralSampleSteps>), with attention to the following:

1. The permissions for the local mmap in this sample is set to local read and write.
2. A receive task is configured for this sample to retrieve the sent data. Failing to submit a receive task prior to the send task results in a fatal failure.
3. In this sample, data is received from the peer verified to be valid and printed in the successful task completion callback.
4. The local mmap is not exported as the peer does not intend to access it.
5. No remote mmap is created as there is no intention to access the remote memory in this sample.

Reference:

- `/opt/mellanox/doca/samples/doca_rdma/rdma_receive/rdma_receive_sample.c`
- `/opt/mellanox/doca/samples/doca_rdma/rdma_receive/rdma_receive_main.c`
- `/opt/mellanox/doca/samples/doca_rdma/rdma_receive/meson.build`

#### RDMA Send and Receive with Immediate
 
  
   
  
 

##### RDMA Send with Immediate
 
  
   
  
 

This sample illustrates how to send a message to a remote peer using DOCA RDMA along with a 32-bit immediate value which is sent OOB.

The sample logic is as presented in the [DOCA RDMA | id (2.5.4 LTS)DOCARDMA GeneralSampleSteps](</doca/archive/2-5-4/doca-rdma#id-(2.5.4-LTS)DOCARDMA-GeneralSampleSteps>), with attention to the following:

1. The permissions for the local mmap in this sample is set to local read and write.
2. A send with immediate task is configured for this sample.
3. In this sample, the data sent is printed during the task preparation, not in the successful task completion callback.
4. The local mmap is not exported as the peer does not intend to access it.
5. No remote mmap is created as there is no intention to access the remote memory in this sample.

Reference:

- `/opt/mellanox/doca/samples/doca_rdma/rdma_send_immediate/rdma_send_immediate_sample.c`
- `/opt/mellanox/doca/samples/doca_rdma/rdma_send_immediate/rdma_send_immediate_main.c`
- `/opt/mellanox/doca/samples/doca_rdma/rdma_send_immediate/meson.build`

##### RDMA Receive with Immediate
 
  
   
  
 

This sample illustrates how the remote peer can receive a message sent by the peer (the sender) while also receiving a 32-bit immediate value from the peer's OOB.

The sample logic is as presented in the [DOCA RDMA | id (2.5.4 LTS)DOCARDMA GeneralSampleSteps](</doca/archive/2-5-4/doca-rdma#id-(2.5.4-LTS)DOCARDMA-GeneralSampleSteps>), with attention to the following:

1. The permissions for the local mmap in this sample is set to local read and write.
2. A receive task is configured for this sample to retrieve the sent data and the immediate value. Failing to submit a receive task prior to the send with immediate task results in a fatal failure.
3. In this sample, the successful task completion callback also includes: 
  1. Checking the result opcode, to verify that the receive task has completed after receiving a sent message with an immediate.
  2. Verifying the data received from the peer is valid and printing it along with the immediate data received.
4. In this sample, data is received from the peer verified to be valid and printed in the successful task completion callback.
5. The local mmap is not exported as the peer does not intend to access it.
6. No remote mmap is created as there is no intention to access the remote memory in this sample.

Reference:

- `/opt/mellanox/doca/samples/doca_rdma/rdma_receive_immediate/rdma_receive_immediate_sample.c`
- `/opt/mellanox/doca/samples/doca_rdma/rdma_receive_immediate/rdma_receive_immediate_main.c`
- `/opt/mellanox/doca/samples/doca_rdma/rdma_receive_immediate/meson.build`

#### RDMA Remote Sync Event
 
  
   
  
 

This sample illustrates how to synchronize between local sync event and a remote sync event DOCA RDMA.

##### RDMA Remote Sync Event Requester
 
  
   
  
 

The sample logic includes:

1. Creating a remote sync event from the peer's exported sync event.
2. Configuring "sync event notify set" and "sync event get" tasks.
3. Notifying the sync event from the remote peer side.
4. Reading the sync event from the remote peer until signaled by the local peer.
5. Notifying for completion by setting the sync event from the remote side.

Reference:

- `/opt/mellanox/doca/samples/doca_rdma/rdma_sync_event_requester/rdma_sync_event_requester_sample.c`
- `/opt/mellanox/doca/samples/doca_rdma/rdma_sync_event_requester/rdma_sync_event_requester_main.c`
- `/opt/mellanox/doca/samples/doca_rdma/rdma_sync_event_requester/meson.build`

##### RDMA Remote Sync Event Responder
 
  
   
  
 

The sample logic includes:

1. Creating a local sync event.
2. Exporting the local sync event to the remote memory to allow the peer to create a remote handle.
3. Waiting for the sync event to be signaled from the remote side.
4. Notifying the sync event from the local side.
5. On the local side, waiting for completion notification from the remote side.

Reference:

- `/opt/mellanox/doca/samples/doca_rdma/rdma_sync_event_responder/rdma_sync_event_responder_sample.c`
- `/opt/mellanox/doca/samples/doca_rdma/rdma_sync_event_responder/rdma_sync_event_responder_main.c`
- `/opt/mellanox/doca/samples/doca_rdma/rdma_sync_event_responder/meson.build`

Last updated: