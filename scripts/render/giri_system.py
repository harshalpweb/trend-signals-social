# -*- coding: utf-8 -*-
"""TrendGiri production system: Direction A ('Bazaar Receipt'), amended
with B's type scale and C's annotation hand, per
docs/consults/2026-08-29-group-cto-instagram-trendy-design-round2-selection.md.
Fixes both named A-prototype bugs: stamps never occlude data; green is
reserved strictly for up-moves."""
import math
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import base as R

FONT_DIR = R.FONT_DIR
W, H, SCALE = R.W, R.H, R.SCALE
SW, SH = R.SW, R.SH

def S(v):
    return R.S(v)

def hx(h):
    return R.hx(h)

# ---- palette ----
CREAM = "#F5EEE2"
PAPER_WHITE = "#FFFDF8"
INK = "#1A1714"
INK_SOFT = "#4A443B"
MUTED = "#6B655A"
MARIGOLD = "#FFB627"
STAMP_RED = "#E23D28"
MARKET_GREEN = "#1F7A4D"
LINE_GRAY = "#C9BFA9"

# ---- fonts ----
def anton(size):
    return ImageFont.truetype(os.path.join(FONT_DIR, "Anton-Regular.ttf"), size)

def archivo_black(size):
    return ImageFont.truetype(os.path.join(FONT_DIR, "ArchivoBlack-Regular.ttf"), size)

