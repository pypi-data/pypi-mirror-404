from __future__ import annotations
import subprocess
from typing import Sequence
from ..errors import ConversionFailed

def run(cmd: Sequence[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    p = subprocess.run(list(cmd), capture_output=True, text=True)
    if check and p.returncode != 0:
        tail = (p.stderr or p.stdout or "")[-4000:]
        raise ConversionFailed(f"Command failed ({p.returncode}): {' '.join(cmd)}\n{tail}")
    return p
