# PyInstaller: gera Meerkat.app (macOS) ou Meerkat.exe (Windows). Use build_mac.sh / build_windows.bat.
import os
import sys

VERSION = os.environ.get("MEERKAT_VERSION", "0.0.0-dev").lstrip("v")

a = Analysis(
    ["app.py"],
    datas=[("icon/icon.png", "icon")],
    hiddenimports=["keyring.backends.macOS", "keyring.backends.Windows", "pystray._darwin", "pystray._win32"],
)
pyz = PYZ(a.pure)

if sys.platform == "darwin":
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Meerkat", console=False)
    coll = COLLECT(exe, a.binaries, a.datas, name="Meerkat")
    app = BUNDLE(
        coll,
        name="Meerkat.app",
        icon="icon/Meerkat.icns",
        bundle_identifier="io.github.railima.meerkat",
        info_plist={
            "CFBundleShortVersionString": VERSION,
            "LSMinimumSystemVersion": "13.0",
            "LSUIElement": True,  # só na barra de menu, sem ícone no Dock
            "NSHighResolutionCapable": True,
        },
    )
else:
    exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="Meerkat", console=False, icon="icon/Meerkat.ico")
