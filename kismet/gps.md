# Kismet — GPS Setup

## Hardware

**VFAN USB GPS GMouse** — u-blox 7 chipset, magnetic base  
Shows up as `/dev/ttyACM0` on the Pi.

---

## How It Was Set Up

**1. Install gpsd:**
```bash
sudo apt install -y gpsd gpsd-clients
```

**2. Set the device in `/etc/default/gpsd`:**
```
DEVICES="/dev/ttyACM0"
USBAUTO="true"
```

**3. Enable gpsd on boot:**
```bash
sudo systemctl enable gpsd
sudo systemctl start gpsd
```

**4. Wire Kismet to gpsd in `config/kismet_site.conf`:**
```
gps=gpsd:host=localhost,port=2947
```

This gets deployed to `/etc/kismet/kismet_site.conf` by `setup.sh`.

---

## Usage

GPS is automatic once gpsd is running. Just start Kismet normally:

```bash
sudo kismet --no-ncurses
```

Kismet connects to gpsd on port 2947 and stamps every captured network with lat/lon. You'll see a GPS status indicator in the web UI at `http://10.10.10.1:2501`.

**You need a clear view of the sky to get a satellite fix.** Indoors won't work. Give it 1-2 minutes outside to lock on.

---

## Check GPS Fix

```bash
# Live GPS monitor (shows satellites, fix quality, coordinates)
gpsmon

# Quick fix check
gpspipe -w -n 5
```

A `TPV` message with `"mode":3` means you have a 3D fix (lat/lon/altitude).  
`"mode":2` is a 2D fix (lat/lon only).  
`"mode":1` means no fix yet.

---

## WigleCSV with GPS

With GPS locked, every network in the WigleCSV log will have real coordinates and show on the Wigle map when uploaded. Without a fix, coordinates are 0,0 and networks won't map.
