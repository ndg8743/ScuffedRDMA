# PCI Express Device Lending

- **Source:** https://dolphinics.com/products/pcie_smart_io_device_lending.html
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA)
- **Retrieved:** 2026-10-22


---

# PCIe Device Lending - Composable Infrastructure made easy

Dolphin eXpressWare SmartIO software offers a flexible way to enable PCIe IO devices (NVMes, FPGAs, GPUs etc) to be accessed within a PCIe Network. Devices can be borrowed over the PCIe network without any software overhead at the performance of PCI Express. Device Lending is a simple way to reconfigure systems and reallocate resources. GPUs, NVMe drives or FPGAs can be added or removed without having to be physically installed in a particular system on the network. The result is a flexible simple method of creating a pool of devices that maximizes usage.

Since this solution uses standard PCIe, it don’t add any software overhead to the communication path. Standard PCIe transactions are used between the systems. Dolphins eXpressWare software manages the connection and is responsible for setting up the PCIe Non Transparent Bridge (NTB) mappings.

Two types of functions are implemented with device lending. These are the lending function and the borrowing function:

- Lending involves making devices available on the network for temporary access. These PCIe devices are still located within the lending system.
- The borrowing function can lookup available devices. Devices can then be temporarily borrowed as long as required. When use of the device is completed, the device can be released and borrowed by other systems on the network or returned for local use.

The Dolphin Device Lending software enables this process to be controlled using a set of command line tools and options. These tools can be used directly or integrated into any other higher level resource management system. The device lending software is very flexible and does not require any boot order or power on sequencing. PCIe devices borrowed from a remote system can be used as if they were local devices until they are given back. The Device Lending software does not require any changes to standard device drivers or to the Linux kernel.

Device lending also enables a SR-IOV device to be shared as a MR-IOV device. SR-IOV functions can be borrowed by any system in the PCIe Network. Thereby enabling the device to be shared by multiple systems. This maximizes the use of SR-IOV devices such as Ethernet cards, GPUs and NVMes.

## Performance

As there is no software involved in data transfers to a remote device, the performance accessing a remote device will be very similar to a local device. If the transparent driver needs to re-map a DMA window, the re-map will be performed locally at the borrowing side, very similar to what happens in a virtualized system. The actual performance is system and device dependent.

### Host to Device transfers

The chart below shows the host to device performance between local and remote GPUs.


### Device to Device transfers

The chart below shows the device to device performance between local and remote GPUs.

Test setup:

- Dolphin MXH530 PCIe 5.0 adapters in direct x16 topology
- Dolphin eXpressWare Driver version 5.24
- Unmodified nvbandwidth v0.8, default buffer size (512 MB), Nvidia CUDA 12.8, Nvidia Open Driver 570.172.08
- Nvidia RTX PRO 4500 Blackwell GPUs
- AMD EPYC 9015 8-core processors CPUs
- Samsung M321R2GA3EB2-CCP DDR5 RAM
- Ubuntu 24.04.3 LTS with kernel 6.8.0-79-generic

## Who will benefit from Device Lending ?

Device Lending can be used in may configurations and use cases where you want to use a PCIe device that is installed in another PC.

- Dynamic reallocation of FPGAs and NVMe drives
- Flexible use of GPUs
- Sharing of SR-IOV devices

## How does it work ?

The implementation is composed of two parts, the lending side and the borrowing side. We rely on a PCIe NTB implementation to setup a flexible address space between systems. The way Device Lending works, the lending side software binds itself as a driver for the targeted PCIe devices. This provides exclusive access to the device, allowing the Device Lending software to access the device’s configuration space while preventing other drivers on the host from interfering.

The Device Lending software then notifies the borrowing side of all available devices. When the user requests an available device, the borrowing side Device Lending software communicates with the lending side software in order to set up the device’s configuration space. The lending side adds the targeted device into a IOMMU domain, isolating the device from the rest of the system and other devices.

The borrowing side then sets up the necessary MMIO mappings using the NTB and tells the lending side to set up the reverse mappings for device to RAM DMA as well as MSI mappings. Following this, the borrowing side then injects the device into the Linux PCIe subsystem and signals a hot-add event. Linux will probe the device, set it up and load the device driver.

The device driver is now able to communicate with the device using MMIO access. Whenever the device driver sets up new DMA mappings using the Linux DMA-API, the borrowing side Device Lending software intercepts these calls and dynamically sets up and tear down the necessary IOMMU mappings. This allows the borrowing side device driver to transfer data to the remote device with no additional software overhead.

## Availability

The Device Lending software is available for Dolphin's [MXH914,](MXH914.html) [MXH918](MXH918.html), [MXH930](/products/MXH930.html), [MXH940](/products/MXH940.html), [MXH950](/products/MXH950.html), [MXH530](/products/MXH530.html) and [MXH570](/products/MXH570.html) NTB enabled cards. Initially, only for Linux. The software can also be licensed to OEMs having a compliant PCIe network (Cables or backplanes).

The Device Lending software is included with the eXpressWare release 5.5.0 and newer. Please consult the [SmartIO documentation](https://docs.dolphinics.com/smartio/introduction.html) for more information on Device Lending and system requirements.