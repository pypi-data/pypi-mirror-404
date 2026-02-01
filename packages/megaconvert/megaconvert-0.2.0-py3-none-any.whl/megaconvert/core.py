from __future__ import annotations
from pathlib import Path
from typing import Any
from .registry import ConverterRegistry
from .errors import NoConverterFound, InvalidRequest
from .utils.files import ext_of, ensure_parent
from .plugins import load_builtin_plugins
from .types import ConvertResult

_REGISTRY: ConverterRegistry | None = None

def get_registry() -> ConverterRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        r = ConverterRegistry()
        load_builtin_plugins(r)
        _REGISTRY = r
    return _REGISTRY

def plan(src_ext: str, dst_ext: str) -> str:
    r = get_registry()
    c = r.find(src_ext, dst_ext)
    if not c:
        raise NoConverterFound(f"No available converter for {src_ext} -> {dst_ext}")
    return c.name

def convert(src: str | Path, dst: str | Path, **opts: Any) -> ConvertResult:
    src_p = Path(src)
    dst_p = Path(dst)
    if not src_p.exists():
        raise InvalidRequest(f"Source does not exist: {src_p}")

    src_ext = ext_of(src_p)
    dst_ext = ext_of(dst_p)

    r = get_registry()
    c = r.find(src_ext, dst_ext)
    if not c:
        raise NoConverterFound(f"No available converter for {src_ext} -> {dst_ext}")

    ensure_parent(dst_p)
    c.convert(src_p, dst_p, **opts)
    return ConvertResult(src=src_p, dst=dst_p, converter=c.name)
