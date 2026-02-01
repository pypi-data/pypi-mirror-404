from __future__ import annotations
from pathlib import Path
from typing import Any
from .base import BaseConverter
from ..utils.which import which
from ..utils.sh import run
from ..errors import ToolMissing

class Inkscape(BaseConverter):
    name = "vector:inkscape"
    priority = 55

    _IN = {"svg", "svgz", "eps", "pdf", "ai"}  # ai mostly if it's PDF-based
    _OUT = {"svg", "pdf", "eps", "png", "jpg", "jpeg"}

    def available(self) -> bool:
        return which("inkscape") is not None

    def list_pairs(self) -> set[tuple[str, str]]:
        pairs = set()
        for a in self._IN:
            for b in self._OUT:
                if a != b:
                    pairs.add((a, b))
        return pairs

    def convert(self, src: Path, dst: Path, **opts: Any) -> None:
        if not self.available():
            raise ToolMissing("inkscape not found on PATH")

        dpi = opts.get("dpi")
        cmd = ["inkscape", str(src), "--export-filename", str(dst)]
        if dpi and dst.suffix.lower() in {".png", ".jpg", ".jpeg"}:
            cmd += ["--export-dpi", str(int(dpi))]
        run(cmd)
