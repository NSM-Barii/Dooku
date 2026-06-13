# THIS MODULE WILL HANDLE KISMET REST API INTERACTION


# ETC IMPORTS
import urllib.request, urllib.error, json, base64
from pathlib import Path


# CONSTANTS
KISMET_URL  = "http://127.0.0.1:2501"
KISMET_CONF = Path.home() / ".kismet" / "kismet_httpd.conf"

# Default credentials written by start.py on first boot
KISMET_USER = "kismet"
KISMET_PASS = "dooku"

FIELDS = [
    ["kismet.device.base.macaddr",                                                                    "mac"        ],
    ["kismet.device.base.name",                                                                       "name"       ],
    ["kismet.device.base.type",                                                                       "type"       ],
    ["kismet.device.base.signal/kismet.common.signal.last_signal",                                    "rssi"       ],
    ["kismet.device.base.channel",                                                                    "channel"    ],
    ["kismet.device.base.frequency",                                                                  "frequency"  ],
    ["kismet.device.base.manuf",                                                                      "vendor"     ],
    ["kismet.device.base.last_time",                                                                  "last_seen"  ],
    ["kismet.device.base.first_time",                                                                 "first_seen" ],
    ["kismet.device.base.packets/kismet.device.base.packets.total",                                  "packets"    ],
    ["dot11.device/dot11.device.last_beaconed_ssid_record/dot11.advertisedssid.crypt_string",         "encryption" ],
]




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
        except Exception: pass

        token     = base64.b64encode(f"{user}:{pw}".encode()).decode()
        cls._auth = f"Basic {token}"

        return cls._auth


    @classmethod
    def get_devices(cls):
        """Pull all devices from Kismet"""

        auth = cls._get_auth()
        if not auth: return None, "Kismet credentials not found — run Kismet once to set up"

        body = json.dumps({"fields": FIELDS}).encode()
        req  = urllib.request.Request(
            f"{KISMET_URL}/devices/views/all/devices.json",
            data=body,
            method="POST",
            headers={
                "Authorization": auth,
                "Content-Type":  "application/json"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=3) as r:
                data = json.loads(r.read())
                # Kismet returns bare array or {"devices": [...]} depending on version
                if isinstance(data, dict): data = data.get("devices", [])
                return data, None

        except urllib.error.URLError:   return None, "Kismet not running"
        except Exception as e:          return None, str(e)
