"""Configurações (JSON na pasta do usuário), memória das pilhas e token do GitHub (cofre do sistema)."""

import json
import os
import sys
from pathlib import Path

import keyring

SERVICE = "Meerkat"
DEFAULTS = {"interval": 2, "ui_language": "en", "paused_until": 0}


def config_dir():
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home())) / "Meerkat"
    return Path.home() / "Library" / "Application Support" / "Meerkat"


def _read(name):
    path = config_dir() / name
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _write(name, data):
    config_dir().mkdir(parents=True, exist_ok=True)
    (config_dir() / name).write_text(json.dumps(data), encoding="utf-8")


def load_config():
    return _read("config.json")


def save_config(**values):
    _write("config.json", {**load_config(), **values})


def setting(key):
    return load_config().get(key, DEFAULTS[key])


def load_memory():
    return _read("state.json")


def save_memory(memory):
    _write("state.json", memory)


def load_token():
    try:
        return keyring.get_password(SERVICE, "github")
    except keyring.errors.KeyringError:
        return None


def save_token(token):
    """Salva o token no Chaveiro/Gerenciador de Credenciais; vazio remove (volta a usar o gh)."""
    try:
        if token:
            keyring.set_password(SERVICE, "github", token)
        else:
            keyring.delete_password(SERVICE, "github")
    except keyring.errors.PasswordDeleteError:
        pass
