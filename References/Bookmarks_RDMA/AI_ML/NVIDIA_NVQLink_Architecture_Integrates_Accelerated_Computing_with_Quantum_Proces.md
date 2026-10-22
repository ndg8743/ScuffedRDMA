# NVIDIA NVQLink Architecture Integrates Accelerated Computing with Quantum Processors | NVIDIA Technical Blog

- **Source:** https://developer.nvidia.com/blog/nvidia-nvqlink-architecture-integrates-accelerated-computing-with-quantum-processors/
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

[Quantum computing](https://www.nvidia.com/en-us/glossary/quantum-computing/) is entering an era where progress will be driven by the integration of accelerated computing with quantum processors. The hardware that controls and measures a quantum processing unit (QPU) faces demanding computational requirements—from real-time calibration to quantum error-correction (QEC) decoding. Useful quantum applications will require QEC and calibration at scales only addressable by tightly integrating the state of the art in accelerated computing.

[NVIDIA NVQLink](https://www.nvidia.com/en-us/solutions/quantum-computing/nvqlink/) brings accelerated computing into the quantum stack, enabling today’s GPU superchips to support the online workloads of the QPU itself.

NVQLink is an open platform architecture that tightly couples a conventional supercomputing host with a quantum system controller (QSC). It is designed to work with existing control systems already used across the industry—including superconducting, trapped-ion, photonic, or spin-based—and to do so without constraining how QPU and controller builders innovate. The goal is simple but transformative: to make the supercomputing node a native part of the QPU environment, accelerating the ability of quantum hardware to compute.

## NVQLink system and software architecture

The NVQLink architecture defines a machine model known as the Logical QPU (Figure 1). It’s a complete system, including the physical qubits, their control and readout electronics, and the compute resources needed for online workloads such as QEC decoding and continuous calibration. Together these elements constitute a machine model of the logical QPU: a real-time host and quantum system controller connected by a low-latency, scalable real-time interconnect joining them into a network capable of handling the runtime workloads of a fault tolerant quantum computer*.*

This hybrid system combines the world of quantum coherent control with that of state-of-the-art conventional supercomputing. On one side sits the real-time host, an accelerated computing node programmable in C++ or Python through the [NVIDIA CUDA-Q](https://nvidia.github.io/cuda-quantum/latest/index.html) platform. On the other side is a third-party quantum system controller (QSC), which manages the low-level analog and digital control of qubits through an array of FPGAs or RFSoCs, known as pulse processing units (PPUs). Connecting these is the real-time interconnect, a low-latency, high-bandwidth network that enables the compute to run within the operating time domain of the quantum hardware.

The real-time interconnect can be implemented using RDMA over Ethernet using an open source FPGA core (NI widget indicating “network interface”) in the Controller, with the CUDA-Q runtime, enabling a real-time callback (fn widget indicating “function” call) to exchange compiled data across this connection at latency \<4 microseconds.

To the application programmer, the Logical QPU, is a new type of heterogeneous device in the supercomputing environment supported by CUDA and CUDA-Q. This arrangement provides QPU developers with the benefit that all CPUs, GPUs, and PPUs required in a logical QPU are targetable by the same type of heterogeneous programming model.

Developers can write a single program, using standard C++ or Python syntax, that expresses both quantum kernels and real-time callbacks to the real-time host. New intrinsic `cudaq::device_call` functionality within CUDA-Q allows quantum kernels to invoke GPU or CPU functions directly and receive results within microseconds. This design brings the familiar CUDA model of heterogeneous programming into the quantum domain, enabling developers to move beyond multi-language, REST-based control stacks toward native, high-performance integration.

The following code provides an example of a real-time QEC memory experiment implemented with a single quantum kernel containing a `cudaq::device_call`.

```
__qpu__ void adaptive_qec_kernel(cudaq::qvector<>& data_qubits, 
                                 cudaq::qvector<>& ancilla_qubits,
                                 int cycles) {
  for(int = 0; i < cycles; ++i){
    // Stabilizer circuits here
    ...
    // Execute syndrome extraction measurements
    auto syndrome = mz(ancilla_qubits);
    // Real-time streaming to dedicated GPU  
    cudaq::device_call(/*gpu_id=*/1, 
                     surface_code_enqueue, 
                     syndrome);
    // Repeat 
  }
  // Real-time decode on dedicated GPU  
  auto correction = cudaq::device_call(/*gpu_id=*/1, 
                                       surface_code_decode);
  
  // Apply corrections physically if desired (typically tracked in software)
  if (correction.x_errors.any()) 
    apply_pauli_x_corrections(data_qubits, correction.x_errors);
  if (correction.z_errors.any())
    apply_pauli_z_corrections(data_qubits, correction.z_errors);
}
```
The underlying runtime uses static polymorphism and trait-based composition to eliminate overhead in critical paths. Each device—GPU, CPU, or FPGA—registers its callable functions and data buffers with the runtime, enabling seamless data marshaling and minimal latency.

Through these innovations, NVQLink transforms the QPU from a peripheral device accessed over a slow API into a first-class peer within a supercomputer. It enables quantum and traditional computation to co-exist in a single, latency-bounded system—a true hybrid accelerated quantum supercomputer.

## Ultrafast networking with standard technology

The real-time interconnect is a critical enabler of NVQLink performance. It’s implemented using RDMA over Converged Ethernet (RoCE). This approach leverages universally available Ethernet infrastructure to achieve state-of-the-art performance.

This has been demonstrated with NVQLink using commercially available components: an RFSoC FPGA connected to an Arm-based host equipped with an [NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation Edition](https://www.nvidia.com/en-us/products/workstations/professional-desktop-gpus/rtx-pro-6000-max-q/) GPU and an [NVIDIA ConnectX-7](https://marketplace.nvidia.com/en-us/enterprise/networking/connectx7/) network interface card (Figure 2). The FPGA and host use the [NVIDIA Holoscan Sensor Bridge (HSB)](https://www.nvidia.com/en-us/technologies/holoscan-sensor-bridge/) and the accompanying [NVIDIA Holoscan SDK (HSDK)](https://developer.nvidia.com/holoscan-sdk), to deliver the data on the FPGA to the software on the host, and vice versa.

The FPGA generates RoCE packets time stamped by a precision time protocol (PTP) counter, which the GPU loops back through a persistent CUDA kernel using DOCA GPUNetIO. The end-to-end latency measured was 3.84 microseconds (mean), with standard deviation 0.035 microseconds and a maximum of 3.96 microseconds over 1,000 samples. This level of latency and jitter are sufficiently low for current and future fault-tolerant QEC decoding and other real-time control tasks.

This simple networking recipe—using an open, lightweight RoCE core on the FPGA side and standard NVIDIA networking hardware on the host—makes NVQLink immediately practical for QPU and QSC builders using the same technology widely deployed in supercomputing centers. Because the FPGA IP is freely available and requires no disclosure of proprietary firmware, builders can adopt the interface unilaterally. This preserves their intellectual property and provides access to a proven, high-performance transport layer supported by NVIDIA.

Importantly, this approach scales. Modern Ethernet equipment within supercomputing centers already supports 400 Gbit/s links and a switch radix of 256 ports. As RDMA technology continues to evolve, driven by large AI and supercomputing deployments, the same innovations will directly benefit quantum systems integrated through NVQLink.

## Real-time decoding with Quantinuum Helios and NVIDIA NVQLink

NVQLink is already being adopted by leaders in the quantum computing ecosystem. QPU builder [Quantinuum](https://www.quantinuum.com/) announced that their future processors will deploy using NVQLink, and their recently announced [Helios QPU](https://www.quantinuum.com/blog/introducing-helios-the-most-accurate-quantum-computer-in-the-world) is deployed with an [NVIDIA GH200 Grace Hopper](https://www.nvidia.com/en-us/data-center/grace-hopper-superchip/) as real-time host. The GH200 server is used for real-time quantum error correction with syndrome decoders from the [CUDA-Q QEC](https://nvidia.github.io/cudaqx/components/qec/introduction.html#) library.

The CUDA-Q [nv-qldpc-decoder](https://nvidia.github.io/cudaqx/components/qec/introduction.html#quantum-low-density-parity-check-decoder) can exploit the all-to-all connectivity of Helios, enabling research into quantum low-density parity check (qLDPC) codes. This shows promise in lowering the overheads of fault-tolerant quantum computing. Helios is a machine capable of running any qLDPC code, and the NVIDIA decoder can decode any qLDPC code for Helios in real time.

The NVIDIA team collaborated with Quantinuum to demonstrate this capability. We decoded a high-rate qLDPC code called Bring’s code, which encodes eight logical qubits into 30 physical qubits. The decoding algorithm for this experiment was BP+OSD (belief propagation plus ordered statistics decoding), which ran with a 67 microsecond median decoding time, enabling error correction with feed-forward corrections in real time.

We used this to build an 8-logical-qubit logical memory. After running three rounds of quantum error correction on Helios, the eight logical qubits exhibited a 0.925±0.38% error rate, a 5.4x improvement over the 4.95±0.67% prior to decoding.

This very early success shows the potential of NVQLink to accelerate the emergence of fault tolerant quantum computing.

## Get started with NVQLink 

NVIDIA NVQLink enables faster experimentation and tighter feedback in designing, building, and deploying more scalable quantum systems. Whether you’re a QPU builder seeking an open, standards-based interface, a researcher developing next-generation decoding and calibration algorithms, or a QPU operator writing next-generation applications, NVQLink provides a foundation to accelerate your roadmap.

NVQLink is an open platform built in collaboration with partners across the quantum computing industry.

Ready to get started?

- Explore the full technical details in [Platform Architecture for Tight Coupling of High-Performance Computing with Quantum Processors](https://arxiv.org/abs/2510.25213).
- Experiment with the capabilities through the [CUDA-Q open-source SDK](https://nvidia.github.io/cuda-quantum/latest/) and [CUDA-Q QEC](https://nvidia.github.io/cudaqx/components/qec/introduction.html#) library.
- [Learn more and connect with the team](https://www.nvidia.com/en-us/solutions/quantum-computing/nvqlink/).