# -*- coding: utf-8 -*-
"""Pass-1 completion gate, mechanical form. Run against a rendered deck dir:

    py -3 gate_check.py <deck_dir>

Checks per slide PNG:
  - ink coverage (share of pixels differing from the dominant background
    color) — target band 8-20% (reported; hook/quote slides judged by eye too)
  - writes a 350px-wide preview to <deck_dir>/_preview350/ for the mandatory
    feed-scale visual re-check (a human/agent must still LOOK at these)

Checks once (type-system tokens, hardcoded to template.css — keep in sync):
  - body size >= 3% of canvas height
  - <= 2 display/heading sizes + 1 body + 1 meta system-wide (by construction)
  - WCAG contrast >= 4.5:1 for every text/background pair the CSS can produce
"""
import sys
from pathlib import Path
from PIL import Image

# ---- tokens (mirror template.css) ----
TOKENS = {"display": 112, "heading": 58, "body": 42, "meta": 26}
CANVAS_H = 1350

PALETTE = {
    "cream": "#F5EEE2", "paper": "#FFFDF8", "ink": "#1A1714",
    "ink_soft": "#4A443B", "marigold": "#FFB627", "line": "#C9BFA9",
}
# every (fg, bg) text pairing template.css can produce:
TEXT_PAIRS = [
    ("ink", "cream"),       # display/heading/body on light slides
    ("ink_soft", "cream"),  # dek/kicker/footer on light slides
    ("ink", "marigold"),    # mark highlights, klabel, handle, num-chip inverse
    ("cream", "ink"),       # num chips; display/body on dark slides
    ("line", "ink"),        # kicker/footer/dek/attr on dark slides
]


def _lin(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lum(hexc):
    r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast(fg, bg):
    a, b = lum(PALETTE[fg]), lum(PALETTE[bg])
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def ink_coverage(img):
    small = img.convert("RGB")
    px = list(small.getdata())
    # dominant color = background
    counts = {}
    for p in px:
        counts[p] = counts.get(p, 0) + 1
    bg = max(counts, key=counts.get)
    thr = 40
    diff = sum(1 for p in px if abs(p[0] - bg[0]) + abs(p[1] - bg[1]) + abs(p[2] - bg[2]) > thr)
    return diff / len(px), bg


def main(deck_dir):
    deck = Path(deck_dir)
    prev = deck / "_preview350"
    prev.mkdir(exist_ok=True)

    print("== type-system checks (static) ==")
    body_pct = TOKENS["body"] / CANVAS_H * 100
    print(f"body {TOKENS['body']}px = {body_pct:.2f}% of canvas height "
          f"[{'PASS' if body_pct >= 3.0 else 'FAIL'} >=3%]")
    print(f"sizes system-wide: display {TOKENS['display']} + heading {TOKENS['heading']} "
          f"+ body {TOKENS['body']} + meta {TOKENS['meta']} (2 display/heading + 1 body + 1 meta) [PASS by construction]")

    print("== contrast (WCAG) ==")
    ok = True
    for fg, bg in TEXT_PAIRS:
        r = contrast(fg, bg)
        p = r >= 4.5
        ok &= p
        print(f"  {fg} on {bg}: {r:.2f}:1 [{'PASS' if p else 'FAIL'}]")

    print("== per-slide ink coverage + 350px previews ==")
    for png in sorted(deck.glob("slide-*.png"), key=lambda p: int(p.stem.split("-")[1])):
        img = Image.open(png)
        # measure at 1/4 res for speed; coverage is scale-stable
        cov, bg = ink_coverage(img.resize((270, 338), Image.LANCZOS))
        band = "PASS" if 0.08 <= cov <= 0.20 else ("low" if cov < 0.08 else "high")
        pimg = img.resize((350, 437), Image.LANCZOS)
        pimg.save(prev / png.name)
        print(f"  {png.name}: ink {cov * 100:.1f}%  bg~{bg}  [{band}]")
    print(f"previews -> {prev}  (feed-scale visual check is still mandatory)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
