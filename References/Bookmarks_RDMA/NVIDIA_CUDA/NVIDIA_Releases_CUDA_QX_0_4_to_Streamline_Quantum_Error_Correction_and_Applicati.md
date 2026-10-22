# NVIDIA Releases CUDA-QX 0.4 to Streamline Quantum Error Correction and Application Development - Quantum Computing Report

- **Source:** https://quantumcomputingreport.com/nvidia-releases-cuda-qx-0-4-to-streamline-quantum-error-correction-and-application-development/
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > NVIDIA & CUDA)
- **Retrieved:** 2026-10-22


---

[NVIDIA](https://developer.nvidia.com/) has released [CUDA-QX 0.4](https://github.com/NVIDIA/cudaqx/releases/tag/0.4.0), a new version of its software development kit designed to streamline quantum error correction (QEC) and application development. The release provides researchers and algorithm developers with tools for creating end-to-end QEC workflows, from defining and simulating codes to configuring decoders and deploying them with physical QPUs.

The new release introduces the ability to automatically generate a detector error model (DEM) from a specified QEC circuit and noise model, which is then used for circuit sampling and syndrome decoding. CUDA-QX 0.4 also adds an open-source, GPU-accelerated tensor network decoder, which achieves theoretical optimum decoding accuracy by exploiting the [cuQuantum](https://developer.nvidia.com/cuquantum-sdk) libraries. Additionally, the release adds an implementation of the Generative Quantum Eigensolver (GQE), a hybrid algorithm for finding eigenstates of quantum Hamiltonians using generative AI models.

Other improvements in CUDA-QX 0.4 include enhanced flexibility and monitoring capabilities for the GPU-accelerated Belief Propagation + Ordered Statistics Decoding (BP+OSD) implementation. These enhancements provide features such as adaptive convergence monitoring and algorithm selection. The release addresses the focus of QPU builders and algorithm developers on QEC as a core challenge. By providing tools for defining, simulating, and decoding QEC codes, NVIDIA aims to accelerate the path toward building larger-scale, commercially viable quantum computers.

Read more about this release on the NVIDIA Developer Blog [here](https://developer.nvidia.com/blog/streamlining-quantum-error-correction-and-application-development-with-cuda-qx-0-4/). For complete information on CUDA-Q QEC’s BP+OSD decoder, see the latest Python API documentation [here](https://nvidia.github.io/cudaqx/api/qec/python_api.html#cudaq_qec.nv_qldpc_decoder), C++ API documentation [here](https://nvidia.github.io/cudaqx/api/qec/cpp_api.html#nvidia-qldpc-decoder), and an example [here](https://nvidia.github.io/cudaqx/examples_rst/qec/decoders.html#getting-started-with-the-nvidia-qldpc-decoder). For complete details on the Solvers implementation of GQE, see the Python API documentation [here](https://nvidia.github.io/cudaqx/api/solvers/python_api.html#cudaq_solvers.gqe) and examples [here](https://nvidia.github.io/cudaqx/examples_rst/solvers/gqe.html).