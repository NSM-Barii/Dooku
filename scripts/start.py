import subprocess, time
from pathlib import Path
from rich.console import Console

console      = Console()
BASE         = Path(__file__).parent.parent
HOSTAPD_CONF = BASE / "config" / "hostapd.conf"
DNSMASQ_CONF = BASE / "config" / "dnsmasq.conf"

AP_IFACE = "wlan0"
AP_IP    = "10.10.10.1/24"


def start():

    console.print("[bold green][+] Dooku starting[/bold green]")

    # unblock RF
    subprocess.run(["rfkill", "unblock", "all"],                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # kill any running hostapd
    subprocess.run(["systemctl", "stop", "hostapd"],                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["pkill", "-x", "hostapd"],                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)

    # release wlan0 from NetworkManager
    subprocess.run(["nmcli", "dev", "set", AP_IFACE, "managed", "no"],              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # configure interface
    subprocess.run(["ip", "link", "set",   AP_IFACE, "down"],                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["ip", "addr", "flush", "dev", AP_IFACE],                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["ip", "addr", "add",   AP_IP,  "dev", AP_IFACE],               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["ip", "link", "set",   AP_IFACE, "up"],                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)

    # deploy dnsmasq config and start
    subprocess.run(["systemctl", "stop", "dnsmasq"],                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["cp", str(DNSMASQ_CONF), "/etc/dnsmasq.d/dooku.conf"],          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["systemctl", "start", "dnsmasq"],                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)

    # start hostapd
    subprocess.Popen(["hostapd", str(HOSTAPD_CONF)], stdout=subprocess.DEVNULL)
    time.sleep(3)

    if subprocess.run(["pgrep", "-x", "hostapd"], stdout=subprocess.DEVNULL).returncode != 0:
        console.print(f"[bold red][!] hostapd failed — check {HOSTAPD_CONF}[/bold red]")
        return

    console.print("[bold green][+] AP live — SSID: Dooku @ 10.10.10.1[/bold green]")

    # launch dashboard so it's always up when the AP is up
    venv_python = str(Path(__file__).parent / "venv" / "bin" / "python")
    server      = str(BASE / "gui" / "server.py")
    subprocess.Popen([venv_python, server], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    console.print("[bold green][+] Dashboard live — http://10.10.10.1:5000[/bold green]")

    # keep process alive so systemd doesn't restart it
    while True:
        time.sleep(60)


if __name__ == "__main__":
    start()
