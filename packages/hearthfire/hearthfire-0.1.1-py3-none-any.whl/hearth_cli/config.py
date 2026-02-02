from pathlib import Path

import yaml


class Config:
    CONFIG_DIR = Path.home() / ".hearth"
    CONFIG_FILE = CONFIG_DIR / "config.yaml"

    def __init__(self) -> None:
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self) -> None:
        if self.CONFIG_FILE.exists():
            with open(self.CONFIG_FILE) as f:
                self._data = yaml.safe_load(f) or {}
        else:
            self._data = {}

    def _save(self) -> None:
        with open(self.CONFIG_FILE, "w") as f:
            yaml.dump(self._data, f)

    @property
    def api_url(self) -> str | None:
        return self._data.get("api_url")

    @api_url.setter
    def api_url(self, value: str) -> None:
        self._data["api_url"] = value
        self._save()

    @property
    def token(self) -> str | None:
        return self._data.get("token")

    @token.setter
    def token(self, value: str | None) -> None:
        if value is None:
            self._data.pop("token", None)
        else:
            self._data["token"] = value
        self._save()


config = Config()
