from __future__ import annotations
from pathlib import Path
import tempfile
from typing import Iterator

def ext_of(p: Path) -> str:
    return p.suffix.lower().lstrip(".")

def ensure_parent(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)

def temp_dir() -> tempfile.TemporaryDirectory[str]:
    return tempfile.TemporaryDirectory()

def first_existing(paths: list[Path]) -> Path | None:
    for p in paths:
        if p.exists():
            return p
    return None
