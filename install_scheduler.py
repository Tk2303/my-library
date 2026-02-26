#!/usr/bin/env python3
"""
Scheduler Installer
Sets up a daily cron job (Linux/macOS) or Task Scheduler entry (Windows)
so github_sync.py runs automatically every day.
"""

import sys
import os
import subprocess
import platform
from pathlib import Path

SCRIPT = Path(__file__).parent / "github_sync.py"
LOG    = Path(__file__).parent / "sync.log"

# Default run time: 9:00 AM daily
HOUR   = 9
MINUTE = 0


def install_cron():
    """Add or replace a cron entry on Linux/macOS."""
    python = sys.executable
    cron_line = f"{MINUTE} {HOUR} * * * {python} {SCRIPT} --run >> {LOG} 2>&1"
    marker = "# github-sync-agent"

    # Read current crontab
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    current = result.stdout if result.returncode == 0 else ""

    # Remove old entry if present
    lines = [l for l in current.splitlines() if marker not in l and "github_sync.py" not in l]

    # Add new entry
    lines.append(f"{cron_line}  {marker}")
    new_crontab = "\n".join(lines) + "\n"

    proc = subprocess.run(["crontab", "-"], input=new_crontab, text=True)
    if proc.returncode == 0:
        print(f"OK  Cron job installed! Will run daily at {HOUR:02d}:{MINUTE:02d}.")
        print(f"    Logs -> {LOG}")
        print("\n  Useful commands:")
        print("    crontab -l          # view all cron jobs")
        print("    crontab -r          # remove all cron jobs")
        print(f"    python {SCRIPT} --run   # run manually")
    else:
        print("❌  Failed to install cron job. Try editing your crontab manually:")
        print(f"    crontab -e")
        print(f"    Add this line:  {cron_line}")


def install_windows():
    """Add a Windows Task Scheduler task."""
    python   = sys.executable
    task_name = "GitHubLibrarySyncAgent"
    cmd = (
        f'schtasks /create /f /tn "{task_name}" '
        f'/tr "{python} {SCRIPT} --run" '
        f'/sc daily /st {HOUR:02d}:{MINUTE:02d}'
    )
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"OK  Windows Task Scheduler task created: {task_name}")
        print(f"    Will run daily at {HOUR:02d}:{MINUTE:02d}")
        print("\n  Useful commands:")
        print(f'    schtasks /query /tn "{task_name}"   # check status')
        print(f'    schtasks /delete /tn "{task_name}"  # remove task')
        print(f'    schtasks /run /tn "{task_name}"     # run now')
    else:
        print("FAILED to create task:", result.stderr)
        print("    Try running this script as Administrator.")


def print_systemd_service():
    """Print a systemd timer unit for Linux servers (optional)."""
    python = sys.executable
    print("\n── Optional: systemd timer (for servers) ──────────────────────")
    print("Create /etc/systemd/system/github-sync.service:")
    print(f"""
[Unit]
Description=GitHub Library Sync Agent

[Service]
Type=oneshot
ExecStart={python} {SCRIPT} --run
StandardOutput=append:{LOG}
StandardError=append:{LOG}
""")
    print("Create /etc/systemd/system/github-sync.timer:")
    print(f"""
[Unit]
Description=Run GitHub Library Sync daily

[Timer]
OnCalendar=*-*-* {HOUR:02d}:{MINUTE:02d}:00
Persistent=true

[Install]
WantedBy=timers.target
""")
    print("Then enable with:")
    print("  sudo systemctl daemon-reload")
    print("  sudo systemctl enable --now github-sync.timer")
    print("  systemctl list-timers   # verify")


def main():
    system = platform.system()
    print(f"\nDetected OS: {system}")
    print(f"Script path: {SCRIPT}\n")

    if system in ("Linux", "Darwin"):
        install_cron()
        if system == "Linux":
            print_systemd_service()
    elif system == "Windows":
        install_windows()
    else:
        print(f"Unsupported OS: {system}")
        print(f"Run manually: {sys.executable} {SCRIPT} --run")


if __name__ == "__main__":
    main()
