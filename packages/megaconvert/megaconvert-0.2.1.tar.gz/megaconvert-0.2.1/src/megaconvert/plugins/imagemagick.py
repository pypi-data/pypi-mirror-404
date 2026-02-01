from __future__ import annotations
from pathlib import Path
from typing import Any
from .base import BaseConverter
from ..utils.which import which
from ..utils.sh import run
from ..errors import ToolMissing

class ImageMagick(BaseConverter):
    name = "images:magick"
    priority = 40

    _MAGICK = {"magick", "convert"}
    _RASTER = {
        "jpg", "jpeg", "png", "gif", "bmp", "tiff", "tif", "webp",
        "heic", "avif",
        "ico", "icns",
        "ppm", "pgm", "pbm",
        "jp2", "j2k", "mj2",
        "emf", "wmf",
        "psd",  # read-only usually
    }
    _DOCIMG = {"pdf", "ps", "eps"}

    def available(self) -> bool:
        return which("magick") is not None or which("convert") is not None

    def _cmd(self) -> str:
        return which("magick") or which("convert") or ""

    def list_pairs(self) -> set[tuple[str, str]]:
        pairs = set()
        all_in = self._RASTER | self._DOCIMG
        all_out = self._RASTER | {"png", "jpg", "jpeg", "tiff", "webp"}
        for a in all_in:
            for b in all_out:
                if a != b:
                    pairs.add((a, b))
        return pairs

    def convert(self, src: Path, dst: Path, **opts: Any) -> None:
        if not self.available():
            raise ToolMissing("ImageMagick (magick/convert) not found on PATH")

        cmd0 = self._cmd()
        quality = opts.get("quality")
        dpi = opts.get("dpi")

        cmd = [cmd0]
        # "magick" expects: magick input output; "convert" expects: convert input output
        if cmd0.endswith("magick"):
            # ok
            pass

        if dpi and src.suffix.lower() in {".pdf", ".ps", ".eps"}:
            cmd += ["-density", str(int(dpi))]

        cmd += [str(src)]
        if quality and dst.suffix.lower() in {".jpg", ".jpeg", ".webp"}:
            cmd += ["-quality", str(int(quality))]
        cmd += [str(dst)]

        run(cmd)
