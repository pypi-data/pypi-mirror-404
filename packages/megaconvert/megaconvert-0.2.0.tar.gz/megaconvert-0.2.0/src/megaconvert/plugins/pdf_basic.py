from __future__ import annotations
from pathlib import Path
from typing import Any
from pypdf import PdfReader, PdfWriter
from .base import BaseConverter

class PdfBasic(BaseConverter):
    name = "pdf:basic"
    priority = 90

    def list_pairs(self) -> set[tuple[str, str]]:
        return {("pdf", "pdf")}

    def _parse_pages(self, spec: str, total: int) -> list[int]:
        out: list[int] = []
        parts = [p.strip() for p in spec.split(",") if p.strip()]
        for p in parts:
            if "-" in p:
                a, b = p.split("-", 1)
                a_i = int(a); b_i = int(b)
                for k in range(a_i, b_i + 1):
                    if 1 <= k <= total:
                        out.append(k - 1)
            else:
                k = int(p)
                if 1 <= k <= total:
                    out.append(k - 1)
        seen = set()
        res = []
        for i in out:
            if i not in seen:
                seen.add(i)
                res.append(i)
        return res

    def convert(self, src: Path, dst: Path, **opts: Any) -> None:
        pages_spec = opts.get("pages")
        r = PdfReader(str(src))
        w = PdfWriter()

        idxs = self._parse_pages(str(pages_spec), len(r.pages)) if pages_spec else list(range(len(r.pages)))
        for i in idxs:
            w.add_page(r.pages[i])

        with open(dst, "wb") as f:
            w.write(f)
