<div align="center">

<img src="assets/dooku.svg" alt="Dooku" width="100%"/>

<img src="assets/IMG_1346.jpg" alt="Dooku Wardriving Rig" width="420"/>

<br/>

![Kali](https://img.shields.io/badge/OS-Kali%20Linux-557C94?style=flat-square&logo=kalilinux&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-crimson?style=flat-square&logo=python&logoColor=white)
![Pi](https://img.shields.io/badge/Hardware-Raspberry%20Pi%205-C51A4A?style=flat-square&logo=raspberrypi&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active%20Development-gold?style=flat-square)

</div>

---

### *By a Star Wars Nerd*

> **"I have become more powerful than any Jedi."** — Count Dooku

Portable RF collection rig built inside a hardened case. Raspberry Pi 5 running Kali Linux, multiple WiFi adapters for passive wardriving, RTL-SDR for sub-GHz RF collection.

---

## What It Does

- **AP on boot** — Pi creates its own WiFi hotspot (SSID: `Dooku`, password: `wardriving123`). Connect and SSH in at `10.10.10.1`
- **Wardriving** — AWUS036ACS adapters run in monitor mode across 2.4GHz and 5GHz via [flock-back](https://github.com/nsm-barii/flock-back) and Kismet
- **Sub-GHz RF** — Nooelec NESDR SMArt v5 for IoT/ISM band collection via `rtl_433`
- **Dashboard** — Web UI at `http://10.10.10.1:5000` (manual start via `gui/server.py`)

---

## Hardware

| Item | Detail |
|---|---|
| Raspberry Pi 5 | 8GB RAM, 128GB storage |
| ALFA AWUS036ACS | RTL8821AU, AC600 — ×4 |
| VFAN USB GPS GMouse | u-blox 7, magnetic base |
| Nooelec NESDR SMArt v5 | RTL-SDR, sub-GHz/IoT RF |
| IVETTO 7-Port USB 3.0 Hub | External powered |
| Portable power station | 99.9Wh, 60W |
| IP67 hardened case | Desert tan |

Full materials list with prices → [materials/README.md](materials/README.md)

---

## Setup

```bash
sudo bash scripts/setup.sh
```

Installs all dependencies, drivers, and registers systemd services. Reboot when done.

---

## Services

| Service | What it does | Default |
|---|---|---|
| `dooku` | Brings up the AP on boot | **Enabled** |
| `flock-back` | flock-back wardriving suite | Disabled |

Enable flock-back auto-start:
```bash
sudo systemctl enable flock-back
sudo systemctl start flock-back
```

---

## SSH Workflow

```bash
# 1. connect to Dooku WiFi
# 2. ssh in
ssh kali@10.10.10.1

# start wardriving
sudo kismet -c wlan1 -c wlan2 -c wlan3 -c wlan4 --no-ncurses

# start flock-back manually
cd /home/kali/Documents/nsm_tools/flock-back/src
venv/bin/python main.py -w -k -p

# sub-GHz RF
sudo rtl_433 -f 314.95M -f 433.92M
```

---

## Scripts

| Script | What it does |
|---|---|
| `setup.sh` | First-time install |
| `install_drivers.sh` | Reinstall WiFi drivers only |
| `start.py` | AP boot sequence (run by systemd) |
| `database.py` | Shared utilities |

---

## About

Created by **NSM-Barii** — Star Wars nerd | Cybersecurity enthusiast

**NSM Toolset:**
- [Vader](https://github.com/nsm-barii/vader) — Recon & discovery
- [Maul](https://github.com/nsm-barii/maul) — Infrastructure mapping
- [Yoda](https://github.com/nsm-barii/yoda) — Passive RF home monitoring
- **Dooku** — Wardriving rig *(this)*

---

*"Your swords, please. We don't want to make a mess of things."*

**Disclaimer:** For educational, ethical, and legal purposes only.
