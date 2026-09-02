# -*- coding: utf-8 -*-
"""Shared Pillow rendering primitives for TrendGiri Instagram carousels.

Two design systems have been built on this base:
- Dark "data dashboard" system (2026-08-29 round-1, since superseded).
- Cream "Bazaar Receipt" system (`giri_system.py`, current -- see
  docs/consults/2026-08-29-group-cto-instagram-trendy-design-round2-selection.md
  in the income-engine repo, and instagram-visual-system/SKILL.md here).

Pillow, 2x supersampled then downsampled to 1080x1350 for anti-aliasing.
"""
import os
from PIL import Image, ImageDraw, ImageFont

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.normpath(os.path.join(_THIS_DIR, "..", "..", "assets", "fonts"))
OUT_ROOT = os.path.normpath(os.path.join(_THIS_DIR, "..", "..", "content", "samples", "2026-08-29-redesign"))

W, H = 1080, 1350
SCALE = 2  # supersample factor
SW, SH = W * SCALE, H * SCALE

# ---- palette ----
BG = "#0A1729"
BG_LIFT = "#10263F"
CARD = "#132A47"
CARD_STROKE = "#23456B"
TEXT_PRIMARY = "#EAF4FA"
TEXT_SECONDARY = "#8FA9C0"
ACCENT = "#2FE0C4"
POS = "#55E08A"
NEG = "#FF8A70"
FROZEN = "#8FA9C0"
AMBER = "#F5C542"

def hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def hxa(h, a):
    return hx(h) + (a,)

# ---- fonts ----
def _var(path, size, axes, values):
    f = ImageFont.truetype(path, size)
    try:
        f.set_variation_by_axes(values)
    except Exception:
        pass
    return f

def space_grotesk_bold(size):
    return _var(os.path.join(FONT_DIR, "SpaceGrotesk-Bold.ttf"), size, None, [700])

def plex_mono_semibold(size):
    return ImageFont.truetype(os.path.join(FONT_DIR, "IBMPlexMono-SemiBold.ttf"), size)

def inter(size, weight=400):
    # axes order: [Optical size, Weight]
    opsz = max(14, min(32, size / SCALE if size > 32 else size))
    return _var(os.path.join(FONT_DIR, "Inter-Regular.ttf"), size, None, [opsz, weight])

# ---- drawing helpers (all coords in 1080x1350 space; multiplied by SCALE internally) ----

def S(v):
    return int(round(v * SCALE))

def rounded_rect(d, box, radius, fill=None, outline=None, width=1):
    x0, y0, x1, y1 = [S(v) for v in box]
    d.rounded_rectangle([x0, y0, x1, y1], radius=S(radius), fill=fill, outline=outline, width=S(width) if outline else 0)

def line(d, xy, fill, width=1, dash=None):
    pts = [S(v) for v in xy]
    if dash:
        # dash: (on, off) in 1080-space px
        x0, y0, x1, y1 = pts
        on, off = S(dash[0]), S(dash[1])
        import math
        length = math.hypot(x1 - x0, y1 - y0)
        if length == 0:
            return
        ux, uy = (x1 - x0) / length, (y1 - y0) / length
        pos = 0.0
        drawing = True
        while pos < length:
            seg = on if drawing else off
            nxt = min(pos + seg, length)
            if drawing:
                d.line([x0 + ux * pos, y0 + uy * pos, x0 + ux * nxt, y0 + uy * nxt], fill=fill, width=S(width))
            pos = nxt
            drawing = not drawing
    else:
        d.line(pts, fill=fill, width=S(width))

def circle(d, cx, cy, r, fill=None, outline=None, width=1):
    x0, y0, x1, y1 = S(cx - r), S(cy - r), S(cx + r), S(cy + r)
    d.ellipse([x0, y0, x1, y1], fill=fill, outline=outline, width=S(width) if outline else 0)

def text(d, xy, s, font, fill, anchor="la", tracking=0):
    x, y = S(xy[0]), S(xy[1])
    if tracking:
        # manual letter spacing
        cx = x
        for ch in s:
            d.text((cx, y), ch, font=font, fill=fill, anchor=anchor)
            w = d.textlength(ch, font=font)
            cx += w + S(tracking)
        return
    d.text((x, y), s, font=font, fill=fill, anchor=anchor)

def text_w(d, s, font, tracking=0):
    w = d.textlength(s, font=font)
    if tracking:
        w += S(tracking) * max(0, len(s) - 1)
    return w / SCALE

def wrap_text(d, s, font, max_width_1080):
    words = s.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_w(d, trial, font) <= max_width_1080:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

# ---- shared chrome ----

