from collections.abc import Generator
from typing import Any

import httpx

from hearth_cli.config import config


class APIError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error ({status_code}): {message}")


class APIClient:
    def __init__(self) -> None:
        if not config.api_url:
            raise RuntimeError("未配置API地址，请先运行 'hearth auth login'")

        self.base_url = config.api_url.rstrip("/")
        self.token = config.token

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise APIError(response.status_code, detail)
        return response.json()

    def get(self, path: str, params: dict | None = None) -> dict[str, Any]:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                f"{self.base_url}{path}",
                params=params,
                headers=self._headers(),
            )
            return self._handle_response(response)

    def post(self, path: str, data: dict | None = None) -> dict[str, Any]:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{self.base_url}{path}",
                json=data,
                headers=self._headers(),
            )
            return self._handle_response(response)

    def delete(self, path: str) -> None:
        with httpx.Client(timeout=30.0) as client:
            response = client.delete(
                f"{self.base_url}{path}",
                headers=self._headers(),
            )
            if response.status_code >= 400:
                try:
                    detail = response.json().get("detail", response.text)
                except Exception:
                    detail = response.text
                raise APIError(response.status_code, detail)

    def stream_get(self, path: str) -> Generator[str, None, None]:
        with httpx.Client(timeout=None) as client, client.stream(
            "GET",
            f"{self.base_url}{path}",
            headers={**self._headers(), "Accept": "text/event-stream"},
        ) as response:
            for line in response.iter_lines():
                if line.startswith("data: "):
                    yield line[6:]

    def download(self, path: str) -> bytes:
        with httpx.Client(timeout=120.0) as client:
            response = client.get(
                f"{self.base_url}{path}",
                headers=self._headers(),
            )
            if response.status_code >= 400:
                raise APIError(response.status_code, response.text)
            return response.content


def get_client() -> APIClient:
    return APIClient()
