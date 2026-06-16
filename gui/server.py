from rich.console import Console; console = Console()

from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import json, subprocess, threading, urllib.request, urllib.error, base64

PORT         = 5000
BASE         = Path(__file__).parent
FLOCK_DB     = Path(__file__).parent.parent.parent / "flock-back" / "database"
FLOCKS_JSON  = FLOCK_DB / "flocks.json"
PACKETS_JSON = FLOCK_DB / "packets.json"
DASHBOARD    = BASE / "dashboard.html"
KISMET_URL   = "http://127.0.0.1:2501"
KISMET_CONF  = Path.home() / ".kismet" / "kismet_httpd.conf"

DEVICE_FIELDS = [
    ["kismet.device.base.macaddr",                                                                "mac"        ],
    ["kismet.device.base.name",                                                                   "name"       ],
    ["kismet.device.base.type",                                                                   "type"       ],
    ["kismet.device.base.signal/kismet.common.signal.last_signal",                               "rssi"       ],
    ["kismet.device.base.signal/kismet.common.signal.max_signal",                                "rssi_max"   ],
    ["kismet.device.base.signal/kismet.common.signal.min_signal",                                "rssi_min"   ],
    ["kismet.device.base.channel",                                                                "channel"    ],
    ["kismet.device.base.frequency",                                                              "frequency"  ],
    ["kismet.device.base.manuf",                                                                  "vendor"     ],
    ["kismet.device.base.last_time",                                                              "last_seen"  ],
    ["kismet.device.base.first_time",                                                             "first_seen" ],
    ["kismet.device.base.packets/kismet.device.base.packets.total",                              "packets"    ],
    ["dot11.device/dot11.device.last_beaconed_ssid_record/dot11.advertisedssid.ssid",            "ssid"       ],
    ["dot11.device/dot11.device.last_beaconed_ssid_record/dot11.advertisedssid.crypt_string",    "encryption" ],
    ["dot11.device/dot11.device.last_beaconed_ssid_record/dot11.advertisedssid.ht_mode",         "ht_mode"    ],
    ["dot11.device/dot11.device.last_beaconed_ssid_record/dot11.advertisedssid.maxrate",         "max_rate"   ],
    ["dot11.device/dot11.device.last_beaconed_ssid_record/dot11.advertisedssid.dot11d_country",  "country"    ],
    ["dot11.device/dot11.device.wpa_handshake_list",                                             "handshakes" ],
    ["kismet.device.base.location/kismet.common.location.last/kismet.common.location.geopoint", "geopoint"   ],
    ["dot11.device/dot11.device.num_associated_clients",                                         "clients"    ],
]


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        if   self.path == "/":                        self._serve_html()
        elif self.path == "/data":                    self._serve_data()
        elif self.path == "/kismet":                  self._serve_kismet_legacy()
        elif self.path.startswith("/kismet/devices"): self._serve_kismet_devices()
        elif self.path == "/kismet/status":           self._serve_kismet_status()
        elif self.path.startswith("/kismet/device/"): self._serve_device_detail()
        elif self.path == "/ssh-mode":                self._ssh_mode()
        elif self.path == "/wardrive":               self._wardrive()
        elif self.path == "/shutdown":               self._shutdown()
        elif self.path == "/wigle-upload":           self._wigle_upload()
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
        self.send_header("Content-Type",                 "application/json")
        self.send_header("Access-Control-Allow-Origin",  "*")
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

    def _serve_data(self):
        devices = []
        try:
            with open(FLOCKS_JSON, "r") as f:
                for line in f:
                    line = line.strip()
                    if line: devices.append(json.loads(line))
        except FileNotFoundError: pass

        packet_counts = {}
        try:
            with open(PACKETS_JSON, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    entry = json.loads(line)
                    mac   = entry.get("mac")
                    count = entry.get("frame_count", 0)
                    if mac and count > packet_counts.get(mac, 0):
                        packet_counts[mac] = count
        except FileNotFoundError: pass

        for device in devices:
            device["frame_count"] = packet_counts.get(device.get("mac"), 0)
        self._json(devices)

    def _serve_kismet_devices(self):
        from urllib.parse import urlparse, parse_qs
        since = parse_qs(urlparse(self.path).query).get("since", [None])[0]
        body  = json.dumps({"fields": DEVICE_FIELDS}).encode()
        try:
            if since:
                # delta — only devices updated since last poll
                devices = self._kpost(f"/devices/last-time/{since}/devices.json", body)
            else:
                # initial load — 2000 most recently seen
                devices = self._kpost("/devices/views/all/devices.json", body)
                devices.sort(key=lambda d: d.get("last_seen", 0), reverse=True)
                devices = devices[:2000]
            self._json(devices)
        except urllib.error.URLError:
            self._json({"error": "Kismet not running"}, 503)
        except Exception as e:
            self._json({"error": str(e)}, 503)

    def _serve_device_detail(self):
        mac = self.path.split("/kismet/device/")[-1].upper()
        try:
            body = json.dumps({
                "fields": DEVICE_FIELDS + [
                    ["dot11.device/dot11.device.advertised_ssid_map", "ssid_map"],
                ],
                "regex": [["kismet.device.base.macaddr", f"^{mac}$"]]
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

            # accurate device type counts from full Kismet database
            try:
                types = self._kpost("/devices/views/all/devices.json",
                                    json.dumps({"fields": [["kismet.device.base.type", "type"]]}).encode())
                counts = {"total": len(types), "aps": 0, "clients": 0, "ble": 0}
                for d in types:
                    t = str(d.get("type", "")).lower()
                    if "ap"        in t: counts["aps"]     += 1
                    elif "client"  in t: counts["clients"] += 1
                    elif "bt" in t or "ble" in t or "bluetooth" in t: counts["ble"] += 1
            except:
                counts = None

            self._json({"status": status, "sources": sources, "gps": gps, "counts": counts})
        except urllib.error.URLError:
            self._json({"error": "Kismet not running"}, 503)
        except Exception as e:
            self._json({"error": str(e)}, 503)

    def _serve_kismet_legacy(self):
        try:
            body = json.dumps({"fields": [
                ["kismet.device.base.macaddr",                                         "mac"    ],
                ["kismet.device.base.name",                                            "name"   ],
                ["kismet.device.base.type",                                            "type"   ],
                ["kismet.device.base.signal/kismet.common.signal.last_signal",        "rssi"   ],
                ["kismet.device.base.channel",                                         "channel"],
                ["kismet.device.base.manuf",                                           "vendor" ],
            ]}).encode()
            self._json(self._kpost("/devices/views/all/devices.json", body))
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

    def _wigle_upload(self):
        import glob, mimetypes
        sessions = sorted(
            glob.glob(str(BASE.parent / "kismet" / "sessions" / "*.wiglecsv")),
            key=lambda f: Path(f).stat().st_mtime, reverse=True
        )
        if not sessions:
            self._json({"error": "No WiGLE CSV files found"}, 404); return

        creds_file = BASE.parent / "config" / "wigle.json"
        if not creds_file.exists():
            self._json({"error": "No WiGLE credentials — add config/wigle.json"}, 401); return

        creds = json.loads(creds_file.read_text())
        api_name  = creds.get("api_name", "")
        api_token = creds.get("api_token", "")
        if not api_name or not api_token:
            self._json({"error": "wigle.json missing api_name or api_token"}, 401); return

        csv_path = sessions[0]
        token    = base64.b64encode(f"{api_name}:{api_token}".encode()).decode()

        try:
            import urllib.request
            boundary = "----DookuBoundary"
            with open(csv_path, "rb") as f: csv_data = f.read()
            filename = Path(csv_path).name
            body = (
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n"
                f"Content-Type: text/csv\r\n\r\n"
            ).encode() + csv_data + f"\r\n--{boundary}--\r\n".encode()

            req = urllib.request.Request(
                "https://api.wigle.net/api/v2/file/upload",
                data=body,
                headers={
                    "Authorization": f"Basic {token}",
                    "Content-Type": f"multipart/form-data; boundary={boundary}",
                }
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                result = json.loads(r.read())
            self._json({"status": "ok", "file": filename, "wigle": result})
        except Exception as e:
            self._json({"error": str(e)}, 500)

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

    def log_message(self, format, *args): pass


class Dashboard_Server():

    server = None

    @staticmethod
    def start():
        Dashboard_Server.server = HTTPServer(("0.0.0.0", PORT), Handler)
        console.print(f"[bold green][+] Dooku Dashboard:[bold yellow] http://10.10.10.1:{PORT}")
        Dashboard_Server.server.serve_forever()


if __name__ == "__main__":
    Dashboard_Server.start()