def new_canvas():
    img = Image.new("RGB", (SW, SH), hx(BG))
    d = ImageDraw.Draw(img, "RGBA")
    # subtle radial-ish lift top-left: draw a soft large ellipse, low alpha, blurred via multiple passes
    overlay = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.ellipse([-SW * 0.3, -SH * 0.35, SW * 0.75, SH * 0.55], fill=hxa(BG_LIFT, 140))
    from PIL import ImageFilter
    overlay = overlay.filter(ImageFilter.GaussianBlur(SW * 0.12))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    d = ImageDraw.Draw(img, "RGBA")
    return img, d

def draw_logo(d, img):
    # simple globe glyph (circle + 2 ellipses + meridian lines) + wordmark, top-left, top edge y~40
    cx, cy, r = 44, 40 + 20, 20
    circle(d, cx, cy, r, outline=hx(ACCENT), width=3)
    d.ellipse([S(cx - r * 0.45), S(cy - r), S(cx + r * 0.45), S(cy + r)], outline=hx(ACCENT), width=S(2))
    line(d, (cx - r, cy, cx + r, cy), fill=hx(ACCENT), width=2)
    text(d, (cx + r + 14, cy), "TrendRadar", space_grotesk_bold(30), hx(TEXT_PRIMARY), anchor="lm")

def draw_footer(d, page="", tagline="TrendRadar | swipe \u2192"):
    y = 1200
    line(d, (60, y, 1020, y), fill=hx(CARD_STROKE), width=1)
    text(d, (60, y + 18), tagline, inter(26, 500), hx(TEXT_SECONDARY), anchor="la")
    if page:
        w = text_w(d, page, plex_mono_semibold(26))
        text(d, (1020 - w, y + 18), page, plex_mono_semibold(26), hx(ACCENT), anchor="la")

def draw_source_line(d, source_text, y=1170):
    text(d, (60, y), source_text, inter(24, 500), hx(TEXT_SECONDARY), anchor="la")

def kicker(d, s, y=118):
    text(d, (60, y), s.upper(), inter(28, 600), hx(TEXT_SECONDARY), anchor="la", tracking=1.5)

def headline(d, lines, y=178, size=68, color=TEXT_PRIMARY, lh=1.15):
    fy = y
    f = space_grotesk_bold(size)
    for ln in lines:
        text(d, (60, fy), ln, f, hx(color), anchor="la")
        fy += size * lh
    return fy

