# megaconvert

Plugin-based **advanced file conversion** toolkit with a clean **Python API** and a practical **CLI**.

- ✅ CLI: `megaconvert convert in.docx out.pdf`
- ✅ Python: `from megaconvert import convert_file, convert_bytes`
- ✅ Extensible: add converters as plugins
- ✅ “As many formats as possible”: uses best-in-class external engines when available

> **Reality check:** there is no single pure-Python library that reliably converts *everything to everything*.  
> `megaconvert` solves this by providing **one unified interface** while delegating to proven tools
> (Pandoc, LibreOffice, FFmpeg, ImageMagick, …) when installed.

---

## Features

### Core
- One API for documents, images, audio/video, ebooks, archives
- Plugin registry with priorities (best converter wins)
- Runtime capability detection (depends on installed tools)
- Safe defaults with optional advanced flags (`dpi`, `quality`, custom args)

### Highlights
- **Docs / Office:** `doc/docx/odt/rtf/xls/xlsx/ods/ppt/pptx/odp` → `pdf` (LibreOffice)
- **Markup:** `md/html/xhtml/tex/latex/txt` → `pdf/docx/odt/epub` (Pandoc)
- **Media:** audio/video + subtitle conversions (FFmpeg)
- **Images:** raster & vector conversions (ImageMagick / Inkscape / Ghostscript)
- **Ebooks:** `epub ↔ mobi` and more (Calibre)
- **Archives:** `zip/rar/7z/tar/gz/bz2/xz/tgz/iso` repack/extract (7-Zip)
- **PDF utilities:** page selection (`pdf → pdf`) in pure Python
- **Structured text:** `json/csv/tsv/yaml/xml/toml` best-effort conversions

---

## Supported formats (best-effort)

### Documents / Text
`txt pdf doc docx odt rtf md html xhtml epub mobi csv tsv xls xlsx ods json xml yaml yml ini toml log tex latex ps ppt pptx odp pdfa djvu odf sxw sxc sxm`

### Images / Graphics
`jpg jpeg png gif bmp tiff tif webp svg svgz heic avif psd ai eps emf wmf ico icns ppm pgm pbm jp2 j2k mj2`

### Audio / Video / Subtitles
`mp3 wav flac aac ogg m4a aiff wma mp4 mkv avi mov webm wmv flv ogv oga opus m3u m3u8 srt ass vtt lrc`

### Archives / Containers
`zip rar 7z tar gz bz2 xz tgz iso cbr cbz`

> Actual support depends on installed external tools.  
> Run `megaconvert capabilities` to see what works on your machine.

---

## Quickstart

### Install package
```bash
pip install -e .

Optional Python extras:

pip install -e ".[dev,yaml,xml,toml,ocr]"

Verify installation

megaconvert list
megaconvert capabilities

Convert a file

megaconvert convert in.docx out.pdf
megaconvert convert in.png out.webp --quality 85
megaconvert convert in.mp4 out.mp3 --ff-args "-vn -b:a 192k"
megaconvert convert in.pdf out.pdf --pages "1-3,5"

External tools (recommended)

megaconvert delegates real work to proven tools when available.

    LibreOffice (soffice) – Office / ODF formats

    Pandoc – Markup & document conversions

    FFmpeg – Audio, video, subtitles

    ImageMagick (magick) – Raster images, PS/PDF routes

    Inkscape – SVG/SVGZ/EPS/PDF vector formats

    Ghostscript (gs) – PS/EPS/PDF, PDF/A

    Calibre (ebook-convert) – EPUB/MOBI and ebooks

    7-Zip (7z) – Archives

    DjVuLibre (ddjvu) – DjVu → PDF/images

    Tesseract – OCR (optional)

Installing external tools
Ubuntu / Debian

sudo apt update
sudo apt install -y \
  pandoc \
  libreoffice \
  ffmpeg \
  imagemagick \
  inkscape \
  ghostscript \
  p7zip-full \
  djvulibre-bin \
  tesseract-ocr \
  tesseract-ocr-hun

macOS (Homebrew)

brew install pandoc libreoffice ffmpeg imagemagick inkscape ghostscript p7zip djvulibre tesseract

Windows

Install tools manually or via Chocolatey and ensure they are on PATH:

    ffmpeg, pandoc, 7zip

    LibreOffice, ImageMagick, Inkscape, Ghostscript, Tesseract

CLI usage
List converters

megaconvert list

Show available conversion pairs

megaconvert capabilities

Check if a conversion is supported

megaconvert supports docx pdf

Convert

megaconvert convert in.docx out.pdf
megaconvert convert in.svg out.png --dpi 300
megaconvert convert in.mp4 out.webm --ff-args "-c:v libvpx -crf 30 -b:v 0"

Archives

# Extract archive
megaconvert convert archive.rar dummy.txt --archive-to extracted_dir

# Extract a single member
megaconvert convert archive.zip report.pdf --archive-member "docs/report.pdf"

Python usage
File → file

from megaconvert import convert_file

res = convert_file("in.docx", "out.pdf")
print(res.converter)

Bytes → bytes (web backend friendly)

from megaconvert import convert_bytes

with open("in.png", "rb") as f:
    out = convert_bytes(f.read(), "png", "webp", quality=80)

with open("out.webp", "wb") as f:
    f.write(out)

Capabilities / supports

from megaconvert import capabilities, supports

print(supports("docx", "pdf"))
caps = capabilities()

Conversion engines overview
Engine	Purpose
LibreOffice	Office/ODF → PDF and office formats
Pandoc	Markup & document conversions
FFmpeg	Audio/video/subtitles
ImageMagick	Raster images, PS/PDF rasterization
Inkscape	Vector graphics
Ghostscript	PS/EPS/PDF, PDF/A
Calibre	Ebook conversions
7-Zip	Archive repack/extract
DjVuLibre	DjVu conversions
Tesseract	OCR
Troubleshooting

    Tool not found → install it and ensure it’s on PATH

    ImageMagick PDF blocked → check policy.xml

    LibreOffice rendering issues → install common fonts

    Different capabilities on different machines → expected; tools differ

Security notes

If exposed as a public service:

    Run conversions in sandboxed containers

    Apply CPU/memory/time limits

    Treat uploaded files as untrusted input

Contributing

PRs welcome:

    New plugins

    Better format coverage

    Tests and docs improvements

pip install -e ".[dev]"
pytest

## License

This project is licensed under the **PolyForm Noncommercial License 1.0.0**.

- ✅ Free for personal, educational, and internal use
- ✅ Modification and redistribution allowed
- ❌ Commercial use is **not permitted**

For commercial licensing, please contact the author.
