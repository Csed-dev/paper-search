from paper_search.config import load_config


class TestLoadConfig:
    def test_missing_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("paper_search.config.CONFIG_PATH", tmp_path / "nonexistent.toml")
        assert load_config() == {}

    def test_reads_toml(self, tmp_path, monkeypatch):
        config_file = tmp_path / "config.toml"
        config_file.write_text('email = "user@example.com"\ns2_key = "abc123"\n')
        monkeypatch.setattr("paper_search.config.CONFIG_PATH", config_file)
        config = load_config()
        assert config["email"] == "user@example.com"
        assert config["s2_key"] == "abc123"
