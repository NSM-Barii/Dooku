# Kismet — Logs

## Default Location

Kismet saves logs to whatever directory you ran it from (`./`).
That's why `.kismet` files end up scattered around wherever you launched it.

---

## Change the Log Directory

**Option 1 — Command line flag (one-time):**
```bash
sudo kismet -c wlan1 --log-prefix=/home/kali/kismet-logs/ --no-ncurses
```

**Option 2 — Permanent (recommended):**

Edit `/etc/kismet/kismet_logging.conf`:
```
log_prefix=/home/kali/kismet-logs/
```

Or add it to `kismet_site.conf` (survives upgrades):
```
log_prefix=/home/kali/kismet-logs/
```

Then create the folder:
```bash
mkdir -p /home/kali/kismet-logs
```

---

## Log File Name Format

```
{prefix}/{title}-{YYYYMMDD}-{HH-MM-SS}-{#}.{type}
```

Example:
```
/home/kali/kismet-logs/Kismet-20260612-05-07-15-1.kismet
```

---

## Log Types

| Type | Description |
|---|---|
| `kismet` | Primary SQLite3 database — packets, devices, location, everything |
| `pcapng` | Packet capture, compatible with Wireshark / tshark |
| `wiglecsv` | WiGLE wardriving upload format |
| `pcap-ppi` | Legacy PCAP with PPI headers |

**Enable multiple types** in `kismet_logging.conf` or `kismet_site.conf`:
```
log_types=kismet,pcapng
```

Default is `kismet` only.

---

## Reading a Log File

```bash
# Open in Wireshark (if pcapng was enabled)
wireshark /home/kali/kismet-logs/Kismet-*.pcapng

# Query the SQLite database directly
sqlite3 /home/kali/kismet-logs/Kismet-*.kismet "SELECT * FROM devices LIMIT 10;"
```
