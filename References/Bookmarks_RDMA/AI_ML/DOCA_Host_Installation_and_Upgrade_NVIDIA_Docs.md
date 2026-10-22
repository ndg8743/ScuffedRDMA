# DOCA-Host Installation and Upgrade - NVIDIA Docs

- **Source:** https://docs.nvidia.com/doca/sdk/doca-host-installation-and-upgrade/index.html#src-4410449037_id-.DOCAHostInstallationandUpgradev3.2.0LC-DOCAExtraPackageanddoca-kernel-support
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

The following options are available for installing or upgrading DOCA-Host:

| Method | Option Name | Description | 
|---|---|---|
| Installation | DOCA local repo package | This option installs DOCA components | 
| Upgrade | DOCA online repo | This option upgrades DOCA components using online repo from the Internet | 

Find the relevant DOCA installation files for your host in the [NVIDIA DOCA Downloads](https://developer.nvidia.com/doca-downloads) page.

This page provides basic instructions for setting up DOCA on a standard system. For device-specific setups, refer to the respective device documentation, as additional steps may be required.

## Uninstalling Software from Host
 
  
   
  
 

If DOCA-Host version 2.6.0 or greater is installed you can refer to "[Upgrading Software on Host](/doca/archive/3-5-0/doca-host-installation-and-upgrade#Upgrading-Software-on-Host)" section.

Full uninstallation is required before installing DOCA-Host:

| Deb-based | ``` host# for f in $( dpkg --list \| grep -E 'doca\|flexio\|dpa-gdbserver\|dpa-stats\|dpa-resource-mgmt\|dpaeumgmt\|dpdk-community' \| awk '{print $2}' ); do echo $f ; sudo apt remove --purge $f -y ; done host# sudo /usr/sbin/ofed_uninstall.sh --force host# sudo apt-get autoremove  ```  | 
|---|---|
| RPM-based | ``` host# for f in $(rpm -qa \| grep -i doca ) ; do sudo yum -y remove $f; done host# sudo /usr/sbin/ofed_uninstall.sh --force host# sudo yum autoremove host# sudo yum makecache  ```  | 

Installation and upgrade requirements:

- Installed kernel headers that match the version of the currently running kernel. If the `build` directory exists in under `/lib/modules/$(uname -r)/build`, then the kernel headers are installed.
- The same gcc version that the currently running kernel was built with.

## Installing Software on Host
 
  
   
  
 

1. Install DOCA local repo package for host: 
  - For deb-based distributions:
    1. Download the DOCA host repo from the [NVIDIA DOCA Downloads](https://developer.nvidia.com/doca-downloads) page.
    2. Install the deb repo: ```
host# sudo dpkg -i <repo_file>.deb
```
    3. Run the update command: ```
host# apt-get update
```
    4. Install any of the profiles supported for your OS and architecture. Refer to "[Supported Host OS per DOCA-Host Installation Profile](/doca/archive/3-5-0/general-support#Supported-Host-OS-per-DOCA-Host-Installation-Profile)" (e.g., `doca-all`) for more information.
```
host# sudo apt install -y doca-all
```
    5. Update the firmware: ```
host# sudo apt install -y mlnx-fw-updater
```
  - For RPM-based distributions: DKMS ≥ 3.2 must be installed on the system as a package. 
    1. Download the DOCA host repo from the [NVIDIA DOCA Downloads](https://developer.nvidia.com/doca-downloads) page.
    2. Install the rpm repo: ```
host# sudo rpm -Uvh <repo_file>.rpm
```
    3. For non-SLES systems, run: ```
host# sudo yum makecache
```
    4. For SLES systems, run the following to verify the package signing: ```
host# zypper --gpg-auto-import-keys refresh
```
Continue the procedure using `zypper` instead of `yum`.
    5. Install any of the profiles supported for your OS and architecture (e.g., doca-all): ```
host# yum/zypper install -y doca-all
```
    6. Update the firmware: ```
host# yum/zypper install -y mlnx-fw-updater
```
If you are running on a secure-boot-enabled OS, please refer to "[DOCA-Host Installation and Upgrade | Kernel Module Signing](/doca/archive/3-5-0/doca-host-installation-and-upgrade#Kernel-Module-Signing)" before continuing.
2. Load the drivers: ```
host# sudo /etc/init.d/openibd restart
```
3. Initialize MST: ```
host# sudo mst restart
```

## Upgrading Software on Host
 
  
   
  
 

To update existing DOCA host packages, follow these steps:

1. Install the newer version of the DOCA host repository as detailed in section "[Installing Software on Host](/doca/archive/3-5-0/doca-host-installation-and-upgrade#Installing-Software-on-Host)".
2. Upgrade the DOCA packages: 
  - To upgrade from DOCA version 2.5.x, all DOCA and OFED related packages should be removed. For detailed instructions on how to uninstall these packages, please refer to the uninstall section "[Uninstalling Software from Host](/doca/archive/3-5-0/doca-host-installation-and-upgrade#Uninstalling-Software-from-Host)".
  - To upgrade from DOCA 2.6.0 or later, use the following command: 
    - For DEB-based distributions: ```
host# apt install <doca-profile>
```
    - For RPM-based distributions: ```
host# yum upgrade <doca-profile>
```
    - For SLES systems: ```
host# zypper update <doca-profile>
```
  - Before upgrading `mlnx-fw-updater`, make sure to restart MST first:
```
host# mst restart
```

## Package and Kernel Module Signing
 
  
   
  
 

This section highlights the signing methods used to ensure the authenticity and integrity of the packages and kernel modules.

### Package Signing
 
  
   
  
 

RPM packages are signed with a GPG key, enabling users to confirm that the packages come from a trusted NVIDIA source and have not been altered.

During installation, package managers automatically fetch and verify the signature while updating their metadata cache.

For more details, see [Installing Software on Host](/doca/archive/3-5-0/doca-host-installation-and-upgrade#Installing-Software-on-Host).

### Kernel Module Signing
 
  
   
  
 

With the integration of DKMS (Dynamic Kernel Module Support), DOCA-Host no longer includes pre-built, Nvidia-signed kernel drivers. Instead, the DOCA-Host installation process uses DKMS to automatically build and sign the kernel modules using a locally generated key pair.

To load these drivers on a secure-boot-enabled OS, the DKMS-generated public key must be enrolled in the system's key database. This enrollment is performed after the DOCA-Host installation is complete:

1. Import the public key to the Machine Owner Key (MOK) list using the `mokutil` utility:
```
# mokutil --import /var/lib/dkms/mok.pub
```
2. You are prompted to create and confirm a password for this one-time enrollment request.
3. Reboot the system.
4. During the boot process, follow the on-screen prompts from the MOK utility to enroll the key. You will need the password created in step 2.

## DOCA Extra Package and doca-kernel-support
 
  
   
  
 

`doca-kernel-support` is a script intended to rebuild kernel modules included with DOCA-host. It builds a single package (i.e., `rpm` or `deb`) that contains a repository of packages (i.e., `dnf` or `apt`).

Rebuilt kernel modules with `doca-kernel-support` are not signed by default. To sign them, follow the note in [step 2](/doca/archive/3-5-0/doca-host-installation-and-upgrade#DOCA-HostInstallationandUpgrade-signkernelmodules) below.

DOCA-host provides binary builds of kernel modules for some specific kernels. This script rebuilds kernel modules included with DOCA-host for a custom kernel version and creates an RPM or DEB package that holds all of those rebuilt modules for easy install.

`doca-kernel-support` does not support customized or unofficial kernels.

`doca-kernel-support` is no longer required when using non-default kernels. DKMS rebuilds kernel modules automatically during the regular installation process.

To run `doca-kernel-support`:

1. Run: ```
host# apt/yum install -y doca-extra
```
2. Execute the `doca-kernel-support` script which rebuilds and installs the DOCA-host kernel modules with the running kernel:
```
host# /opt/mellanox/doca/tools/doca-kernel-support
```
To sign the kernel modules, run this command instead: ```
host# MODULE_SIGN_PUB_KEY=/path/to/pub_key.der MODULE_SIGN_PRIV_KEY=/path/to/priv_key.priv WITH_MOD_SIGN=1 /opt/mellanox/doca/tools/doca-kernel-support
```
The output may end with `rpm` or `deb` with the following general format:
```
doca-kernel-support: Built single package: <doca-kernel-repo>
doca-kernel-support: Done
```
Output example: ```
doca-kernel-support: Built single package: /tmp/DOCA.EuUfkWfV7Z/doca-kernel-repo-2.9.0-1.kver.5.14.0.356.el9.x86.64.x86_64.rpm
doca-kernel-support: Done
```
`doca-kernel-support` does not support customized or unofficial kernels.
3. Install the generated meta-package on the desired DOCA profile: The examples provided install DOCA kernel repos (RPM/DEB) with `doca-ofed` profile, but other profiles may be installed [if they are supported](https://networking-docs.nvidia.com/doca/archive/3-5-0/general-support#Supported-Host-OS-per-DOCA-Host-Installation-Profile).
  - For SLES: ```
host# rpm -Uvh <doca-kernel-repo>
host# zypper refresh
host# zypper install <doca-userspace-metapackage>
host# zypper modifyrepo --disable doca 
host# zypper install doca-kernel-KERNEL_VERSION     # For all the meta-package, not just this single package
host# zypper modifyrepo --enable doca            
```
Example: ```
host# rpm -Uvh <doca-kernel-repo>
host# zypper refresh
host# zypper install doca-ofed-userspace
host# zypper modifyrepo --disable doca 
host# zypper install doca-kernel-5.14.21.150500.53.default     # For all the meta-package, not just this single package
host# zypper modifyrepo --enable doca
```
  - For RPM-based distributions: ```
host# rpm -Uvh <doca-kernel-repo>
host# dnf makecache
host# dnf install <doca-userspace-metapackage>   
host# dnf install --disablerepo=doca doca-kernel-KERNEL_VERSION     # For all the meta-package, not just this single package					
```
Example: ```
host# rpm -Uvh /tmp/DOCA.EuUfkWfV7Z/doca-kernel-repo-2.9.0-1.kver.5.14.0.356.el9.x86.64.x86_64.rpm
host# dnf makecache
host# dnf install doca-ofed-userspace
host# dnf install --disablerepo=doca doca-kernel-5.14.0.356.el9.x86.64.x86_64.noarch
```
  - For DEB-based distributions: ```
host# dpkg -i <doca-kernel-repo>
host# apt update
host# apt install <doca-profile>
```
Example: ```
host# dpkg -i /tmp/DOCA.J8JYxEmffD/doca-kernel-repo-2.9.0-6.4.0.mlnx_2.9.0_amd64.deb
host# apt update
host# apt install doca-ofed
```
4. (Optional) Retrieve installed packages and their versions as part of DOCA Host installation: ```
host# /opt/mellanox/doca/tools/doca-info
Versions:
- DOCA Base MLNX_OFED_LINUX-24.07-0.5.5.0
- MFT 4.29.0-127
 
UEFI\ATF versions:
- mst_device: mt41692_pciconf0
     UEFI Version: 4.7.0-42-g13081ae
     ATF Version: 4.7.0-25-g5569834
Firmware (Current):
- BlueField-3 32.41.1000
 
DOCA:
- doca-all 2.8.0-0.0.4
- doca-apsh-config 2.8.0079-1
- doca-bench 2.8.0079-1
…
 
DOCA Dependencies:
…
- flexio 24.07.2300
- mlnx-dpdk 22.11.0-2407.0.10
 
 
OFED:
…
- rdma-core 2407mlnx52-1.2407055
…
- ucx 1.17.0-1.2407055
…
```
If BlueField has a BF-Bundle version older than 2.7.0 installed on it, the UEFI/ATF versions would appear as N/A. If your version is 2.7.0 or higher and still see N/A, then perform driver restart on the host: ```
/etc/init.d/openibd restart
```

## Storage Installation
 
  
   
  
 

1. Before installation, search for the required package using your system's package manager: ```
# apt/zypper/dnf/yum search mlnx-nvme
# apt/zypper/dnf/yum search mlnx-nfsrdma
```
2. Once the correct package name is identified, install it using: ```
# apt/zypper/dnf/yum install <full-package-name>
```

Installation examples:

- For SLES: ```
# zypper search mlnx-nvme
# zypper install mlnx-nvme-kmp-default
```
- For Debian-based systems: ```
# apt search mlnx-nvme
# apt search mlnx-nfsrdma
# apt install mlnx-nvme-dkms
# apt install mlnx-nfsrdma-dkms
```

### VMA Installation
 
  
   
  
 

VMA is compatible with the latest DOCA-Host drivers, firmware, and libraries.

For users looking to install or upgrade VMA, DOCA provides `doca-libvma`, a meta-package that installs the driver stack, libvma, and all necessary dependencies.

To install `doca-libvma`, follow the instructions under section "[Installing Software on Host](/doca/archive/3-5-0/doca-host-installation-and-upgrade#Installing-Software-on-Host)" and substitute `doca-all` with `doca-libvma` in the following command:

```
# Original command
sudo <apt/yum/zypper> install -y doca-all
# Updated command
sudo <apt/yum/zypper> install -y doca-libvma
```
For the list of systems required to work with VMA, refer to the [VMA documentation](https://nam11.safelinks.protection.outlook.com/?url=https%3A%2F%2Fdocs.nvidia.com%2Fnetworking%2Fsoftware%2Faccelerator-software%2Findex.html%23vma&data=05%7C02%7Camirn%40nvidia.com%7C7eb8fc32af11403160aa08dd6c4c7086%7C43083d15727340c1b7db39efd9ccc17a%7C0%7C0%7C638785797739672375%7CUnknown%7CTWFpbGZsb3d8eyJFbXB0eU1hcGkiOnRydWUsIlYiOiIwLjAuMDAwMCIsIlAiOiJXaW4zMiIsIkFOIjoiTWFpbCIsIldUIjoyfQ%3D%3D%7C0%7C%7C%7C&sdata=ihe2GKSrSgiwjyVoBl8AhSunHEQGxbBAt6EaACbTbOw%3D&reserved=0).

### XLIO Installation
 
  
   
  
 

XLIO is compatible with the latest DOCA-Host drivers, firmware, and libraries.

For users looking to install or upgrade XLIO, DOCA `doca-libxlio`, a meta-package that installs the driver stack, libxlio, and all necessary dependencies.

To install `doca-libxlio`, follow the instructions under section "[Installing Software on Host](/doca/archive/3-5-0/doca-host-installation-and-upgrade#Installing-Software-on-Host)" while substituting `doca-all` with `doca-libxlio` in the following command:

```
# Original command
sudo <apt/yum/zypper> install -y doca-all
# Updated command
sudo <apt/yum/zypper> install -y doca-libxlio
```
For the list of systems required to work with XLIO, please see the [XLIO documentation](https://nam11.safelinks.protection.outlook.com/?url=https%3A%2F%2Fdocs.nvidia.com%2Fnetworking%2Fsoftware%2Faccelerator-software%2Findex.html%23xlio&data=05%7C02%7Camirn%40nvidia.com%7C7eb8fc32af11403160aa08dd6c4c7086%7C43083d15727340c1b7db39efd9ccc17a%7C0%7C0%7C638785797739689569%7CUnknown%7CTWFpbGZsb3d8eyJFbXB0eU1hcGkiOnRydWUsIlYiOiIwLjAuMDAwMCIsIlAiOiJXaW4zMiIsIkFOIjoiTWFpbCIsIldUIjoyfQ%3D%3D%7C0%7C%7C%7C&sdata=ozvr99yJwsHiKFM3dNN6Y%2FKLw%2BN6mK9wUFuRL1gzO6M%3D&reserved=0).

## Installing Proprietary Packages
 
  
   
  
 

The installation procedure does not install proprietary packages. Those packages are installed upon request.

List of close-source proprietary packages:

- Clusterkit
- DPCP
- hcoll
- sharp
- ibutils2
- opensm

Currently, the only way to install these packages is by using an already-built RPM or DEB file from a similar primary OS.

The following table maps community OSs which are most similar to primary OSs:

| Community OS | Most Similar Primary OS | 
|---|---|
| Alma 8.5 | RHEL 8.5 | 
| Anolis OS 8.4 | RHEL 8.5 | 
| CentOS Stream 8 | RHEL 8 | 
| CentOS Stream 9 | RHEL 9 | 
| EulerOS-V2.0.SP10 | EulerOS-V2.0.SP11 | 
| Fedora 35 | RHEL 8.5 | 
| OpenEuler-20.03.SP1 | OpenEuler20 SP3 | 
| OpenSUSE 15.3 | SLES15 SP3 | 
| Photon OS 3.0 | RHEL 7.9 | 
| UOS-V20-1040d | Debian 10.8 | 

### Download and Install MFT and Firmware
 
  
   
  
 

Last updated: