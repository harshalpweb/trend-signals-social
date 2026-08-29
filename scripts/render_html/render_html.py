# -*- coding: utf-8 -*-
"""TrendGiri HTML/CSS -> PNG slide renderer (Playwright sync API, headless
Chromium). Supersedes scripts/render/ (Pillow) per the pass-1 typography
diagnostic (income-engine/docs/consults/2026-08-29-group-cto-typography-
diagnostic-pass1.md): browser engine gives HarfBuzz kerning/shaping, real
flow layout, and no hand-coordinate bugs.

Usage:
    py -3 render_html.py decks/<deck>.json [--out <dir>]
    py -3 render_html.py --verify-shaping

Deck JSON: {"slug": str, "kicker": str, "slides": [ {role, ...}, ... ]}
Roles: hook, list, principle, quote, closer.
Rich text in strings: [[...]] -> <mark> highlight, **...** -> <strong>.

Output: 1080x1350 PNG per slide (rendered at device_scale_factor=2, then
LANCZOS-downsampled — fonts are hinted/shaped by the browser at raster
size, so this supersampling is correct, unlike the old Pillow path).
"""
import argparse
import html as htmllib
import json
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]  # trend-signals-social/
FONT_DIR = "file:///" + (ROOT / "assets" / "fonts").as_posix()
CSS = (HERE / "template.css").read_text(encoding="utf-8").replace("__FONTDIR__", FONT_DIR)

W, H = 1080, 1350
DSF = 2


def esc(s):
    return htmllib.escape(s, quote=False)


def rich(s):
    s = esc(s)
    while "[[" in s and "]]" in s:
        s = s.replace("[[", "<mark>", 1).replace("]]", "</mark>", 1)
    while s.count("**") >= 2:
        s = s.replace("**", "<strong>", 1).replace("**", "</strong>", 1)
    return s


# ---- slide role builders: return (main_inner_html, extra_body_class) ----

def role_hook(sl):
    dek = f'<p class="dek">{rich(sl["dek"])}</p>' if sl.get("dek") else ""
    return f'<h1 class="display">{rich(sl["h"])}</h1>{dek}', ""


def role_list(sl):
    rows = "".join(
        f'<li><span class="num">{i:02d}</span><span class="t">{rich(t)}</span></li>'
        for i, t in enumerate(sl["items"], 1)
    )
    return f'<h2 class="heading">{rich(sl["h"])}</h2><ol class="rows">{rows}</ol>', ""


def role_principle(sl):
    body = "".join(f'<p class="dek">{rich(p)}</p>' for p in sl.get("body", []))
    lbl = f'<span class="klabel">{esc(sl["klabel"])}</span>' if sl.get("klabel") else ""
    return f'{lbl}<h2 class="display">{rich(sl["h"])}</h2>{body}', ""


def role_quote(sl):
    attr = f'<p class="attr">{esc(sl["attr"])}</p>' if sl.get("attr") else ""
    return f'<div class="qbar"></div><h1 class="display">{rich(sl["q"])}</h1>{attr}', "dark"


def role_closer(sl):
    body = f'<p class="dek">{rich(sl["body"])}</p>' if sl.get("body") else ""
    handle = f'<span class="handle">{esc(sl["handle"])}</span>' if sl.get("handle") else ""
    theme = "dark" if sl.get("theme") == "dark" else ""
    return f'<h1 class="display">{rich(sl["h"])}</h1>{body}{handle}', theme


ROLES = {"hook": role_hook, "list": role_list, "principle": role_principle,
         "quote": role_quote, "closer": role_closer}


def slide_html(deck, sl, page_no, total):
    inner, extra_cls = ROLES[sl["role"]](sl)
    kicker = sl.get("kicker", deck.get("kicker", ""))
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head>
<body class="slide {extra_cls}">
<header class="brandrow"><span class="wordmark">TRENDGIRI</span><span class="kicker">{esc(kicker)}</span></header>
<main class="content">{inner}</main>
<footer class="footrow"><span>THE DIGITAL BAZAAR</span><span>{page_no}/{total}</span></footer>
</body></html>"""


def render_deck(deck_path, out_dir=None):
    deck = json.loads(Path(deck_path).read_text(encoding="utf-8"))
    slug = deck["slug"]
    out = Path(out_dir) if out_dir else ROOT / "content" / "samples" / deck["batch"] / slug
    out.mkdir(parents=True, exist_ok=True)
    html_dir = out / "_html"
    html_dir.mkdir(exist_ok=True)
    total = len(deck["slides"])

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=DSF)
        for i, sl in enumerate(deck["slides"], 1):
            doc = slide_html(deck, sl, i, total)
            hpath = html_dir / f"slide-{i}.html"
            hpath.write_text(doc, encoding="utf-8")
            page.goto(hpath.as_uri())
            page.wait_for_function("document.fonts.status === 'loaded'")
            png_2x = page.screenshot()
            img = Image.open(__import__("io").BytesIO(png_2x))
            assert img.size == (W * DSF, H * DSF), f"unexpected raster {img.size}"
            img = img.convert("RGB").resize((W, H), Image.LANCZOS)
            img.save(out / f"slide-{i}.png")
            print(f"  slide-{i}.png  ({sl['role']})")
        browser.close()
    print(f"OK: {total} slides -> {out}")
    return out


def verify_shaping():
    """Prove kerning/shaping is active: measure 'AVATAR To Ye.' width with
    font-kerning normal vs none — a difference means real kerning (the old
    Pillow path had raqm=False and char-by-char drawing: zero kerning)."""
    s = "display:inline-block;width:max-content;font-size:112px;"
    probe = """<!doctype html><html><head><style>{css}</style></head><body class="slide"><div>
    <span id="a" style="font-family:Inter;{s}font-kerning:normal">AVATAR To Ye. WAVY LT.</span><br>
    <span id="b" style="font-family:Inter;{s}font-kerning:none">AVATAR To Ye. WAVY LT.</span><br>
    <span id="c" style="font-family:Anton;{s}font-kerning:normal">AVATAR To Ye. WAVY LT.</span><br>
    <span id="d" style="font-family:Anton;{s}font-kerning:none">AVATAR To Ye. WAVY LT.</span>
    </div></body></html>""".format(css=CSS, s=s)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H})
        tmp = HERE / "_shaping_probe.html"
        tmp.write_text(probe, encoding="utf-8")
        page.goto(tmp.as_uri())
        page.wait_for_function("document.fonts.status === 'loaded'")
        w = {k: page.evaluate(f"document.getElementById('{k}').getBoundingClientRect().width")
             for k in "abcd"}
        browser.close()
        tmp.unlink()
    di = w["b"] - w["a"]
    da = w["d"] - w["c"]
    print(f"Inter: kern={w['a']:.2f}px nokern={w['b']:.2f}px delta={di:.2f}px")
    print(f"Anton: kern={w['c']:.2f}px nokern={w['d']:.2f}px delta={da:.2f}px")
    print("SHAPING ACTIVE" if abs(di) > 0.5 or abs(da) > 0.5
          else "WARNING: no kerning delta measured")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("deck", nargs="?")
    ap.add_argument("--out")
    ap.add_argument("--verify-shaping", action="store_true")
    args = ap.parse_args()
    if args.verify_shaping:
        verify_shaping()
    elif args.deck:
        render_deck(args.deck, args.out)
    else:
        ap.print_help()
        sys.exit(1)
