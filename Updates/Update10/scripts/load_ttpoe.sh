#!/bin/bash
# TTPoe kernel module loader

load_modules() {
    insmod $TTPOE_DIR/modttpoe/modttpoe.ko \
        dev=$INTERFACE dst=$DST_MAC verbose=2
}

unload_modules() {
    rmmod modttpoe 2>/dev/null
}

case "$1" in
    load)   load_modules ;;
    unload) unload_modules ;;
    status) lsmod | grep modttpoe ;;
esac
