# -*- coding: utf-8 -*-
"""Full 4-deck TrendGiri rebuild per the round-2 execution spec."""
import os
import giri_system as G
from PIL import Image, ImageDraw

OUT = r"C:\Users\2026\Documents\trend-signals-social\content\samples\2026-08-29-trendgiri-rebuild"

RAKHI = [0.6211, 0.6282, 0.6337, 0.6506, 0.6512, 0.6747, 0.6747, 0.6747, 0.5360, 0.5032]
RAKHI_DATES = ["8/20", "8/21", "8/22", "8/23", "8/24", "8/25", "8/26", "8/27", "8/28", "8/29"]

BOARD_ROWS = [
    ("Mixer grinder", 0.5866, "up"),
    ("Gift hamper", 0.5749, "flat"),
    ("Face serum", 0.5450, "flat"),
    ("Saree", 0.5399, "down"),
    ("Hair oil", 0.5349, "flat"),
]

# ============================================================
# DECK 1 — SIGNAL: "A kitchen staple just took our #1"
# ============================================================
D1 = os.path.join(OUT, "deck-1-signal-mixer-grinder")

def d1_s1():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.kicker(d, "This Week's Signal · Aug 29")
    G.headline(d, ["A KITCHEN STAPLE", "JUST TOOK OUR #1."], size=110)
    G.text_block(d, ["Mixer grinders went from unranked to the", "top of our board in two days."], y=560)
    G.footer(d, 1, 8)
    G.save(img, os.path.join(D1, "slide-1.png"))

def d1_s2():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["Today's board,", "as a receipt."], size=76, y=140)
    rows = [(n.upper(), f"{v:.4f}", k) for n, v, k in BOARD_ROWS]
    strip, header_h, row_h = G.receipt_strip(680, rows, source_line="SOURCE: TRENDGIRI COMPOSITE · 2 OF 4 IN SIGNAL FAMILIES")
    G.drop_shadow(img, 680, strip.height / G.SCALE, 566, 900, -2.5)
    G.rotate_paste(img, strip, 550, 890, -2.5)
    st = G.stamp("MOVER", G.MARKET_GREEN, size=(200, 90), font_size=36)
    G.rotate_paste(img, st, 190, 795, -87)
    G.footer(d, 2, 8)
    G.save(img, os.path.join(D1, "slide-2.png"))

def d1_s3():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.text_block(d, ["MOMENTUM"], y=260, size=34, color=G.MUTED, weight=800, tracking=2)
    G.text(d, (540, 620), "+0.16", G.archivo_black(210), G.hx(G.MARKET_GREEN), anchor="mm")
    G.text_block(d, ["The fastest move on our board this week —", "and the only one with real momentum behind it."], y=800, align="center")
    G.footer(d, 3, 8)
    G.save(img, os.path.join(D1, "slide-3.png"))

def d1_s4():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["The receipt", "behind the move."], size=68, y=140)
    box = (60, 320, 1020, 900)
    G.card(d, box)
    pts = G.clean_line_chart(d, (150, 420, 900, 760), [0.5433, 0.5866])
    G.text(d, (pts[0][0], pts[0][1] - 34), "0.54", G.mono(26), G.hx(G.MUTED), anchor="ma")
    G.text(d, (pts[1][0], pts[1][1] - 34), "0.59", G.mono(28), G.hx(G.MARKET_GREEN), anchor="ma")
    G.caveat_annotation(d, (200, 800), ["one signal family so far", "(marketplace rank) — we say so"], color=G.STAMP_RED, size=34)
    G.source_line(d, "SOURCE: MARKETPLACE BESTSELLER RANK (IN) · REFRESHED 06:02 IST", y=940)
    G.footer(d, 4, 8)
    G.save(img, os.path.join(D1, "slide-4.png"))

def d1_s5():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["Before you stock", "a mover:"], size=68, y=140)
    box = (60, 340, 1020, 900)
    G.card(d, box)
    items = [
        "Check the direction today, not last month's number.",
        "See if a festival or seasonal date explains it.",
        "Count how many sellers are already in that category.",
    ]
    G.checklist(d, (110, 400, 970, 840), items)
    G.footer(d, 5, 8)
    G.save(img, os.path.join(D1, "slide-5.png"))

