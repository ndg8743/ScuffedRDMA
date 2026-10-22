# Nautilus AeroKernel

- **Source:** https://users.eecs.northwestern.edu/~kch479/nautilus/#:~:text=Nautilus%20is%20the%20first%20example,project%20and%20the%20Hobbes%20project.
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > Papers > Papers)
- **Retrieved:** 2026-10-22


---

Nautilus is the first example of an *AeroKernel* that is available for public use and development. AeroKernels are extermely 
lightweight OS kernels that are intended to support the Hybrid Runtime (HRT) model, 
in which a parallel runtime enjoys full access to the entire machine. An AeroKernel like Nautilus provides a minimal set of functionality to the runtime. Nautilus currently runs
on modern x64 HPC-class hardware and on the Intel Xeon Phi accelerator. Some features of Nautilus include the following:

- Support for large-scale, many-core architectures
- NUMA-aware memory subsystem
- Multiboot2 compliant
- Minimal ACPI and SFI support
- Fast, lightweight synchronization and threading facilities (see the publications below)
- Configurable to run in x64, Xeon Phi, and HVM/HRT environments
- An extremely light-weight event subsystem called *Nemo*

Nautilus is part of the [V3VEE project](http://v3vee.org) and the [Hobbes project](http://xstack.sandia.gov/hobbes).

# People

# Publications

- K. Hale, C. Hetland, and P. Dinda. "Automatic Hybridization of Runtime Systems," *Proceedings of the 25<sup>th</sup> ACM International Symposium on High Performance
Parallel and Distributed Computing (HPDC '16)*, June, 2016. *To Appear*.
- K. Hale and P. Dinda. "Enabling Hybrid Parallel Runtimes Through Kernel and Virtualization Support," *Proceedings of the 12<sup>th</sup> ACM SIGPLAN/SIGOPS International 
Conference on Virtual Execution Envrionments (VEE '16)*, April, 2016. [\[pdf\]](http://pdinda.org/Papers/vee16.pdf) [\[slides\]](http://users.eecs.northwestern.edu/~kch479/docs/vee16-talk.pdf)
- K. Hale and P. Dinda. "Pushing Software Events to the Hardware Limit," Technical Report NU-EECS-16-02, March, 2016. [\[pdf\]](http://www.mccormick.northwestern.edu/eecs/documents/tech-reports/2016/2016-2-pushing-software-events-to-the-hardware-limit.pdf)
- K. Hale and P. Dinda. "Automatic Hybridization of Runtime Systems," Technical Report NU-EECS-16-03, March, 2016. [\[pdf\]](http://www.mccormick.northwestern.edu/eecs/documents/tech-reports/2016/2016-3-automatic-hybridization-of-runtime-systems.pdf)
- K. Hale and P. Dinda. "A Case for Transforming Parallel Runtimes into Operating System Kernels," *Proceedings of the 24<sup>th</sup> ACM International Symposium
on High-performance Parallel and Distributed Computing (HPDC '15)*, June, 2015. [\[pdf\]](http://users.eecs.northwestern.edu/~kch479/docs/nautilus.pdf)  [\[slides\]](http://users.eecs.northwestern.edu/~kch479/docs/kch-hpdc2015pres.pdf)
- K. Hale and P. Dinda. "Details of the Case for Transforming Parallel Runtimes into Operating System Kernels," Technical Report NU-EECS-15-01, April, 2014. [\[pdf\]](http://www.mccormick.northwestern.edu/eecs/documents/tech-reports/2015/details-of-the-case-for-transforming-parallel-runtime-systems-into-operating-system-kernels.pdf)

# Software

You can view the up-to-date source code for Nautilus and download it at our [public git repository](https://bitbucket.org/kchale/nautilus).

You can also clone Nautilus directly:

git clone git@bitbucket.org:kchale/nautilus.git

For instructions on how to configure, compile, and use Nautilus, please see the README in the top-level directory of the source tree.

## philix

Philix is a command-line tool for booting custom, 3<sup>rd</sup> party OSes on the Intel Xeon Phi. We developed it during our work with Nautilus. Find out more [here](http://philix.halek.co).
Nautilus was made possible by support from the United States National Science
Foundation (NSF) via grants CCF-1533560 and CNS-0709168, the Department of
Energy (DOE) via grant DE-SC0005343, and Sandia National Laboratories through
the Hobbes Project, which is funded by the 2013 Exascale Operating and Runtime
Systems Program under the Office of Advanced Scientific Computing Research in
the DOE Office of Science. Sandia National Laboratories is a multi-program
laboratory managed and operated by Sandia Corporation, a wholly owned
subsidiary of Lockheed Martin Corporation, for the U.S. Department of Energy’s
National Nuclear Security Administration under contract DE-AC04-94AL85000.