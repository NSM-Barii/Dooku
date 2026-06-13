# Kismet — First Time Setup

## Set Login Credentials

Kismet requires credentials before it will let you use the web UI.
Set them manually before running for the first time:

```bash
mkdir -p ~/.kismet
nano ~/.kismet/kismet_httpd.conf
```

Add these two lines:
```
httpd_username=kismet
httpd_password=dooku
```

Save and close. Kismet reads this file on every startup.

---

## Stop Kismet (Important)

**Never use `pkill kismet`** — the RTL driver hangs during teardown and freezes the whole system.

Always stop Kismet via the API:
```bash
curl -s -u kismet:dooku http://127.0.0.1:2501/system/shutdown.json
```

Or from the web UI at `http://10.10.10.1:2501` → hamburger menu → Shutdown.

---

## Start Kismet

```bash
sudo kismet -c wlan1 --no-ncurses
```

Wait ~10 seconds, then open the web UI:

```
http://10.10.10.1:2501
```

Login with the credentials you set above.

---

## Config File Locations

| File | Purpose |
|---|---|
| `~/.kismet/kismet_httpd.conf` | Your login credentials |
| `/etc/kismet/kismet.conf` | Main config |
| `/etc/kismet/kismet_logging.conf` | Log settings |
| `/etc/kismet/kismet_site.conf` | Your persistent overrides (won't be overwritten on upgrade) |

**Tip:** Make all your custom changes in `kismet_site.conf` — it survives upgrades.

---

## Change Credentials

Edit `~/.kismet/kismet_httpd.conf` directly and restart Kismet.
Both `httpd_username` and `httpd_password` must be set together — you can't have one without the other.
