#!/bin/bash
# DOOKU FIRST TIME SETUP


set -e

if [ "$EUID" -ne 0 ]; then
    echo "[!] Run as root: sudo bash setup.sh"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE="$(dirname "$SCRIPT_DIR")"
FLOCK_DIR="$(dirname "$BASE")/flock-back"
KERNEL=$(uname -r)
ARCH=$(uname -m)


echo ""
echo "[+] Dooku setup starting..."
echo ""


# ── SYSTEM DEPS ───────────────────────────────────────────
echo "[+] Installing system packages..."
apt update -qq || true
apt install -y tshark hostapd dnsmasq rfkill iw bluetooth bluez python3 python3-venv bc dkms build-essential git libelf-dev wget gnupg
echo "[+] System packages installed"
echo ""



# ── KERNEL HEADERS ────────────────────────────────────────
echo "[+] Installing kernel headers for $ARCH (kernel $KERNEL)..."
apt install --no-install-recommends -y dkms build-essential git bc libelf-dev

apt install -y kalipi-kernel-headers 2>/dev/null || apt install -y linux-headers-${KERNEL} 2>/dev/null || true

if [ ! -d "/lib/modules/$KERNEL/build" ]; then
    echo "[!] Headers not found at /lib/modules/$KERNEL/build — aborting"
    exit 1
fi
echo "[+] Headers verified"
echo ""


# ── DRIVERS ───────────────────────────────────────────────
echo "[+] Cleaning old driver state..."
dkms remove rtl8814au/4.3.21  --all 2>/dev/null || true
dkms remove 8814au/5.8.5.1    --all 2>/dev/null || true
dkms remove 8821au/5.12.5.2   --all 2>/dev/null || true
rm -rf /usr/src/8814au-* /usr/src/8821au-* /usr/src/rtl8812au-*
rm -rf /tmp/8814au /tmp/8821au /tmp/rtl8812au /tmp/rtw88

echo "[+] Increasing swap for build..."
dphys-swapfile swapoff 2>/dev/null || true
sed -i 's/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=2000/' /etc/dphys-swapfile 2>/dev/null || true
dphys-swapfile setup 2>/dev/null || true
dphys-swapfile swapon 2>/dev/null || true

echo "[+] Installing AWUS1900 driver (morrownr/8814au)..."
rm -rf /tmp/8814au
git clone https://github.com/morrownr/8814au.git /tmp/8814au
cd /tmp/8814au && ./install-driver.sh NoPrompt
echo "[+] AWUS1900 done"
echo ""

MAJOR=$(echo "$KERNEL" | cut -d'.' -f1)
MINOR=$(echo "$KERNEL" | cut -d'.' -f2)

echo "[+] Installing AWUS036ACS driver..."
if [ "$MAJOR" -gt 6 ] || { [ "$MAJOR" -eq 6 ] && [ "$MINOR" -ge 14 ]; }; then
    echo "[*] Kernel 6.14+ — using lwfinger/rtw88"
    rm -rf /tmp/rtw88
    git clone https://github.com/lwfinger/rtw88.git /tmp/rtw88
    cd /tmp/rtw88 && make && make install && depmod -a
else
    echo "[*] Kernel below 6.14 — using morrownr/8821au"
    rm -rf /tmp/8821au
    git clone https://github.com/morrownr/8821au-20210708.git /tmp/8821au
    cd /tmp/8821au && ./install-driver.sh NoPrompt
fi
echo "[+] AWUS036ACS done"
echo ""


# ── DOOKU VENV ────────────────────────────────────────────
echo "[+] Setting up Dooku Python environment..."
cd "$SCRIPT_DIR"
python3 -m venv venv
venv/bin/pip install -q -r "$SCRIPT_DIR/requirements.txt"
echo "[+] Dooku venv ready"
echo ""


# ── FLOCK-BACK VENV ───────────────────────────────────────
echo "[+] Setting up flock-back Python environment..."

if [ ! -d "$FLOCK_DIR" ]; then
    echo "[*] flock-back not found — cloning..."
    git clone https://github.com/NSM-Barii/flock-back.git "$FLOCK_DIR"
fi

cd "$FLOCK_DIR/src"
python3 -m venv venv
venv/bin/pip install -q -r "$FLOCK_DIR/requirements.txt"
echo "[+] flock-back venv ready"
echo ""


# ── SERVICES ──────────────────────────────────────────────
echo "[+] Configuring services..."

# mask system hostapd so it never conflicts with ours
systemctl disable hostapd 2>/dev/null || true
systemctl mask    hostapd 2>/dev/null || true

# dnsmasq managed manually by start.py — disable autostart
systemctl disable dnsmasq 2>/dev/null || true

# tell NetworkManager to permanently leave wlan0 alone
mkdir -p /etc/NetworkManager/conf.d
cat > /etc/NetworkManager/conf.d/dooku-unmanaged.conf <<'EOF'
[keyfile]
unmanaged-devices=interface-name:wlan0;interface-name:wlan1;interface-name:wlan2;interface-name:wlan3;interface-name:wlan4
EOF
systemctl restart NetworkManager 2>/dev/null || true
echo "[+] wlan0 unmanaged by NetworkManager"

# install dooku service (AP only — starts automatically)
sed "s|ExecStart=.*|ExecStart=$SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/start.py|" \
    "$BASE/config/dooku.service" > /etc/systemd/system/dooku.service

# install flock-back service (disabled by default — enable with: systemctl enable flock-back)
FLOCK_DIR="$(dirname "$BASE")/flock-back/src"
sed "s|WorkingDirectory=.*|WorkingDirectory=$FLOCK_DIR|; s|ExecStart=.*|ExecStart=$FLOCK_DIR/venv/bin/python main.py -w -k -p|" \
    "$BASE/config/flock-back.service" > /etc/systemd/system/flock-back.service

systemctl daemon-reload
systemctl enable dooku.service
echo "[+] dooku.service enabled (AP auto-start)"
echo "[+] flock-back.service installed but disabled — run: systemctl enable flock-back to auto-start"
echo ""


# ── DEBUG SUMMARY ─────────────────────────────────────────
echo "===== KERNEL ====="
uname -r

echo ""
echo "===== INTERFACES ====="
ip link show

echo ""
echo "===== DKMS STATUS ====="
dkms status

echo ""
echo "===== LOADED MODULES ====="
lsmod | grep -E "rtl|88|8814|8821" || echo "none"

echo ""
echo "===== USB DEVICES ====="
lsusb


# ── DONE ──────────────────────────────────────────────────
echo ""
echo "[+] Setup complete — reboot to start"
echo ""
