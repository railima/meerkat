#!/bin/sh
# Gera dist/Meerkat.app e dist/Meerkat.dmg (requer uv).
set -e
cd "$(dirname "$0")"
uv venv --python 3.12 --allow-existing .venv
uv pip install --python .venv/bin/python -r requirements.txt -r requirements-dev.txt
.venv/bin/pytest -q
.venv/bin/pyinstaller --noconfirm --clean meerkat.spec
rm -f dist/Meerkat.dmg
hdiutil create -volname Meerkat -srcfolder dist/Meerkat.app -ov -format UDZO dist/Meerkat.dmg >/dev/null
echo "Pronto: $(pwd)/dist/Meerkat.app e dist/Meerkat.dmg"
