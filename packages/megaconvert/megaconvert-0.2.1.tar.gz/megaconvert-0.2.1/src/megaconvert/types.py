from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class ConvertRequest:
    src: Path
    dst: Path
    src_ext: str
    dst_ext: str
    opts: dict[str, Any]

@dataclass(frozen=True)
class ConvertPlan:
    converter_name: str
    notes: str | None = None

@dataclass(frozen=True)
class ConvertResult:
    src: Path
    dst: Path
    converter: str
