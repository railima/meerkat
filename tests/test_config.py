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
