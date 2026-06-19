"""Icon saver - saves icons to local filesystem."""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any

from ..lang import t
from ..models import SelectionData, SelectionStatus
from .cache import CacheManager


class IconSaver:
    """Handles saving icons to local files and sending selections to MCP client."""

    def __init__(self, cache: CacheManager):
        self.cache = cache

    SUPPORTED_FORMATS = ("svg", "png", "bmp", "ico")

    async def save_icons(
        self,
        icons: list[dict[str, Any]],
        save_path: str = "./saved-icons",
        fmt: str = "svg",
        size: int = 128,
    ) -> dict[str, Any]:
        """Save icon data to local files in the requested format.

        ``fmt`` is one of svg/png/bmp/ico. ``svg`` writes the raw vector
        markup; the raster formats rasterize the SVG to a ``size`` x ``size``
        image.
        """
        if not icons:
            raise ValueError("No icons to save")

        fmt = (fmt or "svg").lower()
        if fmt not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format '{fmt}'. "
                f"Supported: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        full_path = os.path.abspath(save_path)
        os.makedirs(full_path, exist_ok=True)

        saved: list[str] = []
        failed: list[str] = []

        for icon in icons:
            name = icon.get("name", "unknown")
            svg_content = icon.get("svg", icon.get("show_svg", ""))
            if not svg_content:
                failed.append(name)
                continue

            file_name = f"{name}.{fmt}"
            file_path = os.path.join(full_path, file_name)
            try:
                if fmt == "svg":
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(svg_content)
                else:
                    self._save_raster(svg_content, file_path, fmt, size)
                saved.append(file_name)
                print(t("download.saved", {"fileName": file_name}), file=sys.stderr)
            except Exception as e:
                print(
                    t("download.saveFailed", {"name": name}) + f": {e}",
                    file=sys.stderr,
                )
                failed.append(name)

        return {
            "saved": saved,
            "failed": failed,
            "save_path": full_path,
            "message": t(
                "download.saveCompleted", {"count": len(saved), "path": full_path}
            ),
        }

    @staticmethod
    def _save_raster(svg_content: str, file_path: str, fmt: str, size: int) -> None:
        """Rasterize SVG markup and write it as png/bmp/ico."""
        from PIL import Image

        from .raster import render_svg

        img = render_svg(svg_content, size, edge_transparent=fmt in ("png", "ico"))

        if fmt == "png":
            img.save(file_path, "PNG")
        elif fmt == "ico":
            img.save(file_path, "ICO", sizes=[(size, size)])
        elif fmt == "bmp":
            # BMP has no alpha channel; composite onto a white background.
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            background.save(file_path, "BMP")

    def send_to_mcp_client(
        self, icons: list[dict[str, Any]], search_id: str
    ) -> None:
        """Mark selection as completed in the cache.

        The MCP server will pick up the completed selection
        when check_selection_status is polled.
        """
        self.cache.set_selection(
            search_id,
            SelectionData(
                status=SelectionStatus.COMPLETED,
                search_id=search_id,
                timestamp=time.time(),
                connected=True,
                selected_icons=icons,
            ),
        )

        print(
            t("selection.userSelectedIcons", {"count": len(icons)}),
            file=sys.stderr,
        )
