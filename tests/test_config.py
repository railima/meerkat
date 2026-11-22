import config


def test_config_and_memory_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "config_dir", lambda: tmp_path)
    assert config.load_config() == {}
    assert config.setting("interval") == 2
    assert config.setting("ui_language") == "en"
    config.save_config(interval=5)
    config.save_config(ui_language="pt-BR")
    assert config.load_config() == {"interval": 5, "ui_language": "pt-BR"}
    assert config.setting("interval") == 5

    assert config.load_memory() == {}
    config.save_memory({"B": {"parent_id": "A", "parent_number": 1, "oid": "b1"}})
    assert config.load_memory()["B"]["oid"] == "b1"


def test_corrupted_files_fall_back_to_defaults(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "config_dir", lambda: tmp_path)
    (tmp_path / "config.json").write_text("{nope")
    (tmp_path / "state.json").write_text("[")
    assert config.load_config() == {}
    assert config.load_memory() == {}


def test_save_token_reports_keyring_failure(monkeypatch):
    def fail(*args):
        raise config.keyring.errors.KeyringError("locked")

    monkeypatch.setattr(config.keyring, "set_password", fail)
    assert config.save_token("abc") is False

    saved = {}
    monkeypatch.setattr(config.keyring, "set_password", lambda s, u, p: saved.update({u: p}))
    assert config.save_token("abc") is True
    assert saved == {"github": "abc"}

    def missing(*args):
        raise config.keyring.errors.PasswordDeleteError("missing")

    monkeypatch.setattr(config.keyring, "delete_password", missing)
    assert config.save_token("") is True


def test_write_is_atomic(tmp_path, monkeypatch):
    import json

    monkeypatch.setattr(config, "config_dir", lambda: tmp_path)
    config.save_config(interval=5)
    assert json.loads((tmp_path / "config.json").read_text()) == {"interval": 5}
    assert [p.name for p in tmp_path.iterdir()] == ["config.json"]


def test_setting_ignores_values_of_the_wrong_type(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "config_dir", lambda: tmp_path)
    config.save_config(interval="5", ui_language=3, paused_until=1700000000.5)
    assert config.setting("interval") == 2
    assert config.setting("ui_language") == "en"
    assert config.setting("paused_until") == 1700000000.5
    config.save_config(interval=True)
    assert config.setting("interval") == 2
