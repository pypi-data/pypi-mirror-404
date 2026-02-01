from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class APIError(Exception):
    message: str
    status_code: int | None = None
    error: str | None = None
    hint: str | None = None

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code is not None:
            parts.append(f"status={self.status_code}")
        if self.error:
            parts.append(f"error={self.error}")
        if self.hint:
            parts.append(f"hint={self.hint}")
        return " | ".join(parts)


class MoltbookClient:
    def __init__(self, api_key: str | None, base_url: str, timeout: float = 20.0) -> None:
        if not base_url.startswith("https://www.moltbook.com"):
            raise ValueError("Base URL must use https://www.moltbook.com with www to keep auth headers.")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(
                    method,
                    url,
                    params=params,
                    json=json_body,
                    files=files,
                    headers=headers,
                )
        except httpx.RequestError as exc:
            raise APIError(f"Request failed: {exc}") from exc

        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            raise APIError("Unexpected response content type", status_code=response.status_code)

        try:
            payload = response.json()
        except json.JSONDecodeError as exc:
            raise APIError("Invalid JSON response", status_code=response.status_code) from exc

        if response.status_code >= 400 or payload.get("success") is False:
            raise APIError(
                "API error",
                status_code=response.status_code,
                error=payload.get("error"),
                hint=payload.get("hint"),
            )

        return payload
