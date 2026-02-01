from __future__ import annotations
from pathlib import Path
from typing import Any
from .base import BaseConverter
from ..utils.which import which
from ..utils.sh import run
from ..errors import ToolMissing

class Calibre(BaseConverter):
    name = "ebook:calibre"
    priority = 65

    _IN = {"epub", "mobi", "html", "xhtml", "txt", "pdf", "docx", "odt", "rtf", "md"}
    _OUT = {"epub", "mobi", "pdf", "html"}

    def available(self) -> bool:
        return which("ebook-convert") is not None

    def list_pairs(self) -> set[tuple[str, str]]:
        pairs = set()
        for a in self._IN:
            for b in self._OUT:
                if a != b:
                    pairs.add((a, b))
        return pairs

    def convert(self, src: Path, dst: Path, **opts: Any) -> None:
        if not self.available():
            raise ToolMissing("calibre (ebook-convert) not found on PATH")
        cmd = ["ebook-convert", str(src), str(dst)]
        run(cmd)
