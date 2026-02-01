from __future__ import annotations
from typing import Any
from pathlib import Path

class BaseConverter:
    name = "base"
    priority = 0

    def available(self) -> bool:
        return True

    def supports(self, src_ext: str, dst_ext: str) -> bool:
        return (src_ext.lower(), dst_ext.lower()) in self.list_pairs()

    def list_pairs(self) -> set[tuple[str, str]]:
        return set()

    def convert(self, src: Path, dst: Path, **opts: Any) -> None:
        raise NotImplementedError
