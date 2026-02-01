from __future__ import annotations
from pathlib import Path
from typing import Any
from .base import BaseConverter
from ..utils.which import which
from ..utils.sh import run
from ..errors import ToolMissing

class Pandoc(BaseConverter):
    name = "docs:pandoc"
    priority = 70

    _IN = {"txt", "md", "html", "xhtml", "rtf", "tex", "latex"}
    _OUT = {"pdf", "docx", "odt", "epub", "html", "xhtml", "txt", "rtf"}

    def available(self) -> bool:
        return which("pandoc") is not None

    def list_pairs(self) -> set[tuple[str, str]]:
        pairs = set()
        for a in self._IN:
            for b in self._OUT:
                if a != b:
                    pairs.add((a, b))
        return pairs

    def convert(self, src: Path, dst: Path, **opts: Any) -> None:
        if not self.available():
            raise ToolMissing("pandoc not found on PATH")

        args = ["pandoc", str(src), "-o", str(dst)]
        extra = opts.get("pandoc_args")
        if isinstance(extra, str) and extra.strip():
            args.extend(extra.split())

        run(args)
