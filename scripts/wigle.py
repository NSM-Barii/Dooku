# THIS MODULE WILL HANDLE WIGLE UPLOAD LOGIC
# Uploads Kismet WiGLE CSV sessions to wigle.net
# Tracks history so sessions are never double-uploaded
# Filters personal SSIDs before upload


# UI IMPORTS
from rich.console import Console


# ETC IMPORTS
import csv, json, urllib.request, urllib.error, base64
from pathlib import Path
from datetime import datetime, timezone


# CONSTANTS
console       = Console()
BASE          = Path(__file__).parent.parent
SESSIONS_DIR  = BASE / "kismet" / "sessions"
CREDS_FILE    = BASE / "config" / "wigle.json"
HISTORY_FILE  = BASE / "config" / "wigle_uploaded.json"
WIGLE_URL     = "https://api.wigle.net/api/v2/file/upload"




class WigleUploader():
    """Responsible for uploading wardriving sessions to WiGLE"""


    @classmethod
    def _load_creds(cls):
        """Load WiGLE API credentials from config/wigle.json"""

        console.print("[bold green][+][/bold green]  Loading WiGLE credentials...")

        if not CREDS_FILE.exists():
            raise FileNotFoundError("config/wigle.json not found — add your WiGLE API credentials")

        creds = json.loads(CREDS_FILE.read_text())
        name  = creds.get("api_name",  "").strip()
        token = creds.get("api_token", "").strip()

        if not name or not token:
            raise ValueError("wigle.json is missing api_name or api_token")

        exclude = creds.get("exclude_ssids", [])

        console.print(f"[bold green][+][/bold green]  Credentials loaded — observer: [bold yellow]{name}[/bold yellow]")
        console.print(f"[bold green][+][/bold green]  Excluding SSIDs: [bold yellow]{exclude}[/bold yellow]")

        return name, token, exclude


    @classmethod
    def _load_history(cls):
        """Load set of already-uploaded filenames"""

        if not HISTORY_FILE.exists(): return set()

        data = json.loads(HISTORY_FILE.read_text())
        return {entry["filename"] for entry in data.get("uploads", [])}


    @classmethod
    def _record_upload(cls, filename, wigle_response):
        """Record a successful upload to history file"""

        data = {"uploads": []}

        if HISTORY_FILE.exists():
            try:    data = json.loads(HISTORY_FILE.read_text())
            except: data = {"uploads": []}

        data["uploads"].append({
            "filename":       filename,
            "uploaded_at":    datetime.now(timezone.utc).isoformat(),
            "wigle_response": wigle_response,
        })

        HISTORY_FILE.write_text(json.dumps(data, indent=2))


    @classmethod
    def _filter_csv(cls, path, exclude_ssids):
        """Strip rows whose SSID matches any exclusion — keeps all header lines"""

        raw   = Path(path).read_text(encoding="utf-8", errors="replace")
        lines = raw.splitlines(keepends=True)
        out   = []

        for line in lines:
            stripped = line.strip()
            if not stripped: out.append(line); continue

            if stripped.startswith("WigleWifi") or stripped.startswith("MAC") or stripped.startswith("NetID"):
                out.append(line); continue

            try:
                row  = next(csv.reader([stripped]))
                ssid = row[1] if len(row) > 1 else ""
                if any(ex.lower() in ssid.lower() for ex in exclude_ssids): continue
            except Exception:
                pass

            out.append(line)

        return "".join(out).encode("utf-8")


    @classmethod
    def _post_to_wigle(cls, csv_bytes, filename, api_name, api_token):
        """POST a CSV file to the WiGLE upload API"""

        console.print(f"[bold green][+][/bold green]  Uploading [bold yellow]{filename}[/bold yellow]...")

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
        """Find all unuploaded sessions and upload them — failed uploads are not recorded so they retry"""

        api_name, api_token, exclude_ssids = cls._load_creds()

        uploaded  = cls._load_history()
        all_files = sorted(SESSIONS_DIR.glob("*.wiglecsv"), key=lambda f: f.stat().st_mtime)
        pending   = [f for f in all_files if f.name not in uploaded]

        console.print(f"[bold green][+][/bold green]  Sessions: [bold yellow]{len(all_files)}[/bold yellow] total, [bold yellow]{len(pending)}[/bold yellow] pending, [bold yellow]{len(all_files) - len(pending)}[/bold yellow] already uploaded")

        if not pending:
            console.print("[bold green][+][/bold green]  All sessions already uploaded")
            return {"status": "ok", "message": "All sessions already uploaded", "uploaded": [], "skipped": len(all_files)}

        results = []

        for csv_path in pending:

            try:
                csv_bytes  = cls._filter_csv(csv_path, exclude_ssids)
                line_count = csv_bytes.decode("utf-8", errors="replace").count("\n")

                if line_count < 3:
                    console.print(f"[bold yellow][-][/bold yellow]  Skipping [bold yellow]{csv_path.name}[/bold yellow] — no data rows")
                    results.append({"file": csv_path.name, "status": "skipped", "reason": "no data rows"})
                    continue

                response = cls._post_to_wigle(csv_bytes, csv_path.name, api_name, api_token)
                cls._record_upload(csv_path.name, response)
                console.print(f"[bold green][+][/bold green]  Uploaded [bold yellow]{csv_path.name}[/bold yellow] — transId: [bold cyan]{response.get('results', {}).get('transids', [{}])[0].get('transId', '?')}[/bold cyan]")
                results.append({"file": csv_path.name, "status": "ok", "wigle": response})

            except urllib.error.HTTPError as e:
                body = ""
                try: body = e.read().decode()
                except: pass
                console.print(f"[bold red][!] HTTP {e.code} on {csv_path.name}:[bold yellow] {body}")
                results.append({"file": csv_path.name, "status": "error", "error": f"HTTP {e.code}: {body}"})

            except urllib.error.URLError as e:
                console.print(f"[bold red][!] Network error on {csv_path.name}:[bold yellow] {e.reason}")
                results.append({"file": csv_path.name, "status": "error", "error": f"Network error: {e.reason}"})

            except Exception as e:
                console.print(f"[bold red][!] Error on {csv_path.name}:[bold yellow] {e}")
                results.append({"file": csv_path.name, "status": "error", "error": str(e)})

        ok_count  = sum(1 for r in results if r["status"] == "ok")
        err_count = sum(1 for r in results if r["status"] == "error")

        console.print(f"[bold green][+][/bold green]  Done — [bold yellow]{ok_count}/{len(pending)}[/bold yellow] uploaded" + (f", [bold red]{err_count} failed[/bold red]" if err_count else ""))

        return {
            "status":   "ok" if err_count == 0 else "partial",
            "message":  f"{ok_count}/{len(pending)} sessions uploaded" + (f", {err_count} failed" if err_count else ""),
            "uploaded": results,
            "skipped":  len(all_files) - len(pending),
        }
