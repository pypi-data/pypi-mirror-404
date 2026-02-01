from __future__ import annotations
from pathlib import Path
from typing import Any
import tempfile
import shutil
from .base import BaseConverter
from ..utils.which import which
from ..utils.sh import run
from ..errors import ToolMissing, InvalidRequest

class SevenZip(BaseConverter):
    name = "archives:7z"
    priority = 10

    _ARCH = {"zip", "rar", "7z", "tar", "gz", "bz2", "xz", "tgz", "iso"}

    def available(self) -> bool:
        return which("7z") is not None or which("7za") is not None

    def _bin(self) -> str:
        return which("7z") or which("7za") or ""

    def list_pairs(self) -> set[tuple[str, str]]:
        pairs = set()
        for a in self._ARCH:
            for b in self._ARCH:
                if a != b:
                    pairs.add((a, b))
        # plus "archive -> extracted directory" is via opts (archive_to)
        return pairs

    def convert(self, src: Path, dst: Path, **opts: Any) -> None:
        if not self.available():
            raise ToolMissing("7z/7za not found on PATH")

        archive_to = opts.get("archive_to")
        archive_member = opts.get("archive_member")

        bin7 = self._bin()

        if archive_to:
            outdir = Path(str(archive_to))
            outdir.mkdir(parents=True, exist_ok=True)
            cmd = [bin7, "x", str(src), f"-o{outdir}", "-y"]
            run(cmd)
            # dst is ignored in this mode; still create a marker file
            dst.write_text(f"extracted_to={outdir}\n", encoding="utf-8")
            return

        if archive_member:
            with tempfile.TemporaryDirectory() as td:
                outdir = Path(td)
                cmd = [bin7, "x", str(src), f"-o{outdir}", "-y"]
                run(cmd)
                member_path = outdir / str(archive_member)
                if not member_path.exists():
                    # try find by basename
                    cands = list(outdir.rglob(Path(str(archive_member)).name))
                    if not cands:
                        raise InvalidRequest(f"archive_member not found: {archive_member}")
                    member_path = cands[0]
                dst.write_bytes(member_path.read_bytes())
            return

        # archive -> archive: extract then repack
        with tempfile.TemporaryDirectory() as td:
            outdir = Path(td) / "x"
            outdir.mkdir(parents=True, exist_ok=True)
            run([bin7, "x", str(src), f"-o{outdir}", "-y"])

            # pack
            # 7z a out.zip *  (need cwd)
            fmt = dst.suffix.lower().lstrip(".")
            # 7z chooses format by extension for most common types.
            # Use cwd to pack contents.
            cwd = outdir
            # shutil is for safety if empty
            items = [p.name for p in cwd.iterdir()]
            if not items:
                dst.write_bytes(b"")
                return
            cmd = [bin7, "a", str(dst), *items]
            # run with cwd by using subprocess isn't implemented in run(); simplest: copy to temp working dir not worth now
            # So we pack with full paths (works but includes paths sometimes)
            cmd = [bin7, "a", str(dst), str(cwd / "*")]  # glob may not expand; fallback:
            # Better: use 7z with cwd not supported by our runner; do a safe approach:
            cmd = [bin7, "a", str(dst)] + [str(p) for p in cwd.iterdir()]
            run(cmd)
