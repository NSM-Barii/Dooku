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
        sleep 0.5
        iw dev "$iface" set type monitor
        sleep 0.5
        ip link set "$iface" up
        echo "    $iface -> monitor"
    else
        echo "    $iface not found, skipping"
    fi
done
sleep 2

echo "[+] Starting Kismet in tmux session 'kismet'..."
tmux new-session -d -s kismet "kismet --no-ncurses" 2>/dev/null || \
    tmux send-keys -t kismet "" Enter

echo "[+] Done"
echo "    Kismet:    tmux attach -t kismet"
echo "    Web UI:    http://10.10.10.1:2501"
echo "    Dashboard: http://10.10.10.1:5000"
echo "    Stop:      sudo bash kismet-stop.sh"
