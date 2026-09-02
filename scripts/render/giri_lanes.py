# -*- coding: utf-8 -*-
"""New lane samples per Fable's niche/content strategy:
docs/consults/2026-08-29-group-cto-trendgiri-niche-and-content-strategy.md
Bazaar Bulletin (news), Seller Wisdom (rebuilt, broadened per the
10-theme taxonomy), Seller Playbook (how-to)."""
import os
import giri_system as G

OUT = r"C:\Users\2026\Documents\trend-signals-social\content\samples\2026-08-29-new-lanes"

# ============================================================
# LANE: BAZAAR BULLETIN (news) -- "GST parity flag + a quiet week, honestly"
# ============================================================
DB = os.path.join(OUT, "bazaar-bulletin-gst-parity")

def b_s1():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.kicker(d, "Bazaar Bulletin · Aug 29")
    G.headline(d, ["ONE STORY", "MATTERED THIS", "WEEK. HERE IT IS."], size=88, y=170)
    G.footer(d, 1, 6)
    G.save(img, os.path.join(DB, "slide-1.png"))

def b_s2():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["GST rules aren't", "the same for", "everyone."], size=64, y=140)
    box = (60, 400, 1020, 900)
    G.card(d, box)
    G.text_block(d, ["The India SME Forum flagged that GST",
                      "enforcement and rate treatment isn't uniform",
                      "across e-commerce platforms \u2014 small online",
                      "sellers carry a heavier compliance and", "liquidity load than large sellers on the",
                      "same marketplaces."], y=460, x=110, align="left")
    G.source_line(d, "SOURCE: BUSINESSWORLD, MAY 14 2026 \u00b7 INDIA SME FORUM", y=940)
    G.footer(d, 2, 6)
    G.save(img, os.path.join(DB, "slide-2.png"))

def b_s3():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["Why a seller", "cares."], size=76, y=180)
    box = (60, 420, 1020, 880)
    G.card(d, box)
    G.text_block(d, ["If you're a small seller, your GST", "compliance cost and cash-flow drag can",
                      "be proportionally heavier than a large", "seller's on the exact same platform \u2014",
                      "worth checking your own filing setup", "against this, not assuming it's fine."],
                  y=480, x=110, align="left", size=30)
    G.footer(d, 3, 6)
    G.save(img, os.path.join(DB, "slide-3.png"))

def b_s4():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["Honestly?", "A quiet week."], size=80, y=200)
    box = (60, 440, 1020, 900)
    G.card(d, box)
    G.text_block(d, ["We checked 3 verified outlets today.", "One story cleared our bar for \"a seller",
                      "should know this.\" We're not padding", "this out with 2 more that don't."],
                  y=500, x=110, align="left")
    st = G.stamp("HONEST", G.MARIGOLD, size=(260, 96), font_size=34)
    G.rotate_paste(img, st, 850, 780, -8)
    G.footer(d, 4, 6)
    G.save(img, os.path.join(DB, "slide-4.png"))

def b_s5():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["Check your own", "GST setup"], size=64, y=160)
    box = (60, 360, 1020, 820)
    G.card(d, box)
    items = [
        "Are you filing under the same slab treatment as large sellers on your platform?",
        "Does your platform pass rate changes to your listings automatically, or do you have to update manually?",
    ]
    G.checklist(d, (110, 420, 970, 770), items)
    G.footer(d, 5, 6)
    G.save(img, os.path.join(DB, "slide-5.png"))

def b_s6():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["Follow for", "what actually", "changes."], size=76, y=180)
    G.text(d, (60, 460), "@trendgiri", G.mono(38), G.hx(G.STAMP_RED), anchor="la")
    G.text_block(d, ["Send this to a seller who's still", "on the old GST setup."], y=560, align="left")
    G.footer(d, 6, 6)
    G.save(img, os.path.join(DB, "slide-6.png"))

# ============================================================
# LANE: SELLER WISDOM (rebuilt) -- broadened per the 10-theme taxonomy,
# NONE reference trend-watching mechanics (the founder's own correction)
# ============================================================
DW = os.path.join(OUT, "seller-wisdom-v2-pricing-and-rto")

def w_s1():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.kicker(d, "Seller Wisdom · Aug 29")
    G.headline(d, ["PRICE FOR THE", "RETURNS YOU", "ACTUALLY GET."], size=90, y=180)
    G.footer(d, 1, 6)
    G.save(img, os.path.join(DW, "slide-1.png"))

def w_s2():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["Not the return rate", "you hope for."], size=64, y=160)
    box = (60, 380, 1020, 900)
    G.card(d, box)
    G.text_block(d, ["Most sellers price on the margin they'd", "get with zero returns, then get surprised",
                      "when COD-and-RTO eats 15-20% of orders.", "", "Price for the return rate your category",
                      "actually runs, not the one that makes", "the spreadsheet look good."], y=440, x=110, align="left")
    G.footer(d, 2, 6)
    G.save(img, os.path.join(DW, "slide-2.png"))

def w_s3():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["Inventory judgment,", "not inventory hope."], size=56, y=160)
    box = (60, 380, 1020, 900)
    G.card(d, box)
    G.text_block(d, ["Stocking deep on a category because it", "moved once is how cash gets stuck.",
                      "", "A real mover repeats. A one-time spike", "doesn't. Wait for the second signal",
                      "before you commit inventory \u2014 whatever", "kind of signal you're watching."], y=440, x=110, align="left")
    G.footer(d, 3, 6)
    G.save(img, os.path.join(DW, "slide-3.png"))