def d1_s6():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["Next demand", "windows."], size=68, y=140)
    box = (60, 340, 1020, 900)
    G.card(d, box)
    points = [("Today", "", 0.3, G.MUTED), ("Karwa Chauth", "61d", 0.5, G.INK),
              ("Dhanteras", "69d", 0.7, G.INK), ("Diwali", "71d", 1.0, G.MARIGOLD)]
    G.timeline(d, (150, 550, 930, 670), points)
    G.footer(d, 6, 8)
    G.save(img, os.path.join(D1, "slide-6.png"))

def d1_s7():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["One family isn't", "corroboration yet."], size=58, y=140)
    box = (60, 340, 1020, 820)
    G.card(d, box)
    G.text_block(d, ["We track 4 signal families in India.", "Today's mixer grinder read comes from", "exactly one: marketplace rank.",
                      "", "We'll flag it the moment a second", "family lines up too — never before."], y=420, x=110, align="left")
    G.footer(d, 7, 8)
    G.save(img, os.path.join(D1, "slide-7.png"))

def d1_s8():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["Follow for", "weekly receipts."], size=78, y=160)
    G.text(d, (60, 360), "@trendgiri", G.mono(38), G.hx(G.STAMP_RED), anchor="la")
    st = G.stamp("VERIFIED", G.MARKET_GREEN, size=(280, 100), font_size=38)
    G.rotate_paste(img, st, 800, 820, 8)
    G.text_block(d, ["Send this to a seller friend", "before they find out the slow way."], y=980, align="left")
    G.footer(d, 8, 8)
    G.save(img, os.path.join(D1, "slide-8.png"))

# ============================================================
# DECK 2 — DIGEST: "2 moved. 3 froze."
# ============================================================
D2 = os.path.join(OUT, "deck-2-digest-2-moved-3-froze")

def d2_s1():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.kicker(d, "Weekly Digest · Aug 29")
    G.headline(d, ["2 MOVED.", "3 FROZE."], size=150, y=200)
    G.text_block(d, ["Here's the week, with receipts —", "including the parts that didn't move."], y=680)
    G.footer(d, 1, 8)
    G.save(img, os.path.join(D2, "slide-1.png"))

def d2_s2():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["This week's board,", "as a receipt."], size=68, y=140)
    rows = [(n.upper(), f"{v:.4f}", k) for n, v, k in BOARD_ROWS]
    strip, header_h, row_h = G.receipt_strip(680, rows, source_line="SOURCE: TRENDGIRI COMPOSITE · 2 OF 4 IN SIGNAL FAMILIES")
    G.drop_shadow(img, 680, strip.height / G.SCALE, 566, 900, 2.5)
    G.rotate_paste(img, strip, 550, 890, 2.5)
    st1 = G.stamp("FROZEN x3", G.STAMP_RED, size=(250, 90), font_size=32)
    G.rotate_paste(img, st1, 900, 560, 7)
    G.footer(d, 2, 8)
    G.save(img, os.path.join(D2, "slide-2.png"))

def d2_s3():
    img, d = G.new_canvas()
    G.draw_logo(d)
    st = G.stamp("FROZEN", G.STAMP_RED, size=(560, 220), font_size=100, outline_w=10)
    G.rotate_paste(img, st, 540, 500, -2)
    G.text_block(d, ["3 of today's top 5 are frozen —", "identical to the 6th decimal for 5 days.", "That's a source that stopped reporting,", "not a trend holding steady."], y=760, align="center")
    G.footer(d, 3, 8)
    G.save(img, os.path.join(D2, "slide-3.png"))

def d2_s4():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["The frozen three,", "side by side."], size=62, y=140)
    box = (60, 340, 1020, 900)
    G.card(d, box)
    series = [("Gift hamper", 0.5749), ("Face serum", 0.5450), ("Hair oil", 0.5349)]
    G.flat_rows(d, (110, 400, 970, 840), series)
    G.footer(d, 4, 8)
    G.save(img, os.path.join(D2, "slide-4.png"))

def d2_s5():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["Next demand", "windows."], size=68, y=140)
    box = (60, 340, 1020, 900)
    G.card(d, box)
    points = [("Today", "", 0.3, G.MUTED), ("Karwa Chauth", "61d", 0.5, G.INK),
              ("Dhanteras", "69d", 0.7, G.INK), ("Diwali", "71d", 1.0, G.MARIGOLD)]
    G.timeline(d, (150, 550, 930, 670), points)
    G.footer(d, 5, 8)
    G.save(img, os.path.join(D2, "slide-5.png"))

