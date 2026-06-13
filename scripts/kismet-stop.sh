#!/bin/bash
# Stop Kismet cleanly — never use pkill, it hangs the RTL driver

if [ "$EUID" -ne 0 ]; then
    echo "[!] Run as root: sudo bash kismet-stop.sh"
    exit 1
fi

echo "[+] Shutting down Kismet via API..."
curl -s -u kismet:dooku http://127.0.0.1:2501/system/shutdown.json &>/dev/null && \
    echo "    API shutdown sent" || echo "    API unreachable"

sleep 3

# kill any remaining cap helpers if still running
if pgrep -x kismet_cap_linux_wifi &>/dev/null; then
    echo "[+] Killing lingering cap helpers..."
    kill -9 $(pgrep -x kismet_cap_linux_wifi) 2>/dev/null
fi

if pgrep -x kismet &>/dev/null; then
    echo "[+] Killing Kismet process..."
    kill -9 $(pgrep -x kismet) 2>/dev/null
fi

# kill tmux session if it exists
tmux kill-session -t kismet 2>/dev/null && echo "[+] tmux session closed"

echo "[+] Kismet stopped"
