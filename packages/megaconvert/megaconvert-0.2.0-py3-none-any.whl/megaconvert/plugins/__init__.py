from __future__ import annotations
from ..registry import ConverterRegistry

def load_builtin_plugins(r: ConverterRegistry) -> None:
    from .pdf_basic import PdfBasic
    from .text_structured import TextStructured
    from .pandoc import Pandoc
    from .libreoffice import LibreOffice
    from .ffmpeg import FFmpeg
    from .imagemagick import ImageMagick
    from .inkscape import Inkscape
    from .ghostscript import Ghostscript
    from .calibre import Calibre
    from .archives import SevenZip
    from .djvu import DjVu
    from .comics import Comics

    # higher priority first is handled by registry
    r.register(PdfBasic())
    r.register(TextStructured())
    r.register(Pandoc())
    r.register(LibreOffice())
    r.register(Calibre())
    r.register(Inkscape())
    r.register(Ghostscript())
    r.register(ImageMagick())
    r.register(FFmpeg())
    r.register(DjVu())
    r.register(Comics())
    r.register(SevenZip())