def d2_s6():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["Why we skip", "a frozen story."], size=64, y=140)
    box = (60, 340, 1020, 820)
    G.card(d, box)
    items = [
        "A number that hasn't changed in days isn't a trend — it's a stalled source.",
        "We'd rather say nothing than write a movement story around it.",
    ]
    G.checklist(d, (110, 420, 970, 760), items)
    G.footer(d, 6, 8)
    G.save(img, os.path.join(D2, "slide-6.png"))

def d2_s7():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["Which category", "should we open next?"], size=58, y=180)
    G.text_block(d, ["Reply with a category and we'll", "run the full board on it next week."], y=560)
    G.footer(d, 7, 8)
    G.save(img, os.path.join(D2, "slide-7.png"))

def d2_s8():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["Follow for", "weekly receipts."], size=78, y=160)
    G.text(d, (60, 360), "@trendgiri", G.mono(38), G.hx(G.STAMP_RED), anchor="la")
    st = G.stamp("HONEST", G.MARIGOLD, size=(280, 100), font_size=36)
    G.rotate_paste(img, st, 800, 820, -6)
    G.text_block(d, ["Send this to a seller friend", "who's tired of guessing."], y=980, align="left")
    G.footer(d, 8, 8)
    G.save(img, os.path.join(D2, "slide-8.png"))

# ============================================================
# DECK 3 — BUILD IN PUBLIC: "Our signal froze."
# ============================================================
D3 = os.path.join(OUT, "deck-3-build-in-public-rakhi-freeze")

def d3_s1():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.kicker(d, "Build in Public · Aug 29")
    G.headline(d, ["OUR SIGNAL FROZE.", "WE SHOWED YOU", "ANYWAY."], size=92, y=170)
    G.footer(d, 1, 8)
    G.save(img, os.path.join(D3, "slide-1.png"))

def d3_s2():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["Climb, freeze,", "festival, fade."], size=62, y=140)
    box = (60, 320, 1020, 940)
    G.card(d, box)
    pts = G.clean_line_chart(d, (140, 420, 940, 780), RAKHI, band=(5, 7), vline_idx=8, vline_label="Raksha Bandhan")
    G.text(d, (pts[0][0], pts[0][1] - 34), "0.62", G.mono(24), G.hx(G.MUTED), anchor="ma")
    G.text(d, (pts[5][0], pts[5][1] - 34), "0.67", G.mono(24), G.hx(G.STAMP_RED), anchor="ma")
    G.text(d, (pts[-1][0], pts[-1][1] + 22), "0.50", G.mono(24), G.hx(G.INK), anchor="ma")
    G.caveat_annotation(d, (560, 850), ["stuck at EXACTLY 0.6747", "for 3 days straight"], color=G.STAMP_RED, size=36,
                         arrow_to=(pts[6][0], pts[6][1] + 20))
    G.source_line(d, "SOURCE: SEARCH INTEREST INDEX (IN) · DAILY, AUG 20-29", y=980)
    G.footer(d, 2, 8)
    G.save(img, os.path.join(D3, "slide-2.png"))

def d3_s3():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["The receipt,", "day by day."], size=68, y=140)
    rows = [
        ("AUG 25", "0.6747", "flat"), ("AUG 26", "0.6747", "flat"), ("AUG 27", "0.6747", "flat"),
        ("AUG 28 (RAKHI)", "0.5360", "down"), ("AUG 29", "0.5032", "down"),
    ]
    strip, header_h, row_h = G.receipt_strip(680, rows, source_line="SOURCE: SEARCH INTEREST INDEX (IN) · 1 SIGNAL FAMILY")
    G.drop_shadow(img, 680, strip.height / G.SCALE, 566, 900, -3)
    G.rotate_paste(img, strip, 550, 890, -3)
    st = G.stamp("FROZEN", G.STAMP_RED, size=(300, 190), font_size=44)
    G.rotate_paste(img, st, 250, 800, -85)
    G.footer(d, 3, 8)
    G.save(img, os.path.join(D3, "slide-3.png"))

def d3_s4():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.text_block(d, ["3 DAYS."], y=430, size=180, weight=900, color=G.INK, align="center", font="anton")
    G.text_block(d, ["Same number, to the 4th decimal.", "That's not a trend holding steady —", "that's a source that stopped reporting."], y=760, align="center")
    G.footer(d, 4, 8)
    G.save(img, os.path.join(D3, "slide-4.png"))

