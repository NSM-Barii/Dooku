# THIS MODULE WILL BE RESPONSIBLE FOR LAUNCHING THE WARRIG DASHBOARD SERVER


# UI IMPORTS
from rich.console import Console; console = Console()


# ETC IMPORTS
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import json, subprocess, threading, urllib.request, urllib.error, base64


# CONSTANTS
PORT         = 5000
BASE         = Path(__file__).parent
FLOCK_DB     = Path(__file__).parent.parent.parent / "flock-back" / "database"
FLOCKS_JSON  = FLOCK_DB / "flocks.json"
PACKETS_JSON = FLOCK_DB / "packets.json"
DASHBOARD    = BASE / "dashboard.html"




class Handler(BaseHTTPRequestHandler):
    """This class will be responsible for handling all HTTP requests"""


    def do_GET(self):
        """Route incoming GET requests"""


        if   self.path == "/":         self._serve_html()
        elif self.path == "/data":     self._serve_data()
        elif self.path == "/kismet":   self._serve_kismet()
        elif self.path == "/ssh-mode": self._ssh_mode()
        else:
            self.send_response(404)
            self.end_headers()


    def _serve_html(self):
        """This method will be responsible for serving the dashboard HTML"""


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
        """This method will be responsible for serving device data as JSON"""


        # PULL DEVICES
        devices = []
        try:
            with open(FLOCKS_JSON, "r") as f:
                for line in f:
                    line = line.strip()
                    if line: devices.append(json.loads(line))
        except FileNotFoundError: pass


        # BUILD PACKET COUNT MAP
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


        # ENRICH DEVICES WITH PACKET COUNT
        for device in devices:
            device["frame_count"] = packet_counts.get(device.get("mac"), 0)


        payload = json.dumps(devices).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)


    def _ssh_mode(self):
        """This method will be responsible for dropping the AP and handing control back to NetworkManager"""


        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status": "ok"}')

        def teardown():
            import time; time.sleep(0.5)
            subprocess.run(["pkill", "-x", "hostapd"],                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["rm", "-f", "/etc/dnsmasq.d/dooku.conf"],               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["systemctl", "restart", "dnsmasq"],                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["nmcli", "dev", "set", "wlan0", "managed", "yes"],      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.server.shutdown()

        threading.Thread(target=teardown, daemon=True).start()


    def _serve_kismet(self):
        """This method will be responsible for proxying Kismet device data"""

        try:
            kismet_conf = Path.home() / ".kismet" / "kismet_httpd.conf"
            user, pw    = "kismet", "dooku"
            try:
                for line in kismet_conf.read_text().splitlines():
                    if line.startswith("httpd_username"): user = line.split("=", 1)[1].strip()
                    if line.startswith("httpd_password"): pw   = line.split("=", 1)[1].strip()
            except Exception: pass

            token = base64.b64encode(f"{user}:{pw}".encode()).decode()
            body  = json.dumps({"fields": [
                ["kismet.device.base.macaddr",  "mac"],
                ["kismet.device.base.name",     "name"],
                ["kismet.device.base.type",     "type"],
                ["kismet.device.base.signal/kismet.common.signal.last_signal", "rssi"],
                ["kismet.device.base.channel",  "channel"],
                ["kismet.device.base.manuf",    "vendor"],
            ]}).encode()

            req = urllib.request.Request(
                "http://127.0.0.1:2501/devices/summary/devices.json",
                data=body, method="POST",
                headers={"Authorization": f"Basic {token}", "Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=3) as r:
                data = json.loads(r.read())
                if isinstance(data, dict): data = data.get("devices", [])
            payload = json.dumps(data).encode()
            self.send_response(200)

        except urllib.error.URLError:
            payload = json.dumps({"error": "Kismet not running"}).encode()
            self.send_response(503)
        except Exception as e:
            payload = json.dumps({"error": str(e)}).encode()
            self.send_response(503)

        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)


    def log_message(self, format, *args): pass




class Dashboard_Server():
    """This class will be responsible for controlling the dashboard web server"""


    server = None


    @staticmethod
    def start():
        """Start the HTTP server"""


        Dashboard_Server.server = HTTPServer(("0.0.0.0", PORT), Handler)
        console.print(f"[bold green][+] Dooku Dashboard:[bold yellow] http://10.10.10.1:{PORT}")
        Dashboard_Server.server.serve_forever()




if __name__ == "__main__":
    Dashboard_Server.start()
