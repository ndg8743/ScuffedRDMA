#!/bin/bash
# =============================================================================
# SoftRoCEv2 Setup for Tower 2 (Linux/Proxmox)
# =============================================================================
#
# Configures Soft-RoCE (rxe) on top of ConnectX-4 100GbE for RDMA tensor
# cache development and testing. Tower 2 runs Proxmox with 2x Tesla V100.
#
# Usage:
#   sudo ./setup_softroce_tower2.sh [INTERFACE]
#
# Default interface: enp1s0 (adjust to match your ConnectX-4 port)
#
# =============================================================================

set -e

IFACE="${1:-enp1s0}"
RXE_DEV="rxe0"

red()   { echo -e "\033[0;31m$*\033[0m"; }
green() { echo -e "\033[0;32m$*\033[0m"; }
info()  { echo ">>> $*"; }

# --- Root check ---
if [[ $EUID -ne 0 ]]; then
    red "Error: run as root (sudo $0 $IFACE)"
    exit 1
fi

# --- Verify interface exists ---
if ! ip link show "$IFACE" &>/dev/null; then
    red "Interface $IFACE not found. Available interfaces:"
    ip -o link show | awk -F': ' '{print "  " $2}'
    exit 1
fi

info "Setting up SoftRoCEv2 on $IFACE"

# --- Install dependencies ---
if ! command -v rdma &>/dev/null; then
    info "Installing rdma-core and tools..."
    apt-get update -qq
    apt-get install -y -qq rdma-core ibverbs-utils libibverbs-dev \
        librdmacm-dev python3-pyverbs perftest
fi

# --- Load kernel modules ---
info "Loading RDMA kernel modules..."
modprobe rdma_rxe
modprobe ib_uverbs
modprobe rdma_ucm

# Verify modules
for mod in rdma_rxe ib_uverbs; do
    if lsmod | grep -q "$mod"; then
        green "  $mod loaded"
    else
        red "  $mod failed to load"
        exit 1
    fi
done

# --- Remove existing rxe device if present ---
if rdma link show 2>/dev/null | grep -q "$RXE_DEV"; then
    info "Removing existing $RXE_DEV..."
    rdma link delete "$RXE_DEV" 2>/dev/null || true
fi

# --- Create rxe device on interface ---
info "Creating $RXE_DEV on $IFACE..."
rdma link add "$RXE_DEV" type rxe netdev "$IFACE"

# --- Verify ---
info "Verifying RDMA configuration..."

echo ""
echo "--- rdma link show ---"
rdma link show

echo ""
echo "--- ibv_devices ---"
ibv_devices

echo ""
echo "--- ibv_devinfo $RXE_DEV ---"
ibv_devinfo "$RXE_DEV" 2>/dev/null || ibv_devinfo

# --- Network tuning for 100GbE ---
info "Applying network tuning for 100GbE..."
ip link set "$IFACE" mtu 9000 2>/dev/null && green "  MTU set to 9000 (jumbo frames)" || info "  MTU change skipped"
ethtool -G "$IFACE" rx 8192 tx 8192 2>/dev/null && green "  Ring buffers increased" || true
sysctl -w net.core.rmem_max=67108864 >/dev/null
sysctl -w net.core.wmem_max=67108864 >/dev/null
sysctl -w net.core.rmem_default=33554432 >/dev/null
sysctl -w net.core.wmem_default=33554432 >/dev/null

# --- Make persistent across reboots ---
info "Making configuration persistent..."

MODULES_FILE="/etc/modules-load.d/rdma-rxe.conf"
cat > "$MODULES_FILE" << 'MODULES'
rdma_rxe
ib_uverbs
rdma_ucm
MODULES
green "  Wrote $MODULES_FILE"

RXE_SERVICE="/etc/systemd/system/rxe-setup.service"
cat > "$RXE_SERVICE" << EOF
[Unit]
Description=SoftRoCE RXE Device Setup
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStartPre=/sbin/modprobe rdma_rxe
ExecStart=/usr/bin/rdma link add $RXE_DEV type rxe netdev $IFACE
ExecStop=/usr/bin/rdma link delete $RXE_DEV

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable rxe-setup.service
green "  Enabled rxe-setup.service"

# --- Summary ---
echo ""
echo "============================================================"
green "SoftRoCEv2 setup complete"
echo "============================================================"
echo "  Device:    $RXE_DEV"
echo "  Interface: $IFACE"
echo "  MTU:       $(ip link show $IFACE | grep -oP 'mtu \K\d+')"
echo ""
echo "Quick tests:"
echo "  ibv_rc_pingpong -d $RXE_DEV -g 0    (server)"
echo "  ibv_rc_pingpong -d $RXE_DEV -g 0 <TOWER1_IP>  (client)"
echo "  ib_write_bw -d $RXE_DEV --report_gbits"
echo "============================================================"
