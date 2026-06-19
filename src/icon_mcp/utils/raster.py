"""SVG 栅格化辅助：reportlab/svglib 渲染默认填不透明白底，
本模块提供边界 flood-fill 抠白，把与图像边界连通的白色像素置为透明，
同时保留图标内部被非白色包围的白色（如蓝底白字）。"""

from __future__ import annotations


def render_svg(svg_content: str, size: int, edge_transparent: bool = False):
    """超采样渲染 SVG 到 size×size 的 RGBA 图像。

    在矢量阶段按 (size×supersample) 渲染再缩回目标尺寸，避免"先渲染原生小
    位图再放大"导致的模糊。MCP 保存与 Web 下载两条路径共用此函数，保证一致。

    edge_transparent: True 时把与边界连通的白色像素抠成透明（png/ico 用）。
    """
    import io

    from PIL import Image
    from reportlab.graphics import renderPM
    from svglib.svglib import svg2rlg

    drawing = svg2rlg(io.StringIO(svg_content))
    if drawing is None:
        raise ValueError("Failed to parse SVG content")

    supersample = 4
    target = size * supersample
    ow, oh = drawing.width, drawing.height
    if ow and oh:
        drawing.scale(target / ow, target / oh)
        drawing.width, drawing.height = target, target

    img = renderPM.drawToPIL(drawing)
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    if img.size != (size, size):
        img = img.resize((size, size), Image.LANCZOS)

    if edge_transparent:
        img = make_edge_transparent(img)
    return img


def make_edge_transparent(img, threshold: int = 245):
    """将与边界连通的近白色像素 alpha 置 0，返回处理后的 RGBA 图像。

    img: PIL.Image（任意模式，内部转 RGBA）
    threshold: RGB 三通道均 >= 该值视为白色
    """
    from collections import deque

    if img.mode != "RGBA":
        img = img.convert("RGBA")
    w, h = img.size
    px = img.load()

    def is_white(p):
        return p[0] >= threshold and p[1] >= threshold and p[2] >= threshold

    visited = bytearray(w * h)
    q = deque()
    for x in range(w):
        q.append((x, 0))
        q.append((x, h - 1))
    for y in range(h):
        q.append((0, y))
        q.append((w - 1, y))

    while q:
        x, y = q.popleft()
        if x < 0 or y < 0 or x >= w or y >= h:
            continue
        idx = y * w + x
        if visited[idx]:
            continue
        visited[idx] = 1
        r, g, b, a = px[x, y]
        if not is_white((r, g, b)):
            continue
        px[x, y] = (r, g, b, 0)
        q.append((x + 1, y))
        q.append((x - 1, y))
        q.append((x, y + 1))
        q.append((x, y - 1))

    return img