def w_s4():
    img, d = G.new_canvas()
    G.draw_logo(d)
    st = G.stamp("FOCUS", G.MARIGOLD, size=(340, 130), font_size=56, outline_w=8)
    G.rotate_paste(img, st, 540, 430, -3)
    G.text_block(d, ["Consistency beats a burst.", "A solo seller who posts, restocks,",
                      "and replies every week for a year", "beats one who goes hard for a month",
                      "and disappears."], y=680, align="center")
    G.footer(d, 4, 6)
    G.save(img, os.path.join(DW, "slide-4.png"))

def w_s5():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["Owned audience is", "the only channel", "you can't lose."], size=54, y=150)
    box = (60, 420, 1020, 900)
    G.card(d, box)
    G.text_block(d, ["A marketplace can change its algorithm,", "its fees, or your visibility overnight.",
                      "", "A WhatsApp list or an Instagram", "following is yours \u2014 build it even",
                      "while the marketplace is working."], y=480, x=110, align="left")
    G.footer(d, 5, 6)
    G.save(img, os.path.join(DW, "slide-5.png"))

def w_s6():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["Follow for", "seller wisdom."], size=78, y=200)
    G.text(d, (60, 400), "@trendgiri", G.mono(38), G.hx(G.STAMP_RED), anchor="la")
    G.text_block(d, ["Which one hit closest to home?"], y=560, align="left", size=32)
    G.footer(d, 6, 6)
    G.save(img, os.path.join(DW, "slide-6.png"))

# ============================================================
# LANE: SELLER PLAYBOOK -- how-to depth, RTO cost math worked through
# ============================================================
DP = os.path.join(OUT, "seller-playbook-rto-cost-math")

def p_s1():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.kicker(d, "Seller Playbook · Aug 29")
    G.headline(d, ["WHAT A RETURN", "ACTUALLY COSTS", "YOU. MATH INSIDE."], size=76, y=170)
    G.footer(d, 1, 7)
    G.save(img, os.path.join(DP, "slide-1.png"))

def p_s2():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["The number sellers", "skip."], size=64, y=160)
    box = (60, 380, 1020, 850)
    G.card(d, box)
    G.text_block(d, ["Most sellers count a return as \"lost the", "sale.\" The real cost is bigger \u2014",
                      "forward shipping, reverse shipping,", "repackaging, and the item's damage risk",
                      "all stack on top of the lost margin."], y=440, x=110, align="left")
    G.footer(d, 2, 7)
    G.save(img, os.path.join(DP, "slide-2.png"))

def p_s3():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["The receipt,", "worked through."], size=62, y=150)
    rows = [
        ("PRODUCT PRICE", "₹599", "ink"),
        ("FORWARD SHIPPING", "₹49", "ink"),
        ("REVERSE SHIPPING (RTO)", "₹65", "ink"),
        ("REPACKAGING", "₹15", "ink"),
        ("DAMAGE RISK (EST.)", "₹30", "ink"),
        ("REAL COST OF ONE RETURN", "₹159", "down"),
    ]
    strip, header_h, row_h = G.receipt_strip(680, rows, title="EXAMPLE RECEIPT", source_line="ILLUSTRATIVE MATH \u00b7 SWAP IN YOUR OWN RATES", subhead="RTO COST BREAKDOWN")
    G.drop_shadow(img, 680, strip.height / G.SCALE, 566, 900, -2)
    G.rotate_paste(img, strip, 550, 890, -2)
    G.footer(d, 3, 7)
    G.save(img, os.path.join(DP, "slide-3.png"))

def p_s4():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.text_block(d, ["27%"], y=380, size=200, weight=900, color=G.STAMP_RED, align="center", font="anton")
    G.text_block(d, ["of a ₹599 sale, gone, on a single return.", "That's the number that should be in",
                      "your pricing model \u2014 not just the", "commission line."], y=720, align="center")
    G.footer(d, 4, 7)
    G.save(img, os.path.join(DP, "slide-4.png"))

def p_s5():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["Three ways to", "cut it down."], size=64, y=150)
    box = (60, 380, 1020, 900)
    G.card(d, box)
    items = [
        "Add 2-3 real size/fit photos — most RTOs on apparel are size mismatches, not damage.",
        "Call high-value COD orders before dispatch — a 30-second call cuts fake/impulse orders.",
        "Track RTO rate per pincode — some zones run 3x the average; price or exclude accordingly.",
    ]
    G.checklist(d, (110, 440, 970, 850), items)
    G.footer(d, 5, 7)
    G.save(img, os.path.join(DP, "slide-5.png"))

def p_s6():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["Save this before", "your next", "restock."], size=70, y=180)
    box = (60, 560, 1020, 900)
    G.card(d, box)
    G.text_block(d, ["Redo the math above with your own", "numbers before you price your next batch."], y=620, x=110, align="left")
    G.footer(d, 6, 7)
    G.save(img, os.path.join(DP, "slide-6.png"))

def p_s7():
    img, d = G.new_canvas()
    G.draw_logo(d)
    G.headline(d, ["Follow for", "seller playbooks."], size=68, y=200)
    G.text(d, (60, 400), "@trendgiri", G.mono(38), G.hx(G.STAMP_RED), anchor="la")
    st = G.stamp("SAVE THIS", G.MARKET_GREEN, size=(280, 100), font_size=34)
    G.rotate_paste(img, st, 820, 820, 7)
    G.footer(d, 7, 7)
    G.save(img, os.path.join(DP, "slide-7.png"))

if __name__ == "__main__":
    for fn in [b_s1, b_s2, b_s3, b_s4, b_s5, b_s6]:
        fn()
    for fn in [w_s1, w_s2, w_s3, w_s4, w_s5, w_s6]:
        fn()
    for fn in [p_s1, p_s2, p_s3, p_s4, p_s5, p_s6, p_s7]:
        fn()
    print("DONE — 19 slides across 3 new lanes")
