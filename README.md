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

Portable wardriving rig built inside a hardened case. Raspberry Pi 5 running Kali Linux headless, multiple WiFi adapters, boots headless and runs fully automated.

---

## What It Does

- **AP on boot** — Pi creates its own WiFi hotspot (SSID: `Dooku`). Connect your phone, open `10.10.10.1:5000`
- **Live dashboard** — FLOCK tab shows real-time WiFi and BLE detections. KISMET tab opens Kismet's native wardriving UI at `10.10.10.1:2501`
- **flock-back** — Full WiFi probe request sniffing and BLE wardriving via [flock-back](https://github.com/nsm-barii/flock-back)
- **Kismet** — RF wardriving across all monitor-mode adapters with WiGLE CSV export
- **Multi-adapter** — All non-AP adapters scanning simultaneously across 2.4GHz and 5GHz
- **Auto-start** — Plug in and everything comes up on its own via systemd
- **SSH MODE** — Tap button on dashboard to drop the AP and get SSH access

---

## Hardware

- Raspberry Pi 5 (8GB)
- Kali Linux Headless (64-bit)
- ALFA AWUS1900 (RTL8814AU)
- ALFA AWUS036ACS (RTL8821AU) ×4
- Powered USB hub
- Hardened carry case
- Portable battery bank

Full materials list with prices → [materials/README.md](materials/README.md)

---

## Setup

```bash
sudo bash scripts/setup.sh
```

Installs all dependencies, drivers, and registers the `dooku` systemd service. Reboot when done.

---

## About

Created by **NSM-Barii** — Star Wars nerd | Cybersecurity enthusiast

**NSM Toolset:**
- [Vader](https://github.com/nsm-barii/vader) — Recon & discovery
- [Maul](https://github.com/nsm-barii/maul) — Infrastructure mapping
- [Yoda](https://github.com/nsm-barii/yoda) — Passive RF home monitoring (BLE, WiFi APs, clients, jamming detection)
- **Dooku** — Wardriving rig *(this)*

---

*"Your swords, please. We don't want to make a mess of things."*

**Disclaimer:** For educational, ethical, and legal purposes only.
