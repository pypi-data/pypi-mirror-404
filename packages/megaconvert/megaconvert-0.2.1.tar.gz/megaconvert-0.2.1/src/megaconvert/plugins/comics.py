from __future__ import annotations
from pathlib import Path
from typing import Any
import tempfile
from .base import BaseConverter
from ..utils.which import which
from ..utils.sh import run
from ..errors import ToolMissing

class Comics(BaseConverter):
    name = "comics:cbrcbz"
    priority = 15

    def available(self) -> bool:
        return which("7z") is not None or which("7za") is not None

    def _bin(self) -> str:
        return which("7z") or which("7za") or ""

    def list_pairs(self) -> set[tuple[str, str]]:
        return {("cbz", "zip"), ("cbr", "zip"), ("cbr", "cbz"), ("cbz", "cbr")}

    def convert(self, src: Path, dst: Path, **opts: Any) -> None:
        if not self.available():
            raise ToolMissing("7z/7za not found on PATH")

        bin7 = self._bin()
        with tempfile.TemporaryDirectory() as td:
            outdir = Path(td) / "x"
            outdir.mkdir(parents=True, exist_ok=True)
            run([bin7, "x", str(src), f"-o{outdir}", "-y"])
            # repack contents
            run([bin7, "a", str(dst)] + [str(p) for p in outdir.iterdir()])
