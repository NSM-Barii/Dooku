# THIS MODULE WILL HANDLE FLOCK CAMERA DETECTION
# Detects Flock Safety / Raven / surveillance cameras from Kismet device data
# Uses signatures from signatures.py (copied from flock-back)


# UI IMPORTS
from rich.console import Console


# NSM IMPORTS
from signatures import FLOCK_SIGNATURES


# CONSTANTS
console       = Console()
SSID_PATTERNS = [p.lower() for p in FLOCK_SIGNATURES["wifi_ssid_patterns"]]
MAC_PREFIXES  = [p.lower() for p in FLOCK_SIGNATURES["mac_prefixes"]]
BLE_NAMES     = [p.lower() for p in FLOCK_SIGNATURES["ble_name_patterns"]]
RAVEN_UUIDS   = set(FLOCK_SIGNATURES["raven_service_uuids"])




class Flock_Detector():
    """Responsible for detecting flock cameras from Kismet device data"""


    @classmethod
    def detect(cls, device):
        """Run all signature checks against a single Kismet device dict"""

        ssid = str(device.get("ssid") or device.get("name") or "").lower()
        name = str(device.get("name") or "").lower()
        mac  = str(device.get("mac")  or "").lower()

        checks = {
            "ssid":     bool(ssid and any(p in ssid for p in SSID_PATTERNS)),
            "mac":      bool(mac  and any(mac.startswith(p) for p in MAC_PREFIXES)),
            "ble_name": bool(name and any(p in name for p in BLE_NAMES)),
            "probe":    False,
            "uuid":     False,
        }

        for entry in (device.get("probed_ssids") or []):
            probed = str(entry.get("dot11.probedssid.ssid") or "").lower()
            if probed and any(p in probed for p in SSID_PATTERNS):
                checks["probe"] = True
                break

        for entry in (device.get("ble_services") or []):
            uuid = str(entry.get("kismet.ble.service.uuid") or "").lower()
            if uuid in RAVEN_UUIDS:
                checks["uuid"] = True
                break

        hit   = any(checks.values())
        match = next((k for k, v in checks.items() if v), None)

        return hit, match, checks


    @classmethod
    def tag_devices(cls, devices):
        """Tag every device in a list with flock detection results"""

        count = 0

        for d in devices:

            hit, reason, checks = cls.detect(d)

            d["flock"]        = hit
            d["flock_match"]  = reason
            d["flock_checks"] = checks

            if hit:
                count += 1
                console.print(f"[bold green][+][/bold green]  Flock camera detected:[bold yellow] {d.get('mac')}[/bold yellow] via [bold cyan]{reason}[/bold cyan]")

        return devices, count




# ── BACKWARDS COMPAT ──────────────────────────────────────
# server.py imports these as module-level functions
def detect(device):     return Flock_Detector.detect(device)
def tag_devices(devices): return Flock_Detector.tag_devices(devices)
