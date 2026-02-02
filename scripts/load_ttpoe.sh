#!/bin/bash
# =============================================================================
# TTPoe Kernel Module Management
# =============================================================================
#
# Manages Tesla TTPoe kernel modules for low-latency transport.
#
# Usage:
#   ./load_ttpoe.sh [COMMAND] [OPTIONS]
#
# Commands:
#   load          Load TTPoe modules
#   unload        Unload TTPoe modules
#   status        Show module status
#   build         Build modules from source
#   test          Run TTPoe unit tests
#   peer          Configure peer connection
#
# Options:
#   --dev=IFACE       Network interface (default: eth0)
#   --dst=MAC         Destination MAC address
#   --vc=ID           Virtual circuit ID (default: 0)
#   --verbose=LEVEL   Debug level 0-3 (default: 1)
#   --ttpoe-dir=PATH  TTPoe source directory
#
# =============================================================================

set -e

# Configuration
TTPOE_DIR="${TTPOE_DIR:-/opt/ttpoe}"
INTERFACE="${INTERFACE:-eth0}"
DST_MAC=""
VIRTUAL_CIRCUIT=0
VERBOSE=1
COMMAND="${1:-status}"

# Parse arguments
shift 2>/dev/null || true
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dev=*)
            INTERFACE="${1#*=}"
            shift
            ;;
        --dst=*)
            DST_MAC="${1#*=}"
            shift
            ;;
        --vc=*)
            VIRTUAL_CIRCUIT="${1#*=}"
            shift
            ;;
        --verbose=*)
            VERBOSE="${1#*=}"
            shift
            ;;
        --ttpoe-dir=*)
            TTPOE_DIR="${1#*=}"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# =============================================================================
# Functions
# =============================================================================

check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo "Error: This command requires root privileges"
        echo "Run with: sudo $0 $COMMAND"
        exit 1
    fi
}

is_loaded() {
    lsmod | grep -q "modttpoe"
}

load_modules() {
    check_root

    if is_loaded; then
        echo "TTPoe modules already loaded"
        return 0
    fi

    MODTTPOE="$TTPOE_DIR/modttpoe/modttpoe.ko"
    MODTTPIP="$TTPOE_DIR/modttpip/modttpip.ko"

    if [[ ! -f "$MODTTPOE" ]]; then
        echo "Error: modttpoe.ko not found at $MODTTPOE"
        echo "Run: $0 build --ttpoe-dir=$TTPOE_DIR"
        exit 1
    fi

    echo "Loading TTPoe modules..."
    echo "  Device: $INTERFACE"
    echo "  Destination: ${DST_MAC:-broadcast}"
    echo "  Virtual Circuit: $VIRTUAL_CIRCUIT"
    echo "  Verbose: $VERBOSE"

    # Build insmod command
    CMD="insmod $MODTTPOE dev=$INTERFACE verbose=$VERBOSE"

    if [[ -n "$DST_MAC" ]]; then
        CMD="$CMD dst=$DST_MAC"
    fi

    if [[ $VIRTUAL_CIRCUIT -gt 0 ]]; then
        CMD="$CMD vc=$VIRTUAL_CIRCUIT"
    fi

    echo "Running: $CMD"
    $CMD

    # Verify
    if is_loaded; then
        echo "TTPoe modules loaded successfully"
        show_status
    else
        echo "Error: Failed to load TTPoe modules"
        echo "Check dmesg for details: dmesg | tail -20"
        exit 1
    fi
}

unload_modules() {
    check_root

    if ! is_loaded; then
        echo "TTPoe modules not loaded"
        return 0
    fi

    echo "Unloading TTPoe modules..."

    # Unload in reverse order
    if lsmod | grep -q "modttpip"; then
        rmmod modttpip
    fi

    if lsmod | grep -q "modttpoe"; then
        rmmod modttpoe
    fi

    echo "TTPoe modules unloaded"
}

show_status() {
    echo "============================================================"
    echo "TTPoe Module Status"
    echo "============================================================"

    if is_loaded; then
        echo "Module: LOADED"
        echo ""

        # Show module info
        echo "Module Info:"
        modinfo "$TTPOE_DIR/modttpoe/modttpoe.ko" 2>/dev/null | head -10 || true
        echo ""

        # Show procfs state if available
        if [[ -f /proc/net/ttpoe/state ]]; then
            echo "State:"
            cat /proc/net/ttpoe/state
            echo ""
        fi

        if [[ -f /proc/net/ttpoe/stats ]]; then
            echo "Statistics:"
            cat /proc/net/ttpoe/stats
            echo ""
        fi

        # Show recent kernel messages
        echo "Recent kernel messages:"
        dmesg | grep -i ttp | tail -10 || echo "  (no TTP messages)"

    else
        echo "Module: NOT LOADED"
        echo ""

        # Check if module exists
        if [[ -f "$TTPOE_DIR/modttpoe/modttpoe.ko" ]]; then
            echo "Module file: $TTPOE_DIR/modttpoe/modttpoe.ko (exists)"
        else
            echo "Module file: NOT FOUND"
            echo "Run: $0 build --ttpoe-dir=$TTPOE_DIR"
        fi
    fi

    echo "============================================================"
}

build_modules() {
    if [[ ! -d "$TTPOE_DIR" ]]; then
        echo "TTPoe source not found at $TTPOE_DIR"
        echo "Cloning from GitHub..."

        git clone https://github.com/teslamotors/ttpoe.git "$TTPOE_DIR"
    fi

    echo "Building TTPoe modules..."
    cd "$TTPOE_DIR"

    # Check for kernel headers
    if [[ ! -d "/lib/modules/$(uname -r)/build" ]]; then
        echo "Error: Kernel headers not found"
        echo "Install with: sudo apt-get install linux-headers-$(uname -r)"
        exit 1
    fi

    make clean 2>/dev/null || true
    make all

    echo ""
    echo "Build complete. Module files:"
    ls -la modttpoe/modttpoe.ko modttpip/modttpip.ko 2>/dev/null || echo "Build may have failed"
}

run_tests() {
    if [[ ! -d "$TTPOE_DIR" ]]; then
        echo "Error: TTPoe source not found at $TTPOE_DIR"
        exit 1
    fi

    echo "Running TTPoe unit tests..."
    cd "$TTPOE_DIR"

    if [[ -x tests/run.sh ]]; then
        ./tests/run.sh --target=2 -v
    else
        echo "Test script not found"
        exit 1
    fi
}

configure_peer() {
    if [[ -z "$DST_MAC" ]]; then
        echo "Error: --dst=MAC required for peer configuration"
        exit 1
    fi

    check_root

    if ! is_loaded; then
        echo "Loading modules with peer configuration..."
        load_modules
    else
        echo "Modules already loaded. To change peer, unload first:"
        echo "  $0 unload"
        echo "  $0 load --dst=$DST_MAC"
    fi
}

show_help() {
    head -30 "$0" | tail -27
}

# =============================================================================
# Main
# =============================================================================

case "$COMMAND" in
    load)
        load_modules
        ;;
    unload)
        unload_modules
        ;;
    status)
        show_status
        ;;
    build)
        build_modules
        ;;
    test)
        run_tests
        ;;
    peer)
        configure_peer
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $COMMAND"
        echo "Run '$0 help' for usage"
        exit 1
        ;;
esac
