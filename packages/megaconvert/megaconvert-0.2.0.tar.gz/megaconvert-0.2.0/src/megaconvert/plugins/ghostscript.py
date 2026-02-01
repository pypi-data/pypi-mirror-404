from __future__ import annotations
from pathlib import Path
from typing import Any
from .base import BaseConverter
from ..utils.which import which
from ..utils.sh import run
from ..errors import ToolMissing

class Ghostscript(BaseConverter):
    name = "docs:ghostscript"
    priority = 50

    _IN = {"ps", "eps", "pdf"}
    _OUT = {"pdf", "pdfa", "png", "jpg", "jpeg", "tiff"}

    def available(self) -> bool:
        return which("gs") is not None

    def list_pairs(self) -> set[tuple[str, str]]:
        pairs = set()
        for a in self._IN:
            for b in self._OUT:
                if a != b:
                    pairs.add((a, b))
        return pairs

    def convert(self, src: Path, dst: Path, **opts: Any) -> None:
        if not self.available():
            raise ToolMissing("ghostscript (gs) not found on PATH")

        d = dst.suffix.lower().lstrip(".")
        dpi = int(opts.get("dpi") or 150)

        if d == "pdf":
            cmd = ["gs", "-dBATCH", "-dNOPAUSE", "-sDEVICE=pdfwrite", f"-sOutputFile={dst}", str(src)]
            run(cmd); return

        if d == "pdfa":
            # minimal PDF/A attempt; proper PDF/A often needs ICC profile setup.
            cmd = ["gs", "-dBATCH", "-dNOPAUSE", "-sDEVICE=pdfwrite", "-dPDFA=1", f"-sOutputFile={dst}", str(src)]
            run(cmd); return

        device = {"png": "png16m", "jpg": "jpeg", "jpeg": "jpeg", "tiff": "tiff24nc"}.get(d)
        if not device:
            raise RuntimeError(f"Unsupported gs output: {d}")

        cmd = [
            "gs", "-dBATCH", "-dNOPAUSE",
            f"-sDEVICE={device}",
            f"-r{dpi}",
            f"-sOutputFile={dst}",
            str(src),
        ]
        run(cmd)
