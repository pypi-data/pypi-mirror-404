from __future__ import annotations
from pathlib import Path
from typing import Any
import tempfile
from .base import BaseConverter
from ..utils.which import which
from ..utils.sh import run
from ..errors import ToolMissing
from ..utils.files import first_existing

class LibreOffice(BaseConverter):
    name = "docs:libreoffice"
    priority = 60

    _IN = {
        "doc", "docx", "odt", "rtf",
        "xls", "xlsx", "ods",
        "ppt", "pptx", "odp",
        "odf", "sxw", "sxc", "sxm",
        "pages", "numbers", "keynote",  # sometimes works via import filters; often not
    }
    _OUT = {"pdf", "docx", "odt", "xlsx", "ods", "pptx", "odp", "html", "txt"}

    def available(self) -> bool:
        return (which("soffice") or which("libreoffice")) is not None

    def list_pairs(self) -> set[tuple[str, str]]:
        pairs = set()
        for a in self._IN:
            for b in self._OUT:
                if a != b:
                    pairs.add((a, b))
        return pairs

    def convert(self, src: Path, dst: Path, **opts: Any) -> None:
        soffice = which("soffice") or which("libreoffice")
        if not soffice:
            raise ToolMissing("LibreOffice (soffice) not found on PATH")

        out_ext = dst.suffix.lstrip(".").lower()
        lo_filter = opts.get("lo_filter")  # optional override
        convert_to = out_ext if not lo_filter else f"{out_ext}:{lo_filter}"

        with tempfile.TemporaryDirectory() as td:
            cmd = [
                soffice, "--headless", "--nologo", "--norestore",
                "--convert-to", convert_to,
                "--outdir", td,
                str(src),
            ]
            run(cmd)

            produced = first_existing([
                Path(td) / f"{src.stem}.{out_ext}",
                *list(Path(td).glob(f"*.{out_ext}")),
            ])
            if not produced:
                raise RuntimeError("LibreOffice produced no output file.")
            dst.write_bytes(produced.read_bytes())
