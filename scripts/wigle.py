# WIGLE UPLOAD MODULE
# Handles uploading Kismet WiGLE CSV sessions to wigle.net
# Tracks upload history so sessions are never double-uploaded
# Filters personal SSIDs before upload

import csv, json, urllib.request, urllib.error, base64
from pathlib import Path
from datetime import datetime, timezone

BASE          = Path(__file__).parent.parent
SESSIONS_DIR  = BASE / "kismet" / "sessions"
CREDS_FILE    = BASE / "config" / "wigle.json"
HISTORY_FILE  = BASE / "config" / "wigle_uploaded.json"
WIGLE_URL     = "https://api.wigle.net/api/v2/file/upload"


class WigleUploader:

    @staticmethod
    def _load_creds():
        if not CREDS_FILE.exists():
            raise FileNotFoundError("config/wigle.json not found — add your WiGLE API credentials")
        creds = json.loads(CREDS_FILE.read_text())
        name  = creds.get("api_name",  "").strip()
        token = creds.get("api_token", "").strip()
        if not name or not token:
            raise ValueError("wigle.json is missing api_name or api_token")
        exclude = creds.get("exclude_ssids", ["Jabari"])
        return name, token, exclude

    @staticmethod
    def _load_history():
        if not HISTORY_FILE.exists():
            return set()
        data = json.loads(HISTORY_FILE.read_text())
        return {entry["filename"] for entry in data.get("uploads", [])}

    @staticmethod
    def _record_upload(filename, wigle_response):
        data = {"uploads": []}
        if HISTORY_FILE.exists():
            try:
                data = json.loads(HISTORY_FILE.read_text())
            except Exception:
                data = {"uploads": []}
        data["uploads"].append({
            "filename":       filename,
            "uploaded_at":    datetime.now(timezone.utc).isoformat(),
            "wigle_response": wigle_response,
        })
        HISTORY_FILE.write_text(json.dumps(data, indent=2))

    @staticmethod
    def _filter_csv(path, exclude_ssids):
        """Strip rows whose SSID matches any exclusion. Keep all header lines."""
        raw   = Path(path).read_text(encoding="utf-8", errors="replace")
        lines = raw.splitlines(keepends=True)
        out   = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                out.append(line)
                continue
            # WiGLE CSV header lines — always keep
            if stripped.startswith("WigleWifi") or stripped.startswith("MAC") or stripped.startswith("NetID"):
                out.append(line)
                continue
            # parse SSID safely using csv module (handles quoted commas)
            try:
                row  = next(csv.reader([stripped]))
                ssid = row[1] if len(row) > 1 else ""
                if any(ex.lower() in ssid.lower() for ex in exclude_ssids):
                    continue
            except Exception:
                pass  # unparseable row — keep it, let WiGLE decide
            out.append(line)
        return "".join(out).encode("utf-8")

    @staticmethod
    def _post_to_wigle(csv_bytes, filename, api_name, api_token):
        token    = base64.b64encode(f"{api_name}:{api_token}".encode()).decode()
        boundary = "----DookuWigleBoundary"
        body = (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n"
            f"Content-Type: text/csv\r\n\r\n"
        ).encode() + csv_bytes + f"\r\n--{boundary}--\r\n".encode()

        req = urllib.request.Request(
            WIGLE_URL,
            data=body,
            headers={
                "Authorization": f"Basic {token}",
                "Content-Type":  f"multipart/form-data; boundary={boundary}",
            }
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())

    @classmethod
    def upload_pending(cls):
        """
        Find all unuploaded .wiglecsv sessions, filter personal SSIDs,
        upload each one, record successes. Returns a result summary dict.
        Failed uploads are NOT recorded so they can be retried next time.
        """
        api_name, api_token, exclude_ssids = cls._load_creds()

        uploaded = cls._load_history()
        all_files = sorted(
            SESSIONS_DIR.glob("*.wiglecsv"),
            key=lambda f: f.stat().st_mtime
        )
        pending = [f for f in all_files if f.name not in uploaded]

        if not pending:
            return {
                "status":   "ok",
                "message":  "All sessions already uploaded",
                "uploaded": [],
                "skipped":  len(all_files),
            }

        results = []
        for csv_path in pending:
            try:
                csv_bytes = cls._filter_csv(csv_path, exclude_ssids)

                # skip truly empty files (only headers, no data rows)
                line_count = csv_bytes.decode("utf-8", errors="replace").count("\n")
                if line_count < 3:
                    results.append({"file": csv_path.name, "status": "skipped", "reason": "no data rows"})
                    continue

                response = cls._post_to_wigle(csv_bytes, csv_path.name, api_name, api_token)
                cls._record_upload(csv_path.name, response)
                results.append({"file": csv_path.name, "status": "ok", "wigle": response})

            except urllib.error.HTTPError as e:
                body = ""
                try: body = e.read().decode()
                except Exception: pass
                results.append({"file": csv_path.name, "status": "error", "error": f"HTTP {e.code}: {body}"})

            except urllib.error.URLError as e:
                results.append({"file": csv_path.name, "status": "error", "error": f"Network error: {e.reason}"})

            except Exception as e:
                results.append({"file": csv_path.name, "status": "error", "error": str(e)})

        ok_count  = sum(1 for r in results if r["status"] == "ok")
        err_count = sum(1 for r in results if r["status"] == "error")

        return {
            "status":   "ok" if err_count == 0 else "partial",
            "message":  f"{ok_count}/{len(pending)} sessions uploaded" + (f", {err_count} failed" if err_count else ""),
            "uploaded": results,
            "skipped":  len(all_files) - len(pending),
        }
