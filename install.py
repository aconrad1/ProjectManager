"""
Install required Python packages and create a desktop shortcut for ProjectManager.

Usage:
    python install.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REQUIREMENTS = Path(__file__).resolve().parent / "requirements.txt"
PROJECT_DIR = Path(__file__).resolve().parent


def install_packages() -> bool:
    """Install pip requirements. Returns True on success."""
    print("Installing required packages …\n")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)],
        check=False,
    )
    if result.returncode == 0:
        print("\nAll packages installed successfully.")
        return True
    print("\nSome packages failed to install. Check the output above.", file=sys.stderr)
    return False


def create_shortcut() -> bool:
    """Create a desktop shortcut for the GUI (Windows only)."""
    if sys.platform != "win32":
        print("Shortcut creation is only supported on Windows — skipping.")
        return True

    try:
        import winshell  # type: ignore
    except ImportError:
        pass  # fall through to COM approach

    # Use Windows COM via PowerShell — works without extra packages
    desktop = Path(os.path.join(os.environ.get("USERPROFILE", ""), "Desktop"))
    if not desktop.exists():
        # Fallback: query .NET for the Desktop folder
        desktop = None

    pythonw = Path(sys.exec_prefix) / "pythonw.exe"
    if not pythonw.exists():
        pythonw = Path(sys.executable)

    icon_path = PROJECT_DIR / "icon.ico"
    icon_arg = f"$Shortcut.IconLocation = '{icon_path},0'" if icon_path.exists() else ""

    ps_script = f"""
$WshShell = New-Object -ComObject WScript.Shell
$Desktop  = [System.Environment]::GetFolderPath('Desktop')
$Shortcut = $WshShell.CreateShortcut("$Desktop\\ProjectManager.lnk")
$Shortcut.TargetPath       = '{pythonw}'
$Shortcut.Arguments         = '"{PROJECT_DIR / "scripts" / "gui.py"}"'
$Shortcut.WorkingDirectory  = '{PROJECT_DIR}'
$Shortcut.Description       = 'ProjectManager GUI'
{icon_arg}
$Shortcut.Save()
Write-Host "Shortcut created at: $Desktop\\ProjectManager.lnk"
"""

    result = subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print(result.stdout.strip())
        return True
    print(f"Failed to create shortcut:\n{result.stderr.strip()}", file=sys.stderr)
    return False


def main():
    ok = install_packages()
    if not ok:
        sys.exit(1)

    print()
    create_shortcut()


if __name__ == "__main__":
    main()
