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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python"
SERVER="$(dirname "$SCRIPT_DIR")/gui/server.py"

echo "[+] Starting Kismet in tmux session 'kismet'..."
tmux new-session -d -s kismet "kismet --no-ncurses" 2>/dev/null || \
    tmux send-keys -t kismet "" Enter

echo "[+] Starting dashboard in tmux session 'dashboard'..."
tmux new-session -d -s dashboard "$VENV_PYTHON $SERVER" 2>/dev/null || \
    tmux send-keys -t dashboard "" Enter

echo "[+] Done"
echo "    Kismet:    tmux attach -t kismet"
echo "    Dashboard: tmux attach -t dashboard"
echo "    Web UI:    http://10.10.10.1:2501"
echo "    Dashboard: http://10.10.10.1:5000"
echo "    Stop:      sudo bash kismet-stop.sh"
