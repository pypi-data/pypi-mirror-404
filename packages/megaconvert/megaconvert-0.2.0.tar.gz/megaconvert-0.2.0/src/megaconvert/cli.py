from __future__ import annotations
import argparse
import json
from .api import (
    convert_file,
    probe,
    list_converters,
    capabilities,
    supports,
)

def main() -> None:
    ap = argparse.ArgumentParser(prog="megaconvert", description="Advanced converter (CLI + Python API).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List converters")

    sub.add_parser("capabilities", help="List available conversion pairs (based on installed tools)")

    p_sup = sub.add_parser("supports", help="Check if conversion is possible")
    p_sup.add_argument("src_ext")
    p_sup.add_argument("dst_ext")

    p_probe = sub.add_parser("probe", help="Probe a file")
    p_probe.add_argument("path")

    p_conv = sub.add_parser("convert", help="Convert a file")
    p_conv.add_argument("src")
    p_conv.add_argument("dst")
    p_conv.add_argument("--pages", default=None, help="PDF page range e.g. 1-3,5")
    p_conv.add_argument("--quality", type=int, default=None, help="Image quality 1-95")
    p_conv.add_argument("--dpi", type=int, default=None, help="Rasterize DPI hint (gs/magick)")
    p_conv.add_argument("--ff-args", default=None, help="Extra ffmpeg args (string)")
    p_conv.add_argument("--pandoc-args", default=None, help="Extra pandoc args (string)")
    p_conv.add_argument("--lo-filter", default=None, help="LibreOffice filter string override")
    p_conv.add_argument("--ocr-lang", default=None, help="OCR language (if OCR plugin enabled)")
    p_conv.add_argument("--archive-member", default=None, help="Extract a specific member from archive")
    p_conv.add_argument("--archive-to", default=None, help="Extract archive to directory")

    args = ap.parse_args()

    if args.cmd == "list":
        for n in list_converters(True):
            print(n)
        return

    if args.cmd == "capabilities":
        print(json.dumps(capabilities(), ensure_ascii=False, indent=2))
        return

    if args.cmd == "supports":
        print("yes" if supports(args.src_ext, args.dst_ext) else "no")
        return

    if args.cmd == "probe":
        print(json.dumps(probe(args.path), ensure_ascii=False, indent=2))
        return

    if args.cmd == "convert":
        opts = {}
        if args.pages is not None: opts["pages"] = args.pages
        if args.quality is not None: opts["quality"] = args.quality
        if args.dpi is not None: opts["dpi"] = args.dpi
        if args.ff_args is not None: opts["ff_args"] = args.ff_args
        if args.pandoc_args is not None: opts["pandoc_args"] = args.pandoc_args
        if args.lo_filter is not None: opts["lo_filter"] = args.lo_filter
        if args.ocr_lang is not None: opts["ocr_lang"] = args.ocr_lang
        if args.archive_member is not None: opts["archive_member"] = args.archive_member
        if args.archive_to is not None: opts["archive_to"] = args.archive_to

        res = convert_file(args.src, args.dst, **opts)
        print(json.dumps({"src": str(res.src), "dst": str(res.dst), "converter": res.converter}, ensure_ascii=False))
        return
