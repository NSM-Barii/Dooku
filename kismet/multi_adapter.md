# Kismet — Running with Multiple Adapters

## Basic Multi-Adapter Command

Use a separate `-c` flag for each adapter:

```bash
sudo kismet -c wlan1 -c wlan2 -c wlan3 -c wlan4 --no-ncurses
```

---

## With Custom Names (Recommended)

Name each adapter so you can tell them apart in the UI:

```bash
sudo kismet \
  -c wlan1:name=Alpha \
  -c wlan2:name=Bravo \
  -c wlan3:name=Charlie \
  -c wlan4:name=Delta \
  --no-ncurses
```

---

## Persistent Config (No Need to Type Every Time)

Add sources to `/etc/kismet/kismet_site.conf` so you don't have to pass `-c` every time:

```
source=wlan1:name=Alpha
source=wlan2:name=Bravo
source=wlan3:name=Charlie
source=wlan4:name=Delta
```

Then just run:
```bash
sudo kismet --no-ncurses
```

**Note:** If you pass any `-c` flag on the command line, Kismet ignores `source=` lines in the config entirely and only uses what you passed.

---

## Channel Hopping Across Multiple Adapters

By default Kismet hops channels on each adapter independently. To spread coverage so adapters don't overlap on the same channels at the same time, add this to `kismet_site.conf`:

```
channel_hop_split=true
```

This distributes the channel list across all adapters so you cover more spectrum simultaneously.

---

## Check Sources are Running

```bash
curl -s -u kismet:dooku http://127.0.0.1:2501/datasource/all_sources.json | python3 -m json.tool
```

Or just check the web UI at `http://10.10.10.1:2501` — each adapter shows up as a separate data source.
