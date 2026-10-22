# ARCHER2: OpenFabrics (OFI) vs UCX transport performance on HPE Cray EX

- **Source:** https://github.com/ARCHER2-HPC/performance_ofi-ucx
- **Bookmarked:** 2026-09-14 (Chrome, Bookmarks bar > RDMA > 10-22)
- **Retrieved:** 2026-10-22
- **Local copy:** README below; CUG 2022 slides saved as `ARCHER2_OFI_vs_UCX_CUG2022.pdf`. Full benchmark data (~400 MB) left upstream.

---

# Performance data for comparisons of transport protocols on ARCHER2

A repository for data from the comparison of performance and scaling of the OpenFabrics and UCX transport protocols on the UK national supercomputing service, ARCHER2, an HPE Cray EX supercomputer.

## Benchmarks

 - [CASTEP](CASTEP/)
 - [CP2K](CP2K/)
 - [GROMACS](GROMACS/)
 - [NEMO](NEMO/)
 - [Ohio State University MPI microbenchmarks](OSU-MPI/)
 - [OpenSBLI](OpenSBLI/)
 - [VASP](VASP/)
 - [ReproMPI](ReproMPI/)
 

## Repo layout
    .
    ./CASTEP
    ./CASTEP/OFI
    ./CASTEP/README.md
    ./CASTEP/UCX
    ./CASTEP/analysis
    ./CASTEP/profile
    ./CASTEP/submit
    ./CP2K
    ./CP2K/OFI
    ./CP2K/README.md
    ./CP2K/UCX
    ./CP2K/analysis
    ./CP2K/profile
    ./CP2K/submit
    ./GROMACS
    ./GROMACS/OFI
    ./GROMACS/README.md
    ./GROMACS/UCX
    ./GROMACS/analysis
    ./GROMACS/profile
    ./GROMACS/submit
    ./LICENSE
    ./NEMO
    ./NEMO/OFI
    ./NEMO/README.md
    ./NEMO/UCX
    ./NEMO/analysis
    ./NEMO/build
    ./NEMO/input
    ./NEMO/submit
    ./OSU-MPI
    ./OSU-MPI/OFI
    ./OSU-MPI/README.md
    ./OSU-MPI/UCX
    ./OSU-MPI/analysis
    ./OSU-MPI/submit
    ./OpenSBLI
    ./OpenSBLI/OFI
    ./OpenSBLI/README.md
    ./OpenSBLI/UCX
    ./OpenSBLI/analysis
    ./OpenSBLI/input
    ./OpenSBLI/profile
    ./OpenSBLI/submit
    ./Presentation
    ./Presentation/ARCHER2_OFI-UCX-CUG2022.pdf
    ./Presentation/ARCHER2_OFI-UCX-CUG2022.pptx
    ./README.md
    ./ReproMPI
    ./ReproMPI/README.md
    ./ReproMPI/analyse.py
    ./ReproMPI/analysis_output
    ./ReproMPI/data
    ./VASP
    ./VASP/OFI
    ./VASP/README.md
    ./VASP/UCX
    ./VASP/analysis
    ./VASP/profile
    ./VASP/submit
    ./python-modules
    ./python-modules/appanalysis
    ./python-modules/synthanalysis
    ./python-modules/utilities
