import plistlib
import sys

import pytest

import autostart


@pytest.mark.skipif(sys.platform != "darwin", reason="LaunchAgent só existe no macOS")
def test_mac_launch_agent_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(autostart, "launch_agent_path", lambda: tmp_path / "meerkat.plist")
    assert autostart.is_enabled() is False
    autostart.set_enabled(True)
    plist = plistlib.loads((tmp_path / "meerkat.plist").read_bytes())
    assert plist["RunAtLoad"] is True
    assert plist["ProgramArguments"]
    assert autostart.is_enabled() is True
    autostart.set_enabled(False)
    assert autostart.is_enabled() is False
