from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_PATH = Path("agents") / "credentials.json"


def load_credentials(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in credentials file: {path}") from exc


def save_credentials(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
