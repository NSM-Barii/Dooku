from rich.console import Console; console = Console()

from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import json, subprocess, threading, urllib.request, urllib.error, base64, sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

PORT        = 5000
BASE        = Path(__file__).parent
DASHBOARD   = BASE / "dashboard.html"
KISMET_URL  = "http://127.0.0.1:2501"
KISMET_CONF = Path.home() / ".kismet" / "kismet_httpd.conf"

DEVICE_FIELDS = [
    ["kismet.device.base.macaddr",                                                                "mac"        ],
    ["kismet.device.base.name",                                                                   "name"       ],
    ["kismet.device.base.type",                                                                   "type"       ],
    ["kismet.device.base.signal/kismet.common.signal.last_signal",                               "rssi"       ],
    ["kismet.device.base.signal/kismet.common.signal.max_signal",                                "rssi_max"   ],
    ["kismet.device.base.channel",                                                                "channel"    ],
    ["kismet.device.base.frequency",                                                              "frequency"  ],
    ["kismet.device.base.manuf",                                                                  "vendor"     ],
    ["kismet.device.base.last_time",                                                              "last_seen"  ],
    ["kismet.device.base.first_time",                                                             "first_seen" ],
    ["kismet.device.base.packets.total",                                                          "packets"    ],
    ["dot11.device/dot11.device.last_beaconed_ssid_record/dot11.advertisedssid.ssid",            "ssid"       ],
    ["dot11.device/dot11.device.last_beaconed_ssid_record/dot11.advertisedssid.crypt_string",    "encryption" ],
    ["dot11.device/dot11.device.last_beaconed_ssid_record/dot11.advertisedssid.ht_mode",         "ht_mode"    ],
    ["dot11.device/dot11.device.last_beaconed_ssid_record/dot11.advertisedssid.maxrate",         "max_rate"   ],
    ["dot11.device/dot11.device.last_beaconed_ssid_record/dot11.advertisedssid.dot11d_country",  "country"    ],
    ["dot11.device/dot11.device.wpa_handshake_list",                                             "handshakes" ],
    ["kismet.device.base.location/kismet.common.location.last/kismet.common.location.geopoint", "geopoint"   ],
    ["dot11.device/dot11.device.num_associated_clients",                                         "clients"    ],
    ["dot11.device/dot11.device.probed_ssid_map",                                                "probed_ssids"],
]


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        if   self.path == "/":                        self._serve_html()
        elif self.path.startswith("/kismet/devices"): self._serve_kismet_devices()
        elif self.path == "/kismet/status":           self._serve_kismet_status()
        elif self.path.startswith("/kismet/device/"): self._serve_device_detail()
        elif self.path == "/kismet/flock":            self._serve_flock()
        elif self.path == "/ssh-mode":                self._ssh_mode()
        elif self.path == "/wardrive":                self._wardrive()
        elif self.path == "/shutdown":                self._shutdown()
        elif self.path == "/wigle-upload":            self._wigle_upload()
        else:
            self.send_response(404)
            self.end_headers()

    # ── KISMET HELPERS ────────────────────────────────────────

    def _auth(self):
        user, pw = "kismet", "dooku"
        try:
            for line in KISMET_CONF.read_text().splitlines():
                if line.startswith("httpd_username"): user = line.split("=", 1)[1].strip()
                if line.startswith("httpd_password"): pw   = line.split("=", 1)[1].strip()
        except Exception: pass
        return f"Basic {base64.b64encode(f'{user}:{pw}'.encode()).decode()}"

    def _kpost(self, path, body):
        req = urllib.request.Request(
            f"{KISMET_URL}{path}", data=body, method="POST",
            headers={"Authorization": self._auth(), "Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
            return data.get("devices", data) if isinstance(data, dict) else data

    def _kget(self, path):
        req = urllib.request.Request(f"{KISMET_URL}{path}", headers={"Authorization": self._auth()})
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read())

    def _json(self, data, status=200):
        payload = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type",                "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    # ── ROUTES ────────────────────────────────────────────────

    def _serve_html(self):
        try:
            with open(DASHBOARD, "rb") as f: content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()

    def _serve_kismet_devices(self):
        from urllib.parse import urlparse, parse_qs
        from flock import tag_devices
        since = parse_qs(urlparse(self.path).query).get("since", [None])[0]
        body  = json.dumps({"fields": DEVICE_FIELDS}).encode()
        try:
            if since:
                devices = self._kpost(f"/devices/last-time/{since}/devices.json", body)
                devices, _ = tag_devices(devices)
            else:
                all_devices = self._kpost("/devices/views/all/devices.json", body)
                all_devices, _ = tag_devices(all_devices)
                # always include flock cameras, fill rest with most recently seen
                flock_devices  = [d for d in all_devices if d.get("flock")]
                recent_devices = [d for d in all_devices if not d.get("flock")]
                recent_devices.sort(key=lambda d: d.get("last_seen", 0), reverse=True)
                seen_macs = {d["mac"] for d in flock_devices}
                devices   = flock_devices + [d for d in recent_devices if d.get("mac") not in seen_macs][:2000]
            self._json(devices)
        except urllib.error.URLError:
            self._json({"error": "Kismet not running"}, 503)
        except Exception as e:
            self._json({"error": str(e)}, 503)

    def _serve_device_detail(self):
        mac = self.path.split("/kismet/device/")[-1].upper()
        try:
            body = json.dumps({
                "fields": DEVICE_FIELDS + [["dot11.device/dot11.device.advertised_ssid_map", "ssid_map"]],
                "regex":  [["kismet.device.base.macaddr", f"^{mac}$"]]
            }).encode()
            devices = self._kpost("/devices/views/all/devices.json", body)
            self._json(devices[0] if devices else {})
        except urllib.error.URLError:
            self._json({"error": "Kismet not running"}, 503)
        except Exception as e:
            self._json({"error": str(e)}, 503)

    def _serve_kismet_status(self):
        try:
            status  = self._kget("/system/status.json")
            sources = self._kget("/datasource/all_sources.json")
            try:    gps = self._kget("/gps/location.json")
            except: gps = None

            # use system status for total — avoids pulling all devices just to count
            total = status.get("kismet.system.devices.count", 0)

            # type breakdown — type field only, very fast even with 10k+ devices
            try:
                types   = self._kpost("/devices/views/all/devices.json",
                                      json.dumps({"fields": [["kismet.device.base.type", "type"]]}).encode())
                counts  = {"total": total, "aps": 0, "clients": 0, "ble": 0, "flock": 0}
                for d in types:
                    t = str(d.get("type", "")).lower()
                    if   "ap"     in t:                                counts["aps"]     += 1
                    elif "client" in t:                                counts["clients"] += 1
                    elif "bt" in t or "ble" in t or "bluetooth" in t: counts["ble"]     += 1
            except:
                counts = {"total": total, "aps": 0, "clients": 0, "ble": 0, "flock": 0}

            # flock count — separate query so a timeout here doesn't kill the rest
            try:
                from flock import tag_devices
                flock_types = self._kpost("/devices/views/all/devices.json",
                                          json.dumps({"fields": [
                                              ["kismet.device.base.macaddr", "mac"],
                                              ["kismet.device.base.name",    "name"],
                                              ["dot11.device/dot11.device.last_beaconed_ssid_record/dot11.advertisedssid.ssid", "ssid"],
                                              ["dot11.device/dot11.device.probed_ssid_map", "probed_ssids"],
                                          ]}).encode())
                _, counts["flock"] = tag_devices(flock_types)
            except:
                pass

            self._json({"status": status, "sources": sources, "gps": gps, "counts": counts})
        except urllib.error.URLError:
            self._json({"error": "Kismet not running"}, 503)
        except Exception as e:
            self._json({"error": str(e)}, 503)

    def _serve_flock(self):
        """Always returns all flock cameras from the full Kismet DB — no time filter."""
        try:
            from flock import tag_devices
            body    = json.dumps({"fields": DEVICE_FIELDS + [
                ["dot11.device/dot11.device.probed_ssid_map", "probed_ssids"]
            ]}).encode()
            devices = self._kpost("/devices/views/all/devices.json", body)
            devices, _ = tag_devices(devices)
            self._json([d for d in devices if d.get("flock")])
        except urllib.error.URLError:
            self._json({"error": "Kismet not running"}, 503)
        except Exception as e:
            self._json({"error": str(e)}, 503)

    def _ssh_mode(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status": "ok"}')

        def teardown():
            import time; time.sleep(0.5)
            subprocess.run(["pkill",     "-x",  "hostapd"],                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["rm",        "-f",  "/etc/dnsmasq.d/dooku.conf"],      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["systemctl", "restart", "dnsmasq"],                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["nmcli",     "dev", "set", "wlan0", "managed", "yes"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.server.shutdown()

        threading.Thread(target=teardown, daemon=True).start()

    def _wardrive(self):
        self._json({"status": "starting"})
        script = str(BASE.parent / "scripts" / "kismet-start.sh")
        threading.Thread(target=lambda: subprocess.run(["bash", script]), daemon=True).start()

    def _shutdown(self):
        self._json({"status": "shutdown"})
        def do_shutdown():
            import time; time.sleep(1)
            subprocess.run(["shutdown", "-h", "now"])
        threading.Thread(target=do_shutdown, daemon=True).start()

    def _wigle_upload(self):
        try:
            from wigle import WigleUploader
            self._json(WigleUploader.upload_pending())
        except (FileNotFoundError, ValueError) as e:
            self._json({"error": str(e)}, 401)
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def log_message(self, format, *args): pass


class Dashboard_Server():

    @staticmethod
    def start():
        server = HTTPServer(("0.0.0.0", PORT), Handler)
        console.print(f"[bold green][+] Dooku Dashboard:[bold yellow] http://10.10.10.1:{PORT}")
        server.serve_forever()


if __name__ == "__main__":
    Dashboard_Server.start()