def d3_s5():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["So we hard-coded", "two rules."], size=58, y=140)
    box = (60, 340, 1020, 900)
    G.card(d, box)
    items = [
        "Score identical to yesterday's? No movement words — a frozen input is a stalled source.",
        "Cited source not refreshed in 48h? No post about it at all. Fail closed.",
    ]
    G.checklist(d, (110, 420, 970, 800), items)
    G.text_block(d, ["Both live in the pipeline now,", "not in a style guide."], y=830, x=110, align="left", size=22, color=G.MUTED)
    G.footer(d, 5, 8)
    G.save(img, os.path.join(D3, "slide-5.png"))

def d3_s6():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["What happens", "when it wakes up."], size=62, y=140)
    box = (60, 340, 1020, 820)
    G.card(d, box)
    G.text_block(d, ["The moment the source refreshes,", "rakhi is back in the board like", "any other entity — no special", "treatment either direction."], y=420, x=110, align="left")
    G.footer(d, 6, 8)
    G.save(img, os.path.join(D3, "slide-6.png"))

def d3_s7():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["Building honest,", "not building fast."], size=58, y=180)
    G.text_block(d, ["An honest data account posts", "its boring failure modes too."], y=560)
    G.footer(d, 7, 8)
    G.save(img, os.path.join(D3, "slide-7.png"))

def d3_s8():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["Follow along."], size=90, y=200)
    G.text(d, (60, 380), "@trendgiri", G.mono(38), G.hx(G.STAMP_RED), anchor="la")
    st = G.stamp("HONEST", G.MARIGOLD, size=(280, 100), font_size=36)
    G.rotate_paste(img, st, 800, 850, -6)
    G.footer(d, 8, 8)
    G.save(img, os.path.join(D3, "slide-8.png"))

# ============================================================
# DECK 4 — QUOTE / SELLER WISDOM (new format, founder-requested 2026-08-29)
# ============================================================
D4 = os.path.join(OUT, "deck-4-seller-wisdom")

WISDOM = [
    ("MOST SELLERS FIND A TREND", "AFTER IT'S ALREADY PEAKED."),
    ("A TREND WITHOUT A", "REPEAT BUYER IS A SPIKE,", "NOT A BUSINESS."),
    ("THE BEST TIME TO CHECK", "A SIGNAL IS BEFORE", "IT'S OBVIOUS."),
    ("WE'D RATHER POST", "\"NOTHING MOVED\" THAN", "MAKE UP A REASON IT DID."),
]

def d4_hook():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.kicker(d, "Seller Wisdom · Aug 29")
    G.headline(d, ["4 THINGS WE'VE", "LEARNED WATCHING", "TRENDS ALL WEEK."], size=88, y=170)
    G.footer(d, 1, 6)
    G.save(img, os.path.join(D4, "slide-1.png"))

def d4_wisdom(idx, lines, page):
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, lines, size=92, y=340, lh=1.02)
    if idx == 3:
        st = G.stamp("HONEST", G.MARIGOLD, size=(260, 96), font_size=34)
        G.rotate_paste(img, st, 850, 950, -8)
    G.footer(d, page, 6)
    G.save(img, os.path.join(D4, f"slide-{page}.png"))

def d4_receipt_close():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["Every number we post", "has a source line", "under it."], size=64, y=160)
    box = (60, 560, 1020, 700)
    G.card(d, box)
    G.text_block(d, ["Ask any account that doesn't."], y=608, x=110, align="left", size=32)
    G.footer(d, 5, 6)
    G.save(img, os.path.join(D4, "slide-5.png"))

def d4_close():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["Follow for", "weekly receipts."], size=78, y=200)
    G.text(d, (60, 400), "@trendgiri", G.mono(38), G.hx(G.STAMP_RED), anchor="la")
    G.footer(d, 6, 6)
    G.save(img, os.path.join(D4, "slide-6.png"))

if __name__ == "__main__":
    for fn in [d1_s1, d1_s2, d1_s3, d1_s4, d1_s5, d1_s6, d1_s7, d1_s8]:
        fn()
    for fn in [d2_s1, d2_s2, d2_s3, d2_s4, d2_s5, d2_s6, d2_s7, d2_s8]:
        fn()
    for fn in [d3_s1, d3_s2, d3_s3, d3_s4, d3_s5, d3_s6, d3_s7, d3_s8]:
        fn()
    d4_hook()
    d4_wisdom(0, list(WISDOM[0]), 2)
    d4_wisdom(1, list(WISDOM[1]), 3)
    d4_wisdom(2, list(WISDOM[2]), 4)
    d4_receipt_close()
    d4_close()
    print("DONE")
