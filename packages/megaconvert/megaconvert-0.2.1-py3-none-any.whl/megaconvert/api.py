from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import tempfile

from .core import convert as _convert, get_registry
from .utils.files import ext_of

@dataclass(frozen=True)
class ConvertResult:
    src: Path
    dst: Path
    converter: str

def convert_file(src: str | Path, dst: str | Path, **opts: Any) -> ConvertResult:
    res = _convert(src, dst, **opts)
    return ConvertResult(src=res.src, dst=res.dst, converter=res.converter)

def convert_to_dir(src: str | Path, out_dir: str | Path, out_ext: str, **opts: Any) -> ConvertResult:
    src_p = Path(src)
    out_dir_p = Path(out_dir)
    out_dir_p.mkdir(parents=True, exist_ok=True)
    dst = out_dir_p / f"{src_p.stem}.{out_ext.lstrip('.')}"
    return convert_file(src_p, dst, **opts)

def convert_bytes(data: bytes, src_ext: str, dst_ext: str, **opts: Any) -> bytes:
    src_ext = src_ext.lstrip(".").lower()
    dst_ext = dst_ext.lstrip(".").lower()
    with tempfile.TemporaryDirectory() as td:
        td_p = Path(td)
        src_p = td_p / f"input.{src_ext}"
        dst_p = td_p / f"output.{dst_ext}"
        src_p.write_bytes(data)
        _convert(src_p, dst_p, **opts)
        return dst_p.read_bytes()

def probe(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    return {
        "path": str(p),
        "exists": p.exists(),
        "ext": ext_of(p),
        "size": p.stat().st_size if p.exists() else None,
    }

def list_converters(only_available: bool = True) -> list[str]:
    r = get_registry()
    return [c.name for c in r.converters(only_available=only_available)]

def capabilities() -> dict[str, list[tuple[str, str]]]:
    """
    Returns available conversion pairs by converter.
    """
    r = get_registry()
    pairs = r.all_pairs()
    return {k: sorted(list(v)) for k, v in pairs.items()}

def supports(src_ext: str, dst_ext: str) -> bool:
    r = get_registry()
    return r.find(src_ext.lower().lstrip("."), dst_ext.lower().lstrip(".")) is not None
