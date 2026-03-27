import tomllib
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "paper-search" / "config.toml"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open("rb") as f:
        return tomllib.load(f)
