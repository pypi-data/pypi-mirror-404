from __future__ import annotations
from pathlib import Path
from typing import Any
from .base import BaseConverter
from ..utils.which import which
from ..utils.sh import run
from ..errors import ToolMissing

class FFmpeg(BaseConverter):
    name = "media:ffmpeg"
    priority = 30

    _AUDIO = {"mp3", "wav", "flac", "aac", "ogg", "m4a", "aiff", "wma", "opus", "oga"}
    _VIDEO = {"mp4", "mkv", "avi", "mov", "webm", "wmv", "flv", "ogv"}
    _SUBS = {"srt", "ass", "vtt", "lrc", "m3u", "m3u8"}  # playlists are special; treat as pass-through mostly

    _IN = _AUDIO | _VIDEO | _SUBS
    _OUT = _AUDIO | _VIDEO | {"gif"} | _SUBS

    def available(self) -> bool:
        return which("ffmpeg") is not None

    def list_pairs(self) -> set[tuple[str, str]]:
        pairs = set()
        for a in self._IN:
            for b in self._OUT:
                if a != b:
                    pairs.add((a, b))
        return pairs

    def convert(self, src: Path, dst: Path, **opts: Any) -> None:
        if not self.available():
            raise ToolMissing("ffmpeg not found on PATH")

        extra = opts.get("ff_args")
        cmd = ["ffmpeg", "-y", "-i", str(src)]
        if isinstance(extra, str) and extra.strip():
            cmd.extend(extra.split())
        cmd.append(str(dst))
        run(cmd)
