from __future__ import annotations
from pathlib import Path
from typing import Any
from .base import BaseConverter
from ..utils.which import which
from ..utils.sh import run
from ..errors import ToolMissing

class DjVu(BaseConverter):
    name = "docs:djvu"
    priority = 20

    def available(self) -> bool:
        return which("ddjvu") is not None

    def list_pairs(self) -> set[tuple[str, str]]:
        return {("djvu", "pdf"), ("djvu", "tiff"), ("djvu", "png")}

    def convert(self, src: Path, dst: Path, **opts: Any) -> None:
        if not self.available():
            raise ToolMissing("ddjvu not found on PATH (DjVuLibre)")

        d = dst.suffix.lower().lstrip(".")
        if d == "pdf":
            run(["ddjvu", "-format=pdf", str(src), str(dst)])
        elif d == "tiff":
            run(["ddjvu", "-format=tiff", str(src), str(dst)])
        elif d == "png":
            run(["ddjvu", "-format=png", str(src), str(dst)])
        else:
            raise RuntimeError(f"Unsupported djvu output: {d}")
