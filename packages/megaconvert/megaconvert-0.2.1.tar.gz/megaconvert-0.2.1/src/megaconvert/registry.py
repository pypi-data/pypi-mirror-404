from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Protocol

class Converter(Protocol):
    name: str
    priority: int

    def available(self) -> bool: ...
    def supports(self, src_ext: str, dst_ext: str) -> bool: ...
    def convert(self, src: Path, dst: Path, **opts: Any) -> None: ...
    def list_pairs(self) -> set[tuple[str, str]]: ...

@dataclass
class _Entry:
    c: Converter

class ConverterRegistry:
    def __init__(self) -> None:
        self._items: list[_Entry] = []

    def register(self, c: Converter) -> None:
        self._items.append(_Entry(c=c))
        self._items.sort(key=lambda e: getattr(e.c, "priority", 0), reverse=True)

    def converters(self, *, only_available: bool = False) -> list[Converter]:
        if not only_available:
            return [e.c for e in self._items]
        return [e.c for e in self._items if e.c.available()]

    def find(self, src_ext: str, dst_ext: str) -> Converter | None:
        for c in self.converters(only_available=True):
            if c.supports(src_ext, dst_ext):
                return c
        return None

    def all_pairs(self) -> dict[str, set[tuple[str, str]]]:
        out: dict[str, set[tuple[str, str]]] = {}
        for c in self.converters(only_available=True):
            out[c.name] = c.list_pairs()
        return out
