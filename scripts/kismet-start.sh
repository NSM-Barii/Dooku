#!/bin/bash
# Start Kismet cleanly — pre-sets monitor mode so the RTL driver doesn't hang

if [ "$EUID" -ne 0 ]; then
    echo "[!] Run as root: sudo bash kismet-start.sh"
    exit 1
fi

ADAPTERS=(wlan1 wlan2 wlan3 wlan4)

echo "[+] Setting monitor mode..."
for iface in "${ADAPTERS[@]}"; do
    if ip link show "$iface" &>/dev/null; then
        ip link set "$iface" down
        iw dev "$iface" set type monitor
        ip link set "$iface" up
        echo "    $iface -> monitor"
    else
        echo "    $iface not found, skipping"
    fi
done

echo "[+] Starting Kismet in tmux session 'kismet'..."
tmux new-session -d -s kismet "kismet --no-ncurses" 2>/dev/null || \
    tmux send-keys -t kismet "" Enter

echo "[+] Done — Kismet running in tmux"
echo "    Attach:   tmux attach -t kismet"
echo "    Web UI:   http://10.10.10.1:2501"
echo "    Stop:     sudo bash kismet-stop.sh"
