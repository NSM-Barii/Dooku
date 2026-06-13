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
    ["kismet.device.base.macaddr",                                                                "mac"       ],
    ["kismet.device.base.name",                                                                   "name"      ],
    ["kismet.device.base.type",                                                                   "type"      ],
    ["kismet.device.base.signal/kismet.common.signal.last_signal",                               "rssi"      ],
    ["kismet.device.base.signal/kismet.common.signal.max_signal",                                "rssi_max"  ],
    ["kismet.device.base.channel",                                                                "channel"   ],
    ["kismet.device.base.frequency",                                                              "frequency" ],
    ["kismet.device.base.manuf",                                                                  "vendor"    ],
    ["kismet.device.base.last_time",                                                              "last_seen" ],
    ["kismet.device.base.first_time",                                                             "first_seen"],
    ["kismet.device.base.packets/kismet.device.base.packets.total",                              "packets"   ],
    ["dot11.device/dot11.device.last_beaconed_ssid_record/dot11.advertisedssid.ssid",            "ssid"      ],
    ["dot11.device/dot11.device.last_beaconed_ssid_record/dot11.advertisedssid.crypt_string",    "encryption"],
    ["kismet.device.base.location/kismet.common.location.last/kismet.common.location.geopoint", "geopoint"  ],
    ["dot11.device/dot11.device.num_associated_clients",                                          "clients"   ],
]


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        if   self.path == "/":               self._serve_html()
        elif self.path == "/data":           self._serve_data()
        elif self.path == "/kismet":         self._serve_kismet_legacy()
        elif self.path == "/kismet/devices": self._serve_kismet_devices()
        elif self.path == "/kismet/status":  self._serve_kismet_status()
        elif self.path == "/ssh-mode":       self._ssh_mode()
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
        try:
            body = json.dumps({"fields": DEVICE_FIELDS}).encode()
            self._json(self._kpost("/devices/summary/devices.json", body))
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
            self._json({"status": status, "sources": sources, "gps": gps})
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
            self._json(self._kpost("/devices/summary/devices.json", body))
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
