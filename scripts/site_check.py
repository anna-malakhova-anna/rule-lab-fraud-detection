"""Refuse a site that carries third-party material: image files, <img>, external scripts, stylesheets,
fonts or links to other hosts, and any embedded raster data. Everything on the page is drawn inline.

  uv run python -m scripts.site_check [site_dir]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from scripts.common import ROOT

SITE = ROOT / "site"
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".bmp", ".avif"}
RULES = [
    (re.compile(r"<img\b", re.I), "<img> tag"),
    (re.compile(r"<(script|link|iframe|object|embed)\b[^>]*\b(src|href)\s*=", re.I), "external script/stylesheet/embed"),
    (re.compile(r"url\(\s*['\"]?(https?:)?//", re.I), "remote url() in CSS"),
    (re.compile(r"@import", re.I), "CSS @import"),
    (re.compile(r"data:image/", re.I), "embedded image data"),
    (re.compile(r"<image\b", re.I), "SVG <image>"),
    (re.compile(r"\b(src|href)\s*=\s*['\"]?(https?:)?//", re.I), "link to another host"),
]


def problems(site: Path = SITE) -> list[str]:
    out = []
    for p in sorted(site.rglob("*")):
        if p.is_file() and p.suffix.lower() in IMAGE_EXT:
            out.append(f"{p.relative_to(site)}: image file")
        if p.is_file() and p.suffix.lower() in {".html", ".css", ".js"}:
            text = p.read_text()
            out += [f"{p.relative_to(site)}: {why}" for rx, why in RULES if rx.search(text)]
    return out


def main() -> int:
    site = Path(sys.argv[1]) if len(sys.argv) > 1 else SITE
    found = problems(site)
    for f in found:
        print(f"SITE CHECK: {f}", file=sys.stderr)
    if not found:
        print("site check: OK (no third-party images, scripts, fonts or links)")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
