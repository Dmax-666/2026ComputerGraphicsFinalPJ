"""Filesystem storage helpers for run artifacts."""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from graphic_agent.schemas import model_to_jsonable


class RunStorage:
    """Owns the directory layout for one pipeline run."""

    def __init__(self, output_dir: Path | str) -> None:
        self.output_dir = Path(output_dir)
        self.assets_dir = self.output_dir / "assets"
        self.reports_dir = self.output_dir / "reports"

    def prepare(self) -> None:
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def write_json(self, relative_path: str, payload: BaseModel | dict[str, Any]) -> Path:
        path = self.output_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(payload, BaseModel):
            data = model_to_jsonable(payload)
        else:
            data = payload
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return path
