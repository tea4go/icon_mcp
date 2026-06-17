import asyncio
import glob
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from icon_mcp.utils.cache import CacheManager
from icon_mcp.utils.saver import IconSaver

# Real iconfont SVGs: one with fill, one with currentColor / no fill attr.
svg1 = (
    '<svg class="icon" viewBox="0 0 1025 1024" xmlns="http://www.w3.org/2000/svg">'
    '<path d="M992 443l-388-404C579 13 546 0 512 0s-66 13-91 38L32 443'
    'c-40 41-34 77-28 92 4 10 20 40 66 40l56 0 0 310c0 70 50 137 122 137'
    'l165 0 0-329c0-35-5-54 30-54l130 0c36 0 30 19 30 54l0 329 165 0'
    'c72 0 122-66 122-137l0-310 56 0c45 0 61-29 66-40C1026 520 1032 484 992 443z"'
    ' fill="#272636" /></svg>'
)
svg2 = (
    '<svg class="icon" style="fill: currentColor;" viewBox="0 0 1024 1024" '
    'xmlns="http://www.w3.org/2000/svg"><path d="M512 51l426 355v532H85V406z'
    'M426 853h170V640H426z m256 0h170V446L512 162 170 446v406h170V554h341z" /></svg>'
)

saver = IconSaver(CacheManager())
out = os.path.join(os.path.dirname(__file__), "_repro_out")
icons = [{"name": "with_fill", "show_svg": svg1},
         {"name": "current_color", "show_svg": svg2}]

errors = []
for fmt in ["svg", "png", "bmp", "ico"]:
    try:
        r = asyncio.run(saver.save_icons(icons, save_path=out, fmt=fmt, size=128))
        if r["failed"]:
            errors.append(f"{fmt}: failed={r['failed']}")
    except Exception as e:
        errors.append(f"{fmt}: EXC {type(e).__name__}: {e}")

# Validate produced raster files
from PIL import Image

for path in sorted(glob.glob(out + "/*")):
    if path.endswith(".svg"):
        continue
    try:
        im = Image.open(path)
        im.load()
        if im.size != (128, 128):
            errors.append(f"{os.path.basename(path)}: size {im.size}")
    except Exception as e:
        errors.append(f"{os.path.basename(path)}: open {e}")

with open(os.path.join(os.path.dirname(__file__), "_repro_result.txt"), "w") as f:
    f.write("FAIL: " + " | ".join(errors) if errors else "ALL_OK")
print("done")
