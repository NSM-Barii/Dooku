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

Portable RF collection rig built inside a hardened case. Raspberry Pi 5 running Kali Linux, multiple WiFi adapters for passive wardriving, RTL-SDR for sub-GHz RF collection, and a u-blox GPS for location tagging. Powered by [flock-back](https://github.com/nsm-barii/flock-back) for WiFi probe request sniffing and BLE wardriving.

---

## How It Works

**1. Power it on**

The AP comes up automatically. No screen, no keyboard needed.

**2. Connect to the WiFi**

```
SSID:     Dooku
Password: wardriving123
```

**3. SSH in**

```bash
ssh kali@10.10.10.1
```

**4. Start wardriving**

```bash
# Kismet — passive WiFi + GPS logging
sudo kismet --no-ncurses

# flock-back — WiFi probe + BLE wardriving
cd /home/kali/Documents/nsm_tools/flock-back/src
venv/bin/python main.py -w -k -p
```

**5. Open the web UI from your phone or laptop**

| Tool | URL |
|---|---|
| Kismet | `http://10.10.10.1:2501` — login: `kismet` / `dooku` |
| flock-back | `http://10.10.10.1:8000` |

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

## Setup (First Time)

```bash
sudo bash scripts/setup.sh
```

Installs all dependencies, drivers, configures services and GPS, deploys Kismet config. Reboot when done.

---

## Services

| Service | What it does | Auto-start |
|---|---|---|
| `dooku` | Brings up the AP | Yes |
| `flock-back` | flock-back wardriving suite | No — enable with `systemctl enable flock-back` |
| `gpsd` | GPS daemon | Yes |

---

## Logs

Kismet saves `.kismet` and WigleCSV files to:
```
kismet/sessions/
```

Upload the WigleCSV to [wigle.net](https://wigle.net) after a session.

---

## Docs

| File | What it covers |
|---|---|
| `kismet/first_time_setup.md` | Kismet initial setup |
| `kismet/multi_adapter.md` | Running with 4 adapters |
| `kismet/gps.md` | GPS setup and usage |
| `kismet/logs.md` | Log location and formats |
| `kismet/credentials.md` | Changing Kismet login |

---

## Contributing & Issues

Found a bug? Have a suggestion? Want to add something?

- **Open a pull request** if you have a fix or improvement
- **Open a discussion** if you have a question or idea
- **Open an issue** if something is broken

All feedback welcome — this is a living project.

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
