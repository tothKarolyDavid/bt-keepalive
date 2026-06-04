"""Tray, executable, and installer icon artwork."""

from __future__ import annotations

from PIL import Image, ImageDraw

# Bluetooth blue; green accent when audio is active.
_BT_BLUE = (0, 122, 255, 255)
_BT_BLUE_DARK = (0, 90, 210, 255)
_ACTIVE_RING = (76, 175, 80, 255)
_ACTIVE_GLOW = (120, 210, 125, 90)
_INACTIVE_BG = (88, 92, 100, 255)
_INACTIVE_BG_DARK = (58, 62, 70, 255)
_SYMBOL = (255, 255, 255, 255)
_SYMBOL_DIM = (200, 204, 212, 255)


def _supersample(size: int) -> int:
    return 4 if size <= 64 else 2


def _circle(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    radius: float,
    fill: tuple[int, int, int, int],
) -> None:
    draw.ellipse(
        (cx - radius, cy - radius, cx + radius, cy + radius),
        fill=fill,
    )


def _bluetooth_polygons(
    cx: float, cy: float, h: float
) -> list[list[tuple[float, float]]]:
    """Filled triangles that form the classic Bluetooth rune."""
    w = h * 0.44
    top = cy - h * 0.40
    mid = cy
    bot = cy + h * 0.40
    right = cx + w
    left = cx - w
    return [
        [(cx, top), (right, cy - h * 0.13), (cx, mid)],
        [(cx, mid), (right, cy + h * 0.13), (cx, bot)],
        [(cx, top), (left, cy - h * 0.13), (cx, mid)],
        [(cx, mid), (left, cy + h * 0.13), (cx, bot)],
    ]


def _draw_bluetooth_symbol(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    scale: float,
    fill: tuple[int, int, int, int],
) -> None:
    h = scale * 0.42
    stem_w = max(2, int(scale * 0.085))
    draw.line(
        [(cx, cy - h * 0.44), (cx, cy + h * 0.44)],
        fill=fill,
        width=stem_w,
    )
    for poly in _bluetooth_polygons(cx, cy, h):
        draw.polygon(poly, fill=fill)


def _draw_active_pulse(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    radius: float,
) -> None:
    """Subtle keepalive arcs — readable at 16px without cluttering the symbol."""
    origin = (cx + radius * 0.08, cy + radius * 0.10)
    for i, spread in enumerate((0.34, 0.48, 0.62)):
        r = radius * spread
        bbox = (
            origin[0] - r,
            origin[1] - r,
            origin[0] + r * 0.12,
            origin[1] + r,
        )
        alpha = 170 - i * 45
        draw.arc(
            bbox,
            start=300,
            end=25,
            fill=(*_ACTIVE_RING[:3], alpha),
            width=max(2, int(radius * 0.09)),
        )


def render_icon(*, active: bool, size: int = 64) -> Image.Image:
    """Render the app icon at ``size``×``size`` pixels (RGBA)."""
    ss = _supersample(size)
    canvas = size * ss
    img = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx = cy = canvas / 2
    outer_r = canvas * 0.46
    inner_r = canvas * 0.40

    if active:
        _circle(draw, cx, cy, outer_r, _BT_BLUE_DARK)
        _circle(draw, cx, cy, inner_r, _BT_BLUE)
        _circle(draw, cx, cy, inner_r + canvas * 0.015, _ACTIVE_GLOW)
        symbol_fill = _SYMBOL
        _draw_active_pulse(draw, cx, cy, inner_r)
    else:
        _circle(draw, cx, cy, outer_r, _INACTIVE_BG_DARK)
        _circle(draw, cx, cy, inner_r, _INACTIVE_BG)
        symbol_fill = _SYMBOL_DIM

    _draw_bluetooth_symbol(draw, cx, cy - canvas * 0.02, inner_r * 1.05, symbol_fill)

    if active:
        badge_r = max(2, int(canvas * 0.045))
        badge_cx = cx + inner_r * 0.62
        badge_cy = cy - inner_r * 0.62
        draw.ellipse(
            (
                badge_cx - badge_r,
                badge_cy - badge_r,
                badge_cx + badge_r,
                badge_cy + badge_r,
            ),
            fill=_ACTIVE_RING,
            outline=(255, 255, 255, 220),
            width=max(1, int(canvas * 0.012)),
        )

    if size != canvas:
        return img.resize((size, size), Image.Resampling.LANCZOS)
    return img


def ico_sizes() -> list[tuple[int, int]]:
    return [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def render_master_for_ico() -> Image.Image:
    """256×256 master used when writing multi-size ``.ico`` files."""
    return render_icon(active=True, size=256)
