# FLOCK DETECTION MODULE
# Detects Flock Safety / Raven / surveillance cameras from Kismet device data
# Uses signatures copied from flock-back/src/signatures.py

from signatures import FLOCK_SIGNATURES

SSID_PATTERNS = [p.lower() for p in FLOCK_SIGNATURES["wifi_ssid_patterns"]]
MAC_PREFIXES  = [p.lower() for p in FLOCK_SIGNATURES["mac_prefixes"]]
BLE_NAMES     = [p.lower() for p in FLOCK_SIGNATURES["ble_name_patterns"]]
RAVEN_UUIDS   = set(FLOCK_SIGNATURES["raven_service_uuids"])


def detect(device):
    """
    Check a Kismet device dict for all flock camera signatures.
    Returns (hit, first_match_reason, checks_dict).
    checks_dict has a bool per method so callers can show full ✓/✗ breakdown.
    """
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


def tag_devices(devices):
    """
    Run detect() on every device in a list.
    Adds flock=True/False and flock_match=reason in place.
    Returns (tagged_list, flock_count).
    """
    count = 0
    for d in devices:
        hit, reason, checks = detect(d)
        d["flock"]        = hit
        d["flock_match"]  = reason
        d["flock_checks"] = checks
        if hit:
            count += 1
    return devices, count
