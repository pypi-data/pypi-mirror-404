from __future__ import annotations
from pathlib import Path
from typing import Any
import json as _json
import csv
from .base import BaseConverter

_TEXT = {"txt", "log"}
_TAB = {"csv", "tsv"}
_STRUCT = {"json", "xml", "yaml", "yml", "ini", "toml"}

class TextStructured(BaseConverter):
    name = "text:structured"
    priority = 80

    def list_pairs(self) -> set[tuple[str, str]]:
        pairs: set[tuple[str, str]] = set()

        # pass-through / normalize
        for a in _TEXT | _TAB | {"json"}:
            pairs.add((a, a))
            pairs.add((a, "txt"))

        # csv <-> tsv
        pairs |= {("csv", "tsv"), ("tsv", "csv")}

        # json <-> csv/tsv (basic)
        pairs |= {("json", "csv"), ("json", "tsv"), ("csv", "json"), ("tsv", "json")}

        # yaml/toml/xml are best-effort if libs available
        for a in {"yaml", "yml", "toml", "xml"}:
            pairs.add((a, "txt"))
            pairs.add((a, "json"))
            pairs.add(("json", a))
        return pairs

    def _read_tab(self, src: Path, delimiter: str) -> list[dict[str, Any]]:
        with open(src, "r", encoding="utf-8", errors="ignore", newline="") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            return list(reader)

    def _write_tab(self, dst: Path, rows: list[dict[str, Any]], delimiter: str) -> None:
        if not rows:
            dst.write_text("", encoding="utf-8")
            return
        with open(dst, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter=delimiter)
            writer.writeheader()
            writer.writerows(rows)

    def convert(self, src: Path, dst: Path, **opts: Any) -> None:
        s = src.suffix.lower().lstrip(".")
        d = dst.suffix.lower().lstrip(".")

        if s in _TEXT and d == "txt":
            dst.write_text(src.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
            return

        if s in _TAB and d == "txt":
            dst.write_text(src.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
            return

        if s == "csv" and d == "tsv":
            rows = self._read_tab(src, ",")
            self._write_tab(dst, rows, "\t")
            return

        if s == "tsv" and d == "csv":
            rows = self._read_tab(src, "\t")
            self._write_tab(dst, rows, ",")
            return

        if s == "json" and d in {"csv", "tsv"}:
            obj = _json.loads(src.read_text(encoding="utf-8", errors="ignore") or "[]")
            if isinstance(obj, dict):
                obj = [obj]
            if not isinstance(obj, list):
                obj = []
            rows = [r for r in obj if isinstance(r, dict)]
            self._write_tab(dst, rows, "," if d == "csv" else "\t")
            return

        if s in {"csv", "tsv"} and d == "json":
            rows = self._read_tab(src, "," if s == "csv" else "\t")
            dst.write_text(_json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
            return

        # Optional structured formats
        if d == "json" and s in {"yaml", "yml"}:
            try:
                import yaml
            except Exception:
                raise RuntimeError("PyYAML missing. Install with: pip install megaconvert[yaml]")
            obj = yaml.safe_load(src.read_text(encoding="utf-8", errors="ignore"))
            dst.write_text(_json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
            return

        if s == "json" and d in {"yaml", "yml"}:
            try:
                import yaml
            except Exception:
                raise RuntimeError("PyYAML missing. Install with: pip install megaconvert[yaml]")
            obj = _json.loads(src.read_text(encoding="utf-8", errors="ignore") or "null")
            dst.write_text(yaml.safe_dump(obj, allow_unicode=True, sort_keys=False), encoding="utf-8")
            return

        if d == "json" and s == "toml":
            try:
                import tomllib  # py3.11+
                obj = tomllib.loads(src.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                try:
                    import tomli
                    obj = tomli.loads(src.read_text(encoding="utf-8", errors="ignore"))
                except Exception as e:
                    raise RuntimeError("TOML parser missing. Install with: pip install megaconvert[toml]") from e
            dst.write_text(_json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
            return

        if s == "json" and d == "toml":
            try:
                import tomli_w
            except Exception as e:
                raise RuntimeError("TOML writer missing. Install tomli-w manually: pip install tomli-w") from e
            obj = _json.loads(src.read_text(encoding="utf-8", errors="ignore") or "null")
            dst.write_text(tomli_w.dumps(obj), encoding="utf-8")
            return

        if d == "json" and s == "xml":
            try:
                import xml.etree.ElementTree as ET
            except Exception as e:
                raise RuntimeError("XML parser unavailable") from e
            tree = ET.parse(src)
            root = tree.getroot()
            def to_dict(el):
                return {
                    "tag": el.tag,
                    "attrib": dict(el.attrib),
                    "text": (el.text or "").strip(),
                    "children": [to_dict(c) for c in list(el)],
                }
            obj = to_dict(root)
            dst.write_text(_json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
            return

        if d == "txt":
            dst.write_text(src.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
            return

        raise RuntimeError(f"Unsupported structured conversion {s} -> {d}")
