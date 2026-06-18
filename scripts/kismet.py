# THIS MODULE WILL HANDLE KISMET REST API INTERACTION


# UI IMPORTS
from rich.console import Console


# ETC IMPORTS
import urllib.request, urllib.error, json, base64
from pathlib import Path


# CONSTANTS
console     = Console()
KISMET_URL  = "http://127.0.0.1:2501"
KISMET_CONF = Path.home() / ".kismet" / "kismet_httpd.conf"
KISMET_USER = "kismet"
KISMET_PASS = "dooku"




class Kismet_Client():
    """Handles auth and queries against Kismet's REST API"""


    _auth = None


    @classmethod
    def _get_auth(cls):
        """Read credentials from Kismet's httpd config, fall back to defaults"""

        if cls._auth: return cls._auth

        user, pw = KISMET_USER, KISMET_PASS

        try:
            for line in KISMET_CONF.read_text().splitlines():
                if line.startswith("httpd_username"): user = line.split("=", 1)[1].strip()
                if line.startswith("httpd_password"): pw   = line.split("=", 1)[1].strip()
        except Exception as e:
            console.print(f"[bold red][!] Could not read Kismet config:[bold yellow] {e}")

        token     = base64.b64encode(f"{user}:{pw}".encode()).decode()
        cls._auth = f"Basic {token}"

        return cls._auth


    @classmethod
    def _post(cls, path, body):
        """POST request to Kismet REST API"""

        req = urllib.request.Request(
            f"{KISMET_URL}{path}",
            data=body,
            method="POST",
            headers={
                "Authorization": cls._get_auth(),
                "Content-Type":  "application/json"
            }
        )

        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
            return data.get("devices", data) if isinstance(data, dict) else data


    @classmethod
    def _get(cls, path):
        """GET request to Kismet REST API"""

        req = urllib.request.Request(
            f"{KISMET_URL}{path}",
            headers={"Authorization": cls._get_auth()}
        )

        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read())


    @classmethod
    def get_devices(cls, fields):
        """Pull devices from Kismet with specified fields"""

        console.print("[bold green][+][/bold green]  Fetching devices from Kismet...")

        try:
            body    = json.dumps({"fields": fields}).encode()
            devices = cls._post("/devices/views/all/devices.json", body)
            console.print(f"[bold green][+][/bold green]  Got [bold yellow]{len(devices)}[/bold yellow] devices")
            return devices, None

        except urllib.error.URLError:
            console.print("[bold red][!] Kismet not running[/bold red]")
            return None, "Kismet not running"

        except Exception as e:
            console.print(f"[bold red][!] Kismet error:[bold yellow] {e}")
            return None, str(e)


    @classmethod
    def get_status(cls):
        """Pull system status from Kismet"""

        try:    return cls._get("/system/status.json"), None
        except urllib.error.URLError: return None, "Kismet not running"
        except Exception as e:        return None, str(e)


    @classmethod
    def get_sources(cls):
        """Pull all datasources from Kismet"""

        try:    return cls._get("/datasource/all_sources.json"), None
        except urllib.error.URLError: return None, "Kismet not running"
        except Exception as e:        return None, str(e)
