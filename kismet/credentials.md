# Kismet — Credentials

## Where They're Stored

```
~/.kismet/kismet_httpd.conf
```

## Set / Change Credentials

```bash
nano ~/.kismet/kismet_httpd.conf
```

```
httpd_username=kismet
httpd_password=dooku
```

Both fields must be present together — you can't set one without the other.
Restart Kismet after changing.

---

## Current Dooku Credentials

| Field | Value |
|---|---|
| Username | `kismet` |
| Password | `dooku` |
| Web UI | `http://10.10.10.1:2501` |

---

## Notes

- Credentials are per-user (stored in `~`, not system-wide)
- If you run Kismet as root (`sudo`), the file is at `/root/.kismet/kismet_httpd.conf`
- If the file doesn't exist, Kismet will prompt you to set credentials via the web UI on first launch