def save(img, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    final = img.resize((W, H), Image.LANCZOS)
    final.save(path, "PNG")
    print("saved", path)

# ---- chart primitives ----

def scale_bar(d, box, value, prev_value, vmax=1.0):
    x0, y0, x1, y1 = box
    track_h = y1 - y0
    rounded_rect(d, box, track_h / 2, fill=hx(CARD_STROKE))
    fill_x1 = x0 + (x1 - x0) * (value / vmax)
    rounded_rect(d, (x0, y0, fill_x1, y1), track_h / 2, fill=hx(ACCENT))
    # prev tick
    tick_x = x0 + (x1 - x0) * (prev_value / vmax)
    line(d, (tick_x, y0 - 10, tick_x, y1 + 10), fill=hx(TEXT_SECONDARY), width=3)
    text(d, (tick_x, y1 + 16), f"yesterday {prev_value:.2f}", inter(22, 500), hx(TEXT_SECONDARY), anchor="ma" if False else "la")

def bar_board(d, box, rows, highlight_idx=0):
    """rows: list of (name, value, delta_str, delta_kind) delta_kind in pos/neg/frozen"""
    x0, y0, x1, y1 = box
    n = len(rows)
    row_h = (y1 - y0) / n
    max_val = max(r[1] for r in rows)
    label_w = 260
    chip_w = 180
    bar_x0 = x0 + label_w
    bar_x1 = x1 - chip_w
    value_x = bar_x1 - 12  # fixed right-aligned anchor, independent of bar length
    for i, (name, val, delta, kind) in enumerate(rows):
        ry = y0 + i * row_h
        bar_y0 = ry + row_h * 0.28
        bar_y1 = ry + row_h * 0.72
        color = ACCENT if i == highlight_idx else "#3A5A80"
        # name label
        text(d, (x0, (bar_y0 + bar_y1) / 2), name, inter(30, 600), hx(TEXT_PRIMARY), anchor="lm")
        # bar track
        rounded_rect(d, (bar_x0, bar_y0, bar_x1, bar_y1), (bar_y1 - bar_y0) / 2, fill=hx(CARD_STROKE))
        bw = bar_x0 + (bar_x1 - bar_x0) * (val / max_val)
        rounded_rect(d, (bar_x0, bar_y0, bw, bar_y1), (bar_y1 - bar_y0) / 2, fill=hx(color))
        # value mono: fixed position ABOVE the bar (never collides with the bar or the chip)
        vtxt = f"{val:.2f}"
        text(d, (value_x, bar_y0 - 8), vtxt, plex_mono_semibold(24), hx(TEXT_SECONDARY), anchor="rb")
        # delta chip
        kind_color = {"pos": POS, "neg": NEG, "frozen": FROZEN}[kind]
        chip_x0 = x1 - chip_w + 10
        chip_y0 = (bar_y0 + bar_y1) / 2 - 20
        if kind == "frozen":
            rounded_rect(d, (chip_x0, chip_y0, x1, chip_y0 + 40), 20, outline=hx(kind_color), width=2)
        else:
            rounded_rect(d, (chip_x0, chip_y0, x1, chip_y0 + 40), 20, fill=hxa(kind_color, 40))
        text(d, ((chip_x0 + x1) / 2, chip_y0 + 20), delta, inter(22, 700), hx(kind_color), anchor="mm")

def dot_plot(d, box, p1, p2, label1, label2, vmax=1.0, vmin=0.0):
    x0, y0, x1, y1 = box
    def yof(v):
        return y1 - (y1 - y0) * ((v - vmin) / (vmax - vmin))
    x_p1, x_p2 = x0 + (x1 - x0) * 0.28, x0 + (x1 - x0) * 0.72
    y_p1, y_p2 = yof(p1), yof(p2)
    line(d, (x0, y1, x1, y1), fill=hx(CARD_STROKE), width=2)
    # connecting line with arrowhead
    line(d, (x_p1, y_p1, x_p2, y_p2), fill=hx(ACCENT), width=5)
    import math
    ang = math.atan2(y_p2 - y_p1, x_p2 - x_p1)
    ah = 16
    ax1 = x_p2 - ah * math.cos(ang - 0.5)
    ay1 = y_p2 - ah * math.sin(ang - 0.5)
    ax2 = x_p2 - ah * math.cos(ang + 0.5)
    ay2 = y_p2 - ah * math.sin(ang + 0.5)
    d.polygon([(S(x_p2), S(y_p2)), (S(ax1), S(ay1)), (S(ax2), S(ay2))], fill=hx(ACCENT))
    circle(d, x_p1, y_p1, 10, fill=hx(TEXT_SECONDARY))
    circle(d, x_p2, y_p2, 12, fill=hx(ACCENT))
    text(d, (x_p1, y_p1 - 34), f"{p1:.2f}", plex_mono_semibold(28), hx(TEXT_SECONDARY), anchor="mb" if False else "ma")
    text(d, (x_p1, y1 + 16), label1, inter(22, 500), hx(TEXT_SECONDARY), anchor="ma")
    text(d, (x_p2, y_p2 - 40), f"{p2:.2f}", plex_mono_semibold(30), hx(ACCENT), anchor="ma")
    text(d, (x_p2, y1 + 16), label2, inter(22, 500), hx(TEXT_SECONDARY), anchor="ma")

def line_chart(d, box, values, x_labels, band=None, vline_idx=None, vline_label=None, end_labels=True):
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
        rounded_rect(d, (bx0 - 8, y0, bx1 + 8, y1), 8, fill=hxa(AMBER, 30))
        text(d, ((bx0 + bx1) / 2, y0 - 34), "frozen at 0.6747", inter(24, 700), hx(AMBER), anchor="ma")
    if vline_idx is not None:
        vx, _ = xy(vline_idx, values[vline_idx])
        line(d, (vx, y0, vx, y1), fill=hx(TEXT_SECONDARY), width=2, dash=(6, 6))
        text(d, (vx, y1 + 16), vline_label, inter(22, 600), hx(TEXT_SECONDARY), anchor="ma")
    pts = [xy(i, v) for i, v in enumerate(values)]
    for i in range(len(pts) - 1):
        line(d, (*pts[i], *pts[i + 1]), fill=hx(ACCENT), width=6)
    for i, (px, py) in enumerate(pts):
        circle(d, px, py, 5, fill=hx(ACCENT))
    if end_labels:
        # label first, min/plateau, last only (per brief: endpoint labels only, no y-axis)
        first_i, last_i = 0, len(pts) - 1
        text(d, (pts[first_i][0], pts[first_i][1] - 34), f"{values[first_i]:.2f}", plex_mono_semibold(26), hx(TEXT_SECONDARY), anchor="ma")
        text(d, (pts[last_i][0], pts[last_i][1] + 20), f"{values[last_i]:.2f}", plex_mono_semibold(26), hx(TEXT_PRIMARY), anchor="ma")
        if band:
            bi = band[0]
            text(d, (pts[bi][0], pts[bi][1] - 34), f"{values[bi]:.2f}", plex_mono_semibold(26), hx(AMBER), anchor="ma")

def flat_sparklines(d, box, series):
    """series: list of (label, value)"""
    x0, y0, x1, y1 = box
    n = len(series)
    row_h = (y1 - y0) / n
    for i, (label, val) in enumerate(series):
        ry0 = y0 + i * row_h + row_h * 0.18
        ry1 = y0 + i * row_h + row_h * 0.82
        cy = (ry0 + ry1) / 2
        text(d, (x0, cy), label, inter(28, 600), hx(TEXT_PRIMARY), anchor="lm")
        lx0 = x0 + 260
        lx1 = x1 - 140
        marker_r = 9
        line(d, (lx0, cy, lx1 - marker_r - 6, cy), fill=hx(FROZEN), width=3, dash=(10, 8))
        circle(d, lx1, cy, marker_r, fill=hx(BG), outline=hx(FROZEN), width=3)
        text(d, (lx1 + 24, cy), f"{val:.2f}", plex_mono_semibold(26), hx(FROZEN), anchor="lm")

def timeline(d, box, points):
    """points: list of (label, days, weight 0-1, color)"""
    x0, y0, x1, y1 = box
    y = (y0 + y1) / 2
    line(d, (x0, y, x1, y), fill=hx(CARD_STROKE), width=3)
    n = len(points)
    for i, (label, days, weight, color) in enumerate(points):
        x = x0 + (x1 - x0) * (i / (n - 1)) if n > 1 else x0
        r = 10 + 14 * weight
        circle(d, x, y, r, fill=hx(color) if color else hx(TEXT_SECONDARY))
        text(d, (x, y - r - 20), label, inter(24, 600), hx(TEXT_PRIMARY), anchor="mb" if False else "ma")
        text(d, (x, y + r + 16), days, plex_mono_semibold(22), hx(TEXT_SECONDARY), anchor="ma")

def checklist(d, box, items):
    x0, y0, x1, y1 = box
    n = len(items)
    row_h = (y1 - y0) / n
    for i, itxt in enumerate(items):
        ry = y0 + i * row_h + row_h / 2
        circle(d, x0 + 22, ry, 22, fill=hxa(ACCENT, 40), outline=hx(ACCENT), width=2)
        cxk, cyk = x0 + 22, ry
        d.line([(S(cxk - 10), S(cyk)), (S(cxk - 2), S(cyk + 8)), (S(cxk + 12), S(cyk - 10))], fill=hx(ACCENT), width=S(3.5), joint="curve")
        lines = wrap_text(d, itxt, inter(30, 500), (x1 - x0) - 80)
        ly = ry - (len(lines) - 1) * 19
        for ln in lines:
            text(d, (x0 + 66, ly), ln, inter(30, 500), hx(TEXT_PRIMARY), anchor="lm")
            ly += 38

def legend_card(d, box):
    x0, y0, x1, _y1 = box
    box2 = (x0, y0, x1, y0 + 260)
    rounded_rect(d, box2, 24, fill=hx(CARD), outline=hx(CARD_STROKE), width=2)
    gx = x0 + 60
    ry = y0 + 60
    rounded_rect(d, (gx - 14, ry - 14, gx + 14, ry + 14), 4, fill=hx(ACCENT))
    text(d, (gx + 44, ry), "Featured mover", inter(28, 500), hx(TEXT_SECONDARY), anchor="lm")
    ry += 66
    circle(d, gx, ry, 15, fill=hx(CARD), outline=hx(FROZEN), width=3)
    text(d, (gx + 44, ry), "Frozen — no story", inter(28, 500), hx(TEXT_SECONDARY), anchor="lm")
    ry += 66
    up_x, dn_x = gx - 10, gx + 12
    d.polygon([(S(up_x - 9), S(ry + 8)), (S(up_x + 9), S(ry + 8)), (S(up_x), S(ry - 10))], fill=hx(POS))
    d.polygon([(S(dn_x - 9), S(ry - 8)), (S(dn_x + 9), S(ry - 8)), (S(dn_x), S(ry + 10))], fill=hx(NEG))
    text(d, (gx + 44, ry), "Day-over-day change", inter(28, 500), hx(TEXT_SECONDARY), anchor="lm")

def cta_bottom(d, y0=760, y1=1150):
    legend_card(d, (60, y0, 1020, y1))

print("helpers loaded")
