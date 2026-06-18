# THIS MODULE WILL HOUSE THE BOOT SEQUENCE FOR THE WAR RIG


# UI IMPORTS
from rich.console import Console


# ETC IMPORTS
import subprocess, time
from pathlib import Path


# CONSTANTS
console      = Console()
BASE         = Path(__file__).parent.parent
HOSTAPD_CONF = BASE / "config" / "hostapd.conf"
DNSMASQ_CONF = BASE / "config" / "dnsmasq.conf"
VENV_PYTHON  = str(Path(__file__).parent / "venv" / "bin" / "python")
SERVER       = str(BASE / "gui" / "server.py")

AP_IFACE = "wlan0"
AP_IP    = "10.10.10.1/24"




class Boot():
    """Responsible for booting the war rig"""


    @classmethod
    def _unblock_rf(cls):
        """Unblock all RF interfaces"""

        console.print("[bold green][+][/bold green]  Unblocking RF...")
        subprocess.run(["rfkill", "unblock", "all"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        console.print("[bold green][+][/bold green]  RF unblocked")


    @classmethod
    def _start_ap(cls):
        """Bring up the AP on wlan0"""

        console.print(f"[bold green][+][/bold green]  Bringing up AP on {AP_IFACE}...")

        subprocess.run(["systemctl", "stop",  "hostapd"],                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["pkill",     "-x",    "hostapd"],                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)

        subprocess.run(["nmcli",     "dev",   "set",   AP_IFACE, "managed", "no"],    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["ip",        "link",  "set",   AP_IFACE, "down"],              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["ip",        "addr",  "flush", "dev",    AP_IFACE],            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["ip",        "addr",  "add",   AP_IP,    "dev", AP_IFACE],    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["ip",        "link",  "set",   AP_IFACE, "up"],                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)

        subprocess.run(["systemctl", "stop",  "dnsmasq"],                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["cp",        str(DNSMASQ_CONF), "/etc/dnsmasq.d/dooku.conf"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["systemctl", "start", "dnsmasq"],                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)

        subprocess.Popen(["hostapd", str(HOSTAPD_CONF)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)

        if subprocess.run(["pgrep", "-x", "hostapd"], stdout=subprocess.DEVNULL).returncode != 0:
            console.print(f"[bold red][!] hostapd failed — check {HOSTAPD_CONF}[/bold red]")
            return False

        console.print("[bold green][+][/bold green]  AP live — SSID: Dooku @ 10.10.10.1")
        return True


    @classmethod
    def _start_dashboard(cls):
        """Launch the dashboard server"""

        console.print("[bold green][+][/bold green]  Starting dashboard...")
        subprocess.Popen([VENV_PYTHON, SERVER], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        console.print("[bold green][+][/bold green]  Dashboard live — http://10.10.10.1:5000")


    @classmethod
    def main(cls):
        """Run from here"""

        console.print("[bold green]\n[+] Dooku starting...[/bold green]\n")

        cls._unblock_rf()

        if not cls._start_ap():
            console.print("[bold red][!] Boot failed — AP did not come up[/bold red]")
            return

        cls._start_dashboard()

        console.print("[bold green]\n[+] Dooku is up[/bold green]\n")

        while True:
            time.sleep(60)




if __name__ == "__main__":
    Boot.main()
