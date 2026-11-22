"""Iniciar com o sistema: LaunchAgent no macOS, chave Run do registro no Windows."""

import plistlib
import sys
from pathlib import Path

LABEL = "io.github.railima.meerkat"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _command():
    if getattr(sys, "frozen", False):
        if sys.platform == "darwin":
            app = Path(sys.executable).resolve().parents[2]  # .../Meerkat.app/Contents/MacOS/Meerkat
            return ["/usr/bin/open", "-a", str(app)]
        return [sys.executable]
    return [sys.executable, str(Path(__file__).resolve().parent / "app.py")]


def launch_agent_path():
    return Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"


def is_enabled():
    if sys.platform == "darwin":
        return launch_agent_path().exists()
    if sys.platform == "win32":
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
                winreg.QueryValueEx(key, "Meerkat")
            return True
        except FileNotFoundError:
            return False
    return False


def set_enabled(enabled):
    if sys.platform == "darwin":
        path = launch_agent_path()
        if enabled:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(plistlib.dumps({"Label": LABEL, "ProgramArguments": _command(), "RunAtLoad": True}))
        else:
            path.unlink(missing_ok=True)
    elif sys.platform == "win32":
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                winreg.SetValueEx(key, "Meerkat", 0, winreg.REG_SZ, " ".join(f'"{p}"' for p in _command()))
            else:
                try:
                    winreg.DeleteValue(key, "Meerkat")
                except FileNotFoundError:
                    pass
