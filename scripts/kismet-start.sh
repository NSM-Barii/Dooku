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

# stop bluetooth service entirely so BlueZ fully releases hci1 before Kismet takes it
# simply bringing hci1 down isn't enough — BlueZ keeps the device handle open
echo "[+] Stopping bluetooth service to release BT adapter..."
systemctl stop bluetooth
sleep 2

# always deploy latest kismet config
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$(dirname "$SCRIPT_DIR")/config/kismet_site.conf" /etc/kismet/kismet_site.conf

echo "[+] Starting Kismet in tmux session 'kismet'..."
tmux new-session -d -s kismet "kismet --no-ncurses" 2>/dev/null || \
    tmux send-keys -t kismet "" Enter

# restart bluetooth so hci0 (built-in) is available again — Kismet already owns hci1
sleep 3
systemctl start bluetooth

echo "[+] Done"
echo "    Kismet:    tmux attach -t kismet"
echo "    Web UI:    http://10.10.10.1:2501"
echo "    Dashboard: http://10.10.10.1:5000"
echo "    Stop:      sudo bash kismet-stop.sh"
