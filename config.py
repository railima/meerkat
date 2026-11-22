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
    """Grava de forma atômica (temporário + os.replace); pode levantar OSError, quem chama trata."""
    config_dir().mkdir(parents=True, exist_ok=True)
    path = config_dir() / name
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data), encoding="utf-8")
    os.replace(tmp, path)


def load_config():
    return _read("config.json")


def save_config(**values):
    _write("config.json", {**load_config(), **values})


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def setting(key):
    """Valor salvo, ou o padrão quando ausente ou de tipo errado (números int/float são equivalentes)."""
    default = DEFAULTS[key]
    value = load_config().get(key, default)
    if _is_number(default):
        return value if _is_number(value) else default
    return value if isinstance(value, type(default)) else default


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
    """Salva o token no Chaveiro/Gerenciador de Credenciais; vazio remove (volta a usar o gh).

    Retorna True se deu certo e False se o cofre falhou. Remover um token inexistente conta como sucesso.
    """
    try:
        if token:
            keyring.set_password(SERVICE, "github", token)
        else:
            keyring.delete_password(SERVICE, "github")
    except keyring.errors.PasswordDeleteError:
        pass
    except keyring.errors.KeyringError:
        return False
    return True