def caveat(size, weight=700):
    f = ImageFont.truetype(os.path.join(FONT_DIR, "Caveat-Bold.ttf"), size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f

def mono(size):
    return R.plex_mono_semibold(size)

def sans(size, weight=500):
    return R.inter(size, weight)

def grotesk(size):
    return R.space_grotesk_bold(size)

# ---- canvas / chrome ----
def new_canvas(grain_alpha=13):
    img = Image.new("RGB", (SW, SH), hx(CREAM)).convert("RGBA")
    noise = Image.effect_noise((SW, SH), 24).convert("L")
    ov_rgb = Image.new("RGBA", (SW, SH), (0, 0, 0, 255))
    ov_rgb.putalpha(noise.point(lambda p: int(p * grain_alpha / 255)))
    img = Image.alpha_composite(img, ov_rgb)
    return img, ImageDraw.Draw(img, "RGBA")

def draw_logo(d):
    cx, cy, r = 44, 56, 19
    R.circle(d, cx, cy, r, outline=hx(INK), width=3)
    d.ellipse([S(cx - r * 0.45), S(cy - r), S(cx + r * 0.45), S(cy + r)], outline=hx(INK), width=S(2))
    R.line(d, (cx - r, cy, cx + r, cy), fill=hx(INK), width=2)
    R.text(d, (cx + r + 14, cy), "TrendGiri", grotesk(28), hx(INK), anchor="lm")

def kicker(d, s, y=112):
    R.text(d, (60, y), s.upper(), sans(24, 700), hx(MUTED), anchor="la", tracking=1.3)

def footer(d, page, total):
    fy = 1200
    R.line(d, (60, fy, 1020, fy), fill=hx(LINE_GRAY), width=1)
    R.text(d, (60, fy + 18), "TrendGiri | swipe →", sans(24, 600), hx(INK_SOFT), anchor="la")
    R.text(d, (1020, fy + 18), f"{page}/{total}", mono(24), hx(STAMP_RED), anchor="ra")

def source_line(d, s, y=1170):
    R.text(d, (60, y), s, sans(21, 600), hx(MUTED), anchor="la")

def headline(d, lines, y=170, size=150, lh=0.98):
    f = anton(size)
    fy = y
    for ln in lines:
        R.text(d, (56, fy), ln, f, hx(INK), anchor="la")
        fy += size * lh
    return fy

def rotate_paste(base, layer, cx, cy, angle_deg):
    rotated = layer.rotate(angle_deg, expand=True, resample=Image.BICUBIC)
    x = int(cx * SCALE - rotated.width / 2)
    y = int(cy * SCALE - rotated.height / 2)
    base.alpha_composite(rotated, (x, y))

def drop_shadow(base, w_1080, h_1080, cx, cy, angle, blur=14, alpha=65):
    shadow = Image.new("RGBA", (S(w_1080), S(h_1080)), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rectangle([0, 0, S(w_1080), S(h_1080)], fill=(0, 0, 0, alpha))
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    rotate_paste(base, shadow, cx, cy + 10, angle)

# ---- stamp: margin/bracket only, never over a value ----
def stamp(word, color, size=(300, 118), font_size=52, outline_w=7):
    w, h = size
    layer = Image.new("RGBA", (S(w), S(h)), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([S(7), S(7), S(w - 7), S(h - 7)], radius=S(10), outline=hx(color), width=S(outline_w))
    d.text((S(w / 2), S(h / 2)), word, font=anton(font_size), fill=hx(color) + (232,), anchor="mm")
    return layer

# ---- receipt strip ----
def receipt_strip(width_1080, rows, title="TRENDGIRI", source_line="SOURCE: TRENDGIRI COMPOSITE", subhead="WEEKLY SIGNAL RECEIPT"):
    """rows: list of (label, value, kind) kind in {'up','down','flat','ink'}.
    'up' -> green, 'down'/'flat' -> ink (never colored as if good), stamps
    applied separately by the caller so they never sit fixed over a value."""
    row_h = 60
    header_h = 128
    footer_h = 56
    content_h = header_h + len(rows) * row_h + footer_h
    w, h = S(width_1080), S(content_h)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, 0, w, h], fill=hx(PAPER_WHITE))

    def zigzag(y_1080):
        step = 22
        pts = []
        x, up = 0, True
        while x <= width_1080:
            pts.append((S(x), S(y_1080 + (-10 if up else 10))))
            up = not up
            x += step
        return pts
    d.line(zigzag(0), fill=hx(INK), width=S(2))
    d.line(zigzag(content_h), fill=hx(INK), width=S(2))
    R.text(d, (56, 32), title, mono(28), hx(INK), anchor="la")
    d.line([(S(56), S(76)), (S(width_1080 - 56), S(76))], fill=hx(INK), width=S(2))
    R.text(d, (56, 88), subhead, sans(22, 600), hx(INK), anchor="la")
    ry = header_h
    for label, val, kind in rows:
        cy = ry + row_h / 2
        R.text(d, (56, cy), label, mono(26), hx(INK), anchor="lm")
        color = MARKET_GREEN if kind == "up" else INK
        R.text(d, (width_1080 - 56, cy), val, mono(28), hx(color), anchor="rm")
        ry += row_h
    dash_y = ry + 4
    x = 56
    while x < width_1080 - 56:
        d.line([(S(x), S(dash_y)), (S(x + 14), S(dash_y))], fill=hx(INK), width=S(2))
        x += 24
    R.text(d, (width_1080 / 2, ry + 24), source_line,
           sans(18, 600), hx(MUTED), anchor="ma")
    return img, header_h, row_h

# ---- clean chart primitives (no wobble; Caveat carries the human signal) ----
def clean_line_chart(d, box, values, band=None, vline_idx=None, vline_label=None):
    x0, y0, x1, y1 = box
    vmin, vmax = min(values) - 0.03, max(values) + 0.03
    n = len(values)
    def xy(i, v):
        x = x0 + (x1 - x0) * (i / (n - 1))
        y = y1 - (y1 - y0) * ((v - vmin) / (vmax - vmin))
        return x, y
    if band:
        i0, i1 = band
        bx0, _ = xy(i0, values[i0])
        bx1, _ = xy(i1, values[i1])
        d.rectangle([S(bx0 - 10), S(y0), S(bx1 + 10), S(y1)], fill=hx(MARIGOLD) + (55,))
    if vline_idx is not None:
        vx, _ = xy(vline_idx, values[vline_idx])
        R.line(d, (vx, y0, vx, y1), fill=hx(MUTED), width=2, dash=(6, 6))
        R.text(d, (vx, y1 + 14), vline_label, sans(20, 600), hx(MUTED), anchor="ma")
    pts = [xy(i, v) for i, v in enumerate(values)]
    flat = [S(c) for p in pts for c in p]
    d.line(flat, fill=hx(INK), width=S(5), joint="curve")
    for (px, py) in pts:
        d.ellipse([S(px - 6), S(py - 6), S(px + 6), S(py + 6)], fill=hx(PAPER_WHITE), outline=hx(INK), width=S(3))
    return pts

def caveat_annotation(d, xy_pt, lines, color=STAMP_RED, size=40, arrow_to=None):
    x, y = xy_pt
    d.multiline_text((S(x), S(y)), "\n".join(lines), font=caveat(size, 700), fill=hx(color), anchor="la", spacing=S(4))
    if arrow_to:
        p0 = (x - 24, y - 20)
        p1 = arrow_to
        steps = 10
        curve = []
        for i in range(steps + 1):
            t = i / steps
            cxp = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * (p0[0] - 50) + t ** 2 * p1[0]
            cyp = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * (p1[1] + 40) + t ** 2 * p1[1]
            curve.append((cxp, cyp))
        flat = [S(c) for pt in curve for c in pt]
        d.line(flat, fill=hx(color), width=S(3), joint="curve")

def bar_board(d, box, rows, highlight_idx=None):
    """rows: (name, value, chip_text, kind) kind in up/down/flat"""
    x0, y0, x1, y1 = box
    n = len(rows)
    row_h = (y1 - y0) / n
    max_val = max(r[1] for r in rows)
    label_w, chip_w = 250, 170
    bar_x0, bar_x1 = x0 + label_w, x1 - chip_w
    value_x = bar_x1 - 10
    for i, (name, val, chip_text, kind) in enumerate(rows):
        ry = y0 + i * row_h
        by0, by1 = ry + row_h * 0.30, ry + row_h * 0.70
        color = MARIGOLD if (highlight_idx is not None and i == highlight_idx) else "#D8CBAE"
        R.text(d, (x0, (by0 + by1) / 2), name, sans(28, 700), hx(INK), anchor="lm")
        R.rounded_rect(d, (bar_x0, by0, bar_x1, by1), (by1 - by0) / 2, fill=hx("#EDE3D0"))
        bw = bar_x0 + (bar_x1 - bar_x0) * (val / max_val)
        R.rounded_rect(d, (bar_x0, by0, bw, by1), (by1 - by0) / 2, fill=hx(color))
        R.text(d, (value_x, by0 - 6), f"{val:.2f}", mono(22), hx(MUTED), anchor="rb")
        chip_color = {"up": MARKET_GREEN, "down": STAMP_RED, "flat": MUTED}[kind]
        cx0 = x1 - chip_w + 8
        cy0 = (by0 + by1) / 2 - 19
        if kind == "flat":
            R.rounded_rect(d, (cx0, cy0, x1, cy0 + 38), 19, outline=hx(chip_color), width=2)
        else:
            R.rounded_rect(d, (cx0, cy0, x1, cy0 + 38), 19, fill=hx(chip_color) + (38,))
        R.text(d, ((cx0 + x1) / 2, cy0 + 19), chip_text, sans(20, 700), hx(chip_color), anchor="mm")

def timeline(d, box, points):
    x0, y0, x1, y1 = box
    y = (y0 + y1) / 2
    R.line(d, (x0, y, x1, y), fill=hx(LINE_GRAY), width=3)
    n = len(points)
    for i, (label, days, weight, color) in enumerate(points):
        x = x0 + (x1 - x0) * (i / (n - 1)) if n > 1 else x0
        r = 10 + 15 * weight
        R.circle(d, x, y, r, fill=hx(color) if color else hx(PAPER_WHITE), outline=hx(INK), width=2)
        R.text(d, (x, y - r - 18), label, sans(22, 700), hx(INK), anchor="ma")
        if days:
            R.text(d, (x, y + r + 14), days, mono(20), hx(MUTED), anchor="ma")

def checklist(d, box, items):
    x0, y0, x1, y1 = box
    n = len(items)
    row_h = (y1 - y0) / n
    for i, itxt in enumerate(items):
        ry = y0 + i * row_h + row_h / 2
        R.circle(d, x0 + 22, ry, 22, fill=hx(MARIGOLD) + (60,), outline=hx(INK), width=2)
        cxk, cyk = x0 + 22, ry
        d.line([(S(cxk - 9), S(cyk)), (S(cxk - 2), S(cyk + 7)), (S(cxk + 11), S(cyk - 9))],
               fill=hx(INK), width=S(3.2), joint="curve")
        lines = R.wrap_text(d, itxt, sans(28, 500), (x1 - x0) - 80)
        ly = ry - (len(lines) - 1) * 18
        for ln in lines:
            R.text(d, (x0 + 66, ly), ln, sans(28, 500), hx(INK), anchor="lm")
            ly += 36

def text(d, xy, s, font, color, anchor="la"):
    R.text(d, xy, s, font, color, anchor=anchor)

def card(d, box, fill=PAPER_WHITE, outline=LINE_GRAY):
    R.rounded_rect(d, box, 26, fill=hx(fill), outline=hx(outline), width=2)

def text_block(d, lines, y, size=30, color=INK_SOFT, weight=600, tracking=0, align="left", x=60, font="sans", lh=1.4):
    if font == "anton":
        f = anton(size)
    else:
        f = sans(size, weight)
    fy = y
    for ln in lines:
        if align == "center":
            w = d.textlength(ln, font=f) / SCALE
            xx = 540 - w / 2
            anchor = "la"
        else:
            xx = x
            anchor = "la"
        R.text(d, (xx, fy), ln, f, hx(color), anchor=anchor, tracking=tracking)
        fy += size * lh

def flat_rows(d, box, series):
    x0, y0, x1, y1 = box
    n = len(series)
    row_h = (y1 - y0) / n
    for i, (label, val) in enumerate(series):
        ry0 = y0 + i * row_h + row_h * 0.18
        ry1 = y0 + i * row_h + row_h * 0.82
        cy = (ry0 + ry1) / 2
        R.text(d, (x0, cy), label, sans(28, 700), hx(INK), anchor="lm")
        lx0, lx1 = x0 + 280, x1 - 150
        marker_r = 9
        R.line(d, (lx0, cy, lx1 - marker_r - 6, cy), fill=hx(MUTED), width=3, dash=(10, 8))
        R.circle(d, lx1, cy, marker_r, fill=hx(PAPER_WHITE), outline=hx(MUTED), width=3)
        R.text(d, (lx1 + 24, cy), f"{val:.4f}", mono(24), hx(MUTED), anchor="lm")

def save(img, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.convert("RGB").resize((W, H), Image.LANCZOS).save(path, "PNG")
    print("saved", path)

print("giri_system loaded")
